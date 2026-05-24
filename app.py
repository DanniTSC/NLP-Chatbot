"""Chainlit application for the Social Media Customer Support Chatbot MVP."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import chainlit as cl
from chainlit.chat_context import chat_context
from chainlit.context import init_ws_context
from chainlit.server import app as fastapi_app
from chainlit.session import WebsocketSession
from fastapi import HTTPException, Request
from pydantic import BaseModel

from src.config import APP_DESCRIPTION, APP_NAME, SHOW_NLP_METADATA
from src.conversation_memory import export_history_snapshot
from src.conversation_memory import format_sessions_for_markdown
from src.conversation_memory import get_all_sessions
from src.conversation_memory import init_database
from src.conversation_memory import load_recent_interactions
from src.conversation_memory import load_session_interactions
from src.conversation_memory import resolve_intent_with_context
from src.conversation_memory import resolve_session_id
from src.conversation_memory import save_interaction
from src.demo_data import seed_demo_conversations
from src.intent_classifier import classify_intent
from src.llm_response_generator import try_generate_local_gpt_response
from src.response_generator import build_response
from src.sentiment import analyze_sentiment
from src.urgency import detect_urgency
from src.preprocessing import clean_text
from src.conversation_state import ConversationState

# Import logging for NLP pipeline visibility
import logging

# Configure logging for the NLP pipeline
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




MAX_REPLAY_TURNS = 80
CHAINLIT_SESSION_COOKIE = "X-Chainlit-Session-id"
HISTORY_OPEN_ROUTE = "/history/open"
HISTORY_NEW_ROUTE = "/history/new"


class OpenHistoryRequest(BaseModel):
    """Payload sent by the custom browser sidebar."""

    session_id: str


def _format_percent(value: float) -> str:
    """Format a 0-1 score as a percentage string."""
    return f"{value * 100:.0f}%"


def build_metadata_block(
    intent_result: dict[str, Any],
    sentiment_result: dict[str, Any],
    urgency_result: dict[str, Any],
    response_source: str,
) -> str:
    """Create a compact Markdown block with NLP metadata for the demo."""
    matched_keywords = intent_result.get("matched_keywords") or []
    keywords_text = ", ".join(matched_keywords) if matched_keywords else "none"

    return (
        "\n\n---\n"
        "**NLP metadata**\n\n"
        "| Signal | Value |\n"
        "| --- | --- |\n"
        f"| Intent | `{intent_result['intent']}` |\n"
        f"| Confidence | `{_format_percent(float(intent_result['confidence']))}` |\n"
        f"| Matched keywords | `{keywords_text}` |\n"
        f"| Sentiment | `{sentiment_result['sentiment']}` "
        f"(`{sentiment_result['score']}`) |\n"
        f"| Urgency | `{urgency_result['urgency']}` "
        f"(`{urgency_result['score']}`) |\n"
        f"| Response source | `{response_source}` |\n"
    )


async def run_nlp_pipeline(
    user_message: str,
    session_id: str,
) -> dict[str, Any]:
    """Execute the complete NLP pipeline."""

    # STEP 1: Preprocessing
    cleaned_text = clean_text(user_message)
    logger.info(f"[PREPROCESSING] {user_message[:60]} -> {cleaned_text[:60]}")

    # STEP 2: Load conversation context
    conversation_history = load_recent_interactions(str(session_id))
    logger.info(f"[CONTEXT] {len(conversation_history)} turns loaded")

    # STEP 3: Intent classification (raw)
    intent_result = classify_intent(cleaned_text)
    logger.info(f"[INTENT] raw={intent_result['intent']} ({intent_result['confidence']:.0%})")

    # STEP 4: Refine intent with context, then compute sentiment + urgency
    intent_result = resolve_intent_with_context(
        intent_result,
        cleaned_text,
        conversation_history,
    )

    sentiment_result = analyze_sentiment(cleaned_text)
    urgency_result = detect_urgency(cleaned_text)

    state = ConversationState(conversation_history, current_message=user_message)
    if state.should_force_keep_intent(intent_result["intent"]):
        intent_result = {**intent_result, "intent": state.current_intent}

    # STEP 5: Build safe template response, then optionally rewrite with local GPT.
    template_response = build_response(
        intent_result, sentiment_result, urgency_result,
        conversation_history=conversation_history,
        user_message=user_message,
    )
    llm_result = await try_generate_local_gpt_response(
        user_message=user_message,
        template_response=template_response,
        intent_result=intent_result,
        sentiment_result=sentiment_result,
        urgency_result=urgency_result,
        conversation_history=conversation_history,
    )
    bot_response = str(llm_result["response"])
    response_source = str(llm_result["source"])

    logger.info(f"[INTENT] corrected={intent_result['intent']}")
    if not llm_result["ok"] and llm_result.get("error"):
        logger.info(f"[LOCAL_GPT] fallback used: {llm_result['error']}")
    else:
        logger.info(f"[LOCAL_GPT] response source={response_source}")
    logger.info(f"[RESPONSE] {bot_response[:80]}")

    return {
        "user_message": user_message,
        "cleaned_text": cleaned_text,
        "intent_result": intent_result,   # <-- intentul corectat, nu raw
        "sentiment_result": sentiment_result,
        "urgency_result": urgency_result,
        "bot_response": bot_response,
        "response_source": response_source,
        "session_id": session_id,
    }

def _current_chainlit_thread_id() -> str:
    """Use Chainlit's thread id when available so saved sessions are stable."""
    try:
        return str(cl.context.session.thread_id)
    except Exception:
        return str(uuid4())


