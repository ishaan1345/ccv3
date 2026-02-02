#!/bin/bash
# Auto-Handoff Resume Hook
# PostToolUse: Detects handoff creation, stores for auto-resume
# SessionStart: Injects resume instruction if pending handoff exists
set -e
cd ~/.claude/hooks

if [ -f "dist/auto-handoff-resume.mjs" ]; then
  cat | node dist/auto-handoff-resume.mjs
else
  cat | npx tsx src/auto-handoff-resume.ts
fi
