"""Runtime compatibility fixes loaded automatically by Python.

Chainlit 2.11 with the current Python 3.14/AnyIO stack can fail while serving
static files because AnyIO does not always detect the active asyncio loop.
This shim keeps the app runnable without changing third-party package files.
"""

from __future__ import annotations

import asyncio
import os
import sys


def _patch_anyio_async_backend_detection() -> None:
    """Fallback to asyncio when an event loop is running but AnyIO cannot detect it."""
    try:
        import anyio._core._eventloop as anyio_eventloop
        import anyio.to_thread as anyio_to_thread
    except Exception:
        return

    original_get_async_backend = anyio_eventloop.get_async_backend

    def get_async_backend_with_fallback(asynclib_name: str | None = None):
        if asynclib_name is not None:
            return original_get_async_backend(asynclib_name)

        try:
            return original_get_async_backend()
        except Exception:
            # If AnyIO couldn't detect the backend, prefer asyncio explicitly.
            # Some environments (notably Windows + certain Python/AnyIO combos)
            # may call into AnyIO from contexts where detection fails even
            # though asyncio is the correct backend. Fall back to asyncio
            # to avoid NoCurrentAsyncBackend errors when serving files.
            return original_get_async_backend("asyncio")

    anyio_eventloop.get_async_backend = get_async_backend_with_fallback
    anyio_to_thread.get_async_backend = get_async_backend_with_fallback


_patch_anyio_async_backend_detection()


def _normalize_chainlit_debug_env() -> None:
    """Prevent unrelated DEBUG values from breaking Chainlit's boolean CLI flag."""
    value = os.getenv("DEBUG")
    if value is None:
        return

    valid_boolean_values = {
        "",
        "0",
        "1",
        "f",
        "false",
        "n",
        "no",
        "off",
        "on",
        "t",
        "true",
        "y",
        "yes",
    }
    if value.lower() not in valid_boolean_values:
        os.environ["DEBUG"] = "false"


_normalize_chainlit_debug_env()

if os.getenv("CHATBOT_DEBUG_SITE") == "1":
    print("sitecustomize loaded", file=sys.stderr)
