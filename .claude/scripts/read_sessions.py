#!/usr/bin/env python3
"""Read concurrent Claude Code sessions.

Usage:
    read_sessions.py list [--project PATH] [--last N] [--distributo]
    read_sessions.py summary SESSION_ID [--project PATH]
    read_sessions.py messages SESSION_ID [--project PATH] [--user-only] [--assistant-only] [--limit N] [--tail N]
    read_sessions.py substance SESSION_ID [--project PATH] [--tail N]
    read_sessions.py concurrent [--project PATH] [--window MINUTES] [--last N]
    read_sessions.py diff SESSION_ID1 SESSION_ID2 [--project PATH]
    read_sessions.py edits SESSION_ID [--project PATH]

Session files are JSONL at:
    ~/.claude/projects/{encoded-project-path}/{session-id}.jsonl

The encoded path replaces / with - and prepends -.
Example: /Users/ishaan/ccv3 -> -home-ishaa-Continuous-Claude-v3
"""

from __future__ import annotations

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional


def get_project_dir(project_path: Optional[str] = None) -> Path:
    """Get the .claude/projects/ directory for a project."""
    if project_path is None:
        project_path = os.getcwd()

    # Encode path: /home/ishaa/Foo -> -home-ishaa-Foo
    encoded = project_path.replace("/", "-")
    if not encoded.startswith("-"):
        encoded = "-" + encoded

    return Path.home() / ".claude" / "projects" / encoded


def list_sessions(project_dir: Path, last: int = 15, filter_text: Optional[str] = None) -> list[dict]:
    """List recent sessions with their first user message."""
    sessions = []

    for f in project_dir.glob("*.jsonl"):
        sid = f.stem
        if len(sid) < 30:  # skip non-session files
            continue

        stat = f.stat()
        size_mb = stat.st_size / 1024 / 1024
        mtime = datetime.fromtimestamp(stat.st_mtime)

        # Extract first real user message
        first_msg = ""
        msg_count = {"user": 0, "assistant": 0}
        edit_count = 0

        with open(f) as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                    t = obj.get("type", "")

                    if t == "user":
                        msg_count["user"] += 1
                        if not first_msg:
                            content = _extract_text(obj)
                            if content and "local-command" not in content and "command-name" not in content:
                                first_msg = content[:200].replace("\n", " ").strip()
                    elif t == "assistant":
                        msg_count["assistant"] += 1
                        # Count tool uses (edits)
                        content = obj.get("message", {}).get("content", [])
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "tool_use":
                                    if c.get("name") in ("Edit", "Write"):
                                        edit_count += 1
                except (json.JSONDecodeError, AttributeError):
                    continue

        if filter_text and filter_text.lower() not in first_msg.lower():
            continue

        sessions.append({
            "id": sid,
            "short_id": sid[:8],
            "mtime": mtime,
            "size_mb": size_mb,
            "first_msg": first_msg or "(automated/hook)",
            "user_msgs": msg_count["user"],
            "assistant_msgs": msg_count["assistant"],
            "edit_count": edit_count,
        })

    sessions.sort(key=lambda x: x["mtime"], reverse=True)
    return sessions[:last]


def get_session_summary(project_dir: Path, session_id: str) -> dict:
    """Get a detailed summary of a single session."""
    # Find the file (support short IDs)
    session_file = _find_session_file(project_dir, session_id)
    if not session_file:
        return {"error": f"Session {session_id} not found"}

    messages = {"user": [], "assistant": []}
    tools_used = defaultdict(int)
    files_edited = set()
    files_read = set()

    with open(session_file) as f:
        for line in f:
            try:
                obj = json.loads(line)
                t = obj.get("type", "")

                if t == "user":
                    text = _extract_text(obj)
                    if text and "local-command" not in text:
                        messages["user"].append(text)

                elif t == "assistant":
                    text = _extract_text(obj)
                    if text:
                        messages["assistant"].append(text)

                    # Extract tool uses
                    content = obj.get("message", {}).get("content", [])
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "tool_use":
                                name = c.get("name", "?")
                                tools_used[name] += 1
                                inp = c.get("input", {})
                                if name == "Edit" and "file_path" in inp:
                                    files_edited.add(inp["file_path"])
                                elif name == "Write" and "file_path" in inp:
                                    files_edited.add(inp["file_path"])
                                elif name == "Read" and "file_path" in inp:
                                    files_read.add(inp["file_path"])
            except (json.JSONDecodeError, AttributeError):
                continue

    return {
        "session_id": session_file.stem,
        "size_mb": session_file.stat().st_size / 1024 / 1024,
        "user_messages": len(messages["user"]),
        "assistant_messages": len(messages["assistant"]),
        "first_user_msg": messages["user"][0][:300] if messages["user"] else "(none)",
        "last_user_msg": messages["user"][-1][:300] if messages["user"] else "(none)",
        "tools_used": dict(tools_used),
        "files_edited": sorted(files_edited),
        "files_read": sorted(files_read)[:20],  # cap at 20
        "all_user_messages": [m[:200] for m in messages["user"]],
    }


