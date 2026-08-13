# Requirements: Evidence Panel + Benchmark Harness

## Overview

A benchmark harness that validates linter detection accuracy against known test
cases, extended with adversarial Singapore-SME cases, and a frontend evidence
panel that visualizes remediation impact. The frozen linter core in
`src/linter/` is not modified; this feature wraps it with an executable test
runner and evidence display.

---

## 1. Benchmark Harness — Existing Cases

### FR-1.1: Execute Existing Test Suite

WHEN the user triggers a benchmark run THE System SHALL load all cases from the existing distillation test cases file.

WHEN the user triggers a benchmark run THE System SHALL execute each loaded case's requirement text through the frozen linter.

WHEN the System executes a single test case THE System SHALL compare the linter's reported findings against that case's declared expected flags.

WHEN the System completes a single test case comparison THE System SHALL classify each expected flag as detected or missed.

WHEN the System completes all cases THE System SHALL compute a true-positive ratio by dividing true-positive flags by the sum of true-positive and false-positive flags.

WHEN the System completes all cases THE System SHALL compute a detection-coverage ratio by dividing true-positive flags by the total expected flags declared across all cases.

### FR-1.2: Report Benchmark Results

WHEN the System completes execution of all cases THE System SHALL emit a structured result containing per-case status of either passed or failed.

WHEN the System completes execution of all cases THE System SHALL emit per-case detected flags and per-case missed flags in the structured result.

WHEN the System completes execution of all cases THE System SHALL emit aggregate true-positive ratio and aggregate detection-coverage ratio in the structured result.

WHEN a test case has difficulty marked as control and the linter reports zero findings THE System SHALL mark that case as passed.

WHEN a test case has difficulty marked as control and the linter reports one or more findings THE System SHALL mark that case as failed with a false-positive annotation.

### FR-1.3: Unwanted Behavior — Linter Exception Isolation

IF the frozen linter raises an unhandled exception for a single test case THEN THE System SHALL catch the exception and mark that case as errored with the exception message.

IF the frozen linter raises an unhandled exception for a single test case THEN THE System SHALL continue executing remaining cases without aborting the suite.

### FR-1.4: Unwanted Behavior — Empty Test File

IF the existing distillation test cases file contains zero cases THEN THE System SHALL emit a structured result with zero totals and a warning message indicating no cases were found.

---

## 2. Benchmark Harness — Adversarial Singapore-SME Cases

### FR-2.1: Adversarial Case Coverage

WHEN the user triggers a benchmark run THE System SHALL load adversarial Singapore-SME test cases from the adversarial test cases file.

WHEN the System loads the adversarial test cases file THE System SHALL execute them through the frozen linter using the same true-positive ratio and detection-coverage ratio methodology as existing cases.

WHEN the System loads the adversarial test cases file THE System SHALL verify that the file contains at least ten cases.

WHEN the System validates adversarial case categories THE System SHALL confirm coverage of PayNow payment failure paths, PDPA personal-data handling requirements, and multilingual customer notice requirements spanning English, Mandarin, and Malay for hawker and heartland merchant contexts.

### FR-2.2: PayNow Payment Failure Cases

WHEN the System loads PayNow-category adversarial cases THE System SHALL include cases that exercise vague failure-handling language.

WHEN the System loads PayNow-category adversarial cases THE System SHALL include cases that exercise missing timeout thresholds for QR code expiry.

WHEN the System loads PayNow-category adversarial cases THE System SHALL include cases that exercise ambiguous retry semantics.

WHEN the System loads PayNow-category adversarial cases THE System SHALL include cases that exercise undefined refund-path actors.

### FR-2.3: PDPA Personal-Data Handling Cases

WHEN the System loads PDPA-category adversarial cases THE System SHALL include cases that exercise escape-clause consent language.

WHEN the System loads PDPA-category adversarial cases THE System SHALL include cases that exercise vague data-retention periods.

WHEN the System loads PDPA-category adversarial cases THE System SHALL include cases that exercise undefined anonymisation thresholds.

WHEN the System loads PDPA-category adversarial cases THE System SHALL include cases that exercise accountability gaps in passive wording.

### FR-2.4: Multilingual Customer Notice Cases

WHEN the System loads multilingual-notice adversarial cases THE System SHALL include cases that exercise mixed-script requirement text containing English, Mandarin, and Malay tokens.

WHEN the System loads multilingual-notice adversarial cases THE System SHALL verify that the linter detects ambiguity flags regardless of the language of surrounding prose.

### FR-2.5: Unwanted Behavior — Encoding Failure

IF the adversarial test cases file contains characters outside the ASCII range THEN THE System SHALL decode the file as UTF-8 without raising an encoding error.

IF the adversarial test cases file contains non-ASCII characters THEN THE System SHALL execute all cases to completion regardless of character encoding.

### FR-2.6: Unwanted Behavior — Malformed Case Entry

IF a single adversarial case entry has missing or invalid fields THEN THE System SHALL skip that entry with a warning and continue processing remaining cases.

---

## 3. Evidence Panel — Score Comparison Display

### FR-3.1: Display Score Change

WHEN the user opens the Evidence Panel for a spec whose readiness score has changed following at least one accepted rewrite THE System SHALL display the initial readiness score and the most recent readiness score side by side.