async def _safe_remove_message(message: cl.Message) -> None:
    """Remove a visible Chainlit message without failing the command flow."""
    try:
        await message.remove()
    except Exception:
        pass


async def _clear_visible_chat() -> None:
    """Clear the current Chainlit frame before rendering a selected session."""
    for existing_message in list(chat_context.get()):
        await _safe_remove_message(existing_message)
    chat_context.clear()


async def _replay_saved_conversation(
    session_id: str,
    interactions: list[dict[str, Any]],
) -> None:
    """Render saved SQLite turns as normal chat messages in the main frame."""
    if not interactions:
        await cl.Message(content=f"No saved turns found for `{session_id}`.").send()
        return

    visible_interactions = interactions[-MAX_REPLAY_TURNS:]
    for interaction in visible_interactions:
        await cl.Message(
            content=str(interaction["user_message"]),
            author="User",
            type="user_message",
        ).send()
        await cl.Message(
            content=str(interaction["bot_response"]),
            type="assistant_message",
        ).send()

    if len(interactions) > MAX_REPLAY_TURNS:
        await cl.Message(
            content=(
                f"Loaded the latest {MAX_REPLAY_TURNS} turns from `{session_id}`. "
                f"The full saved conversation has {len(interactions)} turns."
            )
        ).send()


async def _open_saved_session(requested_id: str) -> dict[str, Any] | None:
    """Select a saved session and render it in the current Chainlit frame."""
    selected_session_id = resolve_session_id(requested_id)
    if selected_session_id is None:
        return None

    interactions = load_session_interactions(selected_session_id)
    await _clear_visible_chat()
    cl.user_session.set("session_id", selected_session_id)
    cl.user_session.set("message_count", len(interactions))
    await _replay_saved_conversation(selected_session_id, interactions)

    return {
        "session_id": selected_session_id,
        "turn_count": len(interactions),
    }


async def _start_new_saved_session() -> str:
    """Clear the frame and start saving future turns under a new session id."""
    await _clear_visible_chat()
    new_session_id = str(uuid4())
    cl.user_session.set("session_id", new_session_id)
    cl.user_session.set("message_count", 0)
    await cl.Message(
        content=f"Started a new saved conversation with ID `{new_session_id}`."
    ).send()
    return new_session_id


