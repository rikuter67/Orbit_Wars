#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path


JST = dt.timezone(dt.timedelta(hours=9))
SNAPSHOT_RE = re.compile(r"snapshot_(\d{8})_(\d{6})")
ROW_RE = re.compile(
    r"^\|\s*(?P<ref>\d+)\s*\|.*?\|\s*SubmissionStatus\.(?P<status>[A-Z_]+)\s*\|\s*(?P<score>[^|]+?)\s*\|",
)


@dataclass(frozen=True)
class ScorePoint:
    time: dt.datetime
    score: float
    path: Path


def snapshot_time(path: Path) -> dt.datetime | None:
    match = SNAPSHOT_RE.search(str(path))
    if not match:
        return None
    day, clock = match.groups()
    try:
        parsed = dt.datetime.strptime(f"{day}{clock}", "%Y%m%d%H%M%S")
    except ValueError:
        return None
    return parsed.replace(tzinfo=JST)


def parse_score(raw: str) -> float | None:
    try:
        return float(raw.strip())
    except ValueError:
        return None


def load_scored_points(root: Path, ref: str) -> list[ScorePoint]:
    points: list[ScorePoint] = []
    for path in sorted(root.glob("logs/snapshot_*/status.md")):
        ts = snapshot_time(path)
        if ts is None:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = ROW_RE.match(line)
            if not match or match.group("ref") != ref:
                continue
            if match.group("status") != "COMPLETE":
                break
            score = parse_score(match.group("score"))
            if score is not None:
                points.append(ScorePoint(time=ts, score=score, path=path))
            break
    return points


def fmt(ts: dt.datetime) -> str:
    return ts.astimezone(JST).strftime("%Y-%m-%d %H:%M:%S %Z")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ref", help="Kaggle submission ref to inspect")
    parser.add_argument("--root", default=".")
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--max-spread", type=float, default=8.0)
    parser.add_argument("--min-recent-span-minutes", type=float, default=45.0)
    parser.add_argument("--now", default="", help="override current JST time, e.g. 2026-06-16T19:30:00")
    args = parser.parse_args()

    root = Path(args.root)
    points = load_scored_points(root, args.ref)
    if not points:
        print(f"ref={args.ref} no scored points")
        return 1

    now = (
        dt.datetime.fromisoformat(args.now).replace(tzinfo=JST)
        if args.now else dt.datetime.now(JST)
    )
    window = max(1, args.window)
    recent = points[-window:]
    values = [p.score for p in recent]
    spread = max(values) - min(values)
    span = (recent[-1].time - recent[0].time).total_seconds() / 60.0 if len(recent) >= 2 else 0.0

    # If one new snapshot is taken now, the convergence script's next recent window
    # will be the last window-1 existing points plus the new snapshot.
    projected_base = points[-(window - 1):] if window > 1 else []
    if projected_base:
        next_earliest = projected_base[0].time + dt.timedelta(minutes=args.min_recent_span_minutes)
        projected_span_now = (now - projected_base[0].time).total_seconds() / 60.0
    else:
        next_earliest = now
        projected_span_now = 0.0

    print(f"ref={args.ref}")
    print(f"now={fmt(now)}")
    print(f"last_snapshot={fmt(points[-1].time)} score={points[-1].score:.1f} path={points[-1].path}")
    print(
        f"current_recent{len(recent)}: first={fmt(recent[0].time)} last={fmt(recent[-1].time)} "
        f"span={span:.1f}m spread={spread:.1f} max_spread={args.max_spread:.1f}"
    )
    print(
        f"if_snapshot_now: projected_first={fmt(projected_base[0].time) if projected_base else 'n/a'} "
        f"projected_span={projected_span_now:.1f}m required={args.min_recent_span_minutes:.1f}m"
    )
    print(f"next_useful_snapshot_at_or_after={fmt(next_earliest)}")

    if now < next_earliest:
        wait = (next_earliest - now).total_seconds() / 60.0
        print(f"recommendation=WAIT {wait:.1f}m")
    elif spread > args.max_spread:
        print("recommendation=SNAPSHOT_ALLOWED_BUT_SPREAD_WAS_HIGH")
    else:
        print("recommendation=SNAPSHOT_ALLOWED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
