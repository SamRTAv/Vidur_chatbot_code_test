"""
core_tools.py
─────────────
Section 1 — Core data-access tools.

These are the simple read-paths the LLM uses to fetch user state:
  • get_personal_profile
  • get_recent_chat_history
  • get_wellbeing_trend
  • get_wellbeing_snapshot
  • compare_wellbeing_weeks

Plus the file-based loader `load_user_data` (used by the CLI runner).
"""

from __future__ import annotations

import json

from .schema import ALL_METRICS, METRIC_CATEGORIES, TOP_LEVEL_NUMERIC
from .stats  import _compute_composite_score, _get_value


# ─────────────────────────────────────────────────────────────────────────────
# LOAD USER DATA FROM FILE
# ─────────────────────────────────────────────────────────────────────────────

def load_user_data(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# CORE TOOLS
# ─────────────────────────────────────────────────────────────────────────────

def get_personal_profile(user_data: dict) -> dict:
    return user_data["personal_memory"]


def get_recent_chat_history(user_data: dict, last_n: int = 6) -> list:
    history = user_data["recent_chat_memory"]
    return history[-min(last_n, 20):]


def get_wellbeing_trend(user_data: dict, last_n_weeks: int = None, fields: list = None) -> list:
    """Returns weekly frames. If `fields` is given (list of metric paths), each entry is reduced to
    {week, <each requested path>: value}."""
    frames = user_data["wellbeing_frames"]
    if last_n_weeks:
        frames = frames[-last_n_weeks:]
    if fields:
        reduced = []
        for frame in frames:
            row = {"week": frame.get("week")}
            for path in fields:
                row[path] = _get_value(frame, path)
            reduced.append(row)
        return reduced
    return frames


def get_wellbeing_snapshot(user_data: dict) -> dict:
    """Latest frame plus a flat numeric summary that's easy for the LLM to read."""
    frames = user_data["wellbeing_frames"]
    if not frames:
        return {"error": "No wellbeing frames"}
    latest = frames[-1]
    summary = {
        "week":              latest.get("week"),
        "wellbeing_score":   _compute_composite_score(latest),
        "coping_mechanisms": latest.get("coping_mechanisms", []),
        "exercise_minutes":  latest.get("exercise_minutes"),
        "by_category":       {},
    }
    for cat, subs in METRIC_CATEGORIES.items():
        cat_obj = latest.get(cat) or {}
        summary["by_category"][cat] = {
            sub: (cat_obj.get(sub) or {}).get("value") for sub in subs
        }
    return summary


def compare_wellbeing_weeks(user_data: dict, week_a: int, week_b: int) -> dict:
    frames = {f["week"]: f for f in user_data["wellbeing_frames"] if "week" in f}
    fa, fb = frames.get(week_a), frames.get(week_b)
    if not fa or not fb:
        return {"error": f"Week not found. Available weeks: {sorted(frames.keys())}"}

    diff = {}
    for path in ALL_METRICS + list(TOP_LEVEL_NUMERIC.keys()):
        va, vb = _get_value(fa, path), _get_value(fb, path)
        if va is None or vb is None or va == vb:
            continue
        diff[path] = {f"week_{week_a}": va, f"week_{week_b}": vb, "change": vb - va}

    composite_a = _compute_composite_score(fa)
    composite_b = _compute_composite_score(fb)
    top = sorted(diff.items(), key=lambda kv: abs(kv[1]["change"]), reverse=True)[:10]

    return {
        "wellbeing_score": {
            f"week_{week_a}": composite_a,
            f"week_{week_b}": composite_b,
            "change": (composite_b - composite_a) if (composite_a is not None and composite_b is not None) else None,
        },
        "top_changes": dict(top),
        "summary":     f"Compared weeks {week_a} and {week_b}",
    }
