"""Shared configuration for the MVP chatbot application."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATABASE_DIR = BASE_DIR / "database"
OUTPUTS_DIR = BASE_DIR / "outputs"
PUBLIC_DIR = BASE_DIR / "public"

APP_NAME = "Social Support NLP Chatbot"
APP_DESCRIPTION = (
    "Academic MVP for social media customer support using classic NLP signals."
)

LOW_CONFIDENCE_THRESHOLD = 0.55
SHOW_NLP_METADATA = True


def _env_bool(name: str, default: bool) -> bool:
    """Read a permissive boolean environment flag."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    """Read a float environment setting with a safe default."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError:
        return default


USE_LOCAL_GPT = _env_bool("USE_LOCAL_GPT", False)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT_SECONDS = _env_float("OLLAMA_TIMEOUT_SECONDS", 20.0)

INTENTS = (
    "delivery_issue",
    "refund_request",
    "payment_issue",
    "account_problem",
    "technical_support",
    "product_information",
    "complaint",
    "positive_feedback",
    "general_question",
)

AMBIGUOUS_MESSAGES = {
    "help",
    "hello",
    "hi",
    "hey",
    "support",
    "problem",
    "issue",
}
