#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


JST = dt.timezone(dt.timedelta(hours=9))
SNAPSHOT_RE = re.compile(r"snapshot_(\d{8})_(\d{6})")
ROW_RE = re.compile(
    r"^\|\s*(?P<ref>\d+)\s*\|.*?`(?P<file>[^`]+)`.*?\|\s*SubmissionStatus\.(?P<status>[A-Z_]+)\s*\|\s*(?P<score>[^|]+?)\s*\|",
)


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.strptime(value, "%Y-%m-%d %H:%M")
    return parsed.replace(tzinfo=JST)


def snapshot_time(path: Path) -> dt.datetime | None:
    match = SNAPSHOT_RE.search(str(path))
    if not match:
        return None
    day, clock = match.groups()
    try:
        return dt.datetime.strptime(f"{day}{clock}", "%Y%m%d%H%M%S").replace(tzinfo=JST)
    except ValueError:
        return None


def parse_score(raw: str) -> float | None:
    try:
        return float(raw.strip())
    except ValueError:
        return None


def latest_score(root: Path, ref: str) -> tuple[float | None, Path | None]:
    rows: list[tuple[dt.datetime, float, Path]] = []
    for path in root.glob("logs/snapshot_*/status.md"):
        ts = snapshot_time(path)
        if ts is None:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = ROW_RE.match(line)
            if not match or match.group("ref") != ref:
                continue
            score = parse_score(match.group("score"))
            if score is not None:
                rows.append((ts, score, path))
            break
    if not rows:
        return None, None
    _, score, path = max(rows, key=lambda row: row[0])
    return score, path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--candidate-ref", default="53734299")
    parser.add_argument("--baseline-ref", default="53714957")
    parser.add_argument("--not-before", default="2026-06-16 18:47")
    parser.add_argument("--material-gap", type=float, default=35.0)
    args = parser.parse_args()

    root = Path(args.root)
    now = dt.datetime.now(JST)
    not_before = parse_time(args.not_before)
    cand_score, cand_path = latest_score(root, args.candidate_ref)
    base_score, base_path = latest_score(root, args.baseline_ref)

    print(f"now_jst={now:%Y-%m-%d %H:%M:%S %Z}")
    print(f"not_before={not_before:%Y-%m-%d %H:%M:%S %Z}")
    print(f"candidate_ref={args.candidate_ref} score={cand_score} source={cand_path}")
    print(f"baseline_ref={args.baseline_ref} score={base_score} source={base_path}")

    blockers: list[str] = []
    if now < not_before:
        blockers.append(f"time gate: now < {not_before:%Y-%m-%d %H:%M:%S %Z}")
    if cand_score is None or base_score is None:
        blockers.append("missing candidate or baseline score")
    elif cand_score >= base_score - args.material_gap:
        blockers.append(
            f"candidate not materially below baseline: {cand_score:.1f} >= {base_score - args.material_gap:.1f}"
        )

    if blockers:
        print("restore_readiness=NO")
        for blocker in blockers:
            print(f"- {blocker}")
    else:
        print("restore_readiness=YES_AFTER_CONVERGENCE_CHECK")
        print("- run convergence_report_orbit.py and cautious_submit_orbit.py h19_safety_restore")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
