"""
wellbeing — modular split of the original `basic_tools.py`.

Public API (import from `wellbeing` or `basic_tools`):

    Schema constants:
        METRIC_CATEGORIES, ALL_METRICS, POLARITY, NEGATIVE_POLARITY,
        TOP_LEVEL_NUMERIC, VALUE_MAX, EXERCISE_MAX, CATEGORY_WEIGHTS

    Helpers (math + extraction):
        _safe_mean, _safe_std, _safe_median, _pearson_r, _linear_regression,
        _get_raw_value, _compute_composite_score, _get_value, _extract_series,
        _is_negative

    Data loader:
        load_user_data

    5 core tools:
        get_personal_profile, get_recent_chat_history, get_wellbeing_trend,
        get_wellbeing_snapshot, compare_wellbeing_weeks

    12 analytics tools:
        get_metric_summary_stats, detect_pattern_shift, get_correlated_factors,
        compute_volatility, detect_anomalies, predict_trend,
        compute_wellbeing_composite, get_rate_of_change, cluster_similar_weeks,
        get_lagged_correlation, get_streaks, estimate_coping_effectiveness

    LLM glue:
        TOOLS, dispatch_tool, SYSTEM_PROMPT, run_agentic_turn

    CLI helpers:
        print_banner, main
"""

from .schema import (
    ALL_METRICS,
    CATEGORY_WEIGHTS,
    EXERCISE_MAX,
    METRIC_CATEGORIES,
    NEGATIVE_POLARITY,
    POLARITY,
    TOP_LEVEL_NUMERIC,
    VALUE_MAX,
)

from .stats import (
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

from .core_tools import (
    compare_wellbeing_weeks,
    get_personal_profile,
    get_recent_chat_history,
    get_wellbeing_snapshot,
    get_wellbeing_trend,
    load_user_data,
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

from .registry import TOOLS, dispatch_tool
from .prompt   import SYSTEM_PROMPT
from .agent    import main, print_banner, run_agentic_turn


# Explicit public surface — required so `from wellbeing import *` exports
# the leading-underscore helpers (math + extraction) too. The originals were
# all module-level in `basic_tools.py`, so we preserve full visibility.
__all__ = [
    # Schema
    "ALL_METRICS", "CATEGORY_WEIGHTS", "EXERCISE_MAX", "METRIC_CATEGORIES",
    "NEGATIVE_POLARITY", "POLARITY", "TOP_LEVEL_NUMERIC", "VALUE_MAX",
    # Math + extraction
    "_compute_composite_score", "_extract_series", "_get_raw_value", "_get_value",
    "_is_negative", "_linear_regression", "_pearson_r", "_safe_mean",
    "_safe_median", "_safe_std",
    # Loader + core tools
    "load_user_data",
    "compare_wellbeing_weeks", "get_personal_profile", "get_recent_chat_history",
    "get_wellbeing_snapshot", "get_wellbeing_trend",
    # Analytics
    "cluster_similar_weeks", "compute_volatility", "compute_wellbeing_composite",
    "detect_anomalies", "detect_pattern_shift", "estimate_coping_effectiveness",
    "get_correlated_factors", "get_lagged_correlation", "get_metric_summary_stats",
    "get_rate_of_change", "get_streaks", "predict_trend",
    # LLM glue + CLI
    "TOOLS", "dispatch_tool", "SYSTEM_PROMPT",
    "run_agentic_turn", "print_banner", "main",
]
