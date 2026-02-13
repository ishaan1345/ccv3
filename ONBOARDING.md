# Continuous Claude v3 (CCV3) — Onboarding

**Generated:** 2026-02-02
**Purpose:** Get a new laptop running CCV3 + Distributo

---

## What This Repo Is

CCV3 is the Claude Code infrastructure layer — hooks, skills, agents, scripts, and rules that make Claude Code sessions smarter. It provides:

- **Hooks** (`.claude/hooks/`): Pre/post tool-use interceptors, session lifecycle, compiler-in-the-loop, memory awareness, search routing, etc.
- **Skills** (`.claude/skills/`): 100+ slash-command skills for workflows (/build, /fix, /explore, /team, /commit, /tdd, etc.)
- **Agents** (`.claude/agents/`): Agent prompt definitions (scout, kraken, architect, oracle, etc.)
- **Scripts** (`.claude/scripts/`): Session analysis, status display, recall/store learnings
- **Rules** (`.claude/rules/`): Behavioral rules injected into every session (currently managed via `~/.claude/rules.ccv3/` globally)

## Key Projects Using CCV3

### Distributo (`/Users/ishaan/Distributo/`)
- **Repo:** `github.com/ishaan1345/Distributo`
- **What:** Autonomous lead-finding system. Finds people expressing purchase intent online, matches against ICP, delivers verified leads.
- **Architecture:** Orchestrator + 3 sub-agents (comprehension, search, eval) with compound learning
- **Current status:** Multi-platform search rewrite complete. 8 platforms (Reddit, HN, LinkedIn, Twitter/X, YouTube, forums, discussions, browser). Eval benchmark suite added.
- **Onboarding doc:** `.scout_reports/codebase-onboarding-20260202-170630.md` (in Distributo repo)
- **Known issues:** 25 bugs documented in onboarding doc. Critical: missing `signals` field, undefined import, token accounting gap.

### The /team Skill
CCV3 includes a `/team` skill for multi-session Distributo development:
- `/team lead` — orchestrate pairs, make decisions
- `/team search` — work on search agent
- `/team comp` — work on comprehension agent
- `/team eval` — work on eval agent
- `/team outreach` — work on outreach/DM system

## Setup on New Laptop

### 1. Clone repos
```bash
git clone https://github.com/ishaan1345/ccv3.git ~/Continuous-Claude-v3
git clone https://github.com/ishaan1345/Distributo.git ~/Distributo
```

### 2. Install hooks dependencies
```bash
cd ~/Continuous-Claude-v3/.claude/hooks
npm install
bash build.sh  # Compiles TS → JS in dist/
```

### 3. Install Python dependencies
CCV3 uses `uv` for Python. Install uv first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 4. Global rules
The `.claude/rules/` files were moved to `~/.claude/rules.ccv3/` (global, not per-project). These are loaded via CLAUDE.md references. If rules aren't working, copy from a backup or check the CLAUDE.md for the project.

### 5. Settings
`.claude/settings.json` currently has only `statusLine` configured. Hooks are configured but the settings.json hook block was stripped — hooks fire via the hook files themselves + Claude Code's auto-discovery.

### 6. MCP servers
`.claude/servers/` contains: ast-grep, fetch, firecrawl, git, morph, nia, perplexity, qlty, repoprompt. These may need API keys configured in `~/.claude/mcp_config.json` or environment variables.

### 7. Distributo setup
```bash
cd ~/Distributo
pip install -r requirements.txt  # or uv pip install -r requirements.txt
# Needs: ANTHROPIC_API_KEY, SERPER_API_KEY, REDDIT_CLIENT_ID/SECRET in .env
```

## Current Distributo Status (as of 2026-02-02)

### What's Working
- Multi-platform search with diversity enforcement (must search 3+ platforms)
- Proven channel priming (reuses successful subreddits from prior runs)
- Prefilter for job listings and vendor content
- Batch parallel eval (groups of 5)
- Compound learning via PostgreSQL

### Recent E2E Test Results
- **August (field sales ICP):** 25 matches, $1.42, 127s. Strong quality from r/medicaldevices.
- **Scaylor (enterprise unification ICP):** 4 matches, $2.08, 201s. ICP is hard but matches are real.

### What Needs Work
- Search coverage: system doesn't know enough of the social internet. CCI 54 found 20 Scaylor-type matches in one session — current system finds 4. The people exist, the search strategy needs expansion.
- Comprehension agent generates LinkedIn-heavy communities, misses Reddit/HN targets for enterprise ICPs.
- 69 VENDOR rejections for Scaylor — search finds software companies talking about integration, not buyers.
