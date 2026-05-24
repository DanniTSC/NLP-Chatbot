"""Optional local GPT-style response generation using Ollama."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    USE_LOCAL_GPT,
)


SYSTEM_PROMPT = """You are a customer support chatbot for social media.
Write a short, professional, empathetic response.
Do not invent order status, refund approval, payment status, or account details.
Ask for missing information when needed.
Never ask for passwords, full card numbers, CVV codes, or other sensitive secrets.
Use the provided NLP signals as facts. Do not reclassify the user intent.
Return only the final customer-facing response, with no labels or analysis."""

OLLAMA_HEALTH_TIMEOUT_SECONDS = min(1.5, OLLAMA_TIMEOUT_SECONDS)


def _format_context(conversation_history: list[dict[str, Any]]) -> str:
    """Format recent turns compactly for the local model prompt."""
    if not conversation_history:
        return "No previous turns."

    lines: list[str] = []
    for index, turn in enumerate(conversation_history[-5:], start=1):
        user_message = str(turn.get("user_message") or "").strip()
        bot_response = str(turn.get("bot_response") or "").strip()
        intent = str(turn.get("intent") or "unknown")

        lines.append(f"Turn {index} intent: {intent}")
        if user_message:
            lines.append(f"User: {user_message[:500]}")
        if bot_response:
            lines.append(f"Assistant: {bot_response[:500]}")

    return "\n".join(lines)


def build_local_gpt_prompt(
    *,
    user_message: str,
    template_response: str,
    intent_result: dict[str, Any],
    sentiment_result: dict[str, Any],
    urgency_result: dict[str, Any],
    conversation_history: list[dict[str, Any]],
) -> str:
    """Build the user prompt that constrains Ollama to response writing only."""
    matched_keywords = intent_result.get("matched_keywords") or []
    keywords_text = ", ".join(str(item) for item in matched_keywords) or "none"

    return "\n".join(
        [
            "Use the NLP pipeline output below to write the final support reply.",
            "",
            f"Intent: {intent_result.get('intent')}",
            f"Confidence: {intent_result.get('confidence')}",
            f"Matched keywords: {keywords_text}",
            f"Sentiment: {sentiment_result.get('sentiment')} ({sentiment_result.get('score')})",
            f"Urgency: {urgency_result.get('urgency')} ({urgency_result.get('score')})",
            "",
            "Conversation context:",
            _format_context(conversation_history),
            "",
            f"Current user message: {user_message}",
            "",
            "Fallback/template guidance:",
            template_response,
            "",
            "Write 2-4 concise sentences. Keep the same support intent and ask for any missing details.",
        ]
    )


def _clean_model_response(content: str) -> str:
    """Normalize common assistant labels without altering normal prose."""
    cleaned = content.strip()
    for prefix in ("Assistant:", "Bot:", "Response:", "Final response:"):
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()

    return cleaned


def _call_ollama_chat(prompt: str) -> str:
    """Call Ollama's local chat API and return the assistant content."""
    base_url = OLLAMA_BASE_URL.rstrip("/")
    health_request = Request(base_url + "/api/tags", method="GET")
    with urlopen(health_request, timeout=OLLAMA_HEALTH_TIMEOUT_SECONDS):
        pass

    endpoint = base_url + "/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "options": {
            "temperature": 0.25,
            "num_predict": 220,
        },
    }

    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
        raw_body = response.read().decode("utf-8")

    response_payload = json.loads(raw_body)
    content = str(response_payload.get("message", {}).get("content") or "")
    cleaned_content = _clean_model_response(content)
    if not cleaned_content:
        raise ValueError("Ollama returned an empty response.")

    return cleaned_content


async def try_generate_local_gpt_response(
    *,
    user_message: str,
    template_response: str,
    intent_result: dict[str, Any],
    sentiment_result: dict[str, Any],
    urgency_result: dict[str, Any],
    conversation_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Try local GPT generation and report why fallback was used when it fails."""
    if not USE_LOCAL_GPT:
        return {
            "ok": False,
            "response": template_response,
            "source": "template_fallback",
            "error": "local GPT disabled",
        }

    prompt = build_local_gpt_prompt(
        user_message=user_message,
        template_response=template_response,
        intent_result=intent_result,
        sentiment_result=sentiment_result,
        urgency_result=urgency_result,
        conversation_history=conversation_history,
    )

    try:
        response_text = await asyncio.to_thread(_call_ollama_chat, prompt)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "response": template_response,
            "source": "template_fallback",
            "error": str(exc),
        }

    return {
        "ok": True,
        "response": response_text,
        "source": f"local_gpt: {OLLAMA_MODEL}",
        "error": "",
    }
