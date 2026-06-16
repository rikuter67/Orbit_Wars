#!/usr/bin/env python3
import datetime as dt
import fcntl
import re
import subprocess
import sys
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

ROOT = Path(__file__).resolve().parents[1]
COMP = 'orbit-wars'
JST = dt.timezone(dt.timedelta(hours=9))
SUBMIT_LOCK = ROOT / 'logs' / 'submit.lock'
LOG = ROOT / 'logs' / 'cautious_submit_orbit.log'
MIN_SUBMIT_GAP = dt.timedelta(hours=3)
MIN_PRODUCER_SAFETY_SCORE_FOR_EXPERIMENT = 1150.0
CONVERGENCE_WINDOW = dt.timedelta(minutes=100)
CONVERGENCE_MIN_POINTS = 3
CONVERGENCE_MIN_SPAN = dt.timedelta(minutes=45)
CONVERGENCE_MAX_SPREAD = 35.0

CANDIDATES = {
    'producer_v2': (
        ROOT / 'submissions' / 'slawek_producer_v2_20260613.tar.gz',
        'ProducerV2 baseline | original public code | latest2 safety | 20260613',
    ),
    'producer_v2_refresh': (
        ROOT / 'submissions' / 'slawek_producer_v2_20260613.tar.gz',
        'ProducerV2 baseline refresh | no code change | latest2 safety | 20260614',
    ),
    'reyhan20': (
        ROOT / 'submissions' / 'reyhan_selfcheck20_0_20260613.tar.gz',
        'Reyhan public clone | 2P selfcheck 20勝0敗 | local Kuni 6-0 | 20260613',
    ),
    'hybrid_reyhan2p_producer4p': (
        ROOT / 'submissions' / 'hybrid_reyhan2p_producer4p_20260613.tar.gz',
        'Hybrid | Reyhan 2P 20勝0敗 + ProducerV2 4P | cautious FFA route | 20260613',
    ),
    'roman_smarter': (
        ROOT / 'submissions' / 'roman_smarter_20260613.tar.gz',
        'Roman smarter public clone | local Kuni 5-1 | exploratory | 20260613',
    ),
    'producer_ffa_guard': (
        ROOT / 'submissions' / 'producer_ffa_guard_20260614.tar.gz',
        'ProducerV2 variant | FFA guard tuning | 2P 10-6 vs Producer | FFA top2 16/16 | 20260614',
    ),
    'h18_2ponly': (
        ROOT / 'submissions' / 'h18_roi13_beta18_2ponly_20260614.tar.gz',
        'ProducerV2 2P-only variant | H18 ROI1.3 beta1.8 | 17-11 vs Producer | exact 4P | 20260614',
    ),
    'h19_safety_restore': (
        ROOT / 'submissions' / 'h19_s14t14_2ponly_producer4p_20260614.tar.gz',
        'H19 safety restore | ROI1.6 beta2.4 S14T14 | 2P h19 stable 1241.9 before highfast85 | 4P Producer exact | 20260616',
    ),
    'highfast85': (
        ROOT / 'submissions' / 'highfast85_producer_gate_20260616.tar.gz',
        'H19 highfast85 Producer-gate | 2P switch to Producer when best_fast>=85 | iso127-138 h19 14-6-4 Producer 12-10-2 oldv2 14-10 Kuni6-2 Carbon6-2 | 4P unchanged | 20260616',
    ),
}


def log(msg: str) -> None:
    ts = dt.datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S %Z')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def parse_kaggle_date(value) -> dt.datetime:
    if isinstance(value, dt.datetime):
        parsed = value
    else:
        parsed = dt.datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(JST)


def score_float(value) -> float | None:
    text = str(value or '').strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def snapshot_time(path: Path) -> dt.datetime | None:
    match = re.search(r'snapshot_(\d{8})_(\d{6})', str(path))
    if not match:
        return None
    try:
        parsed = dt.datetime.strptime(''.join(match.groups()), '%Y%m%d%H%M%S')
    except ValueError:
        return None
    return parsed.replace(tzinfo=JST)


