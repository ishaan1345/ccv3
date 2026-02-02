---
name: team:comp
description: Context and coordination for the comprehension agent pair. Injected when a session starts working on comprehension.
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [comprehension, icp, profile, founder, interview, reasoning model, identity signals]
---

# You Are Working on the Comprehension Agent

## What Distributo Is

An autonomous system that finds people expressing intent, responds instantly, and delivers conversations. A founder describes their product → Distributo continuously monitors the internet for people who have that problem → matches them semantically → crafts personalized messages → sends them → tracks responses → learns what works for next time.

The full loop: **COMPREHEND → MONITOR → MATCH → ALERT → DRAFT → SEND → TRACK → LEARN.** This compounds — after thousands of interactions, Distributo knows WHERE each ICP posts, HOW they express pain, WHAT makes them convert. Competitors start at zero.

The core chain right now: **Comprehension → Search → Eval → Outreach.** Each link only matters because of what it enables downstream. If any link breaks, the founder gets nothing.

## Why Comprehension Exists

You can't find someone if you don't know who you're looking for. A founder says "I built a CRM for field sales." That's not enough to find anyone. Comprehension turns that into: what does this person's life look like? What words come out of their mouth? Where do they hang out? What makes them different from someone who looks similar but isn't the customer?

Comprehension builds the mental model that makes finding possible. It interviews the founder and produces an ICPProfile — the shared artifact that every downstream component runs on.

## What Comprehension Must Produce

**Input:** Founder's product description + 1-2 interview answers.

**Output:** An ICPProfile that is a complete search execution plan. Not just "who" the customer is — but WHERE to find them and WHAT to search for.

Each field exists for a reason:

- **`reasoning_model`** — A paragraph that teaches eval to think like the founder. "Is this person someone I should contact?" If this is vague, eval can't discriminate. Must distinguish the ICP from look-alikes (field sales rep vs field service technician — both drive to customer sites, one sells, one repairs).

- **`communities`** — Actionable search targets per platform, **prioritized by ICP type.** Not bare platform names. Search takes these and dispatches them mechanically — if comp doesn't produce them, those platforms don't get searched. Examples: `"reddit:r/sales"`, `"twitter:#fieldsales"`, `"linkedin:posts field sales manager territory"`, `"youtube:SalesGravy channel comments"`, `"facebook:group/MedicalDeviceSalesPros"`.

  **NEVER assume Reddit-first.** Platform priority depends on WHO the customer is:
  | ICP Type | First Platform | Second | Third |
  |----------|----------------|--------|-------|
  | B2B Enterprise | LinkedIn | Twitter | Industry forums |
  | Consumer/Hobbyist | Reddit | Twitter | Facebook groups |
  | Developer/Technical | HackerNews | Twitter | Reddit |
  | Healthcare | Industry forums | LinkedIn | Reddit |

  Comp must prioritize the RIGHT platforms for THIS ICP, then expand to others. The 10 mainstream platforms (Reddit, LinkedIn, Twitter/X, Instagram, TikTok, Bluesky, Mastodon, HackerNews, YouTube, Facebook Groups) are the universe — but comp picks which matter MOST for this founder's customer.

- **`they_say_things_like`** — First-person situation phrases that work as search queries. "I have no idea what my reps are saying to customers" not "lack of visibility into field conversations." Keep under 8 words for Serper compatibility.

- **`identity_signals`** — Things this person leaks in unrelated contexts. "mileage reimbursement", "trunk full of samples." These become cross-platform search queries.

- **`false_positives`** — Who looks similar but isn't the customer. Each with TYPE + DETECT signals. Minimum: COACH_CONSULTANT, VENDOR, ADJACENT_ROLE, NOT_A_PERSON. Eval uses this to reject.

- **`dm_pitch`** — A message that makes the person say "tell me more." Outreach uses this.

- **`coverage_mode`** — "universal" (anyone who IS the ICP) or "active_seeker" (only people actively looking).

## Definition of Done

Comprehension is DONE when:

1. **Search can mechanically execute.** Take the comp output. For each entry in `communities`, can you construct a search query and run it? If any entry is just a platform name with no specifics, comp failed.

2. **The full pipeline finds real people.** Run the full pipeline end-to-end. If search finds 0 people using the ICP, comprehension failed — regardless of how good the profile looks in isolation.

3. **Eval agrees with the founder.** Give eval 10 real candidates (5 customers, 5 look-alikes) using only the `reasoning_model`. If eval misclassifies more than 1, the reasoning_model isn't specific enough.

4. **`they_say_things_like` work as search queries.** Take each phrase, search it on Google. Would the results page contain the founder's customer?

5. **Under $2 total cost.** 1 Opus call for interview + 1 for extraction = ~$0.50-$1.00.

## Task List — Create These on Bootstrap

When you start, create these tasks:

1. **Read comprehension.py end to end** — every line, especially the system prompt and extraction prompt. The extraction prompt IS the comprehension logic.
2. **Read icp_profile.py** — understand every field and `to_prompt_context()` which formats the ICP for downstream.
3. **Read a real ICP output** from `results/` to see what production output looks like.
4. **Read what search does with the ICP** — trace how `communities`, `identity_signals`, and `they_say_things_like` flow into search queries in orchestrator.py.
5. **Assess current output against definition of done** — does the latest ICP have actionable per-platform targets? Does the reasoning_model distinguish the ICP from look-alikes?
6. **Fix gaps** — whatever doesn't meet the definition of done.
7. **Test with real founder input** — the August ICP is the most tested case.

## Files

- **Source:** `/home/ishaa/Distributo/matching_layer/agents/comprehension.py`
- **Data contract:** `/home/ishaa/Distributo/matching_layer/icp_profile.py`
- **Orchestrator wiring:** `orchestrator.py` — comprehension called at the start of `run()`
- **Real results:** `/home/ishaa/Distributo/results/`

## Coordinate

Use `/team broadcast` when you change ICP structure. If you change communities format, search needs to know. If you change reasoning_model, eval's matching behavior changes. If you add a field, everyone downstream needs to know.
