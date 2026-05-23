"""Progressive conversation state management for multi-turn support."""

from __future__ import annotations

from typing import Any
import re


STATEFUL_INTENTS = {
    "account_problem",
    "delivery_issue",
    "refund_request",
    "technical_support",
    "payment_issue",
}

LIKELY_MISCLASSIFIED_AS = {
    "general_question",
    "payment_issue",
    "product_information",
    "technical_support"
}


class ConversationState:
    """Track what information has been collected in the current support case."""

    def __init__(self, history: list[dict[str, Any]], current_message: str = ""):
        self.history = history
        self.current_message = current_message
        self.collected_info = self._extract_collected_info()
        self.current_intent = self._get_locked_intent()

    def _get_locked_intent(self) -> str:
        for interaction in reversed(self.history):
            intent = str(interaction.get("intent") or "")
            if intent and intent in STATEFUL_INTENTS:
                return intent
        for interaction in reversed(self.history):
            intent = str(interaction.get("intent") or "")
            if intent and intent != "general_question":
                return intent
        return "general_question"

    def _extract_collected_info(self) -> dict[str, Any]:
        info = {
            "has_order_id": False,
            "has_email": False,
            "has_phone": False,
            "has_refund_reason": False,
            "has_error_message": False,
            "turn_count": len(self.history),
        }

        all_messages = [
            str(interaction.get("user_message") or "")
            for interaction in self.history
        ]
        if self.current_message:
            all_messages.append(self.current_message)

        for msg in all_messages:
            msg_lower = msg.lower()

            # Email
            if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", msg):
                info["has_email"] = True

            # Phone
            if re.search(r"\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", msg):
                info["has_phone"] = True

            # Order/tracking ID — prinde: "order #20323", "tracking id is 20323",
            # "my tracking id from my order is 20323", sau orice numar 4+ cifre
            if re.search(
                r"\b(order|tracking|ticket|reference|ref|case)[\s\w#:.-]{0,20}?([a-z0-9]{4,})\b",
                msg_lower,
            ):
                info["has_order_id"] = True
            elif re.search(r"\b\d{4,}\b", msg):
                # Fallback: numar standalone de 4+ cifre = tracking number
                info["has_order_id"] = True

            # Refund reason
            if re.search(
                r"(defect|broken|damage|wrong|late|not.*work|poor|bad|unwant|never arriv|missing|lost)",
                msg_lower,
            ):
                info["has_refund_reason"] = True

            # Error / technical description
            if re.search(
                r"(error|fail|crash|freeze|lag|won'?t|cannot|not.*work|doesn'?t|bug|glitch)",
                msg_lower,
            ):
                info["has_error_message"] = True

        return info

    def should_force_keep_intent(self, new_intent: str) -> bool:
        if self.current_intent not in STATEFUL_INTENTS:
            return False
        if len(self.history) == 0:
            return False

        if new_intent in LIKELY_MISCLASSIFIED_AS:
            return True

        info_collected = (
            self.collected_info["has_email"]
            or self.collected_info["has_order_id"]
            or self.collected_info["has_error_message"]
        )
        if info_collected and new_intent != self.current_intent:
            return True

        return False

    def get_next_step(self, intent: str) -> str | None:
        info = self.collected_info

        if intent == "account_problem":
            if not info["has_email"]:
                return "ask_email"
            return "provide_help"

        if intent == "delivery_issue":
            if not info["has_order_id"]:
                return "ask_order_id"
            return "provide_help"

        if intent == "refund_request":
            if not info["has_order_id"]:
                return "ask_order_id"
            if not info["has_refund_reason"]:
                return "ask_refund_reason"
            return "provide_help"

        if intent == "technical_support":
            if not info["has_error_message"]:
                return "ask_error_message"
            return "provide_help"

        if intent == "payment_issue":
            if not info["has_order_id"]:
                return "ask_order_id"
            return "provide_help"

        return None