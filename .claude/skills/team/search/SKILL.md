---
name: team:search
description: Build the 3-tier search system
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [search, crawl4ai, browser-use, platforms]
---

# /team search

You implement search. Take tasks from lead. Test with real data. Report results.

## On Load

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "SELECT finding FROM findings WHERE topic = 'TASK_ASSIGNMENT' AND finding LIKE 'search:%' ORDER BY created_at DESC LIMIT 3;"
```

If no assignment, read code and report readiness. Do NOT self-assign.

## Key Insight

**Identity signals > topic queries.** "72 cents/mile" finds field sales reps. "Field sales CRM" finds consultants. Search for WHO someone IS, not what topic they're discussing.

**Industry subreddits > role subreddits.** r/MedicalDevices = 7 matches from one thread. r/sales = zero across all runs.

## The 3 Tiers

| Tier | What | Status | Files |
|------|------|--------|-------|
| 1 | APIs (Reddit PRAW, HN Algolia, YouTube) | ✅ Done | tools.py |
| 2 | Crawl4AI (headless Chrome for public pages) | ✅ Done (78% success) | tools.py, search.py |
| 3 | browser-use (founder's logged-in accounts) | 🔄 Next | browseruse_sender.py, tools.py |

## Key Files

| File | What |
|------|------|
| `matching_layer/agents/search.py` | **SearchAgent** — LLM that decides what to search, 8 tools |
| `matching_layer/tools.py` | All platform tools, Crawl4AI, browser-use |
| `matching_layer/orchestrator.py` | Calls `search_agent.search()` on lines 510/519 |
| `engagement/browseruse_sender.py` | browser-use DM sender (adapt for search) |

## Validate

```bash
cd /Users/ishaan/Distributo && python3 test_august_fixed.py 2>&1 | tail -50
```

## Report

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "INSERT INTO findings (session_id, topic, finding, relevant_to) VALUES
   ('search', 'TASK_COMPLETE', '<what>. Results: <platforms, matches, cost>.', ARRAY['<files>']);"
```
