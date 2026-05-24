"""Template-based response generation with progressive conversation state."""

from __future__ import annotations

from typing import Any

from src.config import LOW_CONFIDENCE_THRESHOLD
from src.conversation_memory import find_latest_specific_intent, find_order_reference
from src.conversation_state import ConversationState


PROGRESSIVE_RESPONSES = {
    "account_problem": {
        "ask_email": "To look into your account, could you share the email or username linked to it? Please do not send your password.",
        "provide_help": "Thank you! I have your email on file. Let me pull up your account and help you reset your password now.",
        "confirm_resolution": "Is there anything else I can help you with regarding your account?",
    },
    "delivery_issue": {
        "ask_order_id": "To look into the delivery, I will need your order or tracking ID.",
        "provide_help": "Got it — I have your tracking ID and I am checking the status of your package now.",
        "confirm_resolution": "I hope that helps with your delivery issue. Do you need any other assistance?",
    },
    "refund_request": {
        "ask_order_id": "To start a refund request, I will need your order ID.",
        "ask_refund_reason": "Thank you for the order ID. Could you briefly explain why you are requesting a refund?",
        "provide_help": "I have all the details I need. I am escalating your refund request to our support team for review.",
        "confirm_resolution": "Your refund case has been submitted. Is there anything else I can help with?",
    },
    "technical_support": {
        "ask_error_message": "To help troubleshoot, could you share the exact error message or describe what is happening?",
        "provide_help": "Thank you for the details. I am working on resolving this technical issue for you now.",
        "confirm_resolution": "Has this resolved your issue, or is there more I can help with?",
    },
    "payment_issue": {
        "ask_order_id": "To investigate the payment issue, I will need your order ID.",
        "provide_help": "I am reviewing your payment details now to find out what went wrong and how to fix it.",
        "confirm_resolution": "Is your payment issue now resolved, or do you need further assistance?",
    },
}


INTENT_RESPONSES = {
    "delivery_issue": "I can help with the delivery issue. Please send your order or tracking ID so I can check the package status.",
    "refund_request": "I can help start a refund request. Please send your order ID and a short reason for the refund.",
    "payment_issue": "I can help with the payment issue. Please confirm the payment method and whether you were charged once or multiple times.",
    "account_problem": "I can help with the account problem. Please share the email or username linked to the account, but do not send your password.",
    "technical_support": "I can help troubleshoot this. Please describe what device or browser you are using and the exact error message you see.",
    "product_information": "I can help with product information. Please tell me which product you are asking about and what detail you need.",
    "complaint": "I understand this is a complaint. Please share the order ID or case details so the support team can review the situation.",
    "positive_feedback": "Thank you for the feedback. I will record this as positive customer feedback for the support team.",
    "general_question": "I can help route your request. Please tell me if this is about delivery, refunds, payments, account access, technical support, or product details.",
}


def build_response(
    intent_result: dict[str, Any],
    sentiment_result: dict[str, Any],
    urgency_result: dict[str, Any],
    conversation_history: list[dict[str, Any]] | None = None,
    user_message: str = "",
) -> str:
    """Build a support response with progressive multi-turn conversation logic."""
    history = conversation_history or []
    intent = str(intent_result["intent"])
    confidence = float(intent_result["confidence"])
    sentiment = str(sentiment_result["sentiment"])
    urgency = str(urgency_result["urgency"])

    # Starea conversatiei — include mesajul curent pentru detectare corecta
    state = ConversationState(history, current_message=user_message)

    # Decidem intentul final
    if state.should_force_keep_intent(intent):
        intent = state.current_intent
    elif confidence < LOW_CONFIDENCE_THRESHOLD:
        previous_intent = find_latest_specific_intent(history)
        if previous_intent:
            intent = previous_intent

    # Construim raspunsul principal
    if confidence < LOW_CONFIDENCE_THRESHOLD and not history:
        main_response = (
            "I am not fully sure how to classify this request yet. Could you add "
            "one more detail — for example, is this about a delivery, refund, "
            "payment, account, technical issue, or product?"
        )
    else:
        next_step = state.get_next_step(intent)

        if next_step and intent in PROGRESSIVE_RESPONSES and next_step in PROGRESSIVE_RESPONSES[intent]:
            main_response = PROGRESSIVE_RESPONSES[intent][next_step]
        else:
            order_reference = find_order_reference(user_message, history)
            if order_reference and intent in {"delivery_issue", "refund_request", "complaint"}:
                main_response = PROGRESSIVE_RESPONSES.get(intent, {}).get(
                    "provide_help",
                    INTENT_RESPONSES.get(intent, INTENT_RESPONSES["general_question"]),
                )
            else:
                main_response = INTENT_RESPONSES.get(intent, INTENT_RESPONSES["general_question"])

    # Prefix empatie/urgenta
    prefixes: list[str] = []
    if sentiment == "negative":
        prefixes.append("I am sorry you are dealing with this.")
    elif urgency in {"medium", "high"}:
        prefixes.append("I understand this needs attention.")
    if urgency == "high":
        prefixes.append("I will treat this as a high-priority case.")

    response_text = " ".join([*prefixes, main_response])
    return response_text
