# Requirements: Clarification Loop Backend Endpoint

## Overview

A new endpoint that, given a specific linter finding, returns two rewrite
options (A and B). The user selects one option; the system persists the
selected rewrite and reruns the deterministic linter to rescore the spec
within a single transaction.

---

## Functional Requirements

### FR-1: Generate A/B Rewrite Options

WHEN the user submits a clarification request containing a spec identifier, a line number, and a check identifier THE System SHALL return a response containing two candidate rewrites labelled "A" and "B".

WHEN the spec identifier in the clarification request does not match any stored spec THE System SHALL return a not-found error response with status code 404.

WHEN no finding matches the given line number and check identifier combination THE System SHALL return a not-found error response with status code 404.

WHEN the system generates rewrite options THE System SHALL include in each option a label field set to "A" or "B", a rewritten-text field containing a single physical line with no newline characters, and a rationale field explaining why the rewrite resolves the finding.

WHEN the system returns two options THE System SHALL ensure that both options target the same physical line so that selecting one invalidates the other.

### FR-2: Deterministic Option Generation

WHEN the system generates options for a given finding and effective line text THE System SHALL produce identical output on every invocation for the same inputs.

WHEN the system generates options THE System SHALL use data available in the finding record and the current effective line text without invoking network calls or non-deterministic sources.

WHEN the finding record contains a non-empty suggested-rewrite field THE System SHALL derive Option A from that existing suggestion.

WHEN the system generates Option B THE System SHALL produce a rewrite that differs in structure from Option A WHILE still resolving the same finding.

### FR-3: Select and Persist Rewrite

WHEN the user submits a selection request containing a spec identifier, a line number, a check identifier, and a selected value of "A" or "B" THE System SHALL persist the corresponding rewritten text as an overlay on the target line and rerun the linter within a single transaction.

WHEN the selected value in the selection request is neither "A" nor "B" THE System SHALL return a validation error response with status code 422.

WHEN the system processes a valid selection THE System SHALL regenerate the two options using the same deterministic logic and use the rewritten text from the matching option.

WHEN the system persists the selected rewrite THE System SHALL store the overlay and rerun the linter within a single all-or-nothing transaction.

WHEN the selection request succeeds THE System SHALL return the full updated analysis response including score, verdict, tier, findings, and requirements.

WHEN the spec identifier or finding in the selection request does not exist THE System SHALL return a not-found error response with status code 404.

WHEN the effective line text has changed between option generation and selection THE System SHALL return a conflict error response with status code 409.

### FR-4: Deterministic Rerun and Rescore

WHEN the system commits a rewrite overlay THE System SHALL reflect the selected rewrite in the effective text for the target line.

WHEN the system reruns the linter after a rewrite THE System SHALL execute the full linter pipeline on the new effective text within the same transaction as the overlay persistence.

WHEN the linter rerun completes THE System SHALL include the updated score, verdict, tier, findings, and requirements in the response.

---

## Non-Functional Requirements

### NFR-1: Single-Line Constraint

THE System SHALL constrain both Option A and Option B rewritten-text values to single physical lines containing no line-feed or carriage-return characters.

### NFR-2: Idempotent Option Retrieval

WHEN a caller invokes the clarification endpoint multiple times with the same inputs and the same effective text THE System SHALL return byte-identical option payloads.

### NFR-3: Transaction Safety

WHEN the selection endpoint executes THE System SHALL wrap all persistence writes and the linter rerun in a single transaction.

IF the transaction encounters a failure at any step THEN THE System SHALL roll back all changes and return an error response without persisting partial state.

### NFR-4: No New External Dependencies

THE System SHALL use no packages beyond the standard library and the existing project dependencies for the clarification feature.

### NFR-5: Response Latency

WHEN the system generates options or persists a selection for a spec with fewer than 200 lines THE System SHALL complete the response within 100 milliseconds.

---

## Unwanted Behavior

IF the clarification queue receives a request referencing a finding whose underlying line text another committed rewrite already changed THEN THE System SHALL reject the request with a conflict status code 409 and leave the spec unchanged.

IF the deterministic option generator receives a finding with an empty message and empty suggested-rewrite field THEN THE System SHALL return two generic rewrites derived from the check identifier category rather than returning an empty options list.

---

## Acceptance Criteria

WHEN the user requests clarification for a valid finding THEN THE System SHALL return two options with labels "A" and "B".

WHEN the user repeats the same clarification request without any state change THEN THE System SHALL return byte-identical options.

WHEN the user selects option "A" or "B" THEN THE System SHALL persist the corresponding rewritten text and return a rescored analysis.

WHEN the finding referenced in the request does not exist THEN THE System SHALL return status code 404.

WHEN the selected value is not "A" or "B" THEN THE System SHALL return status code 422.

WHEN the effective line has changed between option generation and selection THEN THE System SHALL return status code 409.

IF the rewrite persistence raises an exception THEN THE System SHALL roll back the transaction and persist no partial rewrite.

WHEN option generation completes THE System SHALL ensure both rewritten-text values contain no newline characters.

---

## Out of Scope

- AI or LLM-generated rewrite options (future work).
- More than two options per finding.
- Frontend UI for the clarification loop (separate spec).
- Batch clarification of multiple findings in one request.
