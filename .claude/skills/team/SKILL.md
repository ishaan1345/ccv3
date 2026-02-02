---
name: team
description: Multi-session coordination for paired Claude Code sessions. Status, delegation, peer review, paired engineering protocol.
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [team, sessions, coordinate, delegate, review, status, pair, collaborate, multi-session, parallel]
---

# /team

You are one of multiple Claude Code sessions running simultaneously. Use this to coordinate with other sessions and your pair partner.

## Commands

### `/team status`

```bash
# Active sessions
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "SELECT id, working_on, last_heartbeat FROM sessions WHERE last_heartbeat > NOW() - INTERVAL '30 minutes' ORDER BY last_heartbeat DESC;" 2>/dev/null

# File claims
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "SELECT file_path, session_id, claimed_at FROM file_claims WHERE claimed_at > NOW() - INTERVAL '30 minutes' ORDER BY claimed_at DESC;" 2>/dev/null

# Shared findings
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "SELECT session_id, topic, finding, created_at FROM findings WHERE created_at > NOW() - INTERVAL '2 hours' ORDER BY created_at DESC LIMIT 15;" 2>/dev/null

# Concurrent sessions + file conflicts (JSONL fallback)
python3 $CLAUDE_PROJECT_DIR/.claude/scripts/read_sessions.py concurrent --window 60
```

### `/team review`

Read your partner's work. Don't review code style. Review logic.

```bash
# See what your partner is THINKING and DOING (recent work, not setup boilerplate)
python3 $CLAUDE_PROJECT_DIR/.claude/scripts/read_sessions.py substance <partner-session-id>

# See what files they changed
python3 $CLAUDE_PROJECT_DIR/.claude/scripts/read_sessions.py edits <partner-session-id>

# Read the actual diff
git diff --stat && git diff <file>
```

Challenge protocol -- ask your partner:
1. What invariant does this change preserve?
2. Show me a real input that would be handled differently after this change.
3. Does the test encode the contract or just pass?
4. Does the downstream component still get what it needs?

### `/team broadcast`

Tell other sessions what you discovered or decided.

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "INSERT INTO findings (session_id, topic, finding, relevant_to) VALUES
   ('$(cat /tmp/claude_session_id 2>/dev/null || echo unknown)', '<TOPIC>', '<what you found>', ARRAY['<file1.py>']);" 2>/dev/null
```

Topics: `DISCOVERY`, `BUG_FOUND`, `FIX_APPLIED`, `TEST_RESULT`, `BLOCKER`, `TASK_ASSIGNMENT`

### `/team delegate`

Assign work to pairs.

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "INSERT INTO findings (session_id, topic, finding, relevant_to) VALUES
   ('orchestrator', 'TASK_ASSIGNMENT', '<which pair>: <what to do and why>', ARRAY['<files>']);" 2>/dev/null
```

---

## How to Work as a Pair

You and your partner work on the SAME component. Not dividing tasks -- collaborating. One proposes, the other challenges. Both think.

### Before writing any code

1. **Read the component.** Not skim -- read every line. Understand the data flow in and out. What does this component receive? What does it produce? What does the next component in the chain NEED from you?

2. **Read the prompts.** In agent systems, prompts ARE the logic. A one-line prompt change can move precision 30 points. Understand what the prompt is teaching the model to do and why each instruction exists.

3. **Explain to your partner** what you're about to change and WHY. If you can't explain why the change is correct in plain language, you don't understand it yet. Don't write code to "try things." Understand first, then implement.

4. **Trace the data.** Follow a real input through the entire system end to end. If you can't trace a concrete example from input to final output, you don't understand the system.

### After writing code

Your partner runs `/team review` and challenges:
- What does downstream get now that it didn't before?
- Show me a real input that hits this code path.
- Does the test use realistic data or idealized data? (Tests with hand-crafted perfect inputs that pass 100% while live runs fail is a known pattern -- don't repeat it.)

### Sharing across pairs

Broadcast discoveries to other pairs. If you fix something that changes what another component receives, they need to know. Use `/team broadcast`.

Check `/team status` before editing. If another pair is in the same file, coordinate.

---

## Understanding Your Component

When you start working on a component, develop DEEP understanding before touching code. Here's how:

### 1. Read the source

Read every line of your component file. Not the summary from a digest -- the actual code. Understand:
- What it receives (function signatures, data structures)
- What it produces (return types, side effects)
- What the prompts teach the model to do (for agent components)
- Where the actual logic lives vs where it's just plumbing

### 2. Read adjacent components

Your component doesn't exist alone. Read what feeds into it and what consumes its output. Understand the CONTRACT -- not the type signature, the semantic guarantee. "This function returns a list of candidates" is the type. "Every candidate has a real username on a real platform with enough context for the next component to make an identity-level judgment" is the contract.

### 3. Read the tests

Tests tell you what the author thought was important. But also look for what's MISSING. If the tests use idealized inputs but live data looks different, the tests are lying about quality.

### 4. Read the history

Read session histories or CCI digests to understand WHY the code looks the way it does. There are often hard-won decisions behind specific lines -- a bias that was removed, a batch size that was tuned, a feature that was added and then bypassed. Understanding the history prevents you from reverting good decisions or repeating failed approaches.

### 5. The CTO test

Before writing code, you must be able to answer:
- **WHY** does this component exist? Not what it does -- why the system needs it.
- **What does it PROMISE** to the next component? The semantic guarantee, not the type.
- **What does it ASSUME** from the previous component? What must be true for it to work?
- **What are the known failure modes?** Not theoretical -- what actually went wrong in production.
- **What would a wrong output look like?** Describe a specific false positive or broken output and explain why the current logic allows it.

---

## Engineering Discipline

### Prompts are code

In agent systems, the system prompt IS the primary logic. Python is plumbing. When precision moves 30 points from a prompt change and 0 points from a refactor, spend your time on the prompt.

### Tests prove contracts, not code

Bad test: `assert len(results) > 0` -- proves nothing about quality.
Good test: Tests with realistic data quality that verify the semantic contract holds.

If tests pass with hand-crafted inputs but live runs fail -- the tests are wrong, not the live system.

### Don't analyze forever

8 sessions of analysis with 0 code shipped is a known failure mode. When you understand the problem, build. Understanding is necessary but not sufficient. Ship code, test it with real data, iterate.

### The chain is everything

Every component exists to serve one chain: user intent → understanding → search → evaluation → outreach → response → learning. If any link breaks, the founder gets nothing. Always think about where you sit in the chain and what happens upstream and downstream of you.

### The compound learning moat

Distributo's moat isn't the code — it's the data. After thousands of interactions, the system knows WHERE each ICP type posts, HOW they express pain, WHAT queries find them, WHICH messages get responses. This compounds. Every run makes the next run better. When you write code, ask: does this produce data that makes future runs smarter?
