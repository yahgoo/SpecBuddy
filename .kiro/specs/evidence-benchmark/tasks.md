# Implementation Tasks: Evidence Panel + Benchmark Harness

Source requirements: `.kiro/specs/evidence-benchmark/requirements.md` (CERTIFIED, 100/100)

---

## Task 1 — Create adversarial Singapore-SME test cases data file

**File**: `data/samples/adversarial-sg-sme-cases.json`

Create the adversarial test case file with ≥10 cases following the existing
schema in `data/samples/distillation-test-cases.json`. Cases must cover:

- PayNow failure paths (≥4 cases): vague failure-handling language, missing
  timeout thresholds for QR code expiry, ambiguous retry semantics, undefined
  refund-path actors.
- PDPA personal-data handling (≥4 cases): escape-clause consent language, vague
  data-retention periods, undefined anonymisation thresholds, accountability gaps
  in passive wording.
- Multilingual customer notices (≥2 cases): mixed English/Mandarin/Malay tokens
  in hawker and heartland merchant contexts exercising ambiguity detection
  regardless of language.

Each case object:
```json
{
  "id": "SG01",
  "title": "Short descriptive title",
  "requirement_text": "Raw requirement text under test.",
  "expected_flags": "semicolon-separated list of expected findings",
  "difficulty": "easy|medium|hard|control",
  "category": "paynow|pdpa|multilingual"
}
```

File MUST be saved as UTF-8 with non-ASCII characters (Mandarin/Malay tokens).

**Requirement IDs**: FR-2.1, FR-2.2, FR-2.3, FR-2.4, FR-2.5

**Verification checkpoint**:
```bash
python3 -c "import json, pathlib; d=json.loads(pathlib.Path('data/samples/adversarial-sg-sme-cases.json').read_text('utf-8')); assert len(d)>=10; print('OK:', len(d), 'cases')"
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 2 — Create benchmark runner module

**Files**:
- `tests_benchmark/__init__.py`
- `tests_benchmark/runner.py`

Create the benchmark runner as a Python module importable by tests and
callable as a standalone script (`python3 -m tests_benchmark.runner`).

Logic:
1. Load cases from `data/samples/distillation-test-cases.json` and
   `data/samples/adversarial-sg-sme-cases.json`.
2. For each case, invoke the frozen linter via its public API (`from
   src.linter.parser import parse_requirements`, `from
   src.linter.rule_engine import run_checks`, `from src.linter.evaluator
   import evaluate`) — same import pattern as `backend/linter_adapter.py`.
3. Compare reported findings to `expected_flags` (semicolon-separated).
4. Classify each expected flag as detected (true positive) or missed (false
   negative). Track false positives (findings not matching any expected flag).
5. For `difficulty: "control"` cases: pass if zero findings, fail with
   false-positive annotation if findings present.
6. Compute aggregate true-positive ratio (TP / (TP + FP)) and
   detection-coverage ratio (TP / total expected flags).
7. Return structured result: per-case status, per-case detected/missed flags,
   aggregate ratios.
8. Catch unhandled linter exceptions per case → mark as errored, continue.
9. Handle empty case file gracefully → zero totals + warning.
10. Skip malformed adversarial entries with a warning.

**Requirement IDs**: FR-1.1, FR-1.2, FR-1.3, FR-1.4, FR-2.1, FR-2.5, FR-2.6,
NFR-4.2, NFR-4.3

**Verification checkpoint**:
```bash
python3 -m tests_benchmark.runner
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 3 — Create benchmark runner unit tests

**File**: `tests_benchmark/test_runner.py`

Write unittest-based tests following the pattern in `tests_backend/test_linter_adapter.py`:
- Test loading existing distillation cases produces expected structured output.
- Test loading adversarial cases succeeds (non-zero case count, UTF-8 chars).
- Test a known control case passes (zero findings → passed).
- Test exception isolation: inject a case with requirement_text that would crash
  (mock or known edge) → case marked errored, remaining cases unaffected.
- Test empty file produces zero totals + warning.
- Test malformed entry skipped with warning, other cases processed.
- Test deterministic: two consecutive runs produce identical ratios.
- Test total execution under 10 seconds.

**Requirement IDs**: FR-1.1, FR-1.2, FR-1.3, FR-1.4, FR-2.5, FR-2.6, NFR-4.1,
NFR-4.3

