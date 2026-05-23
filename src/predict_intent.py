from __future__ import annotations

from src.intent_classifier import classify_intent


def predict_intent(message: str) -> dict[str, object]:
    """Return the intent classification result for a single message."""
    return classify_intent(message)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python src/predict_intent.py '<message>'")
        sys.exit(1)

    message = sys.argv[1]
    result = predict_intent(message)
    print(result)
