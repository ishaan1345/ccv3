---
name: cci-digest
description: Parallel CCI session analysis - spawns one agent per CCI transcript to extract all project intentions, technical architecture, product outcomes, and journey details. Synthesizes into a compound report.
allowed-tools: [Read, Glob, Grep, Bash, Task, TaskOutput, Write, Edit, AskUserQuestion]
---

# CCI Digest - Parallel Session Intelligence

Spawn one agent per CCI transcript file. Each agent reads the full file and extracts everything about the project (Distributo or whatever is being built). An orchestrator synthesizes all extractions into a single compound knowledge report.

## When to Use

- "Digest my CCI sessions"
- "Compound learning from CCIs"
- "What's the state of the project across sessions?"
- "Extract everything from my recent sessions"
- "/cci-digest"

## Step 1: Discover CCI Files

```bash
# Find the 20 most recent CCI files by modification time
ls -lt $CLAUDE_PROJECT_DIR/cci*.txt $CLAUDE_PROJECT_DIR/CCI*.txt $CLAUDE_PROJECT_DIR/opc/cci*.txt $CLAUDE_PROJECT_DIR/opc/CCI*.txt 2>/dev/null | head -20
```

Collect the 20 most recent files. If user specifies a count or range, use that instead.

## Step 2: Create Output Directory

```bash
BATCH_ID=$(date +%Y%m%d-%H%M%S)
OUTDIR="$CLAUDE_PROJECT_DIR/.claude/cache/cci-digest/$BATCH_ID"
mkdir -p "$OUTDIR/extractions"
```

Store the `$OUTDIR` and `$BATCH_ID` for all subsequent steps.

## Step 3: Spawn Parallel Extraction Agents

Launch agents in batches of **10** (to stay within limits). Each agent is `general-purpose` with `run_in_background: true`.

**CRITICAL:** Each agent prompt MUST include:
1. The full path to its CCI file
2. The output path where it writes its extraction
3. The complete extraction schema below

### Agent Prompt Template

For each CCI file, spawn a Task with this prompt (fill in `{CCI_FILE}`, `{CCI_NAME}`, `{OUTPUT_FILE}`):

```
You are a session analyst. Read the ENTIRE file at {CCI_FILE} using the Read tool (use offset/limit if needed to read it all — files can be 2000+ lines). Extract EVERY detail about the project being built.

Write your extraction as markdown to {OUTPUT_FILE} using the Write tool.

## Extraction Schema

Your output file MUST contain ALL of these sections:

### 1. Session Identity
- CCI file: {CCI_NAME}
- Date/time range (if visible in transcript)
- Session ID (if visible)

### 2. User Intentions & Goals
What is the user TRYING to achieve? Not just the task — the WHY.
- Immediate goal of this session
- Broader product vision expressed
- Frustrations or urgency signals
- What they want the product to DO for end users

### 3. Product Outcomes Desired
What does the user want Distributo (or the product) to BE?
- Target users / ICP (ideal customer profile)
- Core value proposition
- Features requested or envisioned
- Success metrics mentioned
- Competitive positioning
- Go-to-market signals

### 4. Technical Architecture
Every technical detail mentioned or worked on:
- Tech stack (languages, frameworks, databases, infra)
- System components and how they connect
- API designs, schemas, data models
- File structure and key files modified
- Services, microservices, deployment topology
- Integration points (third-party APIs, auth, payments, etc.)

### 5. What Was Built / Changed
Concrete work done in this session:
- Features implemented (with file paths if visible)
- Bugs fixed (root cause + solution)
- Refactors performed
- Tests added or modified
- Configuration changes
- Infrastructure/deployment changes

### 6. Decisions Made
Architectural and product decisions with rationale:
- Why X approach over Y
- Trade-offs discussed
- Constraints acknowledged
- Design patterns chosen

### 7. Problems & Blockers
- Errors encountered (with stack traces if present)
- Debugging journeys (what was tried, what worked)
- Unresolved issues at session end
- Performance problems
- Missing dependencies or capabilities

### 8. Open Threads
Work that was started but not finished:
- TODOs mentioned
- "Next session" plans
- Partially implemented features
- Known technical debt

### 9. Key Learnings
- What worked well
- What failed and why
- Patterns discovered
- Reusable approaches

### 10. Raw Quotes
Copy 3-5 of the most revealing direct quotes from the user (their actual typed messages) that show intent, frustration, or vision. Preserve exact wording.

---

IMPORTANT: Read the ENTIRE file. If it's long, use offset/limit to page through it. Do NOT summarize from just the first few hundred lines. Every section must be filled — write "None observed" only if truly absent.

When done, write the extraction to {OUTPUT_FILE} and then run:
echo "COMPLETE: {CCI_NAME}" >> {OUTDIR}/status.txt
```