def _route_is_registered(path: str, method: str) -> bool:
    """Avoid duplicate FastAPI routes when Chainlit reloads the app module."""
    return any(
        getattr(route, "path", None) == path
        and method.upper() in (getattr(route, "methods", None) or set())
        for route in fastapi_app.routes
    )


def _get_websocket_session(request: Request) -> WebsocketSession:
    """Resolve the active Chainlit websocket session from its sticky cookie."""
    chainlit_session_id = request.cookies.get(CHAINLIT_SESSION_COOKIE)
    if not chainlit_session_id:
        raise HTTPException(
            status_code=409,
            detail="The Chainlit session is still connecting. Try again in a moment.",
        )

    session = WebsocketSession.get_by_id(chainlit_session_id)
    if session is None:
        raise HTTPException(
            status_code=409,
            detail="The active Chainlit session was not found. Refresh the page.",
        )

    return session


def _register_history_routes() -> None:
    """Expose minimal HTTP hooks for the custom browser sidebar."""
    if not _route_is_registered(HISTORY_OPEN_ROUTE, "POST"):

        @fastapi_app.post(HISTORY_OPEN_ROUTE)
        async def open_history_session(
            payload: OpenHistoryRequest,
            request: Request,
        ) -> dict[str, Any]:
            websocket_session = _get_websocket_session(request)
            context = init_ws_context(websocket_session)
            await context.emitter.task_start()

            try:
                result = await _open_saved_session(payload.session_id)
                if result is None:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            "No saved conversation matched "
                            f"{payload.session_id!r}."
                        ),
                    )
                return {"success": True, **result}
            finally:
                await context.emitter.task_end()

    if not _route_is_registered(HISTORY_NEW_ROUTE, "POST"):

        @fastapi_app.post(HISTORY_NEW_ROUTE)
        async def new_history_session(request: Request) -> dict[str, Any]:
            websocket_session = _get_websocket_session(request)
            context = init_ws_context(websocket_session)
            await context.emitter.task_start()

            try:
                session_id = await _start_new_saved_session()
                return {"success": True, "session_id": session_id}
            finally:
                await context.emitter.task_end()


_register_history_routes()


async def _handle_history_command(message: cl.Message) -> bool:
    """Handle local history commands without saving them as chatbot turns."""
    user_message = message.content
    normalized = user_message.strip()
    lower = normalized.lower()

    if lower == "/history":
        await _safe_remove_message(message)
        sessions = get_all_sessions(limit=10)
        await cl.Message(
            content="**Saved conversations**\n\n"
            + format_sessions_for_markdown(sessions)
            + "\n\nUse `/open <session_id>` to continue a saved conversation."
        ).send()
        return True

    if lower.startswith("/open "):
        requested_id = normalized.split(maxsplit=1)[1]
        result = await _open_saved_session(requested_id)
        if result is None:
            await _safe_remove_message(message)
            await cl.Message(
                content=(
                    f"I could not find a saved conversation matching "
                    f"`{requested_id}`. Use `/history` to list available sessions."
                )
            ).send()
            return True

        return True

    if lower == "/new":
        await _start_new_saved_session()
        return True

    return False


