#!/usr/bin/env python3
import argparse
import csv
import importlib.util
import random
import sys
from pathlib import Path

from kaggle_environments import make


def load_agent(path: str):
    p = Path(path)
    if p.is_dir():
        p = p / "main.py"
    p = p.resolve()
    for key in list(sys.modules):
        if key == "orbit_lite" or key.startswith("orbit_lite."):
            del sys.modules[key]
    sys.path.insert(0, str(p.parent))
    name = "trace_agent_" + str(abs(hash(str(p))))
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod.agent


def obs_dict(state):
    obs = state.observation
    if isinstance(obs, dict):
        return obs
    return {key: obs[key] for key in obs}


def owner_stats(obs):
    stats = {
        owner: {
            "planet_ships": 0.0,
            "fleet_ships": 0.0,
            "production": 0.0,
            "planet_count": 0,
        }
        for owner in (-1, 0, 1, 2, 3)
    }
    owners_by_planet = {}
    for p in obs.get("planets", []):
        pid, owner, _x, _y, _r, ships, prod = p[:7]
        owner = int(owner)
        owners_by_planet[int(pid)] = owner
        if owner not in stats:
            continue
        stats[owner]["planet_ships"] += float(ships)
        stats[owner]["production"] += float(prod)
        stats[owner]["planet_count"] += 1
    for f in obs.get("fleets", []):
        _fid, owner, _x, _y, _angle, _from_id, ships = f[:7]
        owner = int(owner)
        if owner in stats:
            stats[owner]["fleet_ships"] += float(ships)
    return stats, owners_by_planet


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
            paths = [args.agent_b, args.agent_a] if swapped else [args.agent_a, args.agent_b]
            random.seed(seed)
            agents = [load_agent(p) for p in paths]
            env = make("orbit_wars", debug=False, configuration={"randomSeed": seed})
            steps = env.run(agents)
            prev_owner = None
            final = steps[-1]
            rewards = [s.get("reward") for s in final]
            a_reward = rewards[1] if swapped else rewards[0]
            b_reward = rewards[0] if swapped else rewards[1]
            outcome = "W" if (a_reward or 0) > (b_reward or 0) else "L" if (a_reward or 0) < (b_reward or 0) else "T"
            for step_idx, step_states in enumerate(steps):
                obs = obs_dict(step_states[0])
                stats, owners_by_planet = owner_stats(obs)
                flip_to_0 = flip_to_1 = flip_to_neutral = 0
                changed_planets = []
                if prev_owner is not None:
                    for pid, owner in owners_by_planet.items():
                        old = prev_owner.get(pid)
                        if old is None or old == owner:
                            continue
                        changed_planets.append(f"{pid}:{old}->{owner}")
                        if owner == 0:
                            flip_to_0 += 1
                        elif owner == 1:
                            flip_to_1 += 1
                        elif owner == -1:
                            flip_to_neutral += 1
                prev_owner = owners_by_planet
                row = {
                    "seed": seed,
                    "swapped": swapped,
                    "step": step_idx,
                    "a_slot": 1 if swapped else 0,
                    "outcome": outcome,
                    "a_reward": a_reward,
                    "b_reward": b_reward,
                    "p0_total": stats[0]["planet_ships"] + stats[0]["fleet_ships"],
                    "p1_total": stats[1]["planet_ships"] + stats[1]["fleet_ships"],
                    "p0_planet_ships": stats[0]["planet_ships"],
                    "p1_planet_ships": stats[1]["planet_ships"],
                    "p0_fleet_ships": stats[0]["fleet_ships"],
                    "p1_fleet_ships": stats[1]["fleet_ships"],
                    "p0_prod": stats[0]["production"],
                    "p1_prod": stats[1]["production"],
                    "p0_planets": stats[0]["planet_count"],
                    "p1_planets": stats[1]["planet_count"],
                    "neutral_planets": stats[-1]["planet_count"],
                    "flip_to_0": flip_to_0,
                    "flip_to_1": flip_to_1,
                    "flip_to_neutral": flip_to_neutral,
                    "changed_planets": ";".join(changed_planets[:20]),
                }
                rows.append(row)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
