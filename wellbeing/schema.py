"""
schema.py
─────────
Static definitions of the wellbeing-frame schema:
  • Category → sub-dimension map with polarity ("+", "-", "0")
  • Flattened metric paths and helper lookups
  • Top-level numeric fields (not under a category)
  • Value ranges and composite-score category weights
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY DEFINITIONS
# Each frame nests categories → sub-dimensions → {value: 0-5, description}.
# Polarity: "+" higher = better wellbeing, "-" higher = worse, "0" neutral.
# ─────────────────────────────────────────────────────────────────────────────

METRIC_CATEGORIES = {
    "emotions": {
        "calm_neutral":            "+",
        "happy_positive":          "+",
        "anxious_worried":         "-",
        "sad_low":                 "-",
        "angry_irritable":         "-",
        "lonely":                  "-",
        "overwhelmed":             "-",
        "numb_emotionally_flat":   "-",
    },
    "stresses": {
        "work_academic":              "-",
        "relationship":               "-",
        "health_related":             "-",
        "financial":                  "-",
        "time_pressure_overload":     "-",
        "uncertainty_future_anxiety": "-",
        "internal_pressure":          "-",
        "low_manageable":             "+",   # high score = stress feels manageable
    },
    "cognitive_patterns": {
        "balanced_realistic":       "+",
        "rumination":               "-",
        "catastrophizing":          "-",
        "black_and_white":          "-",
        "self_critical":            "-",
        "helplessness_low_control": "-",
        "overanalysis_indecision":  "-",
        "positive_reframing":       "+",
    },
    "motivation_values": {
        "highly_motivated_goal_driven": "+",
        "moderate_motivation":          "+",
        "low_motivation_disengaged":    "-",
        "anhedonia_loss_of_interest":   "-",
        "purpose_driven":               "+",
        "value_conflict":               "-",
        "directionless_unclear_goals":  "-",
    },
    "sleep": {
        "restful_healthy":      "+",
        "mild_disturbance":     "-",
        "insufficient_sleep":   "-",
        "insomnia":             "-",
        "irregular_schedule":   "-",
        "oversleeping_fatigue": "-",
    },
    "energy": {
        "high_energized":    "+",
        "stable_normal":     "+",
        "low_tired":         "-",
        "exhausted_drained": "-",
        "fluctuating":       "-",
        "restless_wired":    "-",
    },
    "personality": {
        "optimistic":                "+",
        "pessimistic":               "-",
        "self_confident":            "+",
        "self_doubting":             "-",
        "emotionally_reactive":      "-",
        "emotionally_stable":        "+",
        "introverted":               "0",   # neutral disposition
        "socially_expressive":       "+",
        "conscientious_disciplined": "+",
        "avoidant_tendency":         "-",
    },
    "habits": {
        "structured_healthy_routines": "+",
        "productive_habits":           "+",
        "inconsistent_routines":       "-",
        "procrastination":             "-",
        "avoidance_behaviors":         "-",
        "compulsive_behaviors":        "-",
        "self_care_present":           "+",
        "self_care_neglect":           "-",
    },
    "social": {
        "strong_support_system": "+",
        "moderate_support":      "+",
        "limited_support":       "-",
        "socially_isolated":     "-",
        "active_engagement":     "+",
        "relationship_conflict": "-",
        "help_seeking_behavior": "+",
        "withdrawing":           "-",
    },
}

# Flattened lookups
ALL_METRICS       = [f"{cat}.{sub}" for cat, subs in METRIC_CATEGORIES.items() for sub in subs]
POLARITY          = {f"{cat}.{sub}": pol for cat, subs in METRIC_CATEGORIES.items() for sub, pol in subs.items()}
NEGATIVE_POLARITY = {p for p, pol in POLARITY.items() if pol == "-"}

# Top-level numerics (not under a category)
TOP_LEVEL_NUMERIC = {"exercise_minutes": "+"}

# Value ranges
VALUE_MAX    = 5      # every sub-dim value
EXERCISE_MAX = 120    # minutes

# Category weights for composite wellbeing score (sum to 1.0)
CATEGORY_WEIGHTS = {
    "emotions":           0.20,
    "stresses":           0.15,
    "cognitive_patterns": 0.15,
    "sleep":              0.15,
    "motivation_values":  0.10,
    "energy":             0.10,
    "habits":             0.05,
    "social":             0.05,
    "personality":        0.05,
}
