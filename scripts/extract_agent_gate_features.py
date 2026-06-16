#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import math
import sys
from pathlib import Path

from kaggle_environments import make


def _agent_path(path: str) -> Path:
    p = Path(path)
    if p.is_dir():
        p = p / "main.py"
    return p.resolve()


def load_module(path: str, suffix: str):
    p = _agent_path(path)
    for key in list(sys.modules):
        if key == "orbit_lite" or key.startswith("orbit_lite."):
            del sys.modules[key]
    sys.path.insert(0, str(p.parent))
    name = f"gate_features_{suffix}_{abs(hash(str(p)))}"
    spec = importlib.util.spec_from_file_location(name, p)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {p}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def obs_for(seed: int, player: int):
    env = make("orbit_wars", configuration={"randomSeed": int(seed)}, debug=False)
    env.reset()
    return env.steps[0][int(player)].observation


def _fleet_speed(ships: float) -> float:
    ships = max(float(ships), 1.0)
    return 1.0 + 5.0 * min((math.log(ships) / math.log(1000.0)), 1.0) ** 1.5


def tensor_features(tensors: dict, player: int) -> dict[str, float]:
    planets = tensors["planets"].detach().cpu().tolist()
    mine = [p for p in planets if int(p[1]) == int(player)]
    enemy = [p for p in planets if int(p[1]) >= 0 and int(p[1]) != int(player)]
    neutral = [p for p in planets if int(p[1]) < 0]
    rows = []
    for n in neutral:
        if not mine or not enemy:
            continue

        def eta(src: list[float]) -> float:
            d = math.hypot(float(src[2]) - float(n[2]), float(src[3]) - float(n[3]))
            gap = float(src[4]) + float(n[4])
            return max(0.0, d - gap) / _fleet_speed(float(src[5]))

        my_eta = min(eta(m) for m in mine)
        en_eta = min(eta(e) for e in enemy)
        value = float(n[6]) * 19.0 + float(n[4]) * 2.0 - float(n[5]) * 0.25
        rows.append({
            "value": value,
            "abs_margin": abs(en_eta - my_eta),
            "margin": en_eta - my_eta,
            "my_eta": my_eta,
            "enemy_eta": en_eta,
        })
    my_fast = [r for r in rows if r["margin"] >= 1.25 and r["my_eta"] <= 9.0]
    enemy_fast = [r for r in rows if r["margin"] <= -1.25 and r["enemy_eta"] <= 9.0]
    contest = [r for r in rows if r["abs_margin"] <= 1.5 and r["my_eta"] <= 9.0]
    top = sorted(rows, key=lambda r: r["value"], reverse=True)[:5]
    return {
        "tensor_my_fast_count": float(len(my_fast)),
        "tensor_enemy_fast_count": float(len(enemy_fast)),
        "tensor_contest_count": float(len(contest)),
        "tensor_min_abs_margin": min([r["abs_margin"] for r in rows], default=99.0),
        "tensor_avg_abs_margin_top5": sum([r["abs_margin"] for r in top]) / max(1, len(top)),
        "tensor_best_fast_value": max([r["value"] for r in my_fast], default=0.0),
        "tensor_best_enemy_fast_value": max([r["value"] for r in enemy_fast], default=0.0),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    mod = load_module(args.agent, "agent")
    if not hasattr(mod, "single_obs_to_tensor"):
        raise RuntimeError("agent module has no single_obs_to_tensor")
    if not hasattr(mod, "_initial_map_features"):
        raise RuntimeError("agent module has no _initial_map_features")

    rows = []
    for seed_text in args.seeds.split(","):
        if not seed_text:
            continue
        seed = int(seed_text)
        for player in (0, 1):
            obs = obs_for(seed, player)
            try:
                tensors = mod.single_obs_to_tensor(obs, player_id=player)
            except TypeError:
                tensors = mod.single_obs_to_tensor(obs)
            values = mod._initial_map_features(tensors, player)
            if not isinstance(values, tuple):
                values = (values,)
            row = {
                "seed": seed,
                "player": player,
                "best_fast_value": float(values[0]) if len(values) > 0 else 0.0,
                "avg_abs_margin_top5": float(values[1]) if len(values) > 1 else 99.0,
            }
            row.update(tensor_features(tensors, player))
            if hasattr(mod, "_use_producer_2p_gate"):
                row["use_producer_2p_gate"] = bool(mod._use_producer_2p_gate(tensors, player))
            rows.append(row)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "seed", "player", "best_fast_value", "avg_abs_margin_top5", "use_producer_2p_gate",
        "tensor_my_fast_count", "tensor_enemy_fast_count", "tensor_contest_count",
        "tensor_min_abs_margin", "tensor_avg_abs_margin_top5", "tensor_best_fast_value",
        "tensor_best_enemy_fast_value",
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
