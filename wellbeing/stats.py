"""
stats.py
────────
Pure math helpers and schema-aware value extraction from wellbeing frames.

Splits into two related concerns kept together because they're tightly coupled:
  • Math helpers — mean/std/median/Pearson r/linear regression
  • Frame extraction — walk nested categories, unwrap {value, description},
    compute composite wellbeing score, flip negative-polarity dimensions
"""

from __future__ import annotations

import math
from typing import Optional

from .schema import (
    CATEGORY_WEIGHTS,
    METRIC_CATEGORIES,
    NEGATIVE_POLARITY,
    TOP_LEVEL_NUMERIC,
    VALUE_MAX,
)

# ─────────────────────────────────────────────────────────────────────────────
# MATH HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _safe_mean(values: list) -> float:
    return sum(values) / len(values) if values else 0.0


def _safe_std(values: list) -> float:
    if len(values) < 2:
        return 0.0
    mu = _safe_mean(values)
    return math.sqrt(sum((x - mu) ** 2 for x in values) / (len(values) - 1))


def _safe_median(values: list) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def _pearson_r(xs: list, ys: list) -> Optional[float]:
    n = min(len(xs), len(ys))
    if n < 3:
        return None
    xs, ys = xs[:n], ys[:n]
    mx, my = _safe_mean(xs), _safe_mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx * dy == 0:
        return None
    return round(num / (dx * dy), 4)


def _linear_regression(values: list) -> tuple:
    n = len(values)
    if n < 2:
        return (0.0, values[0] if values else 0.0)
    x_mean = (n - 1) / 2
    y_mean = _safe_mean(values)
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0.0
    intercept = y_mean - slope * x_mean
    return (round(slope, 4), round(intercept, 4))


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA-AWARE EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def _get_raw_value(frame: dict, path: str):
    """Walk path; return numeric leaf. Handles {value, description} unwrapping."""
    if "." not in path:
        v = frame.get(path)
        return v if isinstance(v, (int, float)) else None
    obj = frame
    for p in path.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(p)
        if obj is None:
            return None
    if isinstance(obj, dict) and isinstance(obj.get("value"), (int, float)):
        return obj["value"]
    if isinstance(obj, (int, float)):
        return obj
    return None


def _compute_composite_score(frame: dict) -> Optional[float]:
    """0-100 composite per frame using category weights."""
    cat_total, weight_total = 0.0, 0.0
    for cat, subs in METRIC_CATEGORIES.items():
        contribs = []
        for sub, pol in subs.items():
            v = _get_raw_value(frame, f"{cat}.{sub}")
            if v is None or pol == "0":
                continue
            normed = v / VALUE_MAX
            if pol == "-":
                normed = 1.0 - normed
            contribs.append(normed)
        if contribs:
            wt = CATEGORY_WEIGHTS.get(cat, 0.0)
            cat_total    += _safe_mean(contribs) * wt
            weight_total += wt
    if weight_total == 0:
        return None
    return round((cat_total / weight_total) * 100, 1)


def _get_value(frame: dict, path: str):
    """Same as _get_raw_value, plus the virtual 'wellbeing_score' path."""
    if path == "wellbeing_score":
        return _compute_composite_score(frame)
    return _get_raw_value(frame, path)


def _extract_series(frames: list, path: str) -> list:
    out = []
    for f in frames:
        v = _get_value(f, path)
        if v is not None:
            out.append(v)
    return out


def _is_negative(path: str) -> bool:
    if path in NEGATIVE_POLARITY:
        return True
    if path == "wellbeing_score":
        return False
    if path in TOP_LEVEL_NUMERIC:
        return TOP_LEVEL_NUMERIC[path] == "-"
    return False
