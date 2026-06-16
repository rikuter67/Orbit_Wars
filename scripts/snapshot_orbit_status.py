#!/usr/bin/env python3
import csv
import datetime as dt
import subprocess
import zipfile
import shutil
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

ROOT = Path(__file__).resolve().parents[1]
KAGGLE = shutil.which("kaggle") or str(Path.home() / ".local" / "bin" / "kaggle")
COMP = 'orbit-wars'
JST = dt.timezone(dt.timedelta(hours=9))


def run(cmd, timeout=180):
    return subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)


def main() -> int:
    ts = dt.datetime.now(JST).strftime('%Y%m%d_%H%M%S')
    out_dir = ROOT / 'logs' / f'snapshot_{ts}'
    suffix = 1
    while out_dir.exists():
        out_dir = ROOT / 'logs' / f'snapshot_{ts}_{suffix}'
        suffix += 1
    out_dir.mkdir(parents=True, exist_ok=False)
    report = out_dir / 'status.md'

    api = KaggleApi()
    api.authenticate()
    submissions = api.competition_submissions(COMP)[:12]

    lines = [
        f'# Orbit Wars Snapshot {ts}',
        '',
        '## Submissions',
        '',
        '| ref | file | date | description | status | score | error |',
        '|---|---|---|---|---|---:|---|',
    ]
    for s in submissions:
        lines.append(
            f'| {s.ref} | `{s.file_name}` | {s.date} | {s.description} | {s.status} | {s.public_score} | {s.error_description} |'
        )

    lb_dir = out_dir / 'leaderboard'
    lb_dir.mkdir()
    p = run([KAGGLE, 'competitions', 'leaderboard', COMP, '-d', '-p', str(lb_dir), '-q'], timeout=180)
    lines += ['', '## Leaderboard Download', '', f'```text\n{p.stdout.strip()[:2000]}\n```']

    zip_path = lb_dir / 'orbit-wars.zip'
    if zip_path.exists():
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(lb_dir)
        csv_files = sorted(lb_dir.glob('*.csv'))
        if csv_files:
            rows = list(csv.DictReader(csv_files[0].open(encoding='utf-8-sig')))
            target = None
            for idx, row in enumerate(rows, start=1):
                if row.get('TeamName') == 'rikuter67' or 'rikuter67' in row.get('TeamMemberUserNames', ''):
                    target = (idx, row)
                    break
            lines += ['', '## Team Rank', '']
            if target:
                idx, row = target
                pct = 100.0 * idx / max(1, len(rows))
                lines.append(f'- rank: {idx}/{len(rows)} ({pct:.2f}%)')
                lines.append(f'- score: {row.get("Score")}')
                lines.append(f'- submissionDate: {row.get("LastSubmissionDate")}')
            else:
                lines.append('- `rikuter67` not found in downloaded leaderboard.')

            lines += ['', '## Cut Lines', '']
            for pct in (1, 2, 3, 5, 10, 20):
                cutoff_idx = max(1, int(len(rows) * pct / 100)) - 1
                row = rows[cutoff_idx]
                lines.append(
                    f'- top {pct}%: rank {cutoff_idx + 1}, score {row.get("Score")}, team {row.get("TeamName")}'
                )

    report.write_text('\n'.join(lines) + '\n')
    print(report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