@cl.on_chat_start
async def on_chat_start() -> None:
    """
    Initialize a new Chainlit chat session.
    
    This handler:
    1. Sets up the SQLite conversation database
    2. Seeds demo conversations for testing
    3. Initializes the session
    4. Sends a welcome message
    5. Displays recent conversations
    """
    logger.info("\n" + "="*70)
    logger.info("[STARTUP] Initializing new chat session")
    logger.info("="*70)
    
    # Initialize the SQLite database for conversation memory
    init_database()
    logger.info("[DB] Database initialized")
    
    # Seed demo conversations (for development/testing)
    demo_count = seed_demo_conversations()
    logger.info(f"[DEMO] Seeded {demo_count} demo conversations")
    
    # Export conversation history for the sidebar
    export_history_snapshot()
    logger.info("[EXPORT] History snapshot exported")

    # Initialize session tracking
    session_id = _current_chainlit_thread_id()
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("message_count", 0)
    logger.info(f"[SESSION] New session ID: {session_id}")

    # Build and send welcome message
    welcome_content = (
        f"**{APP_NAME}**\n\n"
        f"{APP_DESCRIPTION}\n\n"
        "### How to Use\n\n"
        "Send a customer support message, for example:\n"
        "- `My order never arrived`\n"
        "- `I want a refund`\n"
        "- `This is unacceptable, I need help immediately`\n\n"
        "The chatbot will:\n"
        "1. **Clean** your message (remove URLs, mentions, etc.)\n"
        "2. **Classify** your intent (what you need help with)\n"
        "3. **Analyze** your sentiment (happy, frustrated, etc.)\n"
        "4. **Detect** urgency (how time-sensitive it is)\n"
        "5. **Generate** an appropriate response with local GPT if available, "
        "otherwise with the safe template fallback\n\n"
        "---\n\n"
        "💾 **Saved Conversations**: The left sidebar shows past conversations. "
        "Click one to load it, or use `/open <session_id>` to continue with context.\n\n"
        "📝 **Commands**: Use `/history` to list all sessions or `/new` to start fresh."
    )

    all_sessions = get_all_sessions(limit=5)
    if all_sessions:
        welcome_content += (
            "\n\n---\n\n"
            "### Recent Conversations\n\n"
            + format_sessions_for_markdown(all_sessions)
        )

    await cl.Message(content=welcome_content).send()
    logger.info("[STARTUP] Chat session ready\n" + "="*70 + "\n")


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """
    Handle incoming user messages through the complete NLP pipeline.
    
    This async handler:
    1. Extracts the user message from Chainlit
    2. Checks for special commands (like /history)
    3. Runs the NLP pipeline
    4. Sends the response back to the UI
    5. Saves the interaction to the database
    """
    user_message = message.content.strip()
    
    # Handle special history commands without running the NLP pipeline
    if await _handle_history_command(message):
        return

    # ========== Initialize Session ==========
    session_id = cl.user_session.get("session_id")
    if session_id is None:
        session_id = _current_chainlit_thread_id()
        cl.user_session.set("session_id", session_id)

    # Update message count for this session
    message_count = cl.user_session.get("message_count") or 0
    cl.user_session.set("message_count", message_count + 1)
    
    logger.info(f"\n{'='*70}")
    logger.info(f"[SESSION] ID: {session_id}")
    logger.info(f"[SESSION] Message #{message_count + 1}")
    logger.info(f"{'='*70}")

    # ========== RUN NLP PIPELINE ==========
    # Process the message through all NLP modules
    pipeline_results = await run_nlp_pipeline(user_message, str(session_id))
    
    # Extract results
    intent_result = pipeline_results["intent_result"]
    sentiment_result = pipeline_results["sentiment_result"]
    urgency_result = pipeline_results["urgency_result"]
    bot_response = pipeline_results["bot_response"]
    response_source = pipeline_results["response_source"]

    # ========== BUILD RESPONSE MESSAGE ==========
    # Combine response with optional NLP metadata
    message_content = bot_response
    if SHOW_NLP_METADATA:
        message_content += build_metadata_block(
            intent_result,
            sentiment_result,
            urgency_result,
            response_source,
        )

    # ========== SEND RESPONSE TO USER ==========
    await cl.Message(content=message_content).send()
    
    # ========== SAVE TO CONVERSATION MEMORY ==========
    # Store the interaction in SQLite for future context and history
    save_interaction(
        session_id=str(session_id),
        user_message=user_message,
        bot_response=bot_response,
        intent_result=intent_result,
        sentiment_result=sentiment_result,
        urgency_result=urgency_result,
    )
    
    # ========== UPDATE HISTORY SNAPSHOT ==========
    # Export conversation history for the sidebar
    export_history_snapshot()
    
    logger.info(f"[SAVE] Interaction saved to database")
    logger.info(f"{'='*70}\n")
