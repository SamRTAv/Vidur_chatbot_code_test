"""
analytics.py
────────────
Section 2 — Analytics & math tools (A1 – A12).

Each function reads `user_data["wellbeing_frames"]`, computes a derived
statistic, and returns a JSON-friendly structure for the LLM:

    A1  get_metric_summary_stats     — mean/median/std/min/max/latest
    A2  detect_pattern_shift         — recent-vs-older window deltas
    A3  get_correlated_factors       — Pearson r between metrics
    A4  compute_volatility           — coefficient of variation
    A5  detect_anomalies             — per-week z-score outliers
    A6  predict_trend                — linear-regression projection
    A7  compute_wellbeing_composite  — weekly 0-100 score series
    A8  get_rate_of_change           — week-over-week deltas + acceleration
    A9  cluster_similar_weeks        — multivariate similarity clusters
    A10 get_lagged_correlation       — does metric A lead/lag metric B?
    A11 get_streaks                  — improvement/decline run lengths
    A12 estimate_coping_effectiveness — composite-score lift per mechanism
"""

from __future__ import annotations

import math

from .schema import ALL_METRICS, CATEGORY_WEIGHTS, METRIC_CATEGORIES, VALUE_MAX
from .stats  import (
    _compute_composite_score,
    _extract_series,
    _get_raw_value,
    _get_value,
    _is_negative,
    _linear_regression,
    _pearson_r,
    _safe_mean,
    _safe_median,
    _safe_std,
)


# ─────────────────────────────────────────────────────────────────────────────
# A1. METRIC SUMMARY STATS
# ─────────────────────────────────────────────────────────────────────────────

def get_metric_summary_stats(user_data: dict, metrics: list = None) -> dict:
    """Mean, median, std-dev, min, max for each metric path."""
    frames  = user_data["wellbeing_frames"]
    targets = metrics or (ALL_METRICS + ["wellbeing_score", "exercise_minutes"])
    results = {}

    for path in targets:
        series = _extract_series(frames, path)
        if not series:
            continue
        results[path] = {
            "mean":    round(_safe_mean(series), 2),
            "median":  round(_safe_median(series), 2),
            "std":     round(_safe_std(series), 2),
            "min":     min(series),
            "max":     max(series),
            "latest":  series[-1],
            "n_weeks": len(series),
        }
    return results


# ─────────────────────────────────────────────────────────────────────────────
# A2. DETECT PATTERN SHIFTS
# ─────────────────────────────────────────────────────────────────────────────

def detect_pattern_shift(user_data: dict, window: int = 3, threshold: float = 1.0, top_n: int = 15) -> list:
    """Detects significant changes between two time windows. Returns top_n by |z|."""
    frames = user_data["wellbeing_frames"]
    if len(frames) < window * 2:
        mid = len(frames) // 2
        older, recent = frames[:mid], frames[mid:]
    else:
        older, recent = frames[-(window * 2):-window], frames[-window:]

    shifts = []
    for path in ALL_METRICS + ["wellbeing_score", "exercise_minutes"]:
        old_vals = _extract_series(older, path)
        new_vals = _extract_series(recent, path)
        if not old_vals or not new_vals:
            continue

        old_mean, new_mean = _safe_mean(old_vals), _safe_mean(new_vals)
        change   = new_mean - old_mean
        all_vals = _extract_series(frames, path)
        std = _safe_std(all_vals) or 1.0
        z = change / std

        direction = (
            ("worsening" if change > 0 else "improving")
            if _is_negative(path)
            else ("improving" if change > 0 else "worsening")
        )
        severity = "major" if abs(z) >= 2.0 else ("notable" if abs(z) >= 1.0 else "minor")

        shifts.append({
            "metric":    path,
            "old_mean":  round(old_mean, 2),
            "new_mean":  round(new_mean, 2),
            "change":    round(change, 2),
            "z_score":   round(z, 2),
            "direction": direction,
            "severity":  severity,
        })

    shifts.sort(key=lambda s: abs(s["z_score"]), reverse=True)
    return shifts[:top_n]


# ─────────────────────────────────────────────────────────────────────────────
# A3. CORRELATION
# ─────────────────────────────────────────────────────────────────────────────

