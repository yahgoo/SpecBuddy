# Implementation Tasks: P0-2 Agent Handoff Pack Export

Feature: Export a single Markdown handoff document containing certified spec
text, EARS acceptance criteria, unresolved questions, and an implementation
task list.

Certified inputs:
- `.kiro/specs/handoff-export-backend/requirements.md` (100/100)
- `.kiro/specs/handoff-export-frontend/requirements.md` (100/100)

---

## Task 1: Add `HandoffExportRequest` and `HandoffExportResponse` models to `backend/routes.py`

**File:** `backend/routes.py`

**What:** Add two new Pydantic models after the existing `SelectClarifyOptionRequest`
class:
- `HandoffExportRequest` — empty model (accepts empty JSON body, ignores extra
  fields via `model_config = ConfigDict(extra="ignore")`).
- `HandoffExportResponse` — fields: `spec_id: int`, `filename: str`,
  `score: int`, `verdict: str`, `exported_at: str`, `markdown_document: str`.

**Constraints:**
- Do NOT modify `ClarifyOptionsRequest` or `SelectClarifyOptionRequest`.
- Model names exactly as specified (NFR-2).

**Requirement IDs:** BE FR-5, BE NFR-2

**Verification:**
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 2: Add `build_handoff_export` adapter function to `backend/linter_adapter.py`

**File:** `backend/linter_adapter.py`

**What:** Add a new public function `build_handoff_export(conn, spec_id)` that:
1. Reads the spec via `get_spec(conn, spec_id)`. Raises `KeyError` if not found.
2. Reads rewrites via `get_rewrites(conn, spec_id)`.
3. Reconstructs effective text via `_reconstruct_effective_text`.
4. Runs `_run_pipeline` on the effective text to get records, findings, evaluation.
5. Assembles a Markdown document string with four sections:
   - **Certified Spec** — the full effective text (FR-1).
   - **Acceptance Criteria** — each requirement's `statement` grouped by
     `section`, formatted as EARS criteria (FR-2).
   - **Unresolved Questions** — findings with severity `"defect"` or
     `"clarification"` where no rewrite exists for that line (FR-3).
   - **Implementation Tasks** — one task per requirement ordered by line
     number (FR-4).
6. Includes a metadata header (filename, timestamp, score, verdict, tier) (FR-5).
7. Returns a dict with keys: `spec_id`, `filename`, `score`, `verdict`,
   `exported_at`, `markdown_document`.

**Constraints:**
- Read-only: no database writes (FR-7).
- No AI/LLM/network calls (FR-7).
- No new storage tables (NFR-4).
- Do NOT modify `_clarify_option_a`, `_clarify_option_b`, `get_clarify_options`,
  or `select_clarify_option`.
- Uses only existing imports + `datetime` from stdlib.

**Requirement IDs:** BE FR-1, BE FR-2, BE FR-3, BE FR-4, BE FR-5, BE FR-6,
BE FR-7, BE NFR-1, BE NFR-4, BE NFR-5, BE NFR-7

**Verification:**
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 3: Add the `/specs/{spec_id}/handoff-export` route to `backend/routes.py`

**File:** `backend/routes.py`

**What:** Add a new route function after the existing clarify routes:
```python
@router.post("/specs/{spec_id}/handoff-export")
def export_handoff_pack(spec_id: int, body: HandoffExportRequest, request: Request):
```
The handler:
1. Opens a DB connection via `_get_conn(request)`.
2. Calls `build_handoff_export(conn, spec_id)` from `linter_adapter`.
3. Returns the result dict (FastAPI serializes to JSON matching
   `HandoffExportResponse`).
4. Raises `HTTPException(404)` on `KeyError`.
5. Closes connection in `finally`.

**Constraints:**
- Import `build_handoff_export` from `backend.linter_adapter`.
- Do NOT modify any existing route functions.
- Route path within the `/api` prefix router: `/specs/{spec_id}/handoff-export`.

**Requirement IDs:** BE NFR-3, BE FR-6, BE Unwanted Behavior (404 for missing
spec, refused specs still export, extra fields ignored, zero-requirement specs
return valid doc)

**Verification:**
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 4: Add backend unit tests for handoff export

**File:** `tests_backend/test_handoff_export.py` (new file)

**What:** Add a new test module covering:
1. **Happy path** — create spec with requirements, export, assert 200, assert
   all four sections present in `markdown_document`.
2. **With rewrites** — apply a rewrite, export, assert certified spec reflects
   the rewrite.
3. **Unresolved findings** — create spec with ambiguous lines, export, assert
   unresolved questions section lists findings with line number, check_id,
   severity, message.
