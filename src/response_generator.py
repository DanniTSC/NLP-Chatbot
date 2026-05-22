"""Template-based response generation for the chatbot MVP."""

from __future__ import annotations

from typing import Any

from src.config import LOW_CONFIDENCE_THRESHOLD
from src.conversation_memory import find_latest_specific_intent, find_order_reference


INTENT_RESPONSES = {
    "delivery_issue": (
        "I can help with the delivery issue. Please send your order ID so I can "
        "check the package status and tracking details."
    ),
    "refund_request": (
        "I can help start a refund request. Please send your order ID and a short "
        "reason for the refund so the case can be reviewed."
    ),
    "payment_issue": (
        "I can help with the payment issue. Please confirm the payment method and "
        "whether you were charged once or multiple times."
    ),
    "account_problem": (
        "I can help with the account problem. Please share the email or username "
        "linked to the account, but do not send your password."
    ),
    "technical_support": (
        "I can help troubleshoot this. Please describe what device or browser you "
        "are using and the exact error message you see."
    ),
    "product_information": (
        "I can help with product information. Please tell me which product you are "
        "asking about and what detail you need."
    ),
    "complaint": (
        "I understand this is a complaint. Please share the order ID or case details "
        "so the support team can review the situation."
    ),
    "positive_feedback": (
        "Thank you for the feedback. I will record this as positive customer feedback "
        "for the support team."
    ),
    "general_question": (
        "I can help route your request. Please tell me if this is about delivery, "
        "refunds, payments, account access, technical support, or product details."
    ),
}


INTENT_RESPONSES_WITH_REFERENCE = {
    "delivery_issue": (
        "I have the order/reference ID from the conversation. I can continue with "
        "the delivery investigation and check the package status in this demo flow."
    ),
    "refund_request": (
        "I have the order/reference ID from the conversation. I can continue the "
        "refund request; please add the refund reason if you have not already."
    ),
    "complaint": (
        "I have the order/reference ID from the conversation. I will keep it linked "
        "to this complaint so the support team can review the case details."
    ),
}


def build_response(
    intent_result: dict[str, Any],
    sentiment_result: dict[str, Any],
    urgency_result: dict[str, Any],
    conversation_history: list[dict[str, Any]] | None = None,
    user_message: str = "",
) -> str:
    """Build a support response from intent, sentiment, and urgency signals."""
    history = conversation_history or []
    intent = str(intent_result["intent"])
    confidence = float(intent_result["confidence"])
    sentiment = str(sentiment_result["sentiment"])
    urgency = str(urgency_result["urgency"])
    previous_intent = find_latest_specific_intent(history)
    order_reference = find_order_reference(user_message, history)

    if (
        confidence < LOW_CONFIDENCE_THRESHOLD
        and intent == "general_question"
        and previous_intent is not None
    ):
        intent = previous_intent

    if confidence < LOW_CONFIDENCE_THRESHOLD and previous_intent is None:
        main_response = (
            "I am not fully sure how to classify this request yet. Could you add "
            "one more detail about the problem, such as delivery, refund, payment, "
            "account, technical support, or product information?"
        )
    else:
        if order_reference and intent in INTENT_RESPONSES_WITH_REFERENCE:
            main_response = INTENT_RESPONSES_WITH_REFERENCE[intent]
        else:
            main_response = INTENT_RESPONSES.get(
                intent,
                INTENT_RESPONSES["general_question"],
            )

    prefixes: list[str] = []
    if sentiment == "negative":
        prefixes.append("I am sorry you are dealing with this.")
    elif urgency in {"medium", "high"}:
        prefixes.append("I understand this needs attention.")
    if urgency == "high":
        prefixes.append(
            "I will treat this as a high-priority support case in this demo flow."
        )

    return " ".join([*prefixes, main_response])