**Verification checkpoint**:
```bash
python3 -m unittest discover -s tests_benchmark
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 4 — Add benchmark database schema

**File**: `backend/schema.sql` (append new table)

Add a `benchmark_runs` table:
```sql
CREATE TABLE IF NOT EXISTS benchmark_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    total_cases INTEGER NOT NULL,
    true_positives INTEGER NOT NULL,
    false_positives INTEGER NOT NULL,
    false_negatives INTEGER NOT NULL,
    true_positive_ratio REAL NOT NULL,
    detection_coverage_ratio REAL NOT NULL,
    per_case_json TEXT NOT NULL
);
```

**Requirement IDs**: FR-1.2, FR-3.4, FR-3.5

**Verification checkpoint**:
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 5 — Add benchmark database helpers

**File**: `backend/database.py` (append functions)

Add functions:
- `insert_benchmark_run(conn, data: dict) -> int` — inserts a row, returns id.
- `get_latest_benchmark_run(conn) -> dict | None` — returns the most recent run
  or None.
- `is_benchmark_running(conn) -> bool` — returns True if a run is in-progress
  (started_at without completed_at). For queue semantics.

Follow the existing pattern: functions accept `sqlite3.Connection`, never
commit, return `sqlite3.Row` or dicts.

**Requirement IDs**: FR-1.2, FR-3.4, NFR-4.4

**Verification checkpoint**:
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 6 — Add benchmark API routes

**File**: `backend/routes.py` (append new routes)

Add:
- `POST /api/benchmark/run` — triggers a benchmark execution using the runner
  from Task 2, stores results via Task 5 helpers, returns structured result.
  If a run is in progress, queue it (return 202 or wait).
- `GET /api/benchmark/results` — returns the latest stored benchmark result.

Do NOT modify existing routes for specs, rewrites, clarify, or handoff-export.

**Requirement IDs**: FR-1.1, FR-1.2, NFR-4.4

**Verification checkpoint**:
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 7 — Add evidence panel API route

**File**: `backend/routes.py` (append new route)

Add:
- `GET /api/specs/{spec_id}/evidence` — returns:
  - `initial_score`: score at first analysis
  - `current_score`: score after latest rescore
  - `findings_resolved`: count of findings eliminated
  - `questions_answered`: count of clarification findings resolved via rewrites
  - `true_positive_ratio_pct`: from latest benchmark run (or null)
  - `detection_coverage_ratio_pct`: from latest benchmark run (or null)
  - `benchmark_available`: boolean
  - Error 404 if spec_id not found or deleted.

Requires storing `initial_score` at analysis time. Add an `initial_score`
column to the specs table (or compute from stored data). Choose the minimal
change; prefer computing from existing findings rows if possible.

Do NOT modify clarify or handoff-export routes.

**Requirement IDs**: FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-3.5, FR-3.7, FR-3.8

**Verification checkpoint**:
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 8 — Add backend tests for benchmark and evidence routes

**File**: `tests_backend/test_benchmark.py`

Follow existing pattern from `tests_backend/test_routes.py` (RouteTestBase with
temp database, TestClient):
- Test `POST /api/benchmark/run` returns structured result with ratios.
- Test `GET /api/benchmark/results` returns latest stored run.
- Test `GET /api/benchmark/results` when no runs exist returns appropriate empty
  state.
- Test `GET /api/specs/{spec_id}/evidence` returns correct initial/current score
  after applying a rewrite.
- Test evidence endpoint returns benchmark metrics after a benchmark run.
- Test evidence endpoint returns 404 for nonexistent spec.
- Test evidence endpoint returns null benchmark fields when no run recorded.

**Requirement IDs**: FR-1.2, FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-3.5, FR-3.7,
FR-3.8

**Verification checkpoint**:
```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 9 — Add Evidence Panel frontend component

**File**: `frontend/src/EvidencePanel.tsx` (new component)

Create a React component `EvidencePanel` that:
- Accepts `specId: number | null` and optional `benchmarkAvailable: boolean` props.
- Fetches `GET /api/specs/{spec_id}/evidence` on mount and after each rewrite
  cycle (accepts a `refreshTrigger` prop or callback).
- Displays:
  - Before/After score comparison (initial → current) or single score if no
    rewrite applied.
  - Findings resolved count.
  - Questions answered count.
  - True-positive ratio and detection-coverage ratio as percentages, or a
    placeholder message if no benchmark recorded.
- Displays empty-state message when no analysis results exist.
- Displays error state for deleted specs.

No new npm dependencies. Use existing Tailwind/CSS patterns from `App.tsx`.

**Requirement IDs**: FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-3.5, FR-3.6, FR-3.7,
FR-3.8

**Verification checkpoint**:
```bash
cd frontend && npm run build
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
```

---

## Task 10 — Integrate Evidence Panel into App.tsx

**File**: `frontend/src/App.tsx`

Import and render `<EvidencePanel>` in the existing layout alongside the
analysis result view. Wire it to receive:
- The current `spec_id` from analysis state.
- A refresh trigger that fires after each rewrite-apply cycle (same re-score
  callback already used for score updates).

