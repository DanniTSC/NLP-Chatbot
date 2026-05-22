"""Intent classifier facade with real model loading and mock fallback."""

from __future__ import annotations

import math
from typing import Any

import joblib

from src.config import MODELS_DIR
from src.mock_classifier import classify_intent as classify_intent_mock


VECTORIZER_PATH = MODELS_DIR / "vectorizer.pkl"
CLASSIFIER_PATH = MODELS_DIR / "intent_classifier.pkl"

_MODEL_BUNDLE: tuple[Any, Any] | None = None
_MODEL_LOAD_ATTEMPTED = False


def _load_model_bundle() -> tuple[Any, Any] | None:
    """Load vectorizer and classifier once, or return None for mock fallback."""
    global _MODEL_BUNDLE, _MODEL_LOAD_ATTEMPTED

    if _MODEL_LOAD_ATTEMPTED:
        return _MODEL_BUNDLE

    _MODEL_LOAD_ATTEMPTED = True
    if not VECTORIZER_PATH.exists() or not CLASSIFIER_PATH.exists():
        return None

    try:
        vectorizer = joblib.load(VECTORIZER_PATH)
        classifier = joblib.load(CLASSIFIER_PATH)
    except Exception:
        _MODEL_BUNDLE = None
        return None

    _MODEL_BUNDLE = (vectorizer, classifier)
    return _MODEL_BUNDLE


def _clamp_confidence(value: float) -> float:
    """Keep confidence inside the same 0-1 range used by the mock classifier."""
    return round(max(0.0, min(value, 1.0)), 2)


def _find_class_index(classes: Any, predicted_intent: str) -> int | None:
    """Find the predicted class index while tolerating non-string labels."""
    for index, class_label in enumerate(classes):
        if str(class_label) == predicted_intent:
            return index

    return None


def _as_list(value: Any) -> list[Any]:
    """Convert numpy/scipy-like outputs into plain Python lists."""
    if hasattr(value, "tolist"):
        converted = value.tolist()
    else:
        converted = value

    if isinstance(converted, list):
        return converted

    return [converted]


def _confidence_from_predict_proba(
    classifier: Any,
    features: Any,
    predicted_intent: str,
) -> float | None:
    """Read confidence from classifiers that expose predict_proba."""
    if not hasattr(classifier, "predict_proba"):
        return None

    probabilities = _as_list(classifier.predict_proba(features)[0])
    if not probabilities:
        return None

    class_index = _find_class_index(
        getattr(classifier, "classes_", []),
        predicted_intent,
    )
    if class_index is not None and class_index < len(probabilities):
        return _clamp_confidence(float(probabilities[class_index]))

    return _clamp_confidence(max(float(value) for value in probabilities))


def _confidence_from_decision_function(
    classifier: Any,
    features: Any,
    predicted_intent: str,
) -> float | None:
    """Build a simple confidence proxy for classifiers without probabilities."""
    if not hasattr(classifier, "decision_function"):
        return None

    scores = _as_list(classifier.decision_function(features))
    if len(scores) == 1 and isinstance(scores[0], list):
        scores = scores[0]
    if not scores:
        return None

    classes = getattr(classifier, "classes_", [])
    class_index = _find_class_index(classes, predicted_intent)

    if len(scores) == 1:
        raw_score = float(scores[0])
        if class_index == 0 and len(classes) == 2:
            raw_score = -raw_score
    elif class_index is not None and class_index < len(scores):
        raw_score = float(scores[class_index])
    else:
        raw_score = max(float(value) for value in scores)

    raw_score = max(min(raw_score, 20.0), -20.0)
    confidence = 1 / (1 + math.exp(-raw_score))
    return _clamp_confidence(confidence)


def _estimate_confidence(classifier: Any, features: Any, predicted_intent: str) -> float:
    """Estimate model confidence while supporting common scikit-learn classifiers."""
    proba_confidence = _confidence_from_predict_proba(
        classifier,
        features,
        predicted_intent,
    )
    if proba_confidence is not None:
        return proba_confidence

    decision_confidence = _confidence_from_decision_function(
        classifier,
        features,
        predicted_intent,
    )
    if decision_confidence is not None:
        return decision_confidence

    return 0.75


def classify_intent(message: str) -> dict[str, Any]:
    """Classify intent with the real model when available, otherwise use the mock."""
    model_bundle = _load_model_bundle()
    if model_bundle is None:
        return classify_intent_mock(message)

    vectorizer, classifier = model_bundle

    try:
        features = vectorizer.transform([message])
        prediction = classifier.predict(features)
        intent = str(prediction[0])
        confidence = _estimate_confidence(classifier, features, intent)
    except Exception:
        return classify_intent_mock(message)

    return {
        "intent": intent,
        "confidence": confidence,
        "matched_keywords": [],
    }
