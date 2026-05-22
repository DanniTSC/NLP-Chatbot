"""Rule-based urgency detection for customer support messages."""

from __future__ import annotations

import re


HIGH_URGENCY_TERMS = {
    "urgent",
    "immediately",
    "asap",
    "right now",
    "unacceptable",
    "angry",
    "furious",
    "need help",
    "didn't arrive",
    "didnt arrive",
    "never arrived",
    "blocked",
    "locked out",
    "broken",
    "emergency",
}

MEDIUM_URGENCY_TERMS = {
    "paid",
    "charged",
    "late",
    "delayed",
    "cannot access",
    "can't access",
    "not working",
    "missing",
    "refund",
    "complaint",
}

CRITICAL_URGENCY_TERMS = {
    "urgent",
    "immediately",
    "asap",
    "right now",
    "unacceptable",
    "furious",
    "emergency",
}


def _normalize(text: str) -> str:
    """Normalize text for urgency matching."""
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9'\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _count_matches(text: str, terms: set[str]) -> int:
    """Count urgency terms present in the message."""
    count = 0
    for term in terms:
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, text):
            count += 1
    return count


def detect_urgency(message: str) -> dict[str, float | str]:
    """Detect low, medium, or high urgency with a normalized score."""
    normalized = _normalize(message)
    high_hits = _count_matches(normalized, HIGH_URGENCY_TERMS)
    medium_hits = _count_matches(normalized, MEDIUM_URGENCY_TERMS)
    critical_hits = _count_matches(normalized, CRITICAL_URGENCY_TERMS)

    score = min((high_hits * 0.45) + (medium_hits * 0.2), 1.0)
    if critical_hits:
        score = max(score, 0.75)
    score = round(score, 2)

    if score >= 0.65:
        urgency = "high"
    elif score >= 0.25:
        urgency = "medium"
    else:
        urgency = "low"

    return {"urgency": urgency, "score": score}
