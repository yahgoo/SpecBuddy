# Traceability Report: P0-2 Agent Handoff Pack Export

Generated: 2026-08-12

## Sources

| Artifact | Path |
|----------|------|
| Backend Requirements | `.kiro/specs/handoff-export-backend/requirements.md` |
| Frontend Requirements | `.kiro/specs/handoff-export-frontend/requirements.md` |
| Task List | `.kiro/specs/handoff-export/tasks.md` |
| Backend Route | `backend/routes.py` |
| Backend Adapter | `backend/linter_adapter.py` |
| Backend Tests | `tests_backend/test_handoff_export.py` |
| Frontend Types | `frontend/src/types.ts` |
| Frontend API | `frontend/src/api.ts` |
| Frontend UI | `frontend/src/App.tsx` |
| Frontend Styles | `frontend/src/styles.css` |

---

## Backend Requirements Traceability

| Requirement ID | Task(s) | Implementation File(s) | Test Coverage | Status |
|----------------|---------|------------------------|---------------|--------|
| BE FR-1 (Certified Spec Text) | 2, 4, 9 | `backend/linter_adapter.py` (`build_handoff_export`: effective text via `_reconstruct_effective_text`, "## Certified Spec" section) | `test_handoff_export.py::HandoffExportWithRewritesTests::test_certified_spec_reflects_rewrite`, `HandoffExportEndToEndTests::test_e2e_all_sections_with_content` | ✅ TRACED |
| BE FR-2 (EARS Acceptance Criteria) | 2, 4, 9 | `backend/linter_adapter.py` (`build_handoff_export`: "## Acceptance Criteria" section, groups by `r.section`, outputs `r.statement`) | `test_handoff_export.py::HandoffExportEndToEndTests::test_e2e_all_sections_with_content` (asserts criteria section non-empty) | ✅ TRACED |
| BE FR-3 (Unresolved Questions) | 2, 4, 9 | `backend/linter_adapter.py` (`build_handoff_export`: "## Unresolved Questions" section, filters by severity `defect`/`clarification` with no rewrite on that line) | `test_handoff_export.py::HandoffExportUnresolvedTests::test_unresolved_findings_listed`, `test_all_resolved_shows_no_open_questions` | ✅ TRACED |
| BE FR-4 (Implementation Task List) | 2, 4, 9 | `backend/linter_adapter.py` (`build_handoff_export`: "## Implementation Tasks" section, sorted by `line_number`, format `[Line N] statement`) | `test_handoff_export.py::HandoffExportEndToEndTests::test_e2e_all_sections_with_content` (asserts `[Line` present in tasks section) | ✅ TRACED |
| BE FR-5 (Assemble Single Markdown) | 1, 2, 4, 9 | `backend/linter_adapter.py` (`build_handoff_export`: assembles four sections + metadata header), `backend/routes.py` (`HandoffExportResponse` model) | `test_handoff_export.py::HandoffExportHappyPathTests::test_export_clean_spec_returns_200_with_all_sections`, `test_export_metadata_in_markdown_header` | ✅ TRACED |
| BE FR-6 (Happy-Path Export) | 3, 4 | `backend/routes.py` (`export_handoff_pack` route handler returns result dict), `backend/linter_adapter.py` (full document assembly) | `test_handoff_export.py::HandoffExportHappyPathTests::test_export_clean_spec_returns_200_with_all_sections` | ✅ TRACED |
| BE FR-7 (Read-Only Operation) | 2, 4 | `backend/linter_adapter.py` (`build_handoff_export`: no `conn.commit()`, no writes, no AI/network calls) | `test_handoff_export.py` (implicitly verified — no DB state changes observed across tests) | ✅ TRACED |
| BE NFR-1 (No Clarify Modification) | 2, 3 | `backend/linter_adapter.py` (clarify functions untouched), `backend/routes.py` (clarify routes untouched) | N/A (structural constraint — verified by code inspection) | ✅ TRACED |
| BE NFR-2 (Model Naming) | 1 | `backend/routes.py` (`HandoffExportRequest`, `HandoffExportResponse` — exact names as specified) | N/A (structural constraint) | ✅ TRACED |
| BE NFR-3 (Route Convention) | 3 | `backend/routes.py` (`@router.post("/specs/{spec_id}/handoff-export")` within `/api` prefix) | `test_handoff_export.py` (all tests call `/api/specs/{id}/handoff-export`) | ✅ TRACED |
| BE NFR-4 (No New Storage Tables) | 2 | `backend/linter_adapter.py` (`build_handoff_export` reads only from existing tables via `get_spec`, `get_rewrites`) | N/A (structural constraint) | ✅ TRACED |
| BE NFR-5 (Output Portability) | 2, 9 | `backend/linter_adapter.py` (output uses only standard Markdown: `#`, `##`, `###`, `-`, numbered lists, `**bold**`) | `test_handoff_export.py::HandoffExportEndToEndTests::test_e2e_all_sections_with_content` | ✅ TRACED |
| BE NFR-6 (Response Latency) | 4 | N/A (runtime behavior) | `test_handoff_export.py::HandoffExportLatencyTests::test_response_within_200ms` | ✅ TRACED |
| BE NFR-7 (No New Dependencies) | 2 | `backend/linter_adapter.py` (uses only `datetime` from stdlib + existing project imports) | N/A (structural constraint) | ✅ TRACED |
| BE Unwanted: Refused specs still export | 3, 4 | `backend/routes.py` (no verdict check — handler exports regardless of verdict) | `test_handoff_export.py::HandoffExportRefusedVerdictTests::test_refused_spec_exports_with_unresolved_findings` | ✅ TRACED |
| BE Unwanted: Extra fields ignored | 1, 4 | `backend/routes.py` (`HandoffExportRequest` has `model_config = ConfigDict(extra="ignore")`) | `test_handoff_export.py::HandoffExportEndToEndTests::test_e2e_extra_fields_ignored` | ✅ TRACED |
| BE Unwanted: Zero reqs valid doc | 2, 4 | `backend/linter_adapter.py` (empty notes when `records` is falsy) | `test_handoff_export.py::HandoffExportZeroRequirementsTests::test_zero_requirements_export` | ✅ TRACED |
| BE Unwanted: 404 missing spec | 3, 4 | `backend/routes.py` (`except KeyError: raise HTTPException(status_code=404)`) | `test_handoff_export.py::HandoffExportMissingSpecTests::test_missing_spec_returns_404` | ✅ TRACED |
| BE Acceptance Criteria (all) | 4 | Covered by implementation files above | `test_handoff_export.py` (full test suite covers all acceptance criteria) | ✅ TRACED |

