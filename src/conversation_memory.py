"""SQLite-backed conversation memory for the chatbot MVP."""

from __future__ import annotations

import re
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from src.config import DATABASE_DIR, LOW_CONFIDENCE_THRESHOLD, PUBLIC_DIR


DATABASE_PATH = DATABASE_DIR / "chatbot.db"
HISTORY_EXPORT_PATH = PUBLIC_DIR / "conversations.json"
CONTEXT_WINDOW = 5
SHORT_MESSAGE_MAX_WORDS = 4

_ORDER_REFERENCE_RE = re.compile(
    r"\b(?:order(?:\s+id)?|ticket|case|reference|ref|id)"
    r"\s*(?:number|no)?\s*[:#-]?\s*([a-z0-9][a-z0-9-]{3,})\b",
    re.IGNORECASE,
)

_REFUND_REASON_RE = re.compile(
    r"\b(reason|damaged|defective|does not match|wrong item|not as described)\b",
    re.IGNORECASE,
)

_CONTEXT_FOLLOW_UP_TERMS = {
    "also",
    "and",
    "case",
    "continue",
    "here",
    "it",
    "no",
    "order",
    "ref",
    "reference",
    "reason",
    "same",
    "status",
    "still",
    "that",
    "this",
    "ticket",
    "update",
    "yes",
}


