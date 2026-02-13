# PLAN: Fix Every Broken Test Assertion in august-qa

**Context**: Sessions 19, 20, and 27 audited all ~204 tests across 20 files in `august-qa/tests/`.
The core finding: ~40 assertions prove nothing about whether August works. They prove React rendered something. This plan fixes every single one.

**The Principle**: Every assertion must answer "Did the thing the user wanted to happen actually happen?" If August's backend silently broke and returned empty/wrong data but React still rendered a page, would the test catch it? If no, it's a smoke test. If yes, it's a behavioral test.

**Note on session 20 vs 27**: Session 20 launched 4 kraken agents to fix 40 assertions but hit context limit before Ishaan could verify the fixes landed correctly. Session 27 re-audited the full suite and found the same patterns still present. Assume the krakens' fixes either didn't land, were partial, or need to be re-verified. This plan treats the current state as unfixed.

---

## PRIORITY 1: Structural Bugs (tests that pass without asserting anything)

These are the worst. The test reports PASSED having verified literally nothing.

### Bug 1: Silent return in `test_retag_modal_opens`
- **File**: `test_conversation_timeline.py`
- **Line**: ~64
- **Problem**: If the modal isn't detected as `role="dialog"`, the test returns early before any assertion fires. Test reports PASSED.
- **Fix**: Remove the early return. If the modal isn't found, `pytest.fail("Retag modal did not open — no dialog role detected")`. If it IS found, assert it contains the expected retag options (tag names).

### Bug 2: Unreachable assertion in `test_speaker_roles_displayed`
- **File**: `test_conversation_timeline.py`
- **Line**: ~486
- **Problem**: There's a `return` inside the loop body. The final assertion after the loop ("at least one visible role label") can never execute because every iteration either returns or continues.
- **Fix**: Remove the `return` inside the loop. Collect results in a list, then assert after the loop that at least one speaker role label was found AND that each found label is a real name (not "Unknown", not empty).

### Bug 3: Silent return when no edit buttons found
- **File**: `test_conversation_insights.py`
- **Line**: ~86
- **Problem**: If no edit buttons are visible, the test returns without asserting. A user would expect edit buttons to exist — their absence IS a failure.
- **Fix**: Replace `return` with `pytest.fail("No edit buttons found on insights panel — expected at least one editable field")`.

### Bug 4: Silent return in Strategy 3 fallback
- **File**: `test_conversation_insights.py`
- **Line**: ~443
- **Problem**: The test tries 3 strategies to find content. If strategy 3 also fails, it returns silently instead of failing.
- **Fix**: Replace final `return` with `pytest.fail("All 3 strategies failed to find insights content")`.

### Bug 5: Wrong reload verification in `test_meeting_type_saves_value`
- **File**: `test_conversation_insights.py`
- **Line**: ~521
- **Problem**: After `page.reload()`, the test clicks the Insights tab but never verifies the URL still contains the same meeting UUID. Could be reading a different conversation's data and reporting persistence success.
- **Fix**: After reload, assert `meeting_uuid in page.url` before checking the meeting type value. This proves you're still on the same conversation.

---

## PRIORITY 2: The 40 Broken Assertions (4 patterns)

### Pattern 1: `len(body) > N` — "Page not blank = feature works"
27 instances across 13 files. Every one needs to verify SPECIFIC expected content.

#### test_overview_dashboard.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 117 | Team filter works | `len(body) > 20` | After selecting a team member filter, verify that every visible conversation card contains that team member's name. If filtering by "Jamie", assert each card text includes "Jamie". |
| 248 | Clear filters works | `len(body) > 20` | After clearing filters, verify the conversation count returned to the original unfiltered count (capture count before filtering, compare after clear). |
| 322 | Coaching deep dive | `len(body) > 50` | Verify specific coaching section headings exist ("Talk Ratio", "Longest Monologue", "Patience" or similar known labels). Don't just check length. |

#### test_deals.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 111 | Sort changes order | `len(body) > 50` | After sorting by "Last Added", extract dates from the first 3 cards. Assert card1.date >= card2.date >= card3.date. After "Oldest", assert reversed. Verify the sort CONTRACT, not just that content exists. |
| 150 | Card click -> detail | `body grew by 50 chars` | After clicking a deal card, verify the deal's NAME appears in the detail view. Capture the card title before clicking, assert it appears in the expanded/detail body. |
| 260 | Deal detail has content | `len(body) > 150` | Verify known deal detail fields exist: a dollar amount (regex `\$[\d,]+`), a stage name (not numeric), a company name. |
| 272 | Associated entities | `len(body) > 300` | Verify at least one associated contact name and one associated company name appear. These should be real strings, not just "body is long enough". |