def get_correlated_factors(user_data: dict, target_metric: str = "wellbeing_score", min_abs_r: float = 0.3, top_n: int = 15) -> list:
    """Find metric paths correlated with target_metric."""
    frames = user_data["wellbeing_frames"]
    target_series = _extract_series(frames, target_metric)
    if len(target_series) < 3:
        return [{"error": "Not enough data points"}]

    candidates = ALL_METRICS + ["exercise_minutes"]
    if target_metric in candidates:
        candidates = [c for c in candidates if c != target_metric]

    results = []
    for path in candidates:
        other = _extract_series(frames, path)
        r = _pearson_r(target_series, other)
        if r is not None and abs(r) >= min_abs_r:
            results.append({
                "metric":    path,
                "pearson_r": r,
                "strength":  "strong" if abs(r) >= 0.7 else ("moderate" if abs(r) >= 0.5 else "weak"),
            })

    results.sort(key=lambda x: abs(x["pearson_r"]), reverse=True)
    return results[:top_n]


# ─────────────────────────────────────────────────────────────────────────────
# A4. VOLATILITY / STABILITY
# ─────────────────────────────────────────────────────────────────────────────

def compute_volatility(user_data: dict, last_n_weeks: int = None, top_n: int = 15) -> dict:
    frames = user_data["wellbeing_frames"]
    if last_n_weeks:
        frames = frames[-last_n_weeks:]

    rows = []
    for path in ALL_METRICS + ["wellbeing_score", "exercise_minutes"]:
        series = _extract_series(frames, path)
        if len(series) < 2:
            continue
        mean = _safe_mean(series)
        std  = _safe_std(series)
        cv   = round(std / mean, 3) if mean != 0 else 0.0
        wow_changes = [abs(series[i] - series[i - 1]) for i in range(1, len(series))]
        avg_wow = round(_safe_mean(wow_changes), 2)
        max_wow = round(max(wow_changes), 2)
        stability = "stable" if cv < 0.15 else ("moderate" if cv < 0.30 else "volatile")

        rows.append({
            "metric":         path,
            "cv":             cv,
            "std":            round(std, 2),
            "avg_wow_change": avg_wow,
            "max_wow_change": max_wow,
            "stability":      stability,
        })

    rows.sort(key=lambda r: r["cv"], reverse=True)
    return {r["metric"]: r for r in rows[:top_n]}


# ─────────────────────────────────────────────────────────────────────────────
# A5. ANOMALY DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def detect_anomalies(user_data: dict, z_threshold: float = 1.5) -> list:
    frames = user_data["wellbeing_frames"]
    stats = {}
    for path in ALL_METRICS + ["wellbeing_score", "exercise_minutes"]:
        series = _extract_series(frames, path)
        if len(series) >= 3:
            stats[path] = (_safe_mean(series), _safe_std(series))

    anomalies = []
    for frame in frames:
        week = frame.get("week", "?")
        for path, (mu, std) in stats.items():
            val = _get_value(frame, path)
            if val is None or std == 0:
                continue
            z = (val - mu) / std
            if abs(z) < z_threshold:
                continue
            if _is_negative(path):
                direction = "unusually high (worse)" if z > 0 else "unusually low (better)"
            else:
                direction = "unusually high (better)" if z > 0 else "unusually low (worse)"
            anomalies.append({
                "week":      week,
                "metric":    path,
                "value":     val,
                "mean":      round(mu, 2),
                "z_score":   round(z, 2),
                "direction": direction,
            })

    anomalies.sort(key=lambda a: (a["week"], abs(a["z_score"])), reverse=True)
    return anomalies


# ─────────────────────────────────────────────────────────────────────────────
# A6. TREND PREDICTION
# ─────────────────────────────────────────────────────────────────────────────

def predict_trend(user_data: dict, metric: str = "wellbeing_score", forecast_weeks: int = 2) -> dict:
    frames = user_data["wellbeing_frames"]
    series = _extract_series(frames, metric)
    if len(series) < 3:
        return {"error": f"Need at least 3 data points for '{metric}'."}

    slope, intercept = _linear_regression(series)
    n = len(series)
    projections = [
        {"weeks_from_now": i, "projected_value": round(intercept + slope * (n - 1 + i), 2)}
        for i in range(1, forecast_weeks + 1)
    ]

    if _is_negative(metric):
        direction = "worsening" if slope > 0.05 else ("improving" if slope < -0.05 else "flat")
    else:
        direction = "improving" if slope > 0.05 else ("worsening" if slope < -0.05 else "flat")

    return {
        "metric":      metric,
        "data_points": n,
        "slope":       slope,
        "direction":   direction,
        "current":     series[-1],
        "projections": projections,
    }


