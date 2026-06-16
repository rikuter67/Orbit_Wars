from __future__ import annotations

import importlib.util
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


_H19 = _load_agent_module("_h19_partial_switch_agent", "h19_agent")
_M05 = _load_agent_module("_m05_partial_switch_agent", "m05_agent")

_use_m05 = False
_last_step: int | None = None


def _get(obs: Any, key: str, default=None):
    return obs.get(key, default) if isinstance(obs, dict) else getattr(obs, key, default)


def _player_count(obs: Any) -> int:
    owners = set()
    for p in _get(obs, "planets", []) or []:
        owner = int(p[1])
        if owner >= 0:
            owners.add(owner)
    return max(owners) + 1 if owners else 2


def _enemy_partial_launch_seen(obs: Any, player_id: int, *, max_step: int, ratio_cut: float) -> bool:
    step = int(_get(obs, "step", 0) or 0)
    if step > int(max_step):
        return False

    planets = {int(p[0]): p for p in (_get(obs, "planets", []) or [])}
    for fleet in _get(obs, "fleets", []) or []:
        owner = int(fleet[1])
        if owner < 0 or owner == int(player_id):
            continue
        source = planets.get(int(fleet[5]))
        if source is None or int(source[1]) != owner:
            continue
        source_ships = max(float(source[5]), 1.0)
        launched = float(fleet[6])
        if launched / source_ships < float(ratio_cut):
            return True
    return False


def _reset_state() -> None:
    global _use_m05
    _use_m05 = False


def agent(obs):
    global _use_m05, _last_step

    step = int(_get(obs, "step", 0) or 0)
    if step == 0 or (_last_step is not None and step < _last_step):
        _reset_state()
    _last_step = step

    player_id = int(_get(obs, "player", 0) or 0)
    if _player_count(obs) >= 4:
        return _H19.agent(obs)

    if not _use_m05 and _enemy_partial_launch_seen(obs, player_id, max_step=45, ratio_cut=0.95):
        _use_m05 = True

    return _M05.agent(obs) if _use_m05 else _H19.agent(obs)