def score_from_status(path: Path, ref: str) -> float | None:
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        return None
    pattern = re.compile(
        rf'^\|\s*{re.escape(str(ref))}\s*\|.*\|\s*SubmissionStatus\.COMPLETE\s*\|\s*([0-9.]+)\s*\|',
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return None
    return score_float(match.group(1))


def score_has_converged(ref: str, current_score: float | None) -> bool:
    now = dt.datetime.now(JST)
    samples: list[tuple[dt.datetime, float]] = []
    for status in (ROOT / 'logs').glob('snapshot_*/status.md'):
        ts = snapshot_time(status)
        if ts is None or now - ts > CONVERGENCE_WINDOW:
            continue
        score = score_from_status(status, ref)
        if score is not None:
            samples.append((ts, score))
    if current_score is not None:
        samples.append((now, current_score))

    dedup: dict[str, tuple[dt.datetime, float]] = {}
    for ts, score in samples:
        dedup[ts.strftime('%Y%m%d%H%M%S')] = (ts, score)
    samples = sorted(dedup.values(), key=lambda item: item[0])

    if len(samples) < CONVERGENCE_MIN_POINTS:
        log(
            f'latest score convergence not proven for ref={ref}: '
            f'{len(samples)} samples < {CONVERGENCE_MIN_POINTS}'
        )
        return False
    span = samples[-1][0] - samples[0][0]
    scores = [score for _, score in samples]
    spread = max(scores) - min(scores)
    detail = ', '.join(f'{ts:%H:%M}={score:.1f}' for ts, score in samples)
    log(
        f'latest score convergence samples for ref={ref}: '
        f'span={span}, spread={spread:.1f}, points=[{detail}]'
    )
    if span < CONVERGENCE_MIN_SPAN:
        log(f'latest score convergence not proven: span {span} < {CONVERGENCE_MIN_SPAN}')
        return False
    if spread > CONVERGENCE_MAX_SPREAD:
        log(
            f'latest score convergence not proven: '
            f'spread {spread:.1f} > {CONVERGENCE_MAX_SPREAD}'
        )
        return False
    return True


def snapshot(label: str) -> None:
    p = subprocess.run(
        ['python3', str(ROOT / 'scripts' / 'snapshot_orbit_status.py')],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=240,
    )
    log(f'{label}: snapshot rc={p.returncode}; output={p.stdout.strip()[:1000]}')


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CANDIDATES:
        print(f'usage: {Path(sys.argv[0]).name} {"|".join(CANDIDATES)}', file=sys.stderr)
        return 2

    name = sys.argv[1]
    path, message = CANDIDATES[name]
    if not path.exists():
        log(f'{name}: missing archive {path}')
        return 1

    SUBMIT_LOCK.parent.mkdir(parents=True, exist_ok=True)
    with SUBMIT_LOCK.open('w') as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log(f'{name}: submit lock is held; aborting')
            return 1

        api = KaggleApi()
        api.authenticate()
        rows = api.competition_submissions(COMP)[:10]
        now = dt.datetime.now(JST)
        latest = rows[0] if rows else None
        if latest is not None:
            latest_jst = parse_kaggle_date(latest.date)
            gap = now - latest_jst
            log(
                f'latest before submit: ref={latest.ref} file={latest.file_name} '
                f'date_jst={latest_jst:%Y-%m-%d %H:%M:%S %Z} '
                f'status={latest.status} score={latest.public_score} desc={latest.description!r}'
            )
            if gap < MIN_SUBMIT_GAP:
                log(f'{name}: last submission was {gap} ago, below {MIN_SUBMIT_GAP}; aborting')
                return 1
            if not score_has_converged(str(latest.ref), score_float(latest.public_score)):
                log(f'{name}: latest submission score is not converged; aborting')
                return 1

        latest2 = rows[:2]
        for idx, row in enumerate(latest2, start=1):
            log(
                f'latest{idx}: ref={row.ref} file={row.file_name} '
                f'status={row.status} score={row.public_score} desc={row.description!r}'
            )
            if 'PENDING' in str(row.status):
                log(f'{name}: latest{idx} is pending; aborting to preserve latest-2 evaluation')
                return 1

        if name in {'producer_ffa_guard', 'h19_s14t14_2ponly'}:
            producer_rows = [
                row for row in latest2
                if row.file_name == 'slawek_producer_v2_20260613.tar.gz'
            ]
            if not producer_rows:
                log(f'{name}: no Producer safety row in latest2; aborting')
                return 1
            scored = [
                float(row.public_score)
                for row in producer_rows
                if str(row.public_score or '').strip()
            ]
            if not scored:
                log(f'{name}: Producer safety row has no public score yet; aborting')
                return 1
            best_score = max(scored)
            if best_score < MIN_PRODUCER_SAFETY_SCORE_FOR_EXPERIMENT:
                log(
                    f'{name}: Producer safety score {best_score} below '
                    f'{MIN_PRODUCER_SAFETY_SCORE_FOR_EXPERIMENT}; aborting'
                )
                return 1

        snapshot('before-submit')
        log(f'{name}: submitting archive={path} message={message!r}')
        try:
            api.competition_submit(str(path), message, COMP, quiet=False)
        except Exception as exc:
            log(f'{name}: submit call failed: {type(exc).__name__}: {exc}')
            snapshot('after-submit-failure')
            return 1
        log(f'{name}: submit call returned')
        snapshot('after-submit')
        log(f'{name}: done; do not submit another candidate for at least 3 hours')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
