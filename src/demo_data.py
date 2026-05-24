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


DEMO_CONVERSATIONS: dict[str, list[dict[str, str]]] = {
    "demo-delivery-issue": [
        {
            "user": "@ShopHelp my package never arrived and the tracking link has not changed in 5 days.",
            "bot": "I am sorry your package has not arrived. I can help investigate the delivery, but I will need the order or tracking ID first so the support team can check the shipment safely.",
        },
        {
            "user": "The order number is ORD-2026-5678.",
            "bot": "Thank you. I have the order reference and I am checking this as a delivery issue; please do not post your address or phone number here. If the courier scan is still stale, the next step is to open a delivery investigation.",
        },
        {
            "user": "Can I get a status update before tomorrow morning?",
            "bot": "I understand the timing matters. I will keep this under the same delivery case and escalate it for a status update, using order ORD-2026-5678 as the reference.",
        },
    ],
    "demo-refund-request": [
        {
            "user": "I want a refund for order REF-2026-12345.",
            "bot": "I can help start the refund request for that order. Please tell me the reason for the refund so the support team can review the case correctly.",
        },
        {
            "user": "The product does not match the description and the color is different from the photo.",
            "bot": "Thank you for explaining the issue. I will record the reason as product not as described and move this refund request to review; please keep any photos or packaging details ready if the team asks for evidence.",
        },
        {
            "user": "Do I need to return it first?",
            "bot": "The return requirement depends on the product and policy, so I should not promise approval here. The support team can confirm the exact next step after reviewing order REF-2026-12345.",
        },
    ],
    "demo-low-confidence": [
        {
            "user": "help",
            "bot": "I can help, but I need one more detail first. Is this about delivery, refund, payment, account access, technical support, product information, or feedback?",
        },
        {
            "user": "payment, I think my card was charged twice",
            "bot": "Thanks for clarifying. I can treat this as a payment issue; please share the order ID and approximate charge time, but do not send full card details.",
        },
    ],
    "demo-account-access": [
        {
            "user": "I cannot access my account after changing my phone.",
            "bot": "I am sorry you cannot access the account. I can help with account recovery; please share the email or username linked to the account, but do not send your password.",
        },
        {
            "user": "Username is dana_support, and the reset code never arrives.",
            "bot": "Thank you. I will keep this as an account access case and check the password reset flow for username dana_support. If you can, confirm whether the code is missing from both inbox and spam.",
        },
        {
            "user": "It is not in spam either.",
            "bot": "Understood. Since the reset code is not arriving, the next step is to escalate account recovery to the support team without asking for sensitive credentials.",
        },
    ],
    "demo-technical-checkout": [
        {
            "user": "The app has a bug and crashes with an error at checkout.",
            "bot": "I can help troubleshoot that checkout crash. Please tell me your device, app version, and any error message you see so the technical team can reproduce it.",
        },
        {
            "user": "Android 14, app version 5.8.2, error says checkout session expired.",
            "bot": "Thank you for the details. I will record this as a technical support issue involving Android 14, app version 5.8.2, and the checkout session expired error.",
        },
        {
            "user": "Same error, should I try again?",
            "bot": "Before trying again, please check whether your bank shows a completed charge. If there is no completed charge, restarting the app and retrying once is reasonable; if a charge appears, contact support with the order reference first.",
        },
    ],
    "demo-product-question-positive": [
        {
            "user": "Is the black wireless headphones product available in stock, and what details are listed?",
            "bot": "I can help with product information. Please tell me the exact model or product link so I can check availability more accurately.",
        },
        {
            "user": "The SonicAir Pro model.",
            "bot": "Thanks. I will treat this as a product availability question for SonicAir Pro in black and route it to the product information flow.",
        },
        {
            "user": "Great, thank you for the quick help.",
            "bot": "You are welcome. I will record this as positive feedback and keep the product question attached to the same conversation.",
        },
    ],
}


def seed_demo_conversations() -> int:
    """Insert demo sessions once so the sidebar has saved conversations to show."""
    init_database()
    seeded = 0

    for session_id, turns in DEMO_CONVERSATIONS.items():
        delete_session(session_id)

        for turn in turns:
            user_message = turn["user"]
            history = load_recent_interactions(session_id)
            intent_result = resolve_intent_with_context(
                classify_intent(user_message),
                user_message,
                history,
            )
            sentiment_result = analyze_sentiment(user_message)
            urgency_result = detect_urgency(user_message)
            bot_response = turn.get("bot") or build_response(
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
