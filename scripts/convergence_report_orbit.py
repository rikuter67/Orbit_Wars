#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path


SNAPSHOT_RE = re.compile(r"snapshot_(\d{8})_(\d{6})")
ROW_RE = re.compile(
    r"^\|\s*(?P<ref>\d+)\s*\|.*?\|\s*SubmissionStatus\.(?P<status>[A-Z_]+)\s*\|\s*(?P<score>[^|]+?)\s*\|",
)


@dataclass(frozen=True)
class ScorePoint:
    stamp: str
    time: dt.datetime | None
    path: Path
    status: str
    score: float | None


def parse_score(raw: str) -> float | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def snapshot_stamp(path: Path) -> str:
    match = SNAPSHOT_RE.search(str(path))
    if not match:
        return path.parent.name
    day, clock = match.groups()
    return f"{day[:4]}-{day[4:6]}-{day[6:]} {clock[:2]}:{clock[2:4]}:{clock[4:]}"


def snapshot_time(path: Path) -> dt.datetime | None:
    match = SNAPSHOT_RE.search(str(path))
    if not match:
        return None
    day, clock = match.groups()
    try:
        return dt.datetime.strptime(f"{day}{clock}", "%Y%m%d%H%M%S")
    except ValueError:
        return None


def load_points(root: Path, ref: str) -> list[ScorePoint]:
    points: list[ScorePoint] = []
    for path in sorted(root.glob("logs/snapshot_*/status.md")):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            match = ROW_RE.match(line)
            if not match or match.group("ref") != ref:
                continue
            points.append(
                ScorePoint(
                    stamp=snapshot_stamp(path),
                    time=snapshot_time(path),
                    path=path,
                    status=match.group("status"),
                    score=parse_score(match.group("score")),
                )
            )
            break
    return points


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ref", help="Kaggle submission ref to inspect")
    parser.add_argument("--root", default=".", help="repo root containing logs/snapshot_*")
    parser.add_argument("--window", type=int, default=5, help="recent scored points to summarize")
    parser.add_argument("--max-spread", type=float, default=8.0, help="spread threshold for stable")
    parser.add_argument("--min-age-points", type=int, default=5, help="minimum scored points for stable")
    parser.add_argument(
        "--min-age-minutes",
        type=float,
        default=180.0,
        help="minimum time from first scored snapshot to latest scored snapshot for stable",
    )
    parser.add_argument(
        "--min-recent-span-minutes",
        type=float,
        default=45.0,
        help="minimum time span covered by the recent window for stable",
    )
    args = parser.parse_args()

    root = Path(args.root)
    points = load_points(root, args.ref)
    if not points:
        print(f"ref {args.ref}: no snapshot rows found")
        return 1

    scored = [p for p in points if p.score is not None]
    print(f"ref {args.ref}: {len(points)} snapshots, {len(scored)} scored")
    for p in points:
        score = "" if p.score is None else f"{p.score:.1f}"
        print(f"{p.stamp}  status={p.status:<8} score={score:<8}  {p.path}")

    recent = scored[-max(1, args.window):]
    if not recent:
        print("decision: NOT_CONVERGED no scored points yet")
        return 0

    values = [float(p.score) for p in recent if p.score is not None]
    spread = max(values) - min(values)
    scored_times = [p.time for p in scored if p.time is not None]
    recent_times = [p.time for p in recent if p.time is not None]
    age_minutes = (
        (max(scored_times) - min(scored_times)).total_seconds() / 60.0
        if len(scored_times) >= 2 else 0.0
    )
    recent_span_minutes = (
        (max(recent_times) - min(recent_times)).total_seconds() / 60.0
        if len(recent_times) >= 2 else 0.0
    )
    print(
        f"recent{len(values)}: min={min(values):.1f} max={max(values):.1f} "
        f"last={values[-1]:.1f} spread={spread:.1f}"
    )
    print(
        f"time: scored_age={age_minutes:.1f}m recent_span={recent_span_minutes:.1f}m "
        f"required_age={args.min_age_minutes:.1f}m required_recent_span={args.min_recent_span_minutes:.1f}m"
    )

    if len(scored) < args.min_age_points:
        print(f"decision: NOT_CONVERGED only {len(scored)} scored points")
    elif age_minutes < args.min_age_minutes:
        print(f"decision: NOT_CONVERGED scored age {age_minutes:.1f}m < {args.min_age_minutes:.1f}m")
    elif recent_span_minutes < args.min_recent_span_minutes:
        print(
            "decision: NOT_CONVERGED "
            f"recent span {recent_span_minutes:.1f}m < {args.min_recent_span_minutes:.1f}m"
        )
    elif spread > args.max_spread:
        print(f"decision: NOT_CONVERGED spread {spread:.1f} > {args.max_spread:.1f}")
    else:
        print(f"decision: STABLE spread {spread:.1f} <= {args.max_spread:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
