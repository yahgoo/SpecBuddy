# Tasks: Clarification Loop

Implements the A/B clarification loop across backend and frontend, derived from:
- `.kiro/specs/clarification-loop-backend/requirements.md`
- `.kiro/specs/clarification-loop-frontend/requirements.md`

---

## Task 1: Deterministic option generator module

**Implements:** Backend FR-1, FR-2

Create `backend/clarify.py` containing the pure deterministic logic that, given
a finding record and the current effective line text, produces two rewrite
options (A and B).

- When the finding has a non-empty `suggested_rewrite`, derive Option A from it.
- Generate Option B as a structurally different rewrite resolving the same check.
- When `suggested_rewrite` and `message` are both empty, derive two generic
  rewrites from the check-identifier category.
- Each option is a dict with `label` ("A"/"B"), `rewritten_text` (single line,
  no newline chars), and `rationale`.
- The function is pure: same inputs → byte-identical output. No network or
  non-deterministic calls.

**Files:** `backend/clarify.py`

**Tests:** `tests_backend/test_clarify.py` — verify determinism, single-line
constraint, A≠B structure, empty-suggestion fallback.

---

## Task 2: Clarification API endpoint — generate options

**Implements:** Backend FR-1, NFR-2, NFR-5

Add `POST /api/specs/{spec_id}/clarify` to `backend/routes.py`.

- Request body: `{ "line_number": int, "check_id": str }`
- Validate spec exists (404), finding exists for line+check_id (404).
- Compute effective line text from raw_text + committed rewrites.
- Call the generator from Task 1.
- Response: `{ "spec_id", "line_number", "check_id", "effective_line", "options": [optA, optB] }`
- Idempotent: repeated calls with same state return byte-identical JSON.
- Latency ≤ 100 ms for specs < 200 lines.

**Files:** `backend/routes.py`, request/response models inline or in a models
module.

**Tests:** `tests_backend/test_clarify_route.py` — happy path, 404 missing
spec, 404 missing finding, idempotent repeat call.

---

## Task 3: Selection API endpoint — persist and rescore

**Implements:** Backend FR-3, FR-4, NFR-3

Add `POST /api/specs/{spec_id}/clarify/select` to `backend/routes.py`.

- Request body: `{ "line_number": int, "check_id": str, "selected": "A" | "B" }`
- Validate selected value is "A" or "B" (422).
- Validate spec and finding exist (404).
- Regenerate options deterministically; compare effective line text to detect
  stale state (409 conflict if changed).
- Persist the selected rewrite as an overlay and rerun the full linter pipeline
  in a single SQLite transaction (rollback on any failure).
- Return the full `AnalysisResponse` (score, verdict, tier, findings,
  requirements, rewrites, report_markdown).

**Files:** `backend/routes.py`, `backend/linter_adapter.py` (if transaction
helper needed), `backend/clarify.py` (reuse generator).

**Tests:** `tests_backend/test_clarify_select.py` — happy path rescore, 422
invalid selection, 404 missing spec/finding, 409 conflict on stale line,
transaction rollback on simulated failure.

---

## Task 4: Frontend TypeScript types and service functions

**Implements:** Frontend NFR-1, NFR-2

Add clarification types and API functions to the frontend service layer.

- Define `ClarifyOption` type: `{ label: "A" | "B"; rewritten_text: string; rationale: string }`.
- Define `ClarifyResponse` type: `{ spec_id: number; line_number: number; check_id: string; effective_line: string; options: [ClarifyOption, ClarifyOption] }`.
- `fetchClarifyOptions(specId, lineNumber, checkId): Promise<ClarifyResponse>` —
  calls `POST /api/specs/{specId}/clarify`.
- `selectClarifyOption(specId, lineNumber, checkId, selected): Promise<AnalysisResponse>` —
  calls `POST /api/specs/{specId}/clarify/select`.
- Both throw with detail text on non-success status.

**Files:** `frontend/src/types.ts`, `frontend/src/api.ts`

---

## Task 5: Clarify button and A/B chooser panel in App.tsx

**Implements:** Frontend FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, NFR-3, NFR-4, NFR-5, NFR-6

**OWNER: CodeBuddy — hackathon eligibility evidence**

Wire the Clarify button onto each finding card and implement the inline A/B
options panel in `frontend/src/App.tsx`.

- Render a "Clarify" button on every finding card (alongside existing
  Apply-fix when a suggested rewrite exists; sole action otherwise).
- On click: call `fetchClarifyOptions`, show "Loading…", disable all action
  buttons globally (shared busy guard combining clarify + rewrite loading).
- On success: expand inline options panel showing effective line, two option
  cards (label badge, monospace rewritten text, rationale helper text), "Select
  A", "Select B", and "Cancel" buttons.
- On "Select A/B": call `selectClarifyOption`, show "Applying…", disable panel
  buttons, keep all UI unchanged until response.
- On success response: replace entire analysis state in a single setState
  (score card, stats row, mission board, findings list, accepted rewrites,
  parsed requirements, report — one render cycle, no intermediate states).
- On 409 conflict: display "Line has changed — please re-clarify." inline,
  collapse panel.
- On other error: display inline error, collapse panel, restore buttons.
- On "Cancel": collapse panel, no request sent.
- Accessibility: focus panel on open, return focus to Clarify button on close,
  Tab-navigable between Select A / Select B / Cancel, accessible labels.
- Reuse existing button/badge/code-block styles; new class names for panel
  layout only.
- No new npm dependencies.

**Files:** `frontend/src/App.tsx`, `frontend/src/styles.css` (panel layout
classes only)

---

## Task 6: End-to-end integration verification

**Implements:** All acceptance criteria from both specs

Run the full-stack flow and verify:

- `POST /api/specs` → create spec with findings.
- `POST /api/specs/{id}/clarify` → returns two options A/B, idempotent.
- `POST /api/specs/{id}/clarify/select` with "A" → returns rescored analysis.
- Repeat clarify on same finding after rewrite → 409 conflict.
- Frontend: Clarify → options panel → select → single-state refresh with
  updated score/verdict/findings.
- Backend unit tests pass: `python3 -m unittest discover -s tests_backend`.
- Frontend builds: `cd frontend && npm run build`.

**Files:** No new files; run existing test suites + manual verification.
