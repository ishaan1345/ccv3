#!/usr/bin/env python3
"""Jarvis Voice Briefing - Calendar Trigger

Checks for upcoming meetings and triggers briefing calls.
For prototype: Manual trigger via CLI.
For production: Run as cron job or service.
"""

import os
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from call import make_briefing_call, load_customer_context

# Simple file-based tracking of briefed meetings
BRIEFED_FILE = Path(__file__).parent / ".briefed_meetings.json"


def load_briefed() -> dict:
    """Load set of already-briefed meeting IDs."""
    if BRIEFED_FILE.exists():
        with open(BRIEFED_FILE) as f:
            return json.load(f)
    return {}


def save_briefed(briefed: dict):
    """Save briefed meeting IDs."""
    with open(BRIEFED_FILE, "w") as f:
        json.dump(briefed, f, indent=2)


def already_briefed(meeting_id: str) -> bool:
    """Check if we've already briefed for this meeting."""
    briefed = load_briefed()
    return meeting_id in briefed


def mark_briefed(meeting_id: str, call_id: str):
    """Mark a meeting as briefed."""
    briefed = load_briefed()
    briefed[meeting_id] = {
        "call_id": call_id,
        "briefed_at": datetime.now().isoformat(),
    }
    save_briefed(briefed)


# =============================================================================
# Calendar Integration (Stubbed for Prototype)
# =============================================================================


def get_calendar_events_google(minutes_ahead: int = 15) -> list[dict]:
    """Get upcoming calendar events from Google Calendar.

    Requires: google-api-python-client, google-auth-oauthlib
    Setup: OAuth2 credentials for Calendar API

    Returns list of meetings with:
    - id: unique meeting ID
    - title: meeting title
    - start_time: ISO datetime
    - contact_email: attendee email (for CRM lookup)
    - organizer_email: rep's email
    """
    # TODO: Implement Google Calendar integration
    # from googleapiclient.discovery import build
    # service = build('calendar', 'v3', credentials=creds)
    # now = datetime.utcnow().isoformat() + 'Z'
    # later = (datetime.utcnow() + timedelta(minutes=minutes_ahead)).isoformat() + 'Z'
    # events = service.events().list(calendarId='primary', timeMin=now, timeMax=later).execute()
    raise NotImplementedError("Google Calendar integration not yet implemented")


def get_calendar_events_outlook(minutes_ahead: int = 15) -> list[dict]:
    """Get upcoming calendar events from Outlook/Microsoft 365.

    Requires: msal, requests
    Setup: Azure AD app registration

    Returns same format as Google.
    """
    # TODO: Implement Outlook integration
    raise NotImplementedError("Outlook integration not yet implemented")


def get_calendar_events_mock(minutes_ahead: int = 15) -> list[dict]:
    """Mock calendar for testing - returns Linda meeting if within window."""
    # Simulate a meeting starting in 10 minutes
    meeting_time = datetime.now() + timedelta(minutes=10)

    return [
        {
            "id": "mock-meeting-linda-001",
            "title": "Sales Call - Linda Chen @ Acme Corp",
            "start_time": meeting_time.isoformat(),
            "contact_email": "linda.chen@acmecorp.com",
            "organizer_email": "rep@company.com",
            "location": "123 Main St, Suite 400",
        }
    ]


def get_calendar_events(minutes_ahead: int = 15, provider: str = "mock") -> list[dict]:
    """Get upcoming calendar events from configured provider."""
    providers = {
        "mock": get_calendar_events_mock,
        "google": get_calendar_events_google,
        "outlook": get_calendar_events_outlook,
    }

    if provider not in providers:
        raise ValueError(f"Unknown calendar provider: {provider}")

    return providers[provider](minutes_ahead)


# =============================================================================
# Customer Context (Stubbed for Prototype)
# =============================================================================


def get_customer_context_from_crm(contact_email: str) -> Optional[dict]:
    """Look up customer context from CRM by email.

    TODO: Implement integrations for:
    - Salesforce
    - HubSpot
    - Pipedrive
    - August (internal)
    """
    raise NotImplementedError("CRM integration not yet implemented")


def get_customer_context_mock(contact_email: str) -> Optional[dict]:
    """Get customer context from mock data files."""
    mock_dir = Path(__file__).parent / "mock_data"

    # Try to find a matching mock file
    # In prototype, we just use linda.json for everything
    linda_file = mock_dir / "linda.json"
    if linda_file.exists():
        return load_customer_context(str(linda_file))

    return None


def get_customer_context(contact_email: str, provider: str = "mock") -> Optional[dict]:
    """Get customer context for an upcoming meeting."""
    if provider == "mock":
        return get_customer_context_mock(contact_email)
    else:
        return get_customer_context_from_crm(contact_email)


# =============================================================================
# Rep Phone Lookup (Stubbed for Prototype)
# =============================================================================


