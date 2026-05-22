"""Small lexicon-based sentiment analyzer for the MVP."""

from __future__ import annotations

import re


POSITIVE_TERMS = {
    "thanks",
    "thank you",
    "great",
    "excellent",
    "amazing",
    "happy",
    "love",
    "perfect",
    "good",
    "helpful",
    "appreciate",
    "satisfied",
}

NEGATIVE_TERMS = {
    "angry",
    "bad",
    "terrible",
    "awful",
    "unacceptable",
    "disappointed",
    "frustrated",
    "furious",
    "worst",
    "hate",
    "broken",
    "late",
    "delayed",
    "didn't arrive",
    "didnt arrive",
    "never arrived",
    "not working",
    "cannot access",
    "can't access",
}


def _normalize(text: str) -> str:
    """Normalize text for lexicon matching."""
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9'\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _count_terms(text: str, terms: set[str]) -> int:
    """Count lexicon terms found in text."""
    count = 0
    for term in terms:
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, text):
            count += 1
    return count


def analyze_sentiment(message: str) -> dict[str, float | str]:
    """Return a simple sentiment label and signed score."""
    normalized = _normalize(message)
    positive_hits = _count_terms(normalized, POSITIVE_TERMS)
    negative_hits = _count_terms(normalized, NEGATIVE_TERMS)
    total_hits = positive_hits + negative_hits

    if total_hits == 0:
        return {"sentiment": "neutral", "score": 0.0}

    score = round((positive_hits - negative_hits) / total_hits, 2)

    if score > 0.15:
        sentiment = "positive"
    elif score < -0.15:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {"sentiment": sentiment, "score": score}
