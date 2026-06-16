#!/usr/bin/env python3
import argparse
import csv
import importlib.util
import math
import random
import sys
from pathlib import Path

from kaggle_environments import make


def load_agent(path: str, module_suffix: str):
    p = Path(path)
    if p.is_dir():
        p = p / "main.py"
    p = p.resolve()
    for key in list(sys.modules):
        if key == "orbit_lite" or key.startswith("orbit_lite."):
            del sys.modules[key]
    sys.path.insert(0, str(p.parent))
    name = f"trace_actions_{module_suffix}_{abs(hash(str(p)))}"
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod.agent


def obs_get(obs, key, default=None):
    if isinstance(obs, dict):
        return obs.get(key, default)
    try:
        return obs[key]
    except Exception:
        return getattr(obs, key, default)


def planet_by_id(obs) -> dict[int, list]:
    return {int(p[0]): p for p in obs_get(obs, "planets", [])}


def nearest_target_id(obs, from_pid: int, angle: float, ships: float) -> int:
    planets = obs_get(obs, "planets", [])
    source = None
    for p in planets:
        if int(p[0]) == int(from_pid):
            source = p
            break
    if source is None:
        return -1
    sx, sy = float(source[2]), float(source[3])
    ux, uy = math.cos(float(angle)), math.sin(float(angle))
    best_pid = -1
    best_score = float("inf")
    for p in planets:
        pid = int(p[0])
        if pid == int(from_pid):
            continue
        vx, vy = float(p[2]) - sx, float(p[3]) - sy
        proj = vx * ux + vy * uy
        if proj <= 0:
            continue
        perp = abs(vx * uy - vy * ux)
        score = perp / max(float(p[4]), 1.0)
        if score < best_score:
            best_score = score
            best_pid = pid
    return best_pid if best_score <= 2.5 else -1


def make_recorder(agent, agent_label, rows, seed, swapped, slot):
    def wrapped(obs):
        step = int(obs_get(obs, "step", 0) or 0)
        player = int(obs_get(obs, "player", slot) or slot)
        planets_by_id = planet_by_id(obs)
        moves = agent(obs)
        for idx, move in enumerate(moves or []):
            if len(move) < 3:
                continue
            from_pid, angle, ships = move[:3]
            source = planets_by_id.get(int(from_pid))
            target_pid = nearest_target_id(obs, int(from_pid), float(angle), float(ships))
            target = planets_by_id.get(int(target_pid))
            rows.append({
                "seed": seed,
                "swapped": swapped,
                "slot": slot,
                "player": player,
                "agent": agent_label,
                "step": step,
                "move_idx": idx,
                "from_pid": int(from_pid),
                "angle": float(angle),
                "ships": float(ships),
                "source_owner": int(source[1]) if source else -99,
                "source_ships": float(source[5]) if source else -1.0,
                "source_radius": float(source[4]) if source else -1.0,
                "approx_target_pid": target_pid,
                "target_owner": int(target[1]) if target else -99,
                "target_ships": float(target[5]) if target else -1.0,
                "target_radius": float(target[4]) if target else -1.0,
            })
        return moves
    return wrapped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-a", required=True)
    ap.add_argument("--agent-b", required=True)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = []
    for seed_text in args.seeds.split(","):
        if not seed_text:
            continue
        seed = int(seed_text)
        for swapped in (False, True):
            random.seed(seed)
            a = load_agent(args.agent_a, f"a_{seed}_{int(swapped)}")
            b = load_agent(args.agent_b, f"b_{seed}_{int(swapped)}")
            if swapped:
                agents = [
                    make_recorder(b, "B", rows, seed, swapped, 0),
                    make_recorder(a, "A", rows, seed, swapped, 1),
                ]
            else:
                agents = [
                    make_recorder(a, "A", rows, seed, swapped, 0),
                    make_recorder(b, "B", rows, seed, swapped, 1),
                ]
            env = make("orbit_wars", debug=False, configuration={"randomSeed": seed})
            env.run(agents)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "seed", "swapped", "slot", "player", "agent", "step", "move_idx",
        "from_pid", "angle", "ships", "source_owner", "source_ships",
        "source_radius", "approx_target_pid", "target_owner", "target_ships",
        "target_radius",
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
