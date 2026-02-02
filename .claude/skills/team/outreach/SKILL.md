---
name: team:outreach
description: Context and coordination for the outreach/engagement pair. Injected when a session starts working on outreach.
allowed-tools: [Bash, Read, Task, Write, Edit, Grep, Glob]
keywords: [outreach, engagement, dm, message, send, browser, reddit, linkedin, response, followup]
---

# You Are Working on Outreach

## What Distributo Is

An autonomous system that finds people expressing intent, responds instantly, and delivers conversations. A founder describes their product -> Distributo continuously monitors the internet for people who have that problem -> matches them semantically -> crafts personalized messages -> sends them -> tracks responses -> learns what works for next time.

Target: **30-50% response rate** vs 1-5% cold outreach baseline. This is possible because every person Distributo messages was found expressing the exact problem the product solves. The message references what they actually said.

The core chain: **Comprehension -> Search -> Eval -> Outreach.** You are the last link. If outreach doesn't work, everything before it was wasted.

## Why Outreach Exists

Finding someone is worthless if you don't reach them. The founder can't manually DM 50 people across 10 platforms. Outreach takes every match from eval and turns it into a conversation.

This is NOT cold outreach. Every match comes with: who they are, what they said, why they match the ICP, which platform they're on, and the ICP's dm_pitch. The message references their specific situation. That's why the response rate target is 30-50%, not 1-5%.

## What Outreach Must Produce

**Input:** A match from eval: `{who, platform, what_they_said, why_they_match, url, confidence}` + the ICP's `dm_pitch`.

**Output:** A personalized message sent on the correct platform, with response tracking.

Each message must:

1. **Reference the person's specific situation.** Not "Hey, I saw you're in sales." Instead: "I saw your post about tracking customer visits in a spreadsheet -- we built something that does this automatically from your phone." The match's `what_they_said` and `why_they_match` give you the material.

2. **Use the ICP's `dm_pitch` as the template.** The founder (via comp) wrote a pitch that makes the customer say "tell me more." Personalize it with the specific match context.

3. **Send on the right platform using the right method:**
   - Reddit -> `reddit_sender.py` via PRAW DM
   - LinkedIn -> `browseruse_sender.py` via browser automation (requires saved session)
   - Twitter -> `browseruse_sender.py` via browser automation (requires saved session)
   - Other platforms -> `engage.ts` / `simple-engage.ts` via Playwright

4. **Respect rate limits.** `PlatformRateLimiter` in tools.py has hard limits per platform. Don't get the founder's accounts banned.

5. **Track responses.** `inbox_poller.py` watches for replies. `followup_scheduler.py` schedules follow-ups. Response data feeds back into compound learning -- what worked, what didn't, which platforms convert.

## Definition of Done

Outreach is DONE when:

1. **Matches become messages.** Every match from eval is turned into a drafted message. Zero matches go unreached.

2. **The founder approves every message.** Show 10 drafted messages to the founder. They approve all 10. Not generic spam -- each message proves you understood the person's situation.

3. **Messages actually send.** The browser automation works on at least 2 platforms (Reddit + one authenticated platform). Rate limiting prevents bans.

4. **Response tracking works.** When someone replies, the system captures it. Response rate is measured per platform, per ICP, per message variant.

5. **The learn loop closes.** Response data feeds back: which dm_pitch variants work, which platforms convert, which match confidence levels produce responses. This is the compound learning moat -- every outreach batch makes the next one better.

## Task List -- Create These on Bootstrap

1. **Read the engagement layer** -- `engagement/browseruse_sender.py`, `outreach_queue.py`, `followup_scheduler.py`, `inbox_poller.py`, `reddit_sender.py`, `rate_limiter.py`. Understand what's built.
2. **Read the automation layer** -- `automation/engage.ts`, `simple-engage.ts`. Understand the Playwright message filling.
3. **Read how matches come out of the orchestrator** -- trace the `matches` list from `orchestrator.run()` to see what data is available per match.
4. **Wire pipeline output to outreach queue** -- matches from eval should flow into `outreach_queue.py`.
5. **Test message generation** -- take the 22 real matches from `results/august_traced_1769910551.json` and draft messages for each using the dm_pitch.
6. **Test sending on Reddit** -- reddit_sender.py should be able to send a DM using PRAW.
7. **Set up response tracking** -- inbox_poller.py polls for replies and records them.

## Files

- **Engagement layer:** `/home/ishaa/Distributo/engagement/`
- **Automation:** `/home/ishaa/Distributo/automation/`
- **Rate limiter:** `/home/ishaa/Distributo/matching_layer/tools.py` (PlatformRateLimiter class)
- **Match data contract:** `/home/ishaa/Distributo/matching_layer/icp_profile.py` (Match dataclass)
- **Real matches to test with:** `/home/ishaa/Distributo/results/august_traced_1769910551.json`

## Coordinate

Use `/team broadcast` when you change outreach behavior. If you need more data per match (e.g., full post text for personalization), tell the eval pair. If dm_pitch needs refinement, tell the comp pair. If a platform's send mechanism is broken, tell the search pair (they may be using the same browser sessions).