Do NOT modify the ClarifyPanel, handoff-export button, or MissionBoard logic.
Only add the EvidencePanel rendering and its data wiring.

**Requirement IDs**: FR-3.1, FR-3.6

**Verification checkpoint**:
```bash
cd frontend && npm run build
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
```

---

## Task 11 — Add frontend API helpers for evidence and benchmark

**File**: `frontend/src/api.ts` (append functions)

Add:
- `fetchEvidence(specId: number): Promise<EvidenceResponse>`
- `triggerBenchmark(): Promise<BenchmarkRunResponse>`
- `fetchBenchmarkResults(): Promise<BenchmarkRunResponse | null>`

Add corresponding TypeScript interfaces to `frontend/src/types.ts`:
- `EvidenceResponse`
- `BenchmarkRunResponse`

No new npm dependencies.

**Requirement IDs**: FR-3.1, FR-3.4

**Verification checkpoint**:
```bash
cd frontend && npm run build
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
```

---

## Task 12 — End-to-end precision/recall verification test

**File**: `tests_benchmark/test_e2e_known_answer.py`

Create a known-answer mini test set (3–5 cases with hand-verified expected
flags) inline in the test file. Run the benchmark runner against this mini set
and assert:
- True-positive ratio matches the expected value (known answer).
- Detection-coverage ratio matches the expected value (known answer).
- Per-case pass/fail statuses match expectations.
- Control case correctly handled.

This test proves the entire pipeline produces correct metrics on a fixed input.

**Requirement IDs**: FR-1.1, FR-1.2, NFR-4.2, NFR-4.3

**Verification checkpoint**:
```bash
python3 -m unittest tests_benchmark.test_e2e_known_answer
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```

---

## Task 13 — Final full-suite verification

Run all verification commands sequentially and confirm zero failures:

```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
python3 -m unittest discover -s tests_benchmark
cd frontend && npm run build
python3 -m tests_benchmark.runner
```

Confirm:
- All tests pass.
- Frontend builds without errors.
- Benchmark runner prints structured results with non-zero true-positive ratio
  and detection-coverage ratio.
- `src/linter/` has zero modifications (verify with `git diff --stat src/linter/`).

**Requirement IDs**: ALL (integration gate)

---

## Requirement-to-Task Traceability Checklist

| Requirement ID | Task(s) | Description |
|----------------|---------|-------------|
| FR-1.1 | 2, 3, 6, 12 | Execute existing test suite via frozen linter |
| FR-1.2 | 2, 3, 4, 5, 6, 8, 12 | Report structured benchmark results |
| FR-1.3 | 2, 3 | Exception isolation per case |
| FR-1.4 | 2, 3 | Empty test file graceful handling |
| FR-2.1 | 1, 2 | Load adversarial SG-SME cases |
| FR-2.2 | 1 | PayNow failure path cases |
| FR-2.3 | 1 | PDPA personal-data handling cases |
| FR-2.4 | 1 | Multilingual customer notice cases |
| FR-2.5 | 1, 3 | UTF-8 encoding without error |
| FR-2.6 | 2, 3 | Malformed entry skipped with warning |
| FR-3.1 | 7, 8, 9, 10, 11 | Display score change (before/after) |
| FR-3.2 | 7, 8, 9 | Display findings resolved count |
| FR-3.3 | 7, 8, 9 | Display questions answered count |
| FR-3.4 | 4, 5, 7, 8, 9, 11 | Display benchmark detection metrics |
| FR-3.5 | 4, 7, 8, 9 | Placeholder when no benchmark recorded |
| FR-3.6 | 9, 10 | Evidence panel refresh on rewrite |
| FR-3.7 | 7, 8, 9 | Empty state for unanalyzed spec |
| FR-3.8 | 7, 8, 9 | Error state for deleted spec |
| NFR-4.1 | 3 | Benchmark completes within 10 seconds |
| NFR-4.2 | 2, 12 | No linter core modification |
| NFR-4.3 | 2, 3, 12 | Deterministic results across runs |
| NFR-4.4 | 5, 6 | Concurrent run queueing |

---

## Constraints Checklist

- [ ] `src/linter/` is never modified (NFR-4.2)
- [ ] Clarify-related code unchanged (Tasks 6, 7, 10 explicitly exclude)
- [ ] Handoff-export code unchanged (Tasks 6, 7, 10 explicitly exclude)
- [ ] No new npm dependencies added (Task 9, 11 — flag for approval if needed)
- [ ] All tasks independently reviewable (each task produces testable output)
- [ ] Verification checkpoint after every task
