/**
 * PostToolUse Hook - Updates session heartbeat in PostgreSQL.
 *
 * Runs after every tool use to keep the session alive in the
 * coordination layer. Without this, sessions go stale after 5 minutes
 * and become invisible to other terminals.
 */

import { readFileSync } from 'fs';
import { getSessionId, getProject } from './shared/session-id.js';
import { runPgQuery } from './shared/db-utils-pg.js';

function main(): void {
  // Read stdin (required by hook protocol) but we don't need the content
  try {
    readFileSync(0, 'utf-8');
  } catch {
    // ignore
  }

  const sessionId = getSessionId();
  const project = getProject();

  // Update heartbeat - single fast query
  const pythonCode = `
import asyncpg
import os

session_id = sys.argv[1]
project = sys.argv[2]
pg_url = os.environ.get('CONTINUOUS_CLAUDE_DB_URL') or os.environ.get('DATABASE_URL', 'postgresql://claude:claude_dev@localhost:5432/continuous_claude')

async def main():
    conn = await asyncpg.connect(pg_url)
    try:
        result = await conn.execute('''
            UPDATE sessions SET last_heartbeat = NOW()
            WHERE id = $1 AND project = $2
        ''', session_id, project)
        # If no row updated (session not registered yet), insert it
        if result == 'UPDATE 0':
            await conn.execute('''
                INSERT INTO sessions (id, project, working_on, started_at, last_heartbeat)
                VALUES ($1, $2, '', NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET last_heartbeat = NOW()
            ''', session_id, project)
        print('ok')
    finally:
        await conn.close()

asyncio.run(main())
`;

  runPgQuery(pythonCode, [sessionId, project]);

  // Always continue - heartbeat should never block
  console.log(JSON.stringify({ result: 'continue' }));
}

main();
