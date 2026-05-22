"""Rule-based temporary intent classifier for the MVP."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from src.config import AMBIGUOUS_MESSAGES


INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "delivery_issue": (
        "delivery",
        "shipping",
        "shipment",
        "package",
        "parcel",
        "tracking",
        "late",
        "delayed",
        "delay",
        "didn't arrive",
        "didnt arrive",
        "never arrived",
        "not arrived",
        "missing order",
        "lost order",
        "where is my order",
    ),
    "refund_request": (
        "refund",
        "money back",
        "return my money",
        "chargeback",
        "cancel order",
        "cancel my order",
        "return",
        "reimbursement",
    ),
    "payment_issue": (
        "payment",
        "paid",
        "charged",
        "billing",
        "invoice",
        "card",
        "credit card",
        "transaction",
        "double charged",
        "declined",
    ),
    "account_problem": (
        "account",
        "login",
        "log in",
        "password",
        "username",
        "email",
        "blocked account",
        "locked account",
        "cannot access",
        "can't access",
        "reset password",
    ),
    "technical_support": (
        "bug",
        "error",
        "crash",
        "broken",
        "not working",
        "does not work",
        "technical",
        "app issue",
        "website issue",
        "support ticket",
    ),
    "product_information": (
        "product",
        "price",
        "available",
        "availability",
        "stock",
        "features",
        "specifications",
        "details",
        "size",
        "color",
    ),
    "complaint": (
        "complaint",
        "angry",
        "unacceptable",
        "bad service",
        "terrible",
        "awful",
        "disappointed",
        "frustrated",
        "worst",
    ),
    "positive_feedback": (
        "thanks",
        "thank you",
        "great",
        "excellent",
        "amazing",
        "happy",
        "love",
        "perfect",
        "good service",
        "appreciate",
    ),
    "general_question": (
        "question",
        "information",
        "how",
        "what",
        "when",
        "where",
        "can you",
        "do you",
    ),
}


def _normalize(text: str) -> str:
    """Normalize text for simple keyword matching."""
    lowered = text.lower()
    lowered = re.sub(r"https?://\S+|www\.\S+", " ", lowered)
    lowered = re.sub(r"[@#]\w+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9'\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _keyword_matches(normalized_text: str, keywords: tuple[str, ...]) -> list[str]:
    """Return keywords that appear as words or phrases in the message."""
    matches: list[str] = []
    for keyword in keywords:
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, normalized_text):
            matches.append(keyword)
    return matches


def classify_intent(message: str) -> dict[str, Any]:
    """Classify a message into a temporary intent using keyword rules."""
    normalized = _normalize(message)

    if not normalized:
        return {
            "intent": "general_question",
            "confidence": 0.0,
            "matched_keywords": [],
        }

    tokens = normalized.split()
    if normalized in AMBIGUOUS_MESSAGES or len(tokens) == 1:
        return {
            "intent": "general_question",
            "confidence": 0.35,
            "matched_keywords": [],
        }

    scores: Counter[str] = Counter()
    matched_by_intent: dict[str, list[str]] = {}

    for intent, keywords in INTENT_KEYWORDS.items():
        matches = _keyword_matches(normalized, keywords)
        if matches:
            matched_by_intent[intent] = matches
            scores[intent] = sum(2 if " " in item else 1 for item in matches)

    if not scores:
        return {
            "intent": "general_question",
            "confidence": 0.45,
            "matched_keywords": [],
        }

    best_intent, best_score = scores.most_common(1)[0]
    second_score = scores.most_common(2)[1][1] if len(scores) > 1 else 0
    score_gap = max(best_score - second_score, 0)

    confidence = 0.48 + min(best_score * 0.12, 0.36) + min(score_gap * 0.04, 0.12)
    confidence = round(min(confidence, 0.94), 2)

    return {
        "intent": best_intent,
        "confidence": confidence,
        "matched_keywords": matched_by_intent.get(best_intent, []),
    }