def init_database() -> None:
    """Create the SQLite database and conversation table if needed."""
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                intent TEXT NOT NULL,
                confidence REAL NOT NULL,
                sentiment TEXT NOT NULL,
                urgency TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_session_timestamp
            ON conversations (session_id, timestamp)
            """
        )


def load_recent_interactions(
    session_id: str,
    limit: int = CONTEXT_WINDOW,
) -> list[dict[str, Any]]:
    """Load the latest conversation turns for the current Chainlit session."""
    init_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                session_id,
                user_message,
                bot_response,
                intent,
                confidence,
                sentiment,
                urgency,
                timestamp
            FROM conversations
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()

    return [dict(row) for row in reversed(rows)]


def load_session_interactions(session_id: str) -> list[dict[str, Any]]:
    """Load all persisted turns for a session."""
    init_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                session_id,
                user_message,
                bot_response,
                intent,
                confidence,
                sentiment,
                urgency,
                timestamp
            FROM conversations
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def session_exists(session_id: str) -> bool:
    """Return True when a session has at least one saved turn."""
    init_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            "SELECT 1 FROM conversations WHERE session_id = ? LIMIT 1",
            (session_id,),
        ).fetchone()

    return row is not None


def delete_session(session_id: str) -> None:
    """Delete a saved session. Used only for refreshing deterministic demos."""
    init_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "DELETE FROM conversations WHERE session_id = ?",
            (session_id,),
        )


def resolve_session_id(candidate: str) -> str | None:
    """Resolve an exact session id or a unique visible prefix."""
    value = candidate.strip()
    if not value:
        return None
    if session_exists(value):
        return value

    sessions = get_all_sessions(limit=None)
    matches = [
        str(session["session_id"])
        for session in sessions
        if str(session["session_id"]).startswith(value)
    ]

    if len(matches) == 1:
        return matches[0]

    return None


def _truncate_title(value: str, max_length: int = 44) -> str:
    """Build a compact sidebar title from the first user message."""
    clean = re.sub(r"\s+", " ", value).strip()
    if len(clean) <= max_length:
        return clean or "Untitled conversation"

    return f"{clean[: max_length - 3].rstrip()}..."


def get_all_sessions(limit: int | None = 20) -> list[dict[str, Any]]:
    """Get conversation sessions with summary metadata."""
    init_database()

    limit_clause = "" if limit is None else "LIMIT ?"
    parameters: tuple[Any, ...] = () if limit is None else (limit,)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"""
            SELECT
                c.session_id,
                COUNT(*) AS turn_count,
                MAX(c.timestamp) AS last_timestamp,
                GROUP_CONCAT(DISTINCT c.intent) AS intents,
                (
                    SELECT c2.user_message
                    FROM conversations c2
                    WHERE c2.session_id = c.session_id
                    ORDER BY c2.id ASC
                    LIMIT 1
                ) AS first_user_message
            FROM conversations c
            GROUP BY c.session_id
            ORDER BY MAX(c.timestamp) DESC
            {limit_clause}
            """,
            parameters,
        ).fetchall()

    sessions = []
    for row in rows:
        session = dict(row)
        intents = str(session.get("intents") or "")
        intent_list = [item for item in intents.split(",") if item]
        first_message = str(session.get("first_user_message") or "")
        session["title"] = _truncate_title(first_message)
        session["intents"] = intent_list
        session["is_demo"] = str(session["session_id"]).startswith("demo-")
        sessions.append(session)

    return sessions


def format_sessions_for_markdown(sessions: list[dict[str, Any]]) -> str:
    """Format session summaries for a Chainlit Markdown message."""
    if not sessions:
        return "*No previous conversations found.*"

    lines = []
    for index, session in enumerate(sessions, 1):
        intents = session.get("intents") or []
        intent_text = ", ".join(intents[:3]) if intents else "misc"
        timestamp = str(session.get("last_timestamp") or "unknown")
        title = str(session.get("title") or "Untitled conversation")
        session_id = str(session.get("session_id") or "")
        short_id = session_id[:12]
        turn_count = int(session.get("turn_count") or 0)
        demo_flag = " demo" if session.get("is_demo") else ""

        lines.append(
            f"**{index}. {title}**{demo_flag} - "
            f"{turn_count} turns - `{intent_text}` - "
            f"Last: {timestamp[:10]} - ID: `{short_id}`"
        )

    return "\n".join(lines)


def export_history_snapshot(max_sessions: int = 30) -> dict[str, Any]:
    """Export conversation history to a public JSON file for the custom sidebar."""
    sessions = get_all_sessions(limit=max_sessions)
    for session in sessions:
        session["turns"] = load_session_interactions(str(session["session_id"]))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sessions": sessions,
    }

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_EXPORT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def save_interaction(
    *,
    session_id: str,
    user_message: str,
    bot_response: str,
    intent_result: dict[str, Any],
    sentiment_result: dict[str, Any],
    urgency_result: dict[str, Any],
) -> None:
    """Persist one completed user/bot interaction."""
    init_database()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO conversations (
                session_id,
                user_message,
                bot_response,
                intent,
                confidence,
                sentiment,
                urgency,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_message,
                bot_response,
                str(intent_result["intent"]),
                float(intent_result["confidence"]),
                str(sentiment_result["sentiment"]),
                str(urgency_result["urgency"]),
                timestamp,
            ),
        )


def find_latest_specific_intent(
    conversation_history: list[dict[str, Any]],
) -> str | None:
    """Return the most recent non-general intent from previous turns."""
    for interaction in reversed(conversation_history):
        intent = str(interaction.get("intent") or "")
        if intent and intent != "general_question":
            return intent

    return None


def find_order_reference(
    current_message: str,
    conversation_history: list[dict[str, Any]],
) -> str | None:
    """Find an order/reference identifier in the current or previous messages."""
    messages = [current_message]
    messages.extend(str(item.get("user_message") or "") for item in conversation_history)

    for message in messages:
        match = _ORDER_REFERENCE_RE.search(message)
        if match:
            return match.group(1)

    return None


def resolve_intent_with_context(
    intent_result: dict[str, Any],
    current_message: str,
    conversation_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Use previous turns to interpret short, low-confidence follow-up messages."""
    confidence = float(intent_result.get("confidence", 0.0))
    intent = str(intent_result.get("intent") or "")
    previous_intent = find_latest_specific_intent(conversation_history)

    if (
        previous_intent == "refund_request"
        and intent in {"general_question", "product_information"}
        and _REFUND_REASON_RE.search(current_message)
    ):
        contextual_result = dict(intent_result)
        contextual_result["intent"] = previous_intent
        contextual_result["confidence"] = max(confidence, LOW_CONFIDENCE_THRESHOLD)
        contextual_result["matched_keywords"] = ["context:refund_reason"]
        return contextual_result

    if intent != "general_question" or confidence >= LOW_CONFIDENCE_THRESHOLD:
        return intent_result

    if previous_intent is None:
        return intent_result

    normalized_words = re.findall(r"[a-z0-9']+", current_message.lower())
    has_context_marker = bool(
        set(normalized_words).intersection(_CONTEXT_FOLLOW_UP_TERMS)
    )
    is_short_follow_up = len(normalized_words) <= SHORT_MESSAGE_MAX_WORDS
    has_reference = find_order_reference(current_message, conversation_history) is not None

    if not (is_short_follow_up or has_context_marker or has_reference):
        return intent_result

    contextual_result = dict(intent_result)
    contextual_result["intent"] = previous_intent
    contextual_result["confidence"] = max(confidence, LOW_CONFIDENCE_THRESHOLD)
    contextual_result["matched_keywords"] = [f"context:{previous_intent}"]
    return contextual_result