### Launch Pattern

Launch 10 agents at a time in a single message (all `run_in_background: true`). Wait for batch completion by checking:

```bash
wc -l "$OUTDIR/status.txt"
```

When count reaches 10, launch next batch of up to 10.

## Step 4: Monitor Completion

```bash
# Check how many are done
cat "$OUTDIR/status.txt" 2>/dev/null | wc -l

# See which completed
cat "$OUTDIR/status.txt" 2>/dev/null
```

Wait until all agents complete. If an agent seems stuck after 3 minutes, check its output file — it may have written partial results.

## Step 5: Synthesize

Once all extractions are written, read each extraction file and produce a **single compound report** at `$OUTDIR/compound-report.md`.

The compound report structure:

```markdown
# CCI Compound Digest — {BATCH_ID}

**Sessions analyzed:** {N}
**Date range:** {earliest} → {latest}
**Generated:** {now}

## Executive Summary
3-5 sentences: What is this project, where is it headed, what's the current state.

## Product Vision & Outcomes
Synthesize across ALL sessions:
- What is Distributo / the product?
- Who are the target users?
- What outcomes does the user want for end users?
- Core value proposition (evolved across sessions)
- Feature roadmap (implied from sessions)
- Go-to-market signals

## Technical Architecture (Current State)
Synthesize the LATEST state of:
- Tech stack
- System architecture diagram (text-based)
- Key components and their relationships
- Data models / schemas
- API surface
- Infrastructure / deployment

## Timeline of Evolution
Chronological narrative:
| Session | Date | Key Work | Outcome |
|---------|------|----------|---------|
| cci85 | ... | ... | ... |
...

## Accumulated Decisions
All architectural and product decisions, deduplicated:
| Decision | Rationale | Session |
|----------|-----------|---------|
...

## Recurring Patterns
Themes that appear across multiple sessions:
- Technical patterns (approaches used repeatedly)
- Product patterns (features that keep evolving)
- User behavior patterns (how the user works)

## Open Threads & Technical Debt
Everything unfinished, merged across sessions (skip items resolved in later sessions):
- Active open threads
- Known technical debt
- Planned but not started

## Problems & Solutions Log
| Problem | Root Cause | Solution | Session |
|---------|------------|----------|---------|
...

## Key Learnings (Compound)
Deduplicated, ranked by frequency:
1. ...
2. ...

## User Intent Fingerprint
Distilled understanding of what the user cares about most, how they work, what frustrates them, and what excites them. This is the "soul" of the project extracted from raw session transcripts.

## Raw Signal
The most revealing user quotes across all sessions, curated for insight density.
```

Write this report using the Write tool. Then tell the user where to find it.

## Step 6: Report to User

Print:
- Path to compound report
- Count of sessions analyzed
- 5-line executive summary
- Top 3 open threads
- Offer to store key learnings to memory system

## Configuration

| Parameter | Default | Override |
|-----------|---------|---------|
| Batch size | 10 agents | User can request different |
| CCI count | 20 most recent | User can specify range |
| Agent type | general-purpose | Don't change |
| Model | Inherit (Opus) | Never use Haiku |
| Source dirs | Project root + opc/ | User can specify |

## Important Notes

- **Never use Haiku** for extraction agents — these need comprehension
- **Always read full files** — CCI transcripts are 17KB-377KB, agents must page through
- **File-based coordination** — agents write to files, don't use TaskOutput
- **Dedup in synthesis** — later sessions supersede earlier ones for "current state"
- **Preserve raw signal** — quotes and exact details matter more than summaries
