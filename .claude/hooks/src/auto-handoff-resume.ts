#!/usr/bin/env npx tsx
/**
 * Auto-Handoff Resume Hook
 *
 * Two-part hook:
 * 1. PostToolUse: When a handoff is created (Write to thoughts/handoffs/**),
 *    store the path for auto-resume
 * 2. SessionStart: If a pending handoff exists, inject resume instruction
 *
 * This creates seamless handoff cycles without manual /clear and /resume_handoff
 */

import * as fs from 'fs';
import * as path from 'path';

const PENDING_HANDOFF_FILE = path.join(
  process.env.HOME || '~',
  '.claude/cache/pending-handoff.json'
);

interface HookInput {
  tool_name?: string;
  tool_input?: {
    file_path?: string;
    content?: string;
  };
  hook_type?: string;
  session_id?: string;
}

interface PendingHandoff {
  path: string;
  created_at: string;
  session_id?: string;
}

function savePendingHandoff(handoffPath: string, sessionId?: string): void {
  const pending: PendingHandoff = {
    path: handoffPath,
    created_at: new Date().toISOString(),
    session_id: sessionId
  };

  const cacheDir = path.dirname(PENDING_HANDOFF_FILE);
  if (!fs.existsSync(cacheDir)) {
    fs.mkdirSync(cacheDir, { recursive: true });
  }

  fs.writeFileSync(PENDING_HANDOFF_FILE, JSON.stringify(pending, null, 2));
}

function getPendingHandoff(): PendingHandoff | null {
  try {
    if (fs.existsSync(PENDING_HANDOFF_FILE)) {
      const content = fs.readFileSync(PENDING_HANDOFF_FILE, 'utf-8');
      return JSON.parse(content);
    }
  } catch {
    // Ignore errors
  }
  return null;
}

function clearPendingHandoff(): void {
  try {
    if (fs.existsSync(PENDING_HANDOFF_FILE)) {
      fs.unlinkSync(PENDING_HANDOFF_FILE);
    }
  } catch {
    // Ignore errors
  }
}

async function main() {
  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
  }

  let hookInput: HookInput;
  try {
    hookInput = JSON.parse(input);
  } catch {
    // Not JSON, pass through
    console.log(JSON.stringify({}));
    return;
  }

  const hookType = hookInput.hook_type ||
    (hookInput.tool_name ? 'PostToolUse' : 'SessionStart');

  // === PostToolUse: Detect handoff creation ===
  if (hookType === 'PostToolUse' && hookInput.tool_name === 'Write') {
    const filePath = hookInput.tool_input?.file_path || '';

    // Check if this is a handoff file
    const isHandoff = filePath.includes('thoughts/') &&
      filePath.includes('handoff') &&
      (filePath.endsWith('.yaml') || filePath.endsWith('.md'));

    if (isHandoff) {
      savePendingHandoff(filePath, hookInput.session_id);

      // Output instruction to Claude
      console.log(JSON.stringify({
        result: `\n\n` +
          `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n` +
          `📋 HANDOFF SAVED: ${path.basename(filePath)}\n` +
          `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n` +
          `\n` +
          `To continue seamlessly, run:\n` +
          `  /clear\n` +
          `\n` +
          `Then in new session:\n` +
          `  /resume_handoff ${filePath}\n` +
          `\n` +
          `Or just run /clear - the next session will auto-detect this handoff.\n` +
          `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`
      }));
      return;
    }
  }

  // === SessionStart: Check for pending handoff ===
  if (hookType === 'SessionStart') {
    const pending = getPendingHandoff();

    if (pending && fs.existsSync(pending.path)) {
      // Clear the pending flag so we don't loop
      clearPendingHandoff();

      // Inject resume instruction
      console.log(JSON.stringify({
        result: `\n\n` +
          `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n` +
          `🔄 PENDING HANDOFF DETECTED\n` +
          `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n` +
          `\n` +
          `A handoff was created in the previous session:\n` +
          `  ${pending.path}\n` +
          `  Created: ${pending.created_at}\n` +
          `\n` +
          `**AUTO-RESUMING**: Run /resume_handoff ${pending.path}\n` +
          `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`
      }));
      return;
    }
  }

  // No action needed
  console.log(JSON.stringify({}));
}

main().catch(e => {
  console.error('Hook error:', e);
  console.log(JSON.stringify({}));
});
