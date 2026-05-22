"""Shared configuration for the MVP chatbot application."""

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
