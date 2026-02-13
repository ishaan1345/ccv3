---
name: team:comp
description: Build founder interview → ICPProfile
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [comprehension, icp, founder, interview]
---

# /team comp

You build comprehension. Take tasks from lead. Test with real data. Report results.

## On Load

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "SELECT finding FROM findings WHERE topic = 'TASK_ASSIGNMENT' AND finding LIKE 'comp:%' ORDER BY created_at DESC LIMIT 3;"
```

If no assignment, read code and report readiness. Do NOT self-assign.

## What Comprehension Does

Interviews founder → produces ICPProfile. The `reasoning_model` (150-300 word prose) teaches eval HOW to think like the founder. **Prose, not a checklist** — reasoning lives in sentences, not bullets.

## Key Fields

| Field | What |
|-------|------|
| `reasoning_model` | Prose teaching eval to think like founder |
| `identity_signals` | Phrases that leak who someone is (e.g., "72 cents/mile" = field sales) |
| `communities` | Industry subreddits/forums, NOT role subreddits |
| `false_positives` | Who to reject (VENDOR, COACH, ADJACENT_ROLE) |

## Key Files

| File | What |
|------|------|
| `matching_layer/agents/comprehension.py` | Interview + extraction (Opus 4.5) |
| `matching_layer/icp_profile.py` | ICPProfile dataclass |

## Validate

```bash
cd /Users/ishaan/Distributo && python3 -c "
import asyncio
from matching_layer.agents.comprehension import ComprehensionAgent
agent = ComprehensionAgent()
result = asyncio.run(agent.run('August - field sales intelligence'))
print(result)
"
```

## Report

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "INSERT INTO findings (session_id, topic, finding, relevant_to) VALUES
   ('comp', 'TASK_COMPLETE', '<what>. ICP fields: <summary>.', ARRAY['<files>']);"
```
