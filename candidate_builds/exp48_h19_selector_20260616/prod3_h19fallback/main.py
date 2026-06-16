from __future__ import annotations

import importlib.util
import math
import os
import sys
from pathlib import Path
from typing import Any


_HERE = Path(__file__).resolve().parent


def _load_agent_module(name: str, rel: str):
    path = _HERE / rel / "main.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    old_cwd = os.getcwd()
    old_path = list(sys.path)
    try:
        for key in list(sys.modules):
            if key == "orbit_lite" or key.startswith("orbit_lite."):
                del sys.modules[key]
        os.chdir(str(path.parent))
        sys.path.insert(0, str(path.parent))
        spec.loader.exec_module(module)
    finally:
        os.chdir(old_cwd)
        sys.path[:] = old_path
    return module


_EXP48 = _load_agent_module("_exp48_agent", "exp48_agent")
_H19 = _load_agent_module("_h19_agent", "h19_agent")
_PRODUCER = _load_agent_module("_producer_predictor", "producer_agent")


_predicted_enemy_prev: list[tuple[int, float, float]] = []
_producer_like_matches = 0
_producer_like_checks = 0
_use_h19_fallback = False
_last_step: int | None = None


def _get(obs: Any, key: str, default=None):
    return obs.get(key, default) if isinstance(obs, dict) else getattr(obs, key, default)


def _as_dict_obs(obs: Any, *, player: int | None = None) -> dict:
    data = {
        "player": _get(obs, "player", 0),
        "planets": _get(obs, "planets", []),
        "fleets": _get(obs, "fleets", []),
        "angular_velocity": _get(obs, "angular_velocity", 0.0),
        "step": _get(obs, "step", 0),
    }
    if player is not None:
        data["player"] = int(player)
    return data


def _player_count(obs: Any) -> int:
    owners = set()
    for p in _get(obs, "planets", []) or []:
        owner = int(p[1])
        if owner >= 0:
            owners.add(owner)
    return max(owners) + 1 if owners else 2


def _enemy_player_id(obs: Any, player_id: int) -> int | None:
    owners = []
    for p in _get(obs, "planets", []) or []:
        owner = int(p[1])
        if owner >= 0 and owner != int(player_id):
            owners.append(owner)
    for f in _get(obs, "fleets", []) or []:
        owner = int(f[1])
        if owner >= 0 and owner != int(player_id):
            owners.append(owner)
    return min(owners) if owners else None


def _angle_delta(a: float, b: float) -> float:
    return abs((float(a) - float(b) + math.pi) % (2.0 * math.pi) - math.pi)


def _moves_to_tuples(moves: list) -> list[tuple[int, float, float]]:
    out = []
    for move in moves or []:
        if len(move) < 3:
            continue
        ships = float(round(float(move[2])))
        if ships >= 1.0:
            out.append((int(move[0]), float(move[1]), ships))
    return out


def _match_predicted_enemy_launches(
    obs: Any,
    enemy_id: int,
    predicted: list[tuple[int, float, float]],
) -> tuple[int, int]:
    if not predicted:
        return 0, 0
    enemy_fleets = [
        (int(f[5]), float(f[4]), float(round(float(f[6]))))
        for f in (_get(obs, "fleets", []) or [])
        if int(f[0]) >= 0 and int(f[1]) == int(enemy_id)
    ]
    used: set[int] = set()
    matches = 0
    for from_pid, angle, ships in predicted:
        best_idx = None
        best_angle = 999.0
        for idx, (fleet_from, fleet_angle, fleet_ships) in enumerate(enemy_fleets):
            if idx in used or fleet_from != from_pid:
                continue
            if abs(fleet_ships - ships) > 1.0:
                continue
            delta = _angle_delta(fleet_angle, angle)
            if delta < best_angle:
                best_idx = idx
                best_angle = delta
        if best_idx is not None and best_angle <= 0.08:
            used.add(best_idx)
            matches += 1
    return matches, len(predicted)


def _reset_state() -> None:
    global _predicted_enemy_prev, _producer_like_matches, _producer_like_checks, _use_h19_fallback
    _predicted_enemy_prev = []
    _producer_like_matches = 0
    _producer_like_checks = 0
    _use_h19_fallback = False


def agent(obs):
    global _predicted_enemy_prev, _producer_like_matches, _producer_like_checks, _use_h19_fallback, _last_step

    step = int(_get(obs, "step", 0) or 0)
    if step == 0 or (_last_step is not None and step < _last_step):
        _reset_state()
    _last_step = step

    player_id = int(_get(obs, "player", 0) or 0)
    pc = _player_count(obs)
    if pc >= 4:
        return _H19.agent(obs)

    enemy_id = _enemy_player_id(obs, player_id)
    if enemy_id is not None:
        matched, checked = _match_predicted_enemy_launches(obs, enemy_id, _predicted_enemy_prev)
        _producer_like_matches += matched
        _producer_like_checks += checked
        if _producer_like_checks >= 3 and _producer_like_matches >= 3:
            _use_h19_fallback = True

    moves = _H19.agent(obs) if _use_h19_fallback else _EXP48.agent(obs)

    if enemy_id is not None:
        enemy_obs = _as_dict_obs(obs, player=enemy_id)
        _predicted_enemy_prev = _moves_to_tuples(_PRODUCER.agent(enemy_obs))

    return moves
