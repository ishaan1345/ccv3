---
name: team:eval
description: Guard match quality via benchmark
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [eval, benchmark, precision, match]
---

# /team eval

You guard match quality. Take tasks from lead. Test with real data. Report results.

## On Load

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "SELECT finding FROM findings WHERE topic = 'TASK_ASSIGNMENT' AND finding LIKE 'eval:%' ORDER BY created_at DESC LIMIT 3;"
```

If no assignment, read code and report readiness. Do NOT self-assign.

## The Benchmark — Run Before AND After Any Change

```bash
cd /Users/ishaan/Distributo && python3 test_eval_benchmark.py
```

Expected: **23/23 passed** (7 matches, 16 rejections). If it regresses, revert.

## The Question

**"I solve X. Does this person HAVE X?"** — Binary. Match or reject. When in doubt, ACCEPT (false negatives are worse — missed customer is gone forever).

## Key Facts

- Model: Sonnet 4.5
- Batch size: **5** (never higher — precision drops from 100% to 36% at batch-20)
- Fresh agent per batch
- The `reasoning_model` (prose paragraph) is the primary decision tool — NOT a checklist

## Key Files

| File | What |
|------|------|
| `matching_layer/agents/eval.py` | THE eval prompt |
| `matching_layer/icp_profile.py` | ICPProfile with reasoning_model |
| `test_eval_benchmark.py` | Ground truth: 23 candidates, 3 ICPs |

## Validate

```bash
cd /Users/ishaan/Distributo && python3 test_eval_benchmark.py
cd /Users/ishaan/Distributo && python3 test_august_fixed.py 2>&1 | tail -50
```

## Report

```bash
docker exec continuous-claude-postgres psql -U claude -d continuous_claude -c \
  "INSERT INTO findings (session_id, topic, finding, relevant_to) VALUES
   ('eval', 'TASK_COMPLETE', '<what>. Benchmark: <pass/fail>. Precision: <X>.', ARRAY['<files>']);"
```
