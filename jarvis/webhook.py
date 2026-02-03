#!/usr/bin/env python3
"""Jarvis Voice Briefing - Webhook Handler

Receives webhooks from Vapi/Retell when calls complete.
Extracts commands from transcripts and logs them.

Run with: uvicorn webhook:app --port 8000
Or: python webhook.py (uses built-in server)
"""

import os
import json
import hmac
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel

from commands import parse_commands_from_transcript

app = FastAPI(title="Jarvis Webhook Handler")


# =============================================================================
# Vapi Webhook
# =============================================================================


class VapiWebhookPayload(BaseModel):
    """Vapi webhook payload structure."""

    type: str  # "call.ended", "transcript", etc.
    call: Optional[dict] = None
    transcript: Optional[str] = None


def verify_vapi_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Vapi webhook signature."""
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.post("/webhook/vapi")
async def vapi_webhook(
    request: Request,
    x_vapi_signature: Optional[str] = Header(None),
):
    """Handle Vapi webhooks."""
    body = await request.body()

    # Verify signature if secret is configured
    secret = os.environ.get("VAPI_WEBHOOK_SECRET")
    if secret and x_vapi_signature:
        if not verify_vapi_signature(body, x_vapi_signature, secret):
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body)
    event_type = payload.get("type", "")

    print(f"[Vapi] Received event: {event_type}")

    if event_type == "call.ended":
        call_data = payload.get("call", {})
        call_id = call_data.get("id", "unknown")
        transcript = call_data.get("transcript", "")

        if transcript:
            print(f"[Vapi] Processing transcript for call {call_id}")
            commands = parse_commands_from_transcript(call_id, transcript)
            print(f"[Vapi] Extracted {len(commands)} commands")

            return {
                "status": "processed",
                "call_id": call_id,
                "commands_extracted": len(commands),
            }

    return {"status": "received", "type": event_type}


# =============================================================================
# Retell Webhook
# =============================================================================


def verify_retell_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Retell webhook signature."""
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.post("/webhook/retell")
async def retell_webhook(
    request: Request,
    x_retell_signature: Optional[str] = Header(None),
):
    """Handle Retell webhooks."""
    body = await request.body()

    # Verify signature if secret is configured
    secret = os.environ.get("RETELL_WEBHOOK_SECRET")
    if secret and x_retell_signature:
        if not verify_retell_signature(body, x_retell_signature, secret):
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body)
    event_type = payload.get("event", "")

    print(f"[Retell] Received event: {event_type}")

    if event_type == "call_ended":
        call_id = payload.get("call_id", "unknown")
        transcript = payload.get("transcript", "")

        # Retell sends transcript as list of utterances
        if isinstance(transcript, list):
            transcript = " ".join(
                f"{u.get('role', 'unknown')}: {u.get('content', '')}"
                for u in transcript
            )

        if transcript:
            print(f"[Retell] Processing transcript for call {call_id}")
            commands = parse_commands_from_transcript(call_id, transcript)
            print(f"[Retell] Extracted {len(commands)} commands")

            return {
                "status": "processed",
                "call_id": call_id,
                "commands_extracted": len(commands),
            }

    return {"status": "received", "event": event_type}


# =============================================================================
# Health Check
# =============================================================================


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "jarvis-webhook",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/")
async def root():
    """Root endpoint with info."""
    return {
        "service": "Jarvis Webhook Handler",
        "endpoints": {
            "/webhook/vapi": "POST - Vapi call webhooks",
            "/webhook/retell": "POST - Retell call webhooks",
            "/health": "GET - Health check",
        },
    }


# =============================================================================
# Run with built-in server
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("WEBHOOK_PORT", 8000))
    print(f"Starting Jarvis webhook server on port {port}")
    print("Endpoints:")
    print(f"  POST http://localhost:{port}/webhook/vapi")
    print(f"  POST http://localhost:{port}/webhook/retell")
    print(f"  GET  http://localhost:{port}/health")

    uvicorn.run(app, host="0.0.0.0", port=port)
