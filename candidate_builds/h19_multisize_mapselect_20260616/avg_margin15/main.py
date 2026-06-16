from __future__ import annotations

import importlib.util
import math
import os
import sys
from pathlib import Path


_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))


def _load_agent(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.agent


_H19_AGENT = _load_agent("h19_main.py", "h19_mapselect_base")
_MULTISIZE_AGENT = _load_agent("multisize_main.py", "h19_mapselect_multisize")
_CHOICE: str | None = None


def _obs_get(obs, key, default=None):
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)


def _speed(ships: float) -> float:
    ships = max(float(ships), 1.0)
    return 1.0 + 5.0 * min((math.log(ships) / math.log(1000.0)), 1.0) ** 1.5


def _eta(src, tgt) -> float:
    dist = math.hypot(float(src[2]) - float(tgt[2]), float(src[3]) - float(tgt[3]))
    gap = float(src[4]) + float(tgt[4])
    return max(0.0, dist - gap) / _speed(float(src[5]))


def _largest_player_count(planets, fleets) -> int:
    owners = set()
    for p in planets:
        owner = int(p[1])
        if owner >= 0:
            owners.add(owner)
    for f in fleets:
        owner = int(f[1])
        if owner >= 0:
            owners.add(owner)
    return max(owners) + 1 if owners else 2


def _use_multisize(obs, player: int) -> bool:
    planets = _obs_get(obs, "planets", []) or []
    fleets = _obs_get(obs, "fleets", []) or []
    if _largest_player_count(planets, fleets) >= 4:
        return False

    mine = [p for p in planets if int(p[1]) == int(player)]
    enemy = [p for p in planets if int(p[1]) >= 0 and int(p[1]) != int(player)]
    neutral = [p for p in planets if int(p[1]) < 0]
    if not mine or not enemy or not neutral:
        return False

    rows = []
    for n in neutral:
        my_eta = min(_eta(m, n) for m in mine)
        en_eta = min(_eta(e, n) for e in enemy)
        value = float(n[6]) * 19.0 + float(n[4]) * 2.0 - float(n[5]) * 0.25
        rows.append((value, abs(en_eta - my_eta)))
    top = sorted(rows, reverse=True)[:5]
    avg_abs_margin_top5 = sum(margin for _, margin in top) / max(1, len(top))
    return avg_abs_margin_top5 <= 15.0


def agent(obs):
    global _CHOICE
    player = int(_obs_get(obs, "player", 0) or 0)
    step = int(_obs_get(obs, "step", 0) or 0)
    if step == 0 or _CHOICE is None:
        _CHOICE = "multisize" if _use_multisize(obs, player) else "h19"
    if _CHOICE == "multisize":
        return _MULTISIZE_AGENT(obs)
    return _H19_AGENT(obs)
