"""Standalone FastAPI server for voice interview testing.

Run: python voice/server.py
Serves on port 8100 (separate from main API on 8000).
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from livekit.api import AccessToken, VideoGrants

from voice.bridge import create_bridge, get_bridge, END_SENTINEL

app = FastAPI(title="Voice Interview Test Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "")


@app.post("/voice/token")
async def create_token():
    """Create a LiveKit room and return a JWT token for the founder to join."""
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        return JSONResponse(
            {"error": "LIVEKIT_API_KEY and LIVEKIT_API_SECRET env vars must be set"},
            status_code=503,
        )
    if not LIVEKIT_URL:
        return JSONResponse(
            {"error": "LIVEKIT_URL env var must be set"},
            status_code=503,
        )

    room_name = f"interview-{uuid.uuid4().hex[:8]}"
    identity = f"founder-{uuid.uuid4().hex[:6]}"

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_grants(VideoGrants(room_join=True, room=room_name))
    )

    return JSONResponse({
        "token": token.to_jwt(),
        "room_name": room_name,
        "livekit_url": LIVEKIT_URL,
        "identity": identity,
    })


@app.post("/voice/start-interview")
async def start_interview(room_name: str):
    """Start a mock interview loop for testing. Asks 2 hardcoded questions."""
    bridge = get_bridge(room_name)
    if bridge is None:
        bridge = create_bridge(room_name)

    async def mock_comprehension():
        """Simulate comprehension agent asking questions."""
        await asyncio.sleep(3)  # Wait for voice agent to connect

        questions = [
            "Can you tell me about your target customer? Who are you building this for?",
            "What's the main problem they face that your product solves?",
        ]

        answers = []
        for q in questions:
            answer = await bridge.push_question(q, timeout=120)
            answers.append({"question": q, "answer": answer})
            await asyncio.sleep(1)

        bridge.signal_end()
        return answers

    asyncio.create_task(mock_comprehension())

    return JSONResponse({
        "status": "started",
        "room_name": room_name,
        "questions_count": 2,
    })


@app.get("/voice/test")
async def test_page():
    """Serve the standalone test page."""
    html_path = Path(__file__).parent / "test_page.html"
    return HTMLResponse(html_path.read_text())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