def get_rep_phone(organizer_email: str) -> Optional[str]:
    """Look up rep's phone number from their email.

    In production, this would query your user directory.
    For prototype, use REP_PHONE_NUMBER env var.
    """
    return os.environ.get("REP_PHONE_NUMBER")


# =============================================================================
# Main Trigger Loop
# =============================================================================


def check_and_trigger(
    calendar_provider: str = "mock",
    customer_provider: str = "mock",
    dry_run: bool = False,
) -> list[str]:
    """Check for upcoming meetings and trigger briefing calls.

    Args:
        calendar_provider: Calendar source (mock, google, outlook)
        customer_provider: Customer data source (mock, crm)
        dry_run: If True, don't actually make calls

    Returns:
        List of call IDs for triggered briefings
    """
    call_ids = []

    meetings = get_calendar_events(minutes_ahead=15, provider=calendar_provider)
    print(f"Found {len(meetings)} upcoming meetings")

    for meeting in meetings:
        meeting_id = meeting["id"]

        if already_briefed(meeting_id):
            print(f"  Skipping {meeting['title']} - already briefed")
            continue

        # Get customer context
        customer = get_customer_context(
            meeting.get("contact_email", ""), provider=customer_provider
        )

        if not customer:
            print(f"  Skipping {meeting['title']} - no customer context found")
            continue

        # Get rep phone
        rep_phone = get_rep_phone(meeting.get("organizer_email", ""))
        if not rep_phone:
            print(f"  Skipping {meeting['title']} - no rep phone number")
            continue

        # Trigger the call
        print(f"  Triggering briefing for: {meeting['title']}")
        print(f"    Customer: {customer['meeting']['contact_name']}")
        print(f"    Rep phone: {rep_phone}")

        if dry_run:
            print("    [DRY RUN] Would make call here")
            call_id = f"dry-run-{meeting_id}"
        else:
            try:
                call_id = make_briefing_call(rep_phone, customer)
                print(f"    Call initiated: {call_id}")
            except Exception as e:
                print(f"    Error making call: {e}")
                continue

        mark_briefed(meeting_id, call_id)
        call_ids.append(call_id)

    return call_ids


def run_daemon(
    interval_seconds: int = 60,
    calendar_provider: str = "mock",
    customer_provider: str = "mock",
):
    """Run as a daemon, checking calendar every interval."""
    print(f"Starting Jarvis trigger daemon (checking every {interval_seconds}s)")
    print(f"Calendar: {calendar_provider}, Customer: {customer_provider}")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking calendar...")
            check_and_trigger(calendar_provider, customer_provider)
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\nDaemon stopped.")


def main():
    parser = argparse.ArgumentParser(description="Jarvis Calendar Trigger")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Manual trigger
    trigger_parser = subparsers.add_parser("trigger", help="Check calendar and trigger calls")
    trigger_parser.add_argument("--dry-run", action="store_true", help="Don't actually call")
    trigger_parser.add_argument(
        "--calendar", default="mock", choices=["mock", "google", "outlook"]
    )
    trigger_parser.add_argument("--customer", default="mock", choices=["mock", "crm"])

    # Daemon mode
    daemon_parser = subparsers.add_parser("daemon", help="Run continuously")
    daemon_parser.add_argument(
        "--interval", type=int, default=60, help="Check interval in seconds"
    )
    daemon_parser.add_argument(
        "--calendar", default="mock", choices=["mock", "google", "outlook"]
    )
    daemon_parser.add_argument("--customer", default="mock", choices=["mock", "crm"])

    # Direct call (bypass calendar)
    call_parser = subparsers.add_parser("call", help="Directly call a number with customer data")
    call_parser.add_argument("--phone", required=True, help="Phone number (E.164)")
    call_parser.add_argument("--customer", required=True, help="Customer JSON file")

    # Status
    subparsers.add_parser("status", help="Show briefed meetings")

    args = parser.parse_args()

    if args.command == "trigger":
        calls = check_and_trigger(
            calendar_provider=args.calendar,
            customer_provider=args.customer,
            dry_run=args.dry_run,
        )
        print(f"\nTriggered {len(calls)} briefing calls")

    elif args.command == "daemon":
        run_daemon(
            interval_seconds=args.interval,
            calendar_provider=args.calendar,
            customer_provider=args.customer,
        )

    elif args.command == "call":
        customer = load_customer_context(args.customer)
        print(f"Calling {args.phone} with customer: {customer['meeting']['contact_name']}")
        call_id = make_briefing_call(args.phone, customer)
        print(f"Call initiated: {call_id}")

    elif args.command == "status":
        briefed = load_briefed()
        if not briefed:
            print("No meetings briefed yet.")
        else:
            print(f"Briefed meetings ({len(briefed)}):\n")
            for meeting_id, info in briefed.items():
                print(f"  {meeting_id}")
                print(f"    Call: {info['call_id']}")
                print(f"    Time: {info['briefed_at']}")
                print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
