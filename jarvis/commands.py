#!/usr/bin/env python3
"""Jarvis Voice Briefing - Command Logging

Logs commands extracted from call transcripts for later processing.
Commands are stored in JSONL format for easy streaming/processing.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

COMMANDS_FILE = Path(__file__).parent / "jarvis_commands.jsonl"


def log_command(
    call_id: str,
    command_type: str,
    content: str,
    raw_utterance: Optional[str] = None,
) -> dict:
    """Log a command from the call for later processing.

    Args:
        call_id: The voice call ID
        command_type: Type of command (reminder, schedule, note, question)
        content: Extracted command content
        raw_utterance: Original spoken text (optional)

    Returns:
        The logged entry
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "call_id": call_id,
        "type": command_type,
        "content": content,
        "raw": raw_utterance,
        "status": "pending",
    }

    with open(COMMANDS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def parse_commands_from_transcript(call_id: str, transcript: str) -> list[dict]:
    """Parse commands from a call transcript.

    Looks for patterns like:
    - "Remind me to [X]"
    - "Schedule [X]"
    - "Note that [X]"
    - "Don't forget [X]"

    Args:
        call_id: The voice call ID
        transcript: Full call transcript text

    Returns:
        List of logged command entries
    """
    patterns = [
        (r"remind me to (.+?)(?:\.|$)", "reminder"),
        (r"schedule (.+?)(?:\.|$)", "schedule"),
        (r"note that (.+?)(?:\.|$)", "note"),
        (r"don't forget (?:to )?(.+?)(?:\.|$)", "reminder"),
        (r"make sure (?:to |I )(.+?)(?:\.|$)", "reminder"),
        (r"add (.+?) to (?:my |the )(?:list|tasks|todos)", "reminder"),
    ]

    commands = []
    transcript_lower = transcript.lower()

    for pattern, cmd_type in patterns:
        matches = re.finditer(pattern, transcript_lower, re.IGNORECASE)
        for match in matches:
            content = match.group(1).strip()
            entry = log_command(
                call_id=call_id,
                command_type=cmd_type,
                content=content,
                raw_utterance=match.group(0),
            )
            commands.append(entry)

    return commands


def get_pending_commands() -> list[dict]:
    """Get all pending commands."""
    if not COMMANDS_FILE.exists():
        return []

    pending = []
    with open(COMMANDS_FILE) as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                if entry.get("status") == "pending":
                    pending.append(entry)
    return pending


def mark_command_done(timestamp: str) -> bool:
    """Mark a command as done by its timestamp.

    Note: This is a simple implementation. For production,
    use a proper database with atomic updates.
    """
    if not COMMANDS_FILE.exists():
        return False

    lines = []
    found = False
    with open(COMMANDS_FILE) as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                if entry.get("timestamp") == timestamp:
                    entry["status"] = "done"
                    entry["completed_at"] = datetime.now().isoformat()
                    found = True
                lines.append(json.dumps(entry) + "\n")

    if found:
        with open(COMMANDS_FILE, "w") as f:
            f.writelines(lines)

    return found


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python commands.py list          - Show pending commands")
        print("  python commands.py test          - Test with sample transcript")
        print("  python commands.py done <ts>     - Mark command done by timestamp")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        pending = get_pending_commands()
        if not pending:
            print("No pending commands.")
        else:
            print(f"Pending commands ({len(pending)}):\n")
            for p in pending:
                print(f"  [{p['type']}] {p['content']}")
                print(f"    Call: {p['call_id']} | Time: {p['timestamp']}")
                print()

    elif cmd == "test":
        sample_transcript = """
        Jarvis: You're meeting Linda Chen, VP of Sales at Acme Corp in 15 minutes.
        Rep: Got it. Remind me to send the case study after.
        Jarvis: I'll remind you to send the case study after the meeting.
        Rep: Also schedule a follow-up call for next week.
        Jarvis: Noted. I'll add that to your list.
        Rep: What was her main objection again?
        Jarvis: She was concerned about Salesforce integration. Good news - we shipped the new connector last week.
        Rep: Perfect. Don't forget to check if Bob responded to my email.
        Jarvis: I'll make sure to check on Bob's response. Good luck with Linda!
        """

        commands = parse_commands_from_transcript("test-call-001", sample_transcript)
        print(f"Extracted {len(commands)} commands from transcript:\n")
        for c in commands:
            print(f"  [{c['type']}] {c['content']}")

    elif cmd == "done" and len(sys.argv) > 2:
        ts = sys.argv[2]
        if mark_command_done(ts):
            print(f"Marked command done: {ts}")
        else:
            print(f"Command not found: {ts}")

    else:
        print(f"Unknown command: {cmd}")