# ─────────────────────────────────────────────────────────────────────────────
# A7. COMPOSITE WELLBEING SCORE (PER-WEEK SERIES)
# ─────────────────────────────────────────────────────────────────────────────

def compute_wellbeing_composite(user_data: dict, weights: dict = None) -> dict:
    """Per-week 0-100 wellbeing score using category weights (override via `weights`)."""
    frames  = user_data["wellbeing_frames"]
    weights = weights or CATEGORY_WEIGHTS

    scored_weeks = []
    for frame in frames:
        cat_total, w_total = 0.0, 0.0
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
                wt = weights.get(cat, 0.0)
                cat_total += _safe_mean(contribs) * wt
                w_total   += wt
        score = round((cat_total / w_total) * 100, 1) if w_total > 0 else None
        scored_weeks.append({"week": frame.get("week"), "score": score})

    scores = [s["score"] for s in scored_weeks if s["score"] is not None]
    slope, _ = _linear_regression(scores) if len(scores) >= 2 else (0, 0)
    direction = "improving" if slope > 0.3 else ("declining" if slope < -0.3 else "stable")

    return {
        "weekly_scores": scored_weeks,
        "current_score": scored_weeks[-1]["score"] if scored_weeks else None,
        "average_score": round(_safe_mean(scores), 1) if scores else None,
        "trend":         direction,
    }


# ─────────────────────────────────────────────────────────────────────────────
# A8. RATE OF CHANGE
# ─────────────────────────────────────────────────────────────────────────────

def get_rate_of_change(user_data: dict, last_n_weeks: int = 4, top_n: int = 15) -> dict:
    frames = user_data["wellbeing_frames"][-(last_n_weeks + 1):]

    rows = []
    for path in ALL_METRICS + ["wellbeing_score", "exercise_minutes"]:
        series = _extract_series(frames, path)
        if len(series) < 2:
            continue
        deltas = [round(series[i] - series[i - 1], 2) for i in range(1, len(series))]
        if len(deltas) >= 2:
            accel = round(deltas[-1] - deltas[-2], 2)
            accel_label = "accelerating" if abs(accel) > 0.5 else "steady"
        else:
            accel, accel_label = 0.0, "insufficient"

        latest_delta = deltas[-1]
        if _is_negative(path):
            direction = "worsening" if latest_delta > 0 else ("improving" if latest_delta < 0 else "unchanged")
        else:
            direction = "improving" if latest_delta > 0 else ("worsening" if latest_delta < 0 else "unchanged")

        rows.append({
            "metric":      path,
            "deltas":      deltas,
            "latest":      latest_delta,
            "direction":   direction,
            "accel":       accel,
            "accel_label": accel_label,
        })

    rows.sort(key=lambda r: abs(r["latest"]), reverse=True)
    return {r["metric"]: r for r in rows[:top_n]}


# ─────────────────────────────────────────────────────────────────────────────
# A9. CLUSTER SIMILAR WEEKS
# ─────────────────────────────────────────────────────────────────────────────

def cluster_similar_weeks(user_data: dict) -> dict:
    frames = user_data["wellbeing_frames"]
    if len(frames) < 2:
        return {"error": "Need at least 2 weeks"}

    paths = ALL_METRICS
    vectors = []
    for frame in frames:
        vec = []
        for p in paths:
            v = _get_raw_value(frame, p)
            if v is None:
                vec.append(0.5)
                continue
            n = v / VALUE_MAX
            if _is_negative(p):
                n = 1.0 - n
            vec.append(n)
        vectors.append(vec)

    def dist(a, b):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    threshold = 0.3 * math.sqrt(len(paths))
    clusters: list = []
    for i in range(len(frames)):
        placed = False
        for cluster in clusters:
            if any(dist(vectors[i], vectors[j]) < threshold for j in cluster):
                cluster.add(i)
                placed = True
                break
        if not placed:
            clusters.append({i})

    return {
        f"cluster_{ci}": {
            "weeks": [frames[i].get("week", i + 1) for i in sorted(c)],
            "size":  len(c),
        }
        for ci, c in enumerate(clusters)
    }


