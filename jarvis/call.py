#!/usr/bin/env python3
"""Jarvis Voice Briefing - Make Voice Calls

Supports both Vapi (fast prototyping) and Retell (HIPAA compliant).
Set VOICE_PROVIDER env var to 'vapi' or 'retell'.
"""

import os
import json
import argparse
from pathlib import Path

from prompts import BRIEFING_SYSTEM_PROMPT, BRIEFING_USER_PROMPT

VOICE_PROVIDER = os.environ.get("VOICE_PROVIDER", "vapi")


def make_briefing_call_vapi(phone_number: str, customer_context: dict) -> str:
    """Make briefing call using Vapi."""
    try:
        from vapi import Vapi
    except ImportError:
        raise ImportError("Install vapi-python: pip install vapi-python")

    api_key = os.environ.get("VAPI_API_KEY")
    if not api_key:
        raise ValueError("VAPI_API_KEY environment variable required")

    client = Vapi(api_key=api_key)

    # Create the call with inline assistant config
    call = client.calls.create(
        phone_number_id=os.environ.get("VAPI_PHONE_NUMBER_ID"),
        customer={"number": phone_number},
        assistant={
            "model": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "messages": [
                    {"role": "system", "content": BRIEFING_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": BRIEFING_USER_PROMPT.format(
                            customer_json=json.dumps(customer_context, indent=2)
                        ),
                    },
                ],
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "pNInz6obpgDQGcFmaJgB",  # Adam - professional male
            },
            "firstMessage": f"Hey, it's Jarvis. You're meeting {customer_context['meeting']['contact_name']} in about 15 minutes. Quick briefing for you.",
        },
    )

    return call.id


def make_briefing_call_retell(phone_number: str, customer_context: dict) -> str:
    """Make briefing call using Retell (HIPAA compliant)."""
    try:
        from retell import Retell
    except ImportError:
        raise ImportError("Install retell-sdk: pip install retell-sdk")

    api_key = os.environ.get("RETELL_API_KEY")
    if not api_key:
        raise ValueError("RETELL_API_KEY environment variable required")

    client = Retell(api_key=api_key)

    # Retell requires pre-configured agent, we pass dynamic variables
    call = client.call.create_phone_call(
        from_number=os.environ["RETELL_PHONE_NUMBER"],
        to_number=phone_number,
        override_agent_id=os.environ.get("RETELL_AGENT_ID"),
        retell_llm_dynamic_variables={
            "customer_context": json.dumps(customer_context),
            "contact_name": customer_context["meeting"]["contact_name"],
            "company": customer_context["meeting"]["company"],
        },
    )

    return call.call_id


def make_briefing_call(phone_number: str, customer_context: dict) -> str:
    """Route to appropriate voice provider."""
    if VOICE_PROVIDER == "retell":
        return make_briefing_call_retell(phone_number, customer_context)
    else:
        return make_briefing_call_vapi(phone_number, customer_context)


def load_customer_context(filepath: str) -> dict:
    """Load customer context from JSON file."""
    with open(filepath) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Jarvis Voice Briefing")
    parser.add_argument("--phone", required=True, help="Phone number to call (E.164 format)")
    parser.add_argument("--customer", required=True, help="Path to customer JSON file")
    parser.add_argument("--provider", choices=["vapi", "retell"], help="Voice provider override")

    args = parser.parse_args()

    if args.provider:
        global VOICE_PROVIDER
        VOICE_PROVIDER = args.provider

    # Load customer data
    customer_path = Path(args.customer)
    if not customer_path.exists():
        print(f"Error: Customer file not found: {customer_path}")
        return 1

    customer = load_customer_context(str(customer_path))
    print(f"Loaded customer: {customer['meeting']['contact_name']} at {customer['meeting']['company']}")

    # Make the call
    print(f"Calling {args.phone} using {VOICE_PROVIDER}...")
    try:
        call_id = make_briefing_call(args.phone, customer)
        print(f"Call initiated! ID: {call_id}")
        print(f"Jarvis is now briefing the rep on {customer['meeting']['contact_name']}")
        return 0
    except Exception as e:
        print(f"Error making call: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
