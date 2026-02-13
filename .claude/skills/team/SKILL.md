---
name: team
description: Multi-session orchestration for Distributo
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [team, sessions, coordinate, delegate, status]
---

# /team

Distributo finds people expressing problems on the internet and reaches out referencing what they said. 30-50% response rate vs 1-5% for cold outreach.

## The Core Question

**"I solve X. Does this person HAVE X?"**

Not demographics. Not job titles. Semantic intent matching against expressed pain. The founder sees matches and says "holy shit, message this person."

## Key Insights

- **Identity signals > topic queries.** "72 cents/mile" finds field sales reps. "Field sales CRM challenges" finds consultants.
- **Industry subreddits > role subreddits.** r/MedicalDevices = gold. r/sales = zero.
- **Compound learning moat.** Every run teaches WHERE each ICP posts, HOW they describe pain, WHAT signals they leak. After 10,000 runs, competitors can't catch up.

## Pipeline

```
Comprehension (Opus) → 3-Tier Search → Eval (batch-5) → Outreach → Learn
```

| Tier | What | Status |
|------|------|--------|
| 1 | APIs (Reddit, HN, YouTube) | ✅ Done |
| 2 | Crawl4AI (forums, blogs) | ✅ Done |
| 3 | browser-use (LinkedIn, Twitter) | 🔄 In progress |

## Commands

```bash
# See active sessions + what they're editing
python3 $CLAUDE_PROJECT_DIR/.claude/scripts/read_sessions.py concurrent --window 60

# Read a session's actual conversation
python3 $CLAUDE_PROJECT_DIR/.claude/scripts/read_sessions.py substance <session-id> --tail 15

# Task assignments and reports
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "SELECT session_id, topic, finding FROM findings WHERE created_at > NOW() - INTERVAL '2 hours' ORDER BY created_at DESC LIMIT 10;"

# Assign a task
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "INSERT INTO findings (session_id, topic, finding, relevant_to) VALUES
   ('lead', 'TASK_ASSIGNMENT', '<role>: <task>. Acceptance: <criteria>.', ARRAY['<files>']);"
```

## Roles

| Role | Skill | Job |
|------|-------|-----|
| Lead | `/team lead` | Read sessions, validate pipeline, assign tasks |
| Search | `/team search` | Build 3-tier search |
| Eval | `/team eval` | Guard match quality (benchmark: 23/23) |
| Comp | `/team comp` | Interview founder → ICPProfile |
| Outreach | `/team outreach` | Wire matches → DM queue → send → track |

## Repo

`/Users/ishaan/Distributo`

```
matching_layer/
  orchestrator.py      # Pipeline coordinator
  tools.py             # Platform tools, Crawl4AI, browser-use
  agents/
    search.py          # SearchAgent (Sonnet, 8 tools) - ACTIVE
    eval.py            # Eval (Sonnet, batch-5)
    comprehension.py   # Interview (Opus)
engagement/
  browseruse_sender.py # Multi-platform DM sender
  outreach_queue.py    # Redis queue
```

## One Rule

Run the pipeline after any change: `python3 test_august_fixed.py`
