#!/usr/bin/env npx tsx

// src/auto-handoff-resume.ts
import * as fs from "fs";
import * as path from "path";
var PENDING_HANDOFF_FILE = path.join(
  process.env.HOME || "~",
  ".claude/cache/pending-handoff.json"
);
function savePendingHandoff(handoffPath, sessionId) {
  const pending = {
    path: handoffPath,
    created_at: (/* @__PURE__ */ new Date()).toISOString(),
    session_id: sessionId
  };
  const cacheDir = path.dirname(PENDING_HANDOFF_FILE);
  if (!fs.existsSync(cacheDir)) {
    fs.mkdirSync(cacheDir, { recursive: true });
  }
  fs.writeFileSync(PENDING_HANDOFF_FILE, JSON.stringify(pending, null, 2));
}
function getPendingHandoff() {
  try {
    if (fs.existsSync(PENDING_HANDOFF_FILE)) {
      const content = fs.readFileSync(PENDING_HANDOFF_FILE, "utf-8");
      return JSON.parse(content);
    }
  } catch {
  }
  return null;
}
function clearPendingHandoff() {
  try {
    if (fs.existsSync(PENDING_HANDOFF_FILE)) {
      fs.unlinkSync(PENDING_HANDOFF_FILE);
    }
  } catch {
  }
}
async function main() {
  let input = "";
  for await (const chunk of process.stdin) {
    input += chunk;
  }
  let hookInput;
  try {
    hookInput = JSON.parse(input);
  } catch {
    console.log(JSON.stringify({}));
    return;
  }
  const hookType = hookInput.hook_type || (hookInput.tool_name ? "PostToolUse" : "SessionStart");
  if (hookType === "PostToolUse" && hookInput.tool_name === "Write") {
    const filePath = hookInput.tool_input?.file_path || "";
    const isHandoff = filePath.includes("thoughts/") && filePath.includes("handoff") && (filePath.endsWith(".yaml") || filePath.endsWith(".md"));
    if (isHandoff) {
      savePendingHandoff(filePath, hookInput.session_id);
      console.log(JSON.stringify({
        result: `

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
\u{1F4CB} HANDOFF SAVED: ${path.basename(filePath)}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

To continue seamlessly, run:
  /clear

Then in new session:
  /resume_handoff ${filePath}

Or just run /clear - the next session will auto-detect this handoff.
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501`
      }));
      return;
    }
  }
  if (hookType === "SessionStart") {
    const pending = getPendingHandoff();
    if (pending && fs.existsSync(pending.path)) {
      clearPendingHandoff();
      console.log(JSON.stringify({
        result: `

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
\u{1F504} PENDING HANDOFF DETECTED
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

A handoff was created in the previous session:
  ${pending.path}
  Created: ${pending.created_at}

**AUTO-RESUMING**: Run /resume_handoff ${pending.path}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501`
      }));
      return;
    }
  }
  console.log(JSON.stringify({}));
}
main().catch((e) => {
  console.error("Hook error:", e);
  console.log(JSON.stringify({}));
});