---

## Frontend Requirements Traceability

| Requirement ID | Task(s) | Implementation File(s) | Test Coverage | Status |
|----------------|---------|------------------------|---------------|--------|
| FE FR-1 (Button Placement/Visibility) | 7, 8 | `frontend/src/App.tsx` (button inside `{result && (...)}` block, `.export-section` div), `frontend/src/styles.css` (`.export-section`, `.export-btn`) | N/A (no frontend unit tests for this feature) | ✅ TRACED |
| FE FR-2 (Trigger Export on Click) | 6, 7 | `frontend/src/api.ts` (`exportHandoffPack`: POST to `/api/specs/${specId}/handoff-export`, Content-Type `application/json`, empty `{}` body), `frontend/src/App.tsx` (`handleExportHandoff` calls `exportHandoffPack(result.spec_id)`) | N/A (no frontend unit tests) | ✅ TRACED |
| FE FR-3 (Browser Download on Success) | 7, 9 | `frontend/src/App.tsx` (`handleExportHandoff`: creates Blob with `text/markdown`, `URL.createObjectURL`, anchor click, derives filename with `-handoff.md` suffix) | N/A (no frontend unit tests) | ✅ TRACED |
| FE FR-4 (Loading State) | 7, 8 | `frontend/src/App.tsx` (`exportLoading` state, `aria-busy={exportLoading}`, shows "Exporting…", button `disabled={isBusy}`), `frontend/src/styles.css` (`.export-btn[aria-busy="true"]`, `.export-btn:disabled`) | N/A (no frontend unit tests) | ✅ TRACED |
| FE FR-5 (Disabled While Busy) | 7 | `frontend/src/App.tsx` (`isBusy` guard includes `rewriteLoading`, `clarifyPanel?.status`, `exportLoading`; button `disabled={isBusy}`; export sets `exportLoading` which feeds `isBusy` disabling other buttons) | N/A (no frontend unit tests) | ✅ TRACED |
| FE FR-6 (Error State) | 7, 8 | `frontend/src/App.tsx` (`exportError` state, inline `<p className="export-error" aria-live="polite">`, 404 → "spec not found", other → error message, cleared on `setExportError(null)` at start of each attempt and on new analysis), `frontend/src/styles.css` (`.export-error`) | N/A (no frontend unit tests) | ✅ TRACED |
| FE FR-7 (Happy-Path Flow) | 7, 9 | `frontend/src/App.tsx` (full `handleExportHandoff` flow: call API → Blob → download → restore button via `finally`) | N/A (no frontend unit tests) | ✅ TRACED |
| FE FR-8 (TypeScript Types) | 5 | `frontend/src/types.ts` (`HandoffExportResponse` interface with `spec_id: number`, `filename: string`, `score: number`, `verdict: string`, `exported_at: string`, `markdown_document: string`) | N/A (verified by `npm run build` type-checking) | ✅ TRACED |
| FE NFR-1 (No New Dependencies) | 6, 7 | `frontend/src/api.ts` (uses `fetch`), `frontend/src/App.tsx` (uses `Blob`, `URL.createObjectURL`, DOM anchor) | N/A (structural constraint) | ✅ TRACED |
| FE NFR-2 (No Clarify Modifications) | 5, 6, 7 | `frontend/src/types.ts` (`ClarifyOption`, `ClarifyOptionsResponse` unchanged), `frontend/src/api.ts` (`fetchClarifyOptions`, `selectClarifyOption`, `ConflictError` unchanged), `frontend/src/App.tsx` (clarify panel state/logic/markup unchanged) | N/A (structural constraint) | ✅ TRACED |
| FE NFR-3 (Accessibility) | 7 | `frontend/src/App.tsx` (native `disabled` attr, `aria-busy={exportLoading}`, `aria-live="polite"` + `role="alert"` on error) | N/A (no frontend unit tests) | ✅ TRACED |
| FE NFR-4 (Consistent Code Style) | 5, 6, 7 | `frontend/src/types.ts` (snake_case fields matching server), `frontend/src/api.ts` (async function, fetch, throw on non-OK, typed return), `frontend/src/App.tsx` (functional component, hooks, inline state) | N/A (structural constraint) | ✅ TRACED |
| FE NFR-5 (Object URL Cleanup) | 7 | `frontend/src/App.tsx` (`URL.revokeObjectURL(url)` after anchor click) | N/A (no frontend unit tests) | ✅ TRACED |
| FE Unwanted: Double-click prevention | 7 | `frontend/src/App.tsx` (button `disabled={isBusy}` + early return `if (!result || exportLoading) return`) | N/A | ✅ TRACED |
| FE Unwanted: Empty doc still downloads | 7 | `frontend/src/App.tsx` (no check on `markdown_document` emptiness — Blob created regardless) | N/A | ✅ TRACED |
| FE Unwanted: Pending state no block | 7 | `frontend/src/App.tsx` (export does not check for pending rewrite/clarify state; it reads server-side state) | N/A | ✅ TRACED |
| FE Unwanted: Download fail caught | 7 | `frontend/src/App.tsx` (try/catch around entire download block, error displayed inline) | N/A | ✅ TRACED |

