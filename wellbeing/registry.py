"""
registry.py
───────────
The LLM-facing tool catalogue + the dispatcher.

  • TOOLS           — JSON schema list passed to Groq's `tools=` parameter
  • dispatch_tool() — routes a tool call by name to the actual Python function
                      and returns its JSON-serialised result string
"""

from __future__ import annotations

import json

from .core_tools import (
    compare_wellbeing_weeks,
    get_personal_profile,
    get_recent_chat_history,
    get_wellbeing_snapshot,
    get_wellbeing_trend,
)
from .analytics import (
    cluster_similar_weeks,
    compute_volatility,
    compute_wellbeing_composite,
    detect_anomalies,
    detect_pattern_shift,
    estimate_coping_effectiveness,
    get_correlated_factors,
    get_lagged_correlation,
    get_metric_summary_stats,
    get_rate_of_change,
    get_streaks,
    predict_trend,
)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL DEFINITIONS FOR THE LLM
# ─────────────────────────────────────────────────────────────────────────────

_METRIC_PATH_HINT = (
    "Dotted path into a wellbeing frame, e.g. 'emotions.anxious_worried', "
    "'stresses.work_academic', 'sleep.insufficient_sleep'. "
    "Special values: 'wellbeing_score' (0-100 composite), 'exercise_minutes'."
)

TOOLS = [
    # Core
    {"type": "function", "function": {"name": "get_personal_profile", "description": "Returns user's personal info: name, age, gender, occupation, traits, etc.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_recent_chat_history", "description": "Returns last N chat messages with sentiment scores.", "parameters": {"type": "object", "properties": {"last_n": {"type": "integer", "description": "Number of messages (default 6)", "default": 6}}, "required": []}}},
    {"type": "function", "function": {"name": "get_wellbeing_trend", "description": "Returns weekly wellbeing snapshots over time. If `fields` (list of metric paths) is given, each row is reduced to {week, <field>: value}.", "parameters": {"type": "object", "properties": {"last_n_weeks": {"type": "integer"}, "fields": {"type": "array", "items": {"type": "string", "description": _METRIC_PATH_HINT}}}, "required": []}}},
    {"type": "function", "function": {"name": "get_wellbeing_snapshot", "description": "Latest week's full snapshot (composite score + per-category sub-dimension values).", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "compare_wellbeing_weeks", "description": "Compare two specific weeks; returns top 10 changed metrics + composite delta.", "parameters": {"type": "object", "properties": {"week_a": {"type": "integer"}, "week_b": {"type": "integer"}}, "required": ["week_a", "week_b"]}}},

    # Analytics
    {"type": "function", "function": {"name": "get_metric_summary_stats", "description": "Mean, median, std, min, max, latest for each metric path.", "parameters": {"type": "object", "properties": {"metrics": {"type": "array", "items": {"type": "string", "description": _METRIC_PATH_HINT}}}, "required": []}}},
    {"type": "function", "function": {"name": "detect_pattern_shift", "description": "Top-N significant changes between recent vs. older windows (z-score sorted).", "parameters": {"type": "object", "properties": {"window": {"type": "integer", "default": 3}, "threshold": {"type": "number", "default": 1.0}, "top_n": {"type": "integer", "default": 15}}, "required": []}}},
    {"type": "function", "function": {"name": "get_correlated_factors", "description": "Find metric paths correlated with a target metric.", "parameters": {"type": "object", "properties": {"target_metric": {"type": "string", "default": "wellbeing_score", "description": _METRIC_PATH_HINT}, "min_abs_r": {"type": "number", "default": 0.3}, "top_n": {"type": "integer", "default": 15}}, "required": []}}},
    {"type": "function", "function": {"name": "compute_volatility", "description": "Top-N most volatile metrics by coefficient of variation.", "parameters": {"type": "object", "properties": {"last_n_weeks": {"type": "integer"}, "top_n": {"type": "integer", "default": 15}}, "required": []}}},
    {"type": "function", "function": {"name": "detect_anomalies", "description": "Per-week outlier values across all metrics.", "parameters": {"type": "object", "properties": {"z_threshold": {"type": "number", "default": 1.5}}, "required": []}}},
    {"type": "function", "function": {"name": "predict_trend", "description": "Linear-regression projection for a metric path.", "parameters": {"type": "object", "properties": {"metric": {"type": "string", "default": "wellbeing_score", "description": _METRIC_PATH_HINT}, "forecast_weeks": {"type": "integer", "default": 2}}, "required": []}}},
    {"type": "function", "function": {"name": "compute_wellbeing_composite", "description": "Per-week 0-100 wellbeing score using category weights (override via `weights`: {category: weight}).", "parameters": {"type": "object", "properties": {"weights": {"type": "object"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_rate_of_change", "description": "Top-N week-over-week deltas (velocity).", "parameters": {"type": "object", "properties": {"last_n_weeks": {"type": "integer", "default": 4}, "top_n": {"type": "integer", "default": 15}}, "required": []}}},
    {"type": "function", "function": {"name": "cluster_similar_weeks", "description": "Group similar weeks by multivariate similarity across all metric paths.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_lagged_correlation", "description": "Find if one metric leads/lags another.", "parameters": {"type": "object", "properties": {"metric_a": {"type": "string", "default": "stresses.work_academic", "description": _METRIC_PATH_HINT}, "metric_b": {"type": "string", "default": "wellbeing_score", "description": _METRIC_PATH_HINT}, "max_lag": {"type": "integer", "default": 3}}, "required": []}}},
    {"type": "function", "function": {"name": "get_streaks", "description": "Top-N improvement/decline streaks.", "parameters": {"type": "object", "properties": {"top_n": {"type": "integer", "default": 15}}, "required": []}}},
    {"type": "function", "function": {"name": "estimate_coping_effectiveness", "description": "Compares composite wellbeing on weeks where each coping mechanism is active vs. inactive.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]


# ─────────────────────────────────────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────────────────────────────────────

# Maps tool name → Python callable
_HANDLERS = {
    "get_personal_profile":          get_personal_profile,
    "get_recent_chat_history":       get_recent_chat_history,
    "get_wellbeing_trend":           get_wellbeing_trend,
    "get_wellbeing_snapshot":        get_wellbeing_snapshot,
    "compare_wellbeing_weeks":       compare_wellbeing_weeks,
    "get_metric_summary_stats":      get_metric_summary_stats,
    "detect_pattern_shift":          detect_pattern_shift,
    "get_correlated_factors":        get_correlated_factors,
    "compute_volatility":            compute_volatility,
    "detect_anomalies":              detect_anomalies,
    "predict_trend":                 predict_trend,
    "compute_wellbeing_composite":   compute_wellbeing_composite,
    "get_rate_of_change":            get_rate_of_change,
    "cluster_similar_weeks":         cluster_similar_weeks,
    "get_lagged_correlation":        get_lagged_correlation,
    "get_streaks":                   get_streaks,
    "estimate_coping_effectiveness": estimate_coping_effectiveness,
}


def dispatch_tool(name: str, arguments: dict, user_data: dict) -> str:
    arguments = arguments or {}
    handler   = _HANDLERS.get(name)
    try:
        if handler is None:
            result = {"error": f"Unknown tool: {name}"}
        elif name in ("get_personal_profile", "get_wellbeing_snapshot"):
            # These take no kwargs beyond user_data
            result = handler(user_data)
        else:
            result = handler(user_data, **arguments)
    except Exception as e:
        result = {"error": f"Tool execution failed: {str(e)}"}

    return json.dumps(result, indent=2, default=str)