#### test_todos.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 135 | Sort works | `len(body) > 10` | After sorting, verify the first todo's creation date or priority is consistent with the sort order. If "Newest first", first item's date > second item's date. |

#### test_contacts.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 106 | Sort works | `len(body) > 50` | Same as deals sort: extract names or dates from first 3 cards, verify ordering matches the selected sort criterion. |
| 130 | Card has data | `len(card_text) > 3` | Verify the card contains a real name (at least two words) and an email or company name. Not just "more than 3 characters". |
| 145 | Card detail works | `body grew by 50` | Capture the contact's name from the card, click it, verify the name appears in the detail view along with at least one detail field (email, phone, company). |

#### test_companies.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 112 | Sort works | `len(body) > 50` | Same pattern: verify sort order matches criterion. |
| 136 | Card has data | `len(card_text) > 3` | Verify company card has a real company name (not empty, not "undefined", not "null"). |
| 156 | Card detail works | `body grew by 50` | Capture company name from card, click, verify name appears in detail plus domain URL or employee count. |

#### test_workflows.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 194 | Deep link loads | `len(body) > 100` | Verify the deep-linked page contains the expected entity/page title. If deep linking to `/conversations/{id}`, verify the conversation's title or summary text appears. |
| 212 | Refresh preserves page | `len(body) > 100` | Capture a unique content string before refresh. After refresh, assert that same string is still present. Proves state survived the reload. |

#### test_conversation_overview.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 424 | Conversation has content | `len(body) > 100` | Verify the overview contains at least one of: summary text, action items list, participant names. Check for specific structural elements, not raw length. |

#### test_conversation_timeline.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 133 | Highlights have text | `len(body) > 200` | Verify highlights contain actual quoted speech (look for quotation marks or speaker names followed by colons). Not just "the section has 200+ characters". |

#### test_hubspot_sync.py (5 instances at lines 75, 94, 137, 176, 220)

| Lines | Test | Current | Fix |
|-------|------|---------|-----|
| 75 | Sync summary | `len(body) > 100` | After syncing, query HubSpot API (or the sync result panel) for the specific summary text that was visible in August. Verify the exact words landed. |
| 94 | Sync action items | `len(body) > 100` | Verify at least one action item text string from August appears in the HubSpot record. |
| 137 | Sync duration | `len(body) > 100` | Verify the duration value (e.g., "32 min") matches what August shows. |
| 176 | Sync participants | `len(body) > 100` | Verify participant names from August appear in HubSpot. |
| 220 | Sync meeting type | `len(body) > 100` | Verify the meeting type label matches. |

**Note**: If HubSpot API access isn't available in the test environment, at minimum verify the sync confirmation UI shows the correct data that was synced — not just that the page has 100+ characters.

---

### Pattern 2: `body_before != body_after` — "React re-rendered = feature works"
6 instances across 3 files.

#### test_overview_dashboard.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 99 | Scope filter | `body_before != body_after` | After selecting "My Conversations" scope, verify every visible card belongs to the logged-in user. After "Team", verify cards from multiple users appear. The filter CONTRACT must be verified, not just "something changed". |
| 163 | Timeframe filter | `body_before != body_after` | After selecting "Last 7 Days", verify all visible conversation dates are within the last 7 days. Parse actual dates, compare to `datetime.now() - timedelta(days=7)`. |
| 200 | Clear filters | `body_before != body_after` | After clearing, verify count matches original unfiltered count AND that previously-filtered-out items are now visible again. |
| 291 | Coaching toggle | `body_before != body_after` | After toggling coaching view, verify coaching-specific metrics appear (talk ratio, filler words, etc.) or disappear. Not just "DOM changed". |

#### test_todos.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 109 | Filter works | `body_before != body_after` | After filtering to "Completed", verify every visible todo has a completed indicator (checkmark, strikethrough, "completed" status). After "Pending", verify none are marked complete. |

#### test_uiux.py

| Line | Test | Current | Fix |
|------|------|---------|-----|
| 101 | Modal escape closes | `body changed` | After pressing Escape, assert the modal overlay is no longer visible (`modal.is_visible() == False`). Don't check body text — check the modal element's visibility state directly. |

---

### Pattern 3: `len(restored) >= len_before * 0.3` — "Losing 70% is fine"
4 instances across 4 files. All are search-clear tests.

**The fix is the same for all 4**: After clearing search, the card/item count must equal the original count (captured before search was entered). Not 30%, not 50% — the EXACT same count (or within 1, to allow for real-time data changes).