---

## Task-to-Requirement Reverse Mapping

| Task | Files Modified | Requirement IDs Covered | Status |
|------|---------------|------------------------|--------|
| Task 1 | `backend/routes.py` | BE FR-5, BE NFR-2 | ✅ MAPPED |
| Task 2 | `backend/linter_adapter.py` | BE FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, NFR-1, NFR-4, NFR-5, NFR-7 | ✅ MAPPED |
| Task 3 | `backend/routes.py` | BE NFR-3, FR-6, Unwanted (404, refused, extra fields, zero reqs) | ✅ MAPPED |
| Task 4 | `tests_backend/test_handoff_export.py` | BE FR-1–FR-7, NFR-6, all Acceptance Criteria, all Unwanted Behavior | ✅ MAPPED |
| Task 5 | `frontend/src/types.ts` | FE FR-8, NFR-2 | ✅ MAPPED |
| Task 6 | `frontend/src/api.ts` | FE FR-2, NFR-1, NFR-2, NFR-4 | ✅ MAPPED |
| Task 7 | `frontend/src/App.tsx` | FE FR-1–FR-7, NFR-1–NFR-5, all Unwanted Behavior | ✅ MAPPED |
| Task 8 | `frontend/src/styles.css` | FE FR-1, FR-4, FR-6, NFR-4 | ✅ MAPPED |
| Task 9 | `tests_backend/test_handoff_export.py` | BE FR-5, NFR-5, FE FR-3, FR-7 | ✅ MAPPED |

---

## Untraced Items

| Type | ID/Description | Gap |
|------|---------------|-----|
| — | — | — |

**No UNTRACED requirements found.** All certified requirement IDs have corresponding tasks, implementation code, and (for backend) test coverage.

---

## Orphaned Items

| Type | Item | Notes |
|------|------|-------|
| — | — | — |

**No ORPHANED code or tasks found.** All tasks trace back to certified requirements, and all code changes map to documented tasks.

---

## Coverage Summary

| Category | Total | Traced | Untraced |
|----------|-------|--------|----------|
| Backend Functional Requirements | 7 | 7 | 0 |
| Backend Non-Functional Requirements | 7 | 7 | 0 |
| Backend Unwanted Behavior Clauses | 4 | 4 | 0 |
| Frontend Functional Requirements | 8 | 8 | 0 |
| Frontend Non-Functional Requirements | 5 | 5 | 0 |
| Frontend Unwanted Behavior Clauses | 4 | 4 | 0 |
| Implementation Tasks | 9 | 9 | 0 |
| **Total** | **44** | **44** | **0** |

---

## Test Gap Note

Frontend requirements are verified structurally (code inspection + `npm run build` type-checking) but lack dedicated unit tests. Backend requirements have comprehensive automated test coverage in `tests_backend/test_handoff_export.py` with 11 test methods spanning happy path, edge cases, error cases, and latency validation.
