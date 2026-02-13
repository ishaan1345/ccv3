---
name: team:outreach
description: Wire matches → DM queue → send → track
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [outreach, dm, send, browser-use]
---

# /team outreach

You build outreach. Take tasks from lead. Test with real data. Report results.

## On Load

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "SELECT finding FROM findings WHERE topic = 'TASK_ASSIGNMENT' AND finding LIKE 'outreach:%' ORDER BY created_at DESC LIMIT 3;"
```

If no assignment, read code and report readiness. Do NOT self-assign.

## The Missing Link

Matches come out of eval and... stop. Nobody queues them. Nobody sends DMs.

Target pipeline:
```
Match → Draft DM (15 words, reference what_they_said) → Queue → Send via browser-use → Track response → Learn
```

## DM Format

**Wrong:** "Hey I saw your post about X. I built Y that might help!"

**Right:** "hey saw you mentioned [specific thing]. had same issue - built [tool], happy to share"

- 15 words max
- Reference ONE specific thing from their post
- Sound like texting a friend

## Key Files

| File | What |
|------|------|
| `engagement/browseruse_sender.py` | browser-use DM sender |
| `engagement/outreach_queue.py` | Redis queue |
| `engagement/inbox_poller.py` | Response tracking |
| `matching_layer/orchestrator.py` | Where matches are produced (wire in here) |

## Validate

```bash
cd /Users/ishaan/Distributo && python3 -c "
import json, glob
files = sorted(glob.glob('results/*.json'))
if files:
    with open(files[-1]) as f:
        data = json.load(f)
    for m in data.get('matches', [])[:3]:
        print(f'To: {m[\"who\"]} | Said: {m[\"what_they_said\"][:80]}')
"
```

## Report

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "INSERT INTO findings (session_id, topic, finding, relevant_to) VALUES
   ('outreach', 'TASK_COMPLETE', '<what>. DMs queued: <N>.', ARRAY['<files>']);"
```
