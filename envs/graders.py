"""Deterministic graders for BugTriage tasks.

Each grader returns a score in [0.0, 1.0].
"""

from typing import Any, Dict


def grade_easy(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """Easy grader: severity, component, label all required."""
    score = 0.0
    weights = {"severity": 0.4, "component": 0.3, "label": 0.3}

    if str(state.get("assigned_severity", "")).lower() == ground_truth["severity"]:
        score += weights["severity"]
    if str(state.get("assigned_component", "")).lower() == ground_truth["component"]:
        score += weights["component"]
    if str(state.get("assigned_label", "")).lower() == ground_truth["label"]:
        score += weights["label"]

    return round(0.01 + 0.98 * min(score, 1.0), 4)


def grade_medium(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """Medium grader: severity, component, label, and duplicate detection."""
    score = 0.0
    weights = {"severity": 0.25, "component": 0.25, "label": 0.2, "duplicate_of": 0.3}

    if str(state.get("assigned_severity", "")).lower() == ground_truth["severity"]:
        score += weights["severity"]
    if str(state.get("assigned_component", "")).lower() == ground_truth["component"]:
        score += weights["component"]
    if str(state.get("assigned_label", "")).lower() == ground_truth["label"]:
        score += weights["label"]

    assigned_dup = str(state.get("duplicate_of", "")).strip()
    expected_dup = ground_truth.get("duplicate_of")
    if expected_dup is not None and assigned_dup == expected_dup:
        score += weights["duplicate_of"]
    elif expected_dup is None and assigned_dup in ("", "none", "null"):
        score += weights["duplicate_of"]

    return round(0.01 + 0.98 * min(score, 1.0), 4)


def grade_hard(state: Dict[str, Any], ground_truth: Dict[str, Any]) -> float:
    """Hard grader: severity, component, label, and summary quality."""
    score = 0.0
    weights = {"severity": 0.2, "component": 0.2, "label": 0.15,
               "duplicate_of": 0.15, "summary": 0.3}

    if str(state.get("assigned_severity", "")).lower() == ground_truth["severity"]:
        score += weights["severity"]
    if str(state.get("assigned_component", "")).lower() == ground_truth["component"]:
        score += weights["component"]
    if str(state.get("assigned_label", "")).lower() == ground_truth["label"]:
        score += weights["label"]

    # Duplicate check - only if ground truth explicitly requires it
    expected_dup = ground_truth.get("duplicate_of")
    if expected_dup is not None:
        assigned_dup = str(state.get("duplicate_of", "")).strip()
        if assigned_dup.lower() == expected_dup.lower():
            score += weights["duplicate_of"]
    # If no duplicate expected and state explicitly set to none, award partial
    elif expected_dup is None and str(state.get("duplicate_of", "")).strip() in ("none",):
        score += weights["duplicate_of"]

    # Summary scoring - only counts if summary is non-empty
    summary = str(state.get("summary", "")).strip()
    min_length = ground_truth.get("summary_min_length", 20)
    required_terms = ground_truth.get("summary_required_terms", [])

    if summary and len(summary) >= min_length:
        score += weights["summary"] * 0.5  # Half for meeting length

        # Check required terms (case-insensitive)
        summary_lower = summary.lower()
        terms_found = sum(1 for t in required_terms if t.lower() in summary_lower)
        if required_terms:
            score += weights["summary"] * 0.5 * (terms_found / len(required_terms))

    return round(0.01 + 0.98 * min(score, 1.0), 4)


GRADERS = {
    "bug_triage_easy": grade_easy,
    "bug_triage_medium": grade_medium,
    "bug_triage_hard": grade_hard,
}
