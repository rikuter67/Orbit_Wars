#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import tempfile
from pathlib import Path

from kaggle_environments import make


def _agent_root(path: str) -> Path:
    p = Path(path)
    if p.is_file():
        return p.parent
    return p


def _copy_agent(path: str, dst_parent: Path, label: str) -> str:
    src_root = _agent_root(path)
    dst_root = dst_parent / label

    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {n for n in names if n == "__pycache__" or n.endswith(".pyc")}

    shutil.copytree(src_root, dst_root, ignore=ignore)

    pkg_name = f"orbit_lite_{label}"
    old_pkg = dst_root / "orbit_lite"
    if old_pkg.exists():
        old_pkg.rename(dst_root / pkg_name)
        for py in dst_root.rglob("*.py"):
            text = py.read_text()
            text = text.replace("from orbit_lite.", f"from {pkg_name}.")
            text = text.replace("import orbit_lite.", f"import {pkg_name}.")
            text = text.replace("from orbit_lite import", f"from {pkg_name} import")
            text = text.replace("import orbit_lite", f"import {pkg_name}")
            py.write_text(text)

    p = Path(path)
    if p.is_file():
        rel = p.relative_to(src_root)
        return str(dst_root / rel)
    return str(dst_root / "main.py")


def _safe_label(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def run_game(agent_paths: list[str], seed: int, prefix: str):
    random.seed(int(seed))
    with tempfile.TemporaryDirectory(prefix=f"orbit_eval_{prefix}_") as td:
        root = Path(td)
        copied = [
            _copy_agent(path, root, f"{_safe_label(prefix)}_a{i}_{_safe_label(Path(path).parent.name)}")
            for i, path in enumerate(agent_paths)
        ]
        env = make("orbit_wars", debug=False, configuration={"randomSeed": int(seed)})
        final = env.run(copied)[-1]
    return [s.get("reward") for s in final], [s.get("status") for s in final]


def pair_score(candidate: str, opponent: str, seeds: list[int], label: str):
    wins = losses = ties = errors = 0
    rows = []
    diff_sum = 0.0
    for seed in seeds:
        for swapped in (False, True):
            paths = [opponent, candidate] if swapped else [candidate, opponent]
            try:
                rewards, statuses = run_game(paths, seed, f"{label}_{seed}_{int(swapped)}")
                cr = rewards[1] if swapped else rewards[0]
                or_ = rewards[0] if swapped else rewards[1]
                diff = (cr or 0) - (or_ or 0)
                if diff > 0:
                    wins += 1
                    outcome = "W"
                elif diff < 0:
                    losses += 1
                    outcome = "L"
                else:
                    ties += 1
                    outcome = "T"
                diff_sum += diff
                rows.append({
                    "seed": seed,
                    "swapped": swapped,
                    "candidate": cr,
                    "opponent": or_,
                    "diff": diff,
                    "outcome": outcome,
                    "statuses": statuses,
                })
            except Exception as exc:
                errors += 1
                rows.append({"seed": seed, "swapped": swapped, "error": repr(exc)})
    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "errors": errors,
        "diff_sum": diff_sum,
        "rows": rows,
    }


def ffa_score(candidate: str, opponents: list[str], seeds: list[int], label: str):
    wins = top2 = losses = errors = 0
    rows = []
    for seed in seeds:
        for slot in range(4):
            paths = list(opponents)
            paths.insert(slot, candidate)
            paths = paths[:4]
            try:
                rewards, statuses = run_game(paths, seed, f"{label}_{seed}_{slot}")
                cr = rewards[slot]
                rank = 1 + sum((r or 0) > (cr or 0) for r in rewards)
                if rank == 1:
                    wins += 1
                if rank <= 2:
                    top2 += 1
                else:
                    losses += 1
                rows.append({
                    "seed": seed,
                    "slot": slot,
                    "candidate": cr,
                    "rank": rank,
                    "rewards": rewards,
                    "statuses": statuses,
                })
            except Exception as exc:
                errors += 1
                rows.append({"seed": seed, "slot": slot, "error": repr(exc)})
    return {"wins": wins, "top2": top2, "losses": losses, "errors": errors, "rows": rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", action="append", required=True, help="name=path")
    ap.add_argument("--opponent", action="append", default=[], help="name=path for pair eval")
    ap.add_argument("--ffa-opponents", default="", help="comma-separated paths, exactly 3 for 4p eval")
    ap.add_argument("--seeds", default="1,2")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    seeds = [int(x) for x in args.seeds.split(",") if x]
    candidates = [x.split("=", 1) for x in args.candidate]
    opponents = [x.split("=", 1) for x in args.opponent]
    ffa_opponents = [x for x in args.ffa_opponents.split(",") if x]

    out = []
    for cname, cpath in candidates:
        item = {
            "candidate": cname,
            "path": cpath,
            "seeds": seeds,
            "mode": "path_isolated",
            "isolation": "renamed orbit_lite package per agent copy",
        }
        if opponents:
            item["pairs"] = {}
            for oname, opath in opponents:
                item["pairs"][oname] = pair_score(cpath, opath, seeds, f"{cname}_{oname}")
        if ffa_opponents:
            item["ffa"] = ffa_score(cpath, ffa_opponents, seeds, cname)
        out.append(item)
        print(json.dumps(item, sort_keys=True), flush=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
