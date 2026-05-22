"""Demo conversation seeding for the local SQLite database."""

from __future__ import annotations

from src.conversation_memory import (
    delete_session,
    init_database,
    load_recent_interactions,
    save_interaction,
    resolve_intent_with_context,
)
from src.intent_classifier import classify_intent
from src.response_generator import build_response
from src.sentiment import analyze_sentiment
from src.urgency import detect_urgency


DEMO_CONVERSATIONS: dict[str, list[str]] = {
    "demo-delivery-issue": [
        "My package never arrived",
        "The order number is ORD-2024-5678",
        "Can I get a status update?",
    ],
    "demo-refund-request": [
        "I want a refund",
        "Order ID: REF-12345",
        "The product does not match the description",
    ],
    "demo-urgent-payment": [
        "This is unacceptable, I was double charged and need help immediately",
    ],
    "demo-low-confidence": [
        "help",
    ],
}


def seed_demo_conversations() -> int:
    """Insert demo sessions once so the sidebar has saved conversations to show."""
    init_database()
    seeded = 0

    for session_id, messages in DEMO_CONVERSATIONS.items():
        delete_session(session_id)

        for user_message in messages:
            history = load_recent_interactions(session_id)
            intent_result = resolve_intent_with_context(
                classify_intent(user_message),
                user_message,
                history,
            )
            sentiment_result = analyze_sentiment(user_message)
            urgency_result = detect_urgency(user_message)
            bot_response = build_response(
                intent_result,
                sentiment_result,
                urgency_result,
                conversation_history=history,
                user_message=user_message,
            )

            save_interaction(
                session_id=session_id,
                user_message=user_message,
                bot_response=bot_response,
                intent_result=intent_result,
                sentiment_result=sentiment_result,
                urgency_result=urgency_result,
            )

        seeded += 1

    return seeded