# ─────────────────────────────────────────────────────────────────────────────
# A10. LAGGED CORRELATION
# ─────────────────────────────────────────────────────────────────────────────

def get_lagged_correlation(user_data: dict, metric_a: str = "stresses.work_academic", metric_b: str = "wellbeing_score", max_lag: int = 3) -> dict:
    frames = user_data["wellbeing_frames"]
    sa = _extract_series(frames, metric_a)
    sb = _extract_series(frames, metric_b)
    n = min(len(sa), len(sb))
    if n < 4:
        return {"error": "Need at least 4 weeks"}

    results, best_r, best_lag = [], 0.0, 0
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            a_slice = sa[: n - lag] if lag > 0 else sa[:n]
            b_slice = sb[lag:n]
        else:
            a_slice = sa[-lag:n]
            b_slice = sb[: n + lag]
        r = _pearson_r(a_slice, b_slice)
        if r is None:
            continue
        results.append({"lag": lag, "r": r})
        if abs(r) > abs(best_r):
            best_r, best_lag = r, lag

    return {
        "metric_a":      metric_a,
        "metric_b":      metric_b,
        "results":       results,
        "strongest_lag": best_lag,
        "strongest_r":   best_r,
    }


# ─────────────────────────────────────────────────────────────────────────────
# A11. STREAKS
# ─────────────────────────────────────────────────────────────────────────────

def get_streaks(user_data: dict, top_n: int = 15) -> dict:
    frames = user_data["wellbeing_frames"]
    rows = []

    for path in ALL_METRICS + ["wellbeing_score", "exercise_minutes"]:
        series = _extract_series(frames, path)
        if len(series) < 2:
            continue

        streak_type = None
        streak_len  = 0
        for i in range(len(series) - 1, 0, -1):
            diff = series[i] - series[i - 1]
            if diff > 0:
                d = "worsening" if _is_negative(path) else "improving"
            elif diff < 0:
                d = "improving" if _is_negative(path) else "worsening"
            else:
                d = "flat"
            if streak_type is None:
                streak_type, streak_len = d, 1
            elif d == streak_type:
                streak_len += 1
            else:
                break

        avg = _safe_mean(series)
        above_avg_streak = 0
        for v in reversed(series):
            if v >= avg:
                above_avg_streak += 1
            else:
                break

        rows.append({
            "metric":          path,
            "streak_type":     streak_type or "flat",
            "streak_weeks":    streak_len,
            "avg":             round(avg, 2),
            "weeks_above_avg": above_avg_streak,
            "latest":          series[-1],
        })

    rows.sort(key=lambda r: r["streak_weeks"], reverse=True)
    return {r["metric"]: r for r in rows[:top_n]}


# ─────────────────────────────────────────────────────────────────────────────
# A12. COPING EFFECTIVENESS
# ─────────────────────────────────────────────────────────────────────────────

def estimate_coping_effectiveness(user_data: dict) -> list:
    """Compares weeks where each coping mechanism is active vs. not, by composite wellbeing."""
    frames = user_data["wellbeing_frames"]
    if len(frames) < 3:
        return [{"error": "Need at least 3 weeks"}]

    all_coping = set()
    for f in frames:
        mechs = f.get("coping_mechanisms") or []
        if isinstance(mechs, str):
            mechs = [mechs]
        all_coping.update(mechs)

    if not all_coping:
        return [{"error": "No coping mechanism data"}]

    results = []
    for mech in sorted(all_coping):
        with_scores, without_scores = [], []
        for f in frames:
            active = f.get("coping_mechanisms") or []
            if isinstance(active, str):
                active = [active]
            score = _compute_composite_score(f)
            if score is None:
                continue
            (with_scores if mech in active else without_scores).append(score)

        if not with_scores:
            continue
        diff = round(_safe_mean(with_scores) - _safe_mean(without_scores), 2)
        results.append({
            "mechanism":     mech,
            "weeks_used":    len(with_scores),
            "avg_with":      round(_safe_mean(with_scores), 1),
            "avg_without":   round(_safe_mean(without_scores), 1) if without_scores else None,
            "effectiveness": diff,
            "verdict":       "helpful" if diff > 3 else ("neutral" if diff > -3 else "may not help"),
        })

    results.sort(key=lambda x: x["effectiveness"], reverse=True)
    return results