4. **All resolved** — apply rewrites for all findings, export, assert unresolved
   section contains "no open questions" note.
5. **Zero requirements** — create spec with no parseable requirements, export,
   assert empty sections with appropriate notes.
6. **Missing spec 404** — request export for non-existent spec_id, assert 404.
7. **Refused verdict still exports** — create spec that gets "refused" verdict,
   export, assert 200 with unresolved findings listed.
8. **Metadata fields** — assert response contains spec_id, filename, score,
   verdict, exported_at.
9. **Response latency** — assert response completes within 200ms for a spec
   under 200 lines.

Use the same test patterns as `tests_backend/test_routes.py` (TestClient from
FastAPI, in-memory SQLite).

**Requirement IDs:** BE FR-1, BE FR-2, BE FR-3, BE FR-4, BE FR-5, BE FR-6,
BE FR-7, BE NFR-6, BE Acceptance Criteria (all), BE Unwanted Behavior (all)

**Verification:**
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 5: Add `HandoffExportResponse` interface to `frontend/src/types.ts`

**File:** `frontend/src/types.ts`

**What:** Add a new exported interface at the end of the file:
```typescript
export interface HandoffExportResponse {
  spec_id: number;
  filename: string;
  score: number;
  verdict: string;
  exported_at: string;
  markdown_document: string;
}
```

**Constraints:**
- Do NOT modify `ClarifyOption`, `ClarifyOptionsResponse`, or any other
  existing interface.
- Use snake_case field names matching server JSON contract (NFR-4).

**Requirement IDs:** FE FR-8, FE NFR-2

**Verification:**
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 6: Add `exportHandoffPack` function to `frontend/src/api.ts`

**File:** `frontend/src/api.ts`

**What:** Add a new async function after the existing exports:
```typescript
export async function exportHandoffPack(
  specId: number,
): Promise<HandoffExportResponse> {
  const response = await fetch(
    `${API_BASE}/api/specs/${specId}/handoff-export`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    },
  );

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Export failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  return response.json() as Promise<HandoffExportResponse>;
}
```

**Constraints:**
- Import `HandoffExportResponse` from `./types`.
- Do NOT modify `fetchClarifyOptions`, `selectClarifyOption`, or
  `ConflictError`.
- Follow existing function style (NFR-4).
- No new dependencies (NFR-1).

**Requirement IDs:** FE FR-2, FE NFR-1, FE NFR-2, FE NFR-4

**Verification:**
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 7: Add "Export Handoff Pack" button with loading, disabled, and error states to `frontend/src/App.tsx`

**File:** `frontend/src/App.tsx`

**What:** Add a functional export button component/section that:
1. **Visibility:** Only renders when `analysisResult` is non-null (FR-1).
2. **Placement:** Alongside other post-analysis action buttons (FR-1).
3. **On click:** Calls `exportHandoffPack(analysisResult.spec_id)` (FR-2).
4. **Loading state:** Sets `aria-busy="true"`, shows a loading indicator text
   (e.g., "Exporting…"), disables the button (FR-4, NFR-3).
5. **Busy guard integration:** Disables when `isBusy` is true (rewrites or
   clarify in progress) (FR-5). Sets shared busy state while export is in
   flight so rewrite/clarify/reset buttons are also disabled (FR-5).
6. **On success:** Triggers browser download via Blob + Object URL + anchor
   click pattern (FR-3). Uses `response.filename` or derives
   `{specFilename}-handoff.md` as fallback. Revokes Object URL after download
   (NFR-5). Stays on current page (FR-3).
7. **On error:** Displays inline error message with `aria-live="polite"`
   (FR-6, NFR-3). Shows "spec not found" for 404, "export failed due to
   network error" for network errors (FR-6). Clears error on next successful
   export or new analysis (FR-6).
8. **Accessibility:** Native `disabled` attribute when disabled (NFR-3).

**Constraints:**
- Do NOT modify the Clarify button, A/B chooser panel, or any clarify-related
  state logic.
- Use React hooks, functional component pattern (NFR-4).
- No new npm packages (NFR-1).
- Use browser-native Blob, URL.createObjectURL, URL.revokeObjectURL (NFR-1).

**Requirement IDs:** FE FR-1, FE FR-2, FE FR-3, FE FR-4, FE FR-5, FE FR-6,
FE FR-7, FE NFR-1, FE NFR-2, FE NFR-3, FE NFR-4, FE NFR-5, FE Unwanted
Behavior (all)

**Verification:**
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 8: Add CSS styles for the export button states

**File:** `frontend/src/styles.css`

