---
name: team:search
description: Context and coordination for the search agent pair. Injected when a session starts working on search.
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [search, candidates, platforms, reddit, linkedin, queries, tools, mine thread]
---

# You Are Working on Search

## What Distributo Is

An autonomous system that finds people expressing intent, responds instantly, and delivers conversations. A founder describes their product → Distributo continuously monitors the internet for people who have that problem → matches them semantically → crafts personalized messages → sends them → tracks responses → learns what works for next time.

The full loop: **COMPREHEND → MONITOR → MATCH → ALERT → DRAFT → SEND → TRACK → LEARN.** This compounds — after thousands of interactions, Distributo knows WHERE each ICP posts, HOW they express pain, WHAT makes them convert.

The core chain right now: **Comprehension → Search → Eval → Outreach.** Each link only matters because of what it enables downstream. If any link breaks, the founder gets nothing.

## Why Search Exists

People are scattered across the entire internet. They're on Reddit complaining about their CRM. They're on LinkedIn posting about managing their territory. They're on TikTok showing their daily routine. They're in niche forums asking for advice. Search goes everywhere these people could be and brings back anyone who might be the customer.

Search takes the ICP from comprehension — specifically `communities`, `they_say_things_like`, and `identity_signals` — and executes across every platform to find real humans with real usernames who might be the founder's customer.

## How Search Works — The Architecture

**Current state: Mechanical dispatch.** The search agent was tried and failed (48% of tool calls on Reddit, 0 matches for a real ICP). Mechanical search was chosen deliberately: cheap, deterministic, covers every platform comp specifies.

**End state: Agent-directed search with compound learning.** CLAUDE.md says "This is an AGENT. Do NOT hardcode query logic." The vision is that after many runs, Distributo learns WHERE each ICP posts, WHICH queries find them, and adapts automatically. The compound learning data in the orchestrator is the seed of this — proven_channels, successful_queries, match_profiles all feed future runs. The mechanical layer becomes the tool layer that an intelligent agent directs.

Comprehension produces platform-specific search targets in `communities`. The orchestrator dispatches each target through a 3-tier system:

| Tier | When | Examples |
|------|------|----------|
| **Tier 1: Native API** | Platform has API access | Reddit (PRAW), HackerNews (Algolia), YouTube (Data API v3), Bluesky (AT Protocol) |
| **Tier 2: Crawl** | Public page, no API | Crawl4AI scrape for TikTok comments, Facebook group posts, forum threads |
| **Tier 3: Browser** | Needs login | browser-use with saved session for LinkedIn, Twitter, Instagram |

**Fallback for all platforms:** Serper `site:` filter (Google index of the platform). This works but returns Google snippets (150 chars), not full platform content. Enrichment must add context before eval.

**Cycle 2+ optimization.** After mechanical search runs and eval produces matches + rejections, the search agent generates NEW queries based on what worked. LLM reasoning adds value in adaptation, not initial search. Over time, this is how the system learns which platforms and queries work for each ICP type — the compound learning moat.

## What Search Must Produce

**Input:** ICPProfile — `communities` (platform-specific targets), `they_say_things_like` (query seeds), `identity_signals` (cross-platform queries).

**Output:** Real people with real usernames on real platforms, with enough text for eval to judge.

Each candidate: `{who, platform, text, title, url, source_query}`

Requirements:
- **Real usernames** — not "[deleted]", not page metadata, not "anonymous"
- **Enough context** — eval needs to see what the person actually said. A 150-char snippet is barely enough. Enrichment (Crawl4AI, cross-platform Serper) should add context to thin candidates BEFORE they reach eval.
- **Platform diversity** — if all candidates come from one platform, the founder only finds people on that one platform. The whole internet means the whole internet.
- **Deduped** — don't send the same person to eval twice
- **Prefiltered** — kill obvious bots, job postings, vendor marketing with string heuristics (free) before they hit eval (costs money). But don't kill real people — a field rep complaining about CRM is not a vendor because they mention "our product."

## Definition of Done

Search is DONE when:

1. **Reproducible results.** Run the same ICP 3 times, 1 hour apart. Similar people appear each time. If run 1 finds 22 and run 2 finds 1 completely different person, search is broken.

2. **Platform diversity.** Matches from at least 3 different platforms. No single platform is more than 50% of candidates sent to eval.

3. **Candidates have enough text for eval.** If 80% of candidates have ≤100 chars, eval will correctly reject them as NO_SIGNAL. The fix isn't in eval — it's in search producing richer candidates or enriching thin ones.

4. **Under $3 for search + enrichment.** This leaves $2 for comp + eval to stay under $5 total. Cut sources that produce 0 matches. Don't spend money searching platforms that return nothing.

5. **Zero garbage reaches eval.** Prefilter kills bots, page metadata, job postings. But doesn't kill real people.

6. **The orchestrator is plumbing, not a search engine.** Search logic (query generation, platform-specific rules) lives in functions. The orchestrator decides WHAT and WHEN. The tools decide HOW.

## Task List — Create These on Bootstrap

When you start, create these tasks:

1. **Read orchestrator.py mechanical search sections** — understand how the parallel search system works, what it dispatches, what it skips.
2. **Read tools.py** — understand every search function, what it calls, what it returns. Note the `PLATFORMS` / `PLATFORM_SITES` dict.
3. **Read search.py** — the AI search agent. Understand its prompt and tools. Understand why it was bypassed and what role it plays in cycle 2+.
4. **Trace which platforms actually get searched** — for each of the 10 mainstream platforms, is there a code path that searches it? What tier does it use? What does it return?
5. **Assess current results against definition of done** — check the latest `results/` files. How many platforms produced matches? Is deep_read reproducible?
6. **Fix gaps** — wire missing platforms, fix deep_read temporal issue (use Reddit search with `time_filter=week` not `sub.new()`), enrich thin candidates.
7. **Run E2E and measure** — platform distribution, hit rate into eval, cost.

## Files

- **Orchestrator mechanical search:** `/home/ishaa/Distributo/orchestrator.py` ~lines 927-1326
- **Tools:** `/home/ishaa/Distributo/matching_layer/tools.py`
- **Search agent:** `/home/ishaa/Distributo/matching_layer/agents/search.py`
- **Real results:** `/home/ishaa/Distributo/results/`

## Coordinate

Use `/team broadcast` when you change search behavior. If you add a platform, eval needs to know what candidates look like from it. If you change query generation, the feedback loop may need adjustment. If a platform returns garbage, tell the lead.
