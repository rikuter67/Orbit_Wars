#!/usr/bin/env python3
import datetime as dt
import subprocess
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

ROOT = Path(__file__).resolve().parents[1]
COMP = 'orbit-wars'
JST = dt.timezone(dt.timedelta(hours=9))
LOG = ROOT / 'logs' / 'post_submit_audit_orbit.log'
SUBMISSION_LOG = ROOT / 'SUBMISSION_LOG.md'


def log(msg: str) -> None:
    ts = dt.datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S %Z')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def snapshot() -> str:
    p = subprocess.run(
        ['python3', str(ROOT / 'scripts' / 'snapshot_orbit_status.py')],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=240,
    )
    output = p.stdout.strip()
    log(f'snapshot rc={p.returncode}; output={output[:1000]}')
    return output.splitlines()[-1] if p.returncode == 0 and output else f'FAILED rc={p.returncode}'


def fmt(row) -> str:
    return (
        f'ref `{row.ref}` file `{row.file_name}` status `{row.status}` '
        f'score `{row.public_score}` desc `{row.description}`'
    )


def main() -> int:
    api = KaggleApi()
    api.authenticate()
    rows = api.competition_submissions(COMP)[:4]
    snap = snapshot()

    now = dt.datetime.now(JST).strftime('%Y-%m-%d %H:%M JST')
    latest = rows[0] if rows else None
    second = rows[1] if len(rows) > 1 else None
    if latest is None:
        line = f'- {now}: post-submit audit found no submission rows. Snapshot: `{snap}`.'
    else:
        latest_text = fmt(latest)
        second_text = fmt(second) if second is not None else 'none'
        line = (
            f'- {now}: post-submit audit snapshot `{snap}`. '
            f'latest1 is {latest_text}; latest2 is {second_text}. '
            'No submission was made by this audit.'
        )
    log(line)
    with SUBMISSION_LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