def get_messages(project_dir: Path, session_id: str,
                 user_only: bool = False, assistant_only: bool = False,
                 limit: int = 0, tail: int = 0) -> list[dict]:
    """Get messages from a session.

    --limit N: first N messages (from the start)
    --tail N: last N messages (from the end) -- use this for recent work
    """
    session_file = _find_session_file(project_dir, session_id)
    if not session_file:
        return [{"error": f"Session {session_id} not found"}]

    results = []
    with open(session_file) as f:
        for line in f:
            try:
                obj = json.loads(line)
                t = obj.get("type", "")

                if t == "user" and not assistant_only:
                    text = _extract_text(obj)
                    if text and "local-command" not in text and "command-name" not in text:
                        results.append({"role": "user", "text": text})

                elif t == "assistant" and not user_only:
                    text = _extract_text(obj)
                    if text and len(text) > 20:
                        results.append({"role": "assistant", "text": text})
            except (json.JSONDecodeError, AttributeError):
                continue

    if tail > 0:
        results = results[-tail:]
    elif limit > 0:
        results = results[:limit]

    return results


def get_substance(project_dir: Path, session_id: str, tail: int = 15) -> dict:
    """Extract the substance of a session -- what they're thinking, deciding, and doing.

    Returns the last N user+assistant exchanges with full content,
    plus a summary of files edited and key decisions.
    Unlike 'messages', this gives you BOTH sides of the conversation
    and focuses on recent work, not setup boilerplate.
    """
    session_file = _find_session_file(project_dir, session_id)
    if not session_file:
        return {"error": f"Session {session_id} not found"}

    all_messages = []
    files_edited = set()
    broadcasts = []

    with open(session_file) as f:
        for line in f:
            try:
                obj = json.loads(line)
                t = obj.get("type", "")

                if t == "user":
                    text = _extract_text(obj)
                    if text and "local-command" not in text and "command-name" not in text:
                        # Skip skill injection boilerplate (long system content)
                        if len(text) > 2000 and ("Base directory" in text or "---\nname:" in text):
                            all_messages.append({"role": "user", "text": "[skill injection -- skipped]"})
                        else:
                            all_messages.append({"role": "user", "text": text})

                elif t == "assistant":
                    text = _extract_text(obj)
                    if text and len(text) > 20:
                        all_messages.append({"role": "assistant", "text": text})

                    # Track edits and broadcasts
                    content = obj.get("message", {}).get("content", [])
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "tool_use":
                                name = c.get("name", "")
                                inp = c.get("input", {})
                                if name in ("Edit", "Write"):
                                    fp = inp.get("file_path", "")
                                    if fp:
                                        files_edited.add(fp)
                                elif name == "Bash":
                                    cmd = inp.get("command", "")
                                    if "INSERT INTO findings" in cmd:
                                        broadcasts.append(cmd[:200])
            except (json.JSONDecodeError, AttributeError):
                continue

    # Take the last N messages
    recent = all_messages[-tail:] if tail > 0 else all_messages

    return {
        "session_id": session_file.stem[:8],
        "total_messages": len(all_messages),
        "showing_last": len(recent),
        "files_edited": sorted(files_edited),
        "broadcast_count": len(broadcasts),
        "recent_messages": recent,
    }


