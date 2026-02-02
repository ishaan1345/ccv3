---
name: team:eval
description: Context and coordination for the eval agent pair. Injected when a session starts working on eval.
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [eval, evaluation, match, reject, precision, confidence, reasoning model]
---

# You Are Working on the Eval Agent

## What Distributo Is

An autonomous system that finds people expressing intent, responds instantly, and delivers conversations. A founder describes their product → Distributo continuously monitors the internet for people who have that problem → matches them semantically → crafts personalized messages → sends them → tracks responses → learns what works for next time.

The core question for every match: **"I solve X. Does this person HAVE X?"** Not keyword matching. Not buying signals. Semantic understanding of whether this person is genuinely experiencing the problem.

The core chain: **Comprehension → Search → Eval → Outreach.** Each link only matters because of what it enables downstream. If any link breaks, the founder gets nothing.

## Why Eval Exists

Search is noisy. You search for "field sales manager" and get vendors selling to field sales managers, coaches advising field sales managers, recruiters hiring field sales managers, and actual field sales managers. Eval looks at each person and answers one question: **is this the founder's customer?**

Not "does this mention the topic." Not keyword matching. Recognition — would this person respond to the founder's DM with "yes I need that"?

Eval is a pure reasoning agent. No tools. It receives an ICPProfile (specifically the `reasoning_model`) and a batch of candidates. For each one, it "becomes" the founder and answers: **"Is this person IN THE PROBLEMSPACE?"** Binary. YES or NO. Not scores, not percentages — semantic recognition of whether this person genuinely has the problem the product solves.

The founder should see every match and think: **"Holy shit. This person wants MY product."**

## What Eval Must Produce

**Input:** ICPProfile + batch of 5 candidates (as XML with who, platform, text, url, source_query).

**Output:** For each candidate, a binary decision.

- **Matches:** `{who, platform, what_they_said, why_they_match, confidence, detected_signals, url, source_query}`. The founder reads `why_they_match` and immediately understands why this person is their customer. Not "matches ICP" — specific: "posted about managing 15 field reps across 3 territories and tracking visits in a spreadsheet."

- **Rejections:** `{who, reason, source_query}`. The `reason` must be a defined category: NOT_A_PERSON, VENDOR, FALSE_POSITIVE, COACH_CONSULTANT, NO_SIGNAL, WRONG_DOMAIN. The feedback loop uses these categories to tell search what to change. "OTHER" is not valid — if eval produces it, eval is broken.

**Philosophy (from CLAUDE.md): When in doubt, ACCEPT.** False negatives are worse than false positives. Better to show the founder a borderline match than to miss a real customer. The founder can skip someone in 2 seconds. But a missed customer is gone forever.

## Definition of Done

Eval is DONE when:

1. **The founder would agree with every match and every rejection.** Show 10 matches to the founder — they say "yes, message this person" for each. Show 10 rejections — they agree each is NOT their customer.

2. **Eval handles thin data correctly.** Most candidates arrive with 50-200 chars of text. Eval must make correct decisions with limited info. A genuinely ambiguous candidate should get MEDIUM confidence, not rejected as NO_SIGNAL.

3. **Known-good matches survive.** Take the best matches from previous runs and feed them through the current eval. If eval rejects known-good matches, eval is too strict.

4. **Rejection categories are meaningful.** Every rejection uses a defined category the feedback loop can act on. Zero "OTHER" rejections.

5. **Eval works across platforms.** LinkedIn candidates use third-person professional language. Reddit uses first-person venting. TikTok has short captions. The prompt handles all of these.

6. **Batch cost under $0.05.** Each batch of 5 uses Sonnet. Tune `max_tokens` — eval output is typically 200-500 tokens, not 8192.

## Task List — Create These on Bootstrap

When you start, create these tasks:

1. **Read eval.py end to end** — the system prompt IS the logic. Understand what it teaches the model to do and why each section exists.
2. **Read icp_profile.py** — understand `to_prompt_context()` which formats the ICP that eval reads.
3. **Read real results** from `results/` to see what production matches and rejections look like.
4. **Run the controlled experiment** — take known-good matches from a previous run and feed them through the current eval prompt. If eval rejects them, eval is too strict. This is the most important test.
5. **Check rejection categories** — are any rejections using "OTHER" or undefined categories?
6. **Test on messy data** — not curated benchmarks. Real candidates with 150-char snippets, ambiguous profiles, cross-platform data.
7. **Verify cost** — is `max_tokens` set appropriately?

## Files

- **Source:** `/home/ishaa/Distributo/matching_layer/agents/eval.py`
- **Data contract:** `/home/ishaa/Distributo/matching_layer/icp_profile.py`
- **Tests:** `/home/ishaa/Distributo/tests/unit/test_eval_component.py`
- **Trace tools:** `/home/ishaa/Distributo/trace_eval_batch.py`, `trace_eval_economics.py`
- **Real results:** `/home/ishaa/Distributo/results/`
- **Orchestrator eval wiring:** `orchestrator.py` — batching at ~lines 565-640

## Coordinate

Use `/team broadcast` when you change eval behavior. If you change what eval accepts or rejects, search and comp need to know. The search pair needs to know if you need more context per candidate. The comp pair needs to know if the reasoning_model is specific enough.