| File | Line | Fix |
|------|------|-----|
| `test_deals.py` | 227 | `count_after_clear == count_before_search` (not `>= 0.3 * count_before`) |
| `test_todos.py` | 176 | Same |
| `test_contacts.py` | 215 | Same |
| `test_companies.py` | 232 | Same (was 50% threshold — still wrong) |

---

### Pattern 4: Either/or assertions that always pass
3 instances in `test_conversations_list.py`.

#### test_sort_dropdown
- **Current**: `first_card_changed OR count_stayed_same` — count ALWAYS stays the same, so this always passes
- **Fix**: After sorting by "Last Added", extract timestamps/dates from first 3 conversation cards. Assert chronological descending order. After "Oldest", assert ascending. The sort must be VERIFIED, not just "something happened".

#### test_filters_button
- **Current**: Tries 4 filter options, accepts any body change — React always re-renders
- **Fix**: After applying a specific filter (e.g., "Internal"), verify every visible conversation card matches that filter type. Check for the type badge/label on each card. If filtering by call type, every visible card should show that call type.

#### test_multi_word_search
- **Current**: `results found OR no-results message` — one is always true, so the test always passes
- **Fix**: Search for a known multi-word string that EXISTS in the data (hardcode from ground truth or capture from the first conversation's title). Assert the results contain that conversation. Then search for a nonsense string ("zzz_nonexistent_xyx"). Assert the no-results message appears. Test BOTH paths, don't accept either.

---

## PRIORITY 3: Fake Tests (presence-only, need click + verify)

### test_three_dot_menu (test_conversation_overview.py)
- **Current**: Opens the 3-dot menu, asserts 3 buttons exist. Never clicks any.
- **Fix**: Click each button. Verify the action occurs:
  - "Copy link" -> clipboard contains URL (or toast confirms copy)
  - "Download" -> network request fires for download endpoint
  - "Delete" -> confirmation dialog appears (don't confirm)

### test_conversation_variety (test_conversation_overview.py)
- **Current**: Same template rendered 3 times, doesn't verify different data
- **Fix**: Navigate to 3 different conversations. Capture the title/summary of each. Assert all 3 are DIFFERENT from each other. Proves it's not the same conversation rendered 3 times.

### test_outline_copy_button (test_conversation_overview.py)
- **Current**: Can't distinguish outline content from summary content
- **Fix**: Click the Outline tab. Verify the content contains outline-specific structure (numbered points, section headers, or bullet hierarchy). Then test the copy button: click it, read clipboard, assert clipboard text matches the outline content (not the summary).

---

## PRIORITY 4: Negative-Only Tests (add positive assertions)

These tests only verify the ABSENCE of a bug. They should also verify the PRESENCE of correct behavior.

### test_no_nan_timestamps (test_conversation_overview.py)
- **Current**: `assert "NaN" not in page_text` — if the section is empty, this passes vacuously
- **Fix**: ALSO assert that at least one valid timestamp IS present. Regex for `\d{1,2}:\d{2}` or similar. Proves timestamps exist AND are valid.

### test_no_speaker_unknown (test_conversation_timeline.py)
- **Current**: Asserts "Unknown" not in speaker labels
- **Fix**: ALSO assert that at least 2 distinct speaker names ARE present. A conversation with zero speakers passes the negative check.

### test_no_untitled_deals (test_deals.py)
- **Current**: Asserts "Untitled" not in any deal card
- **Fix**: ALSO assert every deal card has a title with at least 2 words (real deal names aren't single characters).

### test_no_numeric_stages (test_deals.py)
- **Current**: Asserts stage values aren't raw numbers (HubSpot IDs)
- **Fix**: ALSO assert each stage is a known valid stage name from the pipeline (e.g., "Appointment Scheduled", "Qualified to Buy", "Decision Maker Bought-In", etc.). Maintain a list of valid stages.

---

## PRIORITY 5: Systemic Issues

### The Ask August sidebar fragility
- **conftest.py** has a 50+ line `force_hide_ask_august()` JS hack
- The sidebar can reopen between test interactions, covering buttons
- **Fix**: Call `force_hide_ask_august()` in a `@pytest.fixture(autouse=True)` that runs before EVERY test, not just when sort dropdowns need it. Make it defensive — if the sidebar doesn't exist, no-op.

### The xfail escape hatch (5 tests)
- Tests marked `@pytest.mark.xfail` count as "passed" in CI even when the feature is broken
- **Fix**: For each xfail test, determine:
  - Is the underlying August bug filed? Add the ticket number as `reason=`
  - Is it a test infrastructure problem? Fix the test.
  - Is it a real but low-priority bug? Change to `@pytest.mark.skip(reason="AUGUST-XXX: description")` so it doesn't inflate pass count
- **Files affected**: `test_deals.py` (3 xfail), `test_conversation_timeline.py` (2 xfail)

### The "button disappeared = success" antipattern (3 Load More tests)
- **Current**: `assert cards_after > cards_before or load_more_gone` — if JS crashes and removes the button, test passes
- **Fix**: Only accept `cards_after > cards_before`. The Load More button disappearing is not proof of success — more cards appearing IS proof.
- **Files**: `test_deals.py`, `test_contacts.py`, `test_companies.py`

### Mark Important -> Todo (the stickiest feature)
- **Current**: Goes to `/todos` and checks `len(body.strip()) > 20`
- **Fix**: After marking a conversation as important, navigate to `/todos`. Search or scan for the SPECIFIC conversation title or action item text that was just marked. Assert that exact string appears in the Pending tab. Proves the data flowed from conversations to todos.

---

## PRIORITY 6: Cross-System Data Integrity (the crown jewels)

No test currently starts in August and ends in HubSpot with verified data.

### Needed test: Full sync verification flow
1. Open a conversation in August
2. Capture: summary text, first action item, duration, participant names
3. Click "Sync to HubSpot"
4. Wait for sync confirmation
5. Query HubSpot API for that meeting record
6. Assert: summary matches, action items match, duration matches, participants match

**Prerequisite**: One-time Google SSO login for HubSpot tests (currently blocking the 2 FULL sync tests that already exist in `test_hubspot_sync.py`).

---

## Execution Order

If someone has 1 hour:
1. Fix the 5 structural bugs (P1) — 15 min total, 2-line edits each
2. Fix the 4 search-clear thresholds (P3 of assertions) — 10 min
3. Fix the 3 either/or assertions (P4 of assertions) — 15 min
4. Fix the 4 negative-only tests (P4 priorities) — 10 min

If someone has 3 hours:
- All of the above PLUS
- Fix all 27 `len(body) > N` assertions (P1 of assertions) — 90 min
- Fix all 6 `body_before != body_after` assertions (P2 of assertions) — 30 min

If someone has a full day:
- All of the above PLUS
- Upgrade 3 fake tests to functional (P3 priorities) — 60 min
- Fix systemic issues: sidebar autouse, xfail audit, Load More antipattern — 60 min
- Mark Important -> Todo full flow — 30 min
- HubSpot cross-system test (if SSO is set up) — 60 min

---

## How to Verify Fixes Are Real

After fixing each assertion, ask: "If I replaced August's API response with `{'data': []}` (empty), would this test fail?" If the answer is no, the fix isn't behavioral enough. Every fixed test should fail when August returns wrong/empty data, and pass only when the correct data is present.

---

## Current Suite Numbers (from session 27 audit)

| Metric | Count |
|--------|-------|
| Total tests | ~204 |
| Genuinely functional | ~98 (68%) |
| Weak (presence-only) | ~34 (24%) |
| Fake (inflate coverage) | ~3 (2%) |
| Structural bugs (silent pass) | 5 |
| xfail (pass vacuously) | 5 |

**Target after this plan**: 190+ genuinely functional (93%+), 0 structural bugs, 0 fake tests.

---

## Files to Edit (complete list)

1. `august-qa/tests/test_conversation_timeline.py` — 2 structural bugs + 1 len assertion + 1 negative-only
2. `august-qa/tests/test_conversation_insights.py` — 3 structural bugs
3. `august-qa/tests/test_overview_dashboard.py` — 3 len assertions + 4 body_before/after + 1 negative-only
4. `august-qa/tests/test_deals.py` — 4 len assertions + 1 search-clear + 2 negative-only + 1 Load More + 3 xfail audit
5. `august-qa/tests/test_contacts.py` — 3 len assertions + 1 search-clear + 1 Load More
6. `august-qa/tests/test_companies.py` — 3 len assertions + 1 search-clear + 1 Load More
7. `august-qa/tests/test_todos.py` — 1 len assertion + 1 body_before/after + 1 search-clear
8. `august-qa/tests/test_workflows.py` — 2 len assertions
9. `august-qa/tests/test_conversations_list.py` — 3 either/or assertions
10. `august-qa/tests/test_hubspot_sync.py` — 5 len assertions (the money tests)
11. `august-qa/tests/test_conversation_overview.py` — 1 len assertion + 3 fake tests + 1 negative-only
12. `august-qa/tests/test_uiux.py` — 1 body_before/after
13. `august-qa/tests/conftest.py` — sidebar autouse fixture
14. `august-qa/tests/test_conversation_timeline.py` — 2 xfail audit (same file as #1)

**Total: 14 files, ~55 individual edits**