def find_concurrent(project_dir: Path, window_minutes: int = 30, last: int = 20) -> list[list[dict]]:
    """Find sessions that overlapped in time (concurrent editing)."""
    sessions = []

    for f in project_dir.glob("*.jsonl"):
        sid = f.stem
        if len(sid) < 30:
            continue

        stat = f.stat()
        size_kb = stat.st_size / 1024
        if size_kb < 10:  # skip tiny files
            continue

        # Get first and last event timestamps
        first_ts = None
        last_ts = None
        first_msg = ""
        edit_files = set()

        with open(f) as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                    ts = obj.get("timestamp")
                    if ts:
                        if first_ts is None:
                            first_ts = ts
                        last_ts = ts

                    if not first_msg and obj.get("type") == "user":
                        text = _extract_text(obj)
                        if text and "local-command" not in text and "command-name" not in text:
                            first_msg = text[:150].replace("\n", " ")

                    # Track edited files
                    if obj.get("type") == "assistant":
                        content = obj.get("message", {}).get("content", [])
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "tool_use":
                                    if c.get("name") in ("Edit", "Write"):
                                        fp = c.get("input", {}).get("file_path", "")
                                        if fp:
                                            edit_files.add(os.path.basename(fp))
                except (json.JSONDecodeError, AttributeError):
                    continue

        if first_ts and last_ts:
            sessions.append({
                "id": sid[:8],
                "full_id": sid,
                "start": first_ts,
                "end": last_ts,
                "first_msg": first_msg or "(automated)",
                "size_mb": stat.st_size / 1024 / 1024,
                "edit_files": sorted(edit_files),
            })

    # Sort by start time
    sessions.sort(key=lambda x: x["start"], reverse=True)
    sessions = sessions[:last]

    # Find overlapping groups
    groups = []
    used = set()

    for i, s1 in enumerate(sessions):
        if s1["full_id"] in used:
            continue
        group = [s1]
        used.add(s1["full_id"])

        for j, s2 in enumerate(sessions):
            if i == j or s2["full_id"] in used:
                continue
            # Check overlap: s1.start <= s2.end AND s2.start <= s1.end
            if s1["start"] <= s2["end"] and s2["start"] <= s1["end"]:
                group.append(s2)
                used.add(s2["full_id"])

        if len(group) > 1:
            groups.append(group)

    return groups


def get_edits(project_dir: Path, session_id: str) -> list[dict]:
    """Extract all file edits from a session."""
    session_file = _find_session_file(project_dir, session_id)
    if not session_file:
        return [{"error": f"Session {session_id} not found"}]

    edits = []
    with open(session_file) as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj.get("type") != "assistant":
                    continue
                content = obj.get("message", {}).get("content", [])
                if not isinstance(content, list):
                    continue
                for c in content:
                    if not isinstance(c, dict) or c.get("type") != "tool_use":
                        continue
                    name = c.get("name", "")
                    inp = c.get("input", {})
                    if name == "Edit":
                        edits.append({
                            "tool": "Edit",
                            "file": inp.get("file_path", "?"),
                            "old": inp.get("old_string", "")[:100],
                            "new": inp.get("new_string", "")[:100],
                        })
                    elif name == "Write":
                        content_preview = inp.get("content", "")[:100]
                        edits.append({
                            "tool": "Write",
                            "file": inp.get("file_path", "?"),
                            "preview": content_preview,
                        })
            except (json.JSONDecodeError, AttributeError):
                continue

    return edits


def _extract_text(obj: dict) -> str:
    """Extract text content from a message object."""
    msg = obj.get("message", {})
    if isinstance(msg, str):
        return msg
    if isinstance(msg, dict):
        content = msg.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    parts.append(c.get("text", ""))
            return "\n".join(parts)
    return ""


def _find_session_file(project_dir: Path, session_id: str) -> Optional[Path]:
    """Find session file by full or partial ID."""
    # Try exact match
    exact = project_dir / f"{session_id}.jsonl"
    if exact.exists():
        return exact

    # Try prefix match
    matches = list(project_dir.glob(f"{session_id}*.jsonl"))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"Ambiguous ID {session_id}, matches: {[m.stem[:8] for m in matches]}", file=sys.stderr)
        return matches[0]

    return None