WHEN the user opens the Evidence Panel and the user has not applied any rewrite THE System SHALL display the current score and omit the comparison value.

### FR-3.2: Display Findings Resolved Count

WHEN the user views the Evidence Panel THE System SHALL display the count of findings that were present at initial analysis and are absent following the most recent rescore.

WHEN the user has resolved zero findings THE System SHALL display the resolved count as zero.

### FR-3.3: Display Clarification Questions Answered

WHEN the user views the Evidence Panel THE System SHALL display the count of clarification questions answered through accepted rewrites.

WHEN the user has answered zero clarification questions THE System SHALL display the answered count as zero.

### FR-3.4: Display Detection Metrics from Benchmark

WHEN the System has completed at least one benchmark execution THE System SHALL display the most recent aggregate true-positive ratio as a percentage in the Evidence Panel.

WHEN the System has completed at least one benchmark execution THE System SHALL display the most recent aggregate detection-coverage ratio as a percentage in the Evidence Panel.

### FR-3.5: Unwanted Behavior — No Benchmark Execution Recorded

IF the Evidence Panel renders and the System has recorded zero benchmark executions THEN THE System SHALL display a placeholder message stating that benchmark results are not yet available.

### FR-3.6: Evidence Panel Refresh

WHEN the user applies a rewrite and the linter rescores the spec THE System SHALL update the score comparison within the same response cycle.

WHEN the user applies a rewrite and the linter rescores the spec THE System SHALL update the resolved count within the same response cycle.

WHEN the user applies a rewrite and the linter rescores the spec THE System SHALL update the answered count within the same response cycle.

### FR-3.7: Unwanted Behavior — Missing Analysis Results

IF the Evidence Panel renders for a spec identifier that has no stored analysis results THEN THE System SHALL display an empty state message indicating that analysis has not been run.

IF the Evidence Panel renders for a spec identifier that has no stored analysis results THEN THE System SHALL suppress rendering of any numeric values.

### FR-3.8: Unwanted Behavior — Stale Data on Spec Deletion

IF the user deletes a spec and navigates to the Evidence Panel for that spec identifier THEN THE System SHALL display an error message indicating the spec no longer exists.

---

## 4. Non-Functional Requirements

### NFR-4.1: Benchmark Execution Time

WHEN the System executes the full suite of twenty or more cases THE System SHALL complete all cases and produce results within ten seconds on a machine meeting the project's minimum requirements.

### NFR-4.2: No Linter Core Modification

WHEN the System invokes the linter THE System SHALL call the frozen linter's existing public interface without modifying any file under the linter source directory.

### NFR-4.3: Deterministic Results

WHEN the System executes the suite twice against the same test case file without modification to linter logic THE System SHALL produce identical true-positive ratio and detection-coverage ratio values on both runs.

### NFR-4.4: Unwanted Behavior — Concurrent Benchmark Runs

WHILE a benchmark run is executing, IF a user triggers a second benchmark run THEN THE System SHALL queue the second run and execute it after the first run completes.

---

## Interface Notes

This section contains implementation-level routing and file details excluded
from requirement lines above.

### Benchmark Runner

- Test case source (existing): `data/samples/distillation-test-cases.json`
- Test case source (TC11–20): `data/samples/distillation-test-cases-tc11-20.json`
- Adversarial case file: `data/samples/adversarial-sg-sme-cases.json`
- Runner entry point: new module under `tests_benchmark/` or equivalent test
  directory; must be executable via `python3 -m unittest` or a standalone script.
- The runner imports the linter's public API from `src/linter/` and does not
  shell out to the CLI unless verifying CLI exit codes.
- True-positive ratio replaces the term "precision" in outputs.
- Detection-coverage ratio replaces the term "recall" in outputs.

### Adversarial Case Structure

Each adversarial case JSON object follows the same schema as existing cases:

```json
{
  "id": "SG01",
  "title": "Short descriptive title",
  "requirement_text": "The raw requirement text under test.",
  "expected_flags": "semicolon-separated list of expected findings",
  "difficulty": "easy|medium|hard|control",
  "category": "paynow|pdpa|multilingual"
}
```

### Backend API

- Benchmark trigger endpoint: `POST /api/benchmark/run`
- Benchmark results endpoint: `GET /api/benchmark/results`
- Evidence panel data endpoint: `GET /api/specs/{spec_id}/evidence`
- These endpoints are additions to the existing FastAPI app in `backend/`.

### Frontend UI

- Evidence panel component lives alongside existing analysis result views.
- The panel fetches from `/api/specs/{spec_id}/evidence` on spec load and after
  each rewrite-apply cycle.
- Benchmark results are fetched from `/api/benchmark/results` and rendered as a
  summary row within the evidence panel.
- No new npm dependencies required beyond what is already in `frontend/package.json`.

### File Boundaries

- `src/linter/` — frozen, read-only. No changes permitted.
- `backend/` — new route module for benchmark and evidence endpoints.
- `frontend/src/` — new Evidence Panel component and benchmark summary display.
- `data/samples/` — new `adversarial-sg-sme-cases.json` file.
- `tests_benchmark/` — new test module for the benchmark runner itself.
