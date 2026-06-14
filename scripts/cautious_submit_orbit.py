#!/usr/bin/env python3
import datetime as dt
import fcntl
import subprocess
import sys
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

ROOT = Path('/mnt/c/Users/rikuter/kaggle/Orbit_Wars')
COMP = 'orbit-wars'
JST = dt.timezone(dt.timedelta(hours=9))
SUBMIT_LOCK = ROOT / 'logs' / 'submit.lock'
LOG = ROOT / 'logs' / 'cautious_submit_orbit.log'
MIN_SUBMIT_GAP = dt.timedelta(hours=3)
MIN_PRODUCER_SAFETY_SCORE_FOR_EXPERIMENT = 1150.0

CANDIDATES = {
    'producer_v2': (
        ROOT / 'submissions' / 'slawek_producer_v2_20260613.tar.gz',
        'cautious latest2 producer_v2 20260613 one-shot',
    ),
    'producer_v2_refresh': (
        ROOT / 'submissions' / 'slawek_producer_v2_20260613.tar.gz',
        'cautious latest2 producer_v2 safety refresh 20260614',
    ),
    'reyhan20': (
        ROOT / 'submissions' / 'reyhan_selfcheck20_0_20260613.tar.gz',
        'cautious latest2 reyhan 20勝0敗 selfcheck20-0 localKuni6-0 20260613',
    ),
    'hybrid_reyhan2p_producer4p': (
        ROOT / 'submissions' / 'hybrid_reyhan2p_producer4p_20260613.tar.gz',
        'cautious latest2 hybrid reyhan2p 20勝0敗 selfcheck20-0 producer4p 20260613',
    ),
    'roman_smarter': (
        ROOT / 'submissions' / 'roman_smarter_20260613.tar.gz',
        'cautious latest2 roman_smarter localKuni5-1 20260613',
    ),
    'producer_ffa_guard': (
        ROOT / 'submissions' / 'producer_ffa_guard_20260614.tar.gz',
        'cautious latest2 producer_ffa_guard local2p10-6vsProducer ffaTop2-16of16 20260614',
    ),
    'h18_2ponly': (
        ROOT / 'submissions' / 'h18_roi13_beta18_2ponly_20260614.tar.gz',
        'cautious latest2 h18_2ponly local2p17-11vsProducer poolBetter exact4p 20260614',
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

        latest2 = rows[:2]
        for idx, row in enumerate(latest2, start=1):
            log(
                f'latest{idx}: ref={row.ref} file={row.file_name} '
                f'status={row.status} score={row.public_score} desc={row.description!r}'
            )
            if 'PENDING' in str(row.status):
                log(f'{name}: latest{idx} is pending; aborting to preserve latest-2 evaluation')
                return 1

        if name == 'producer_ffa_guard':
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