def main():
    parser = argparse.ArgumentParser(description="Read Claude Code sessions")
    parser.add_argument("command", choices=["list", "summary", "messages", "substance", "concurrent", "diff", "edits"])
    parser.add_argument("args", nargs="*")
    parser.add_argument("--project", default=None, help="Project path (default: cwd)")
    parser.add_argument("--last", type=int, default=15)
    parser.add_argument("--distributo", action="store_true", help="Filter for distributo sessions")
    parser.add_argument("--user-only", action="store_true")
    parser.add_argument("--assistant-only", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="First N messages (from start)")
    parser.add_argument("--tail", type=int, default=0, help="Last N messages (from end) -- use for recent work")
    parser.add_argument("--window", type=int, default=30, help="Concurrency window in minutes")

    args = parser.parse_args()
    project_dir = get_project_dir(args.project)

    if not project_dir.exists():
        print(f"Project directory not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    if args.command == "list":
        filter_text = "distributo" if args.distributo else None
        sessions = list_sessions(project_dir, last=args.last, filter_text=filter_text)
        print(f"{'ID':>10}  {'Size':>6}  {'User':>4}  {'Edits':>5}  {'First Message'}")
        print("-" * 100)
        for s in sessions:
            print(f"{s['short_id']:>10}  {s['size_mb']:.1f}MB  {s['user_msgs']:>4}  {s['edit_count']:>5}  {s['first_msg'][:60]}")

    elif args.command == "summary":
        if not args.args:
            print("Usage: read_sessions.py summary SESSION_ID", file=sys.stderr)
            sys.exit(1)
        result = get_session_summary(project_dir, args.args[0])
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "messages":
        if not args.args:
            print("Usage: read_sessions.py messages SESSION_ID", file=sys.stderr)
            sys.exit(1)
        msgs = get_messages(project_dir, args.args[0],
                           user_only=args.user_only,
                           assistant_only=args.assistant_only,
                           limit=args.limit,
                           tail=args.tail)
        for m in msgs:
            role = m.get("role", "?")
            text = m.get("text", "")
            print(f"\n[{role.upper()}]:")
            print(text[:2000])
            print("---")

    elif args.command == "substance":
        if not args.args:
            print("Usage: read_sessions.py substance SESSION_ID [--tail N]", file=sys.stderr)
            sys.exit(1)
        tail_n = args.tail if args.tail > 0 else 15
        result = get_substance(project_dir, args.args[0], tail=tail_n)
        if "error" in result:
            print(result["error"], file=sys.stderr)
            sys.exit(1)
        print(f"Session: {result['session_id']}  |  Total: {result['total_messages']} msgs  |  Showing last: {result['showing_last']}")
        print(f"Files edited: {', '.join(os.path.basename(f) for f in result['files_edited']) or 'none'}")
        print(f"Broadcasts: {result['broadcast_count']}")
        print("=" * 80)
        for m in result["recent_messages"]:
            role = m["role"]
            text = m["text"]
            if role == "user":
                print(f"\n>>> USER:")
                print(text[:1500])
            else:
                print(f"\n<<< ASSISTANT:")
                print(text[:2000])
            print("---")

    elif args.command == "concurrent":
        groups = find_concurrent(project_dir, window_minutes=args.window, last=args.last)
        if not groups:
            print("No concurrent sessions found.")
        for i, group in enumerate(groups):
            print(f"\n=== Concurrent Group {i+1} ({len(group)} sessions) ===")
            # Find file conflicts
            all_files = defaultdict(list)
            for s in group:
                for ef in s["edit_files"]:
                    all_files[ef].append(s["id"])

            conflicts = {f: sids for f, sids in all_files.items() if len(sids) > 1}

            for s in group:
                print(f"  {s['id']}  {s['size_mb']:.1f}MB  edits:{','.join(s['edit_files']) or 'none':30s}  {s['first_msg'][:50]}")

            if conflicts:
                print(f"  CONFLICTS: {', '.join(f'{f} ({len(sids)} sessions)' for f, sids in conflicts.items())}")

    elif args.command == "edits":
        if not args.args:
            print("Usage: read_sessions.py edits SESSION_ID", file=sys.stderr)
            sys.exit(1)
        edits = get_edits(project_dir, args.args[0])
        for e in edits:
            if e.get("tool") == "Edit":
                print(f"EDIT {os.path.basename(e['file'])}: {e['old'][:50]} -> {e['new'][:50]}")
            elif e.get("tool") == "Write":
                print(f"WRITE {os.path.basename(e['file'])}: {e['preview'][:80]}")

    elif args.command == "diff":
        if len(args.args) < 2:
            print("Usage: read_sessions.py diff SESSION_ID1 SESSION_ID2", file=sys.stderr)
            sys.exit(1)
        s1 = get_session_summary(project_dir, args.args[0])
        s2 = get_session_summary(project_dir, args.args[1])

        print(f"Session A: {s1.get('session_id', '?')[:8]}")
        print(f"  Messages: {s1.get('user_messages', 0)} user, {s1.get('assistant_messages', 0)} assistant")
        print(f"  First msg: {s1.get('first_user_msg', '?')[:100]}")
        print(f"  Files edited: {s1.get('files_edited', [])}")

        print(f"\nSession B: {s2.get('session_id', '?')[:8]}")
        print(f"  Messages: {s2.get('user_messages', 0)} user, {s2.get('assistant_messages', 0)} assistant")
        print(f"  First msg: {s2.get('first_user_msg', '?')[:100]}")
        print(f"  Files edited: {s2.get('files_edited', [])}")

        # Find overlapping edits
        e1 = set(s1.get("files_edited", []))
        e2 = set(s2.get("files_edited", []))
        overlap = e1 & e2
        if overlap:
            print(f"\nCONFLICTS (both edited): {sorted(overlap)}")
        only_a = e1 - e2
        only_b = e2 - e1
        if only_a:
            print(f"Only A edited: {sorted(only_a)}")
        if only_b:
            print(f"Only B edited: {sorted(only_b)}")


if __name__ == "__main__":
    main()
