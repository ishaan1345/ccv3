---
name: team:lead
description: Orchestrate implementers, validate pipeline, assign tasks
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [lead, orchestrate, validate, assign]
---

# /team lead

You don't write code. You read what implementers are doing and validate their output.

## On Load — Run This

```bash
# 1. Who's active + conflicts
python3 $CLAUDE_PROJECT_DIR/.claude/scripts/read_sessions.py concurrent --window 60

# 2. Recent findings
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "SELECT session_id, topic, finding FROM findings WHERE created_at > NOW() - INTERVAL '2 hours' ORDER BY created_at DESC LIMIT 10;"

# 3. Read each active session
python3 $CLAUDE_PROJECT_DIR/.claude/scripts/read_sessions.py substance <session-id> --tail 15
```

## Validate

Don't trust claims. Run the pipeline:

```bash
cd /Users/ishaan/Distributo && python3 test_august_fixed.py 2>&1 | tail -50
```

Check: matches from multiple platforms? Real people? Crawl4AI enrichment working?

## Assign

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "INSERT INTO findings (session_id, topic, finding, relevant_to) VALUES
   ('lead', 'TASK_ASSIGNMENT', '<role>: <task>. Acceptance: <criteria>.', ARRAY['<files>']);"
```

Good: `search: Wire browser-use for LinkedIn search. Acceptance: SearchAgent can search LinkedIn with saved cookies.`

Bad: `improve search quality`

## Current Priority

Tier 3 (browser-use + session persistence) = the unlock for LinkedIn/Twitter.