**What:** Add styles for:
- `.export-btn` — consistent with existing action button styling.
- `.export-btn:disabled` — grayed out appearance.
- `.export-btn[aria-busy="true"]` — loading indicator styling.
- `.export-error` — inline error message styling (consistent with existing
  error patterns).

**Constraints:**
- Do NOT modify existing clarify-related styles.
- Match existing design patterns in the file.

**Requirement IDs:** FE FR-1, FE FR-4, FE FR-6, FE NFR-4

**Verification:**
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 9: End-to-end verification — exported Markdown contains all four required sections

**What:** Manual or scripted verification that exercises the full path:
1. Start the backend (`python3 -m uvicorn backend.main:create_app --factory
   --host 127.0.0.1 --port 8000`).
2. POST a spec with requirements to `/api/specs`.
3. POST to `/api/specs/{id}/handoff-export`.
4. Assert the `markdown_document` field in the JSON response contains:
   - A `## Certified Spec` section (or `# Certified Spec`) with the effective
     spec text.
   - A `## Acceptance Criteria` section with EARS-formatted criteria.
   - A `## Unresolved Questions` section.
   - A `## Implementation Tasks` section with line-referenced tasks.
5. Assert metadata header includes filename, score, verdict, timestamp.

**File:** `tests_backend/test_handoff_export.py` (extend the happy-path test
from Task 4 to explicitly validate all four section headers and content
structure).

**Requirement IDs:** BE FR-5, BE NFR-5, FE FR-3, FE FR-7

**Verification:**
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Requirement-to-Task Traceability Checklist

| Requirement ID | Task(s) | Covered |
|----------------|---------|---------|
| **Backend** | | |
| BE FR-1 (Certified Spec Text) | 2, 4, 9 | ✓ |
| BE FR-2 (EARS Acceptance Criteria) | 2, 4, 9 | ✓ |
| BE FR-3 (Unresolved Questions) | 2, 4, 9 | ✓ |
| BE FR-4 (Implementation Task List) | 2, 4, 9 | ✓ |
| BE FR-5 (Assemble Single Markdown) | 1, 2, 4, 9 | ✓ |
| BE FR-6 (Happy-Path Export) | 3, 4 | ✓ |
| BE FR-7 (Read-Only Operation) | 2, 4 | ✓ |
| BE NFR-1 (No Clarify Modification) | 2, 3 | ✓ |
| BE NFR-2 (Model Naming) | 1 | ✓ |
| BE NFR-3 (Route Convention) | 3 | ✓ |
| BE NFR-4 (No New Storage Tables) | 2 | ✓ |
| BE NFR-5 (Output Portability) | 2, 9 | ✓ |
| BE NFR-6 (Response Latency) | 4 | ✓ |
| BE NFR-7 (No New Dependencies) | 2 | ✓ |
| BE Unwanted Behavior (refused specs) | 3, 4 | ✓ |
| BE Unwanted Behavior (extra fields) | 1, 4 | ✓ |
| BE Unwanted Behavior (zero reqs) | 2, 4 | ✓ |
| BE Unwanted Behavior (404 missing) | 3, 4 | ✓ |
| **Frontend** | | |
| FE FR-1 (Button Placement/Visibility) | 7, 8 | ✓ |
| FE FR-2 (Trigger Export on Click) | 6, 7 | ✓ |
| FE FR-3 (Browser Download) | 7, 9 | ✓ |
| FE FR-4 (Loading State) | 7, 8 | ✓ |
| FE FR-5 (Disabled While Busy) | 7 | ✓ |
| FE FR-6 (Error State) | 7, 8 | ✓ |
| FE FR-7 (Happy-Path Flow) | 7, 9 | ✓ |
| FE FR-8 (TypeScript Types) | 5 | ✓ |
| FE NFR-1 (No New Dependencies) | 6, 7 | ✓ |
| FE NFR-2 (No Clarify Modifications) | 5, 6, 7 | ✓ |
| FE NFR-3 (Accessibility) | 7 | ✓ |
| FE NFR-4 (Consistent Code Style) | 5, 6, 7 | ✓ |
| FE NFR-5 (Object URL Cleanup) | 7 | ✓ |
| FE Unwanted Behavior (double-click) | 7 | ✓ |
| FE Unwanted Behavior (empty doc) | 7 | ✓ |
| FE Unwanted Behavior (pending state) | 7 | ✓ |
| FE Unwanted Behavior (download fail) | 7 | ✓ |

---

## Execution Order Summary

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8 → Task 9
 (models)  (logic)  (route)  (tests)  (types)   (api)    (UI)    (CSS)    (E2E)
```

Tasks 5–8 (frontend) are independent of each other after Task 4 passes, but
are ordered for logical build dependency (types → api → component → styles).
