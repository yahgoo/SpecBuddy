# Requirements: Handoff Export Backend Endpoint

## Overview

A new endpoint that packages the certified analysis state of a spec into a
single downloadable Markdown document structured for direct pasting into any
coding agent. The document contains the certified spec text, EARS-formatted
acceptance criteria, unresolved clarification questions, and an implementation
task list. No new AI calls, no new storage tables, and no modifications to
clarify-related code.

---

## Functional Requirements

### FR-1: Export Certified Spec Text

WHEN the user requests a handoff export for a valid spec identifier THE System SHALL include the full effective Markdown text of the spec with all accepted rewrite overlays applied in the exported document under a section headed "Certified Spec".

WHEN the spec has no rewrite overlays THE System SHALL include the original raw text as the certified spec text.

WHEN the spec has one or more rewrite overlays THE System SHALL include the reconstructed effective text reflecting all applied rewrites.

### FR-2: Extract EARS-Formatted Acceptance Criteria

WHEN the System builds the handoff export THE System SHALL extract acceptance criteria from the certified requirements and format them using EARS patterns.

WHEN a requirement record contains a statement field THE System SHALL include that statement as an acceptance criterion in the exported document.

WHEN the System lists acceptance criteria THE System SHALL group them by section heading from the original spec for each section that has data.

WHEN the certified text contains zero requirements THE System SHALL include an empty acceptance criteria section with a note indicating no requirements exist.

### FR-3: Include Unresolved Clarification Questions

WHEN the System builds the handoff export THE System SHALL include a section listing all unresolved findings that represent open clarification questions.

WHEN a finding has severity "defect" or "clarification" and no corresponding accepted rewrite overlay exists for that line THE System SHALL include that finding in the unresolved questions list.

WHEN the System lists an unresolved question THE System SHALL include the line number, check identifier, severity, and the finding message.

WHEN all findings have corresponding accepted rewrites THE System SHALL include an empty unresolved questions section with a note indicating no open questions remain.

### FR-4: Generate Implementation Task List

WHEN the System builds the handoff export THE System SHALL derive an implementation task list from the certified requirements.

WHEN a requirement record exists in the certified analysis THE System SHALL produce a corresponding task item that references the requirement line number and summarizes the required behavior.

WHEN the System produces the task list THE System SHALL order tasks by line number ascending.

WHEN the certified analysis contains zero requirements THE System SHALL include an empty task list section with a note indicating no tasks exist.

### FR-5: Assemble Single Markdown Document

WHEN the System assembles the export document THE System SHALL produce a single Markdown string containing four sequential sections: Certified Spec, Acceptance Criteria, Unresolved Questions, and Implementation Tasks.

WHEN the System produces the document THE System SHALL use standard Markdown headings for each section with no proprietary formatting, custom tags, or tool-specific syntax.

WHEN the System produces the document THE System SHALL include a metadata header with the spec filename, export timestamp, readiness score, verdict, and tier.

### FR-6: Happy-Path Export

WHEN the user requests a handoff export for a spec that has a "certified" verdict and at least one requirement THE System SHALL return a complete export document containing all four sections populated with the spec content, acceptance criteria, an empty unresolved questions note, and the derived task list.

### FR-7: Read-Only Operation

WHEN the System processes a handoff export request THE System SHALL read from the existing certified analysis state without writing to persistent storage.

WHEN the System processes a handoff export request THE System SHALL not invoke any AI, LLM, or network calls.

WHEN the System processes a handoff export request THE System SHALL not create new storage tables or modify existing table schemas.

---

## Non-Functional Requirements

### NFR-1: No Modification to Clarify Code

THE System SHALL not modify any clarify-option or select-clarify-option logic in the adapter layer.

THE System SHALL not modify the existing clarify-related request or response model definitions.

### NFR-2: Model Naming Convention

THE System SHALL name the request model "HandoffExportRequest" and the response model "HandoffExportResponse".

THE System SHALL not reuse or create model names that resemble existing clarify-specific model names.

### NFR-3: Route Convention Compliance

THE System SHALL register the endpoint so that it is reachable at the designated handoff-export path from the client.

### NFR-4: No New Storage Tables

THE System SHALL not create any new storage tables, columns, or migrations for this feature.

THE System SHALL derive all export content from the existing specs, rewrites, requirements, and findings data already stored.

### NFR-5: Output Portability

THE System SHALL produce Markdown output that contains no proprietary formatting, no tool-specific metadata blocks, and no syntax requiring a specific agent or IDE to parse.

THE System SHALL use standard CommonMark-compatible Markdown constructs and no other formatting in the exported document.

### NFR-6: Response Latency

WHEN the System exports a spec with fewer than 200 lines THE System SHALL complete the response within 200 milliseconds.

### NFR-7: No New External Dependencies

THE System SHALL use no packages beyond the standard library and the existing project dependencies for the handoff export feature.

---

## Unwanted Behavior

IF the user requests a handoff export for a spec whose verdict is "refused" THEN THE System SHALL still produce the export document including all unresolved findings rather than rejecting the request.

IF the request body includes fields not defined in the request model THEN THE System SHALL ignore extra fields and process the request without error.

IF the System encounters a spec with zero requirements and zero findings THEN THE System SHALL return a valid export document with empty sections rather than an error response.

IF the spec identifier references a spec that does not exist THEN THE System SHALL return a not-found error response with status code 404.

---

## Acceptance Criteria

WHEN the user requests a handoff export for a valid spec THE System SHALL return status code 200 with a response containing a non-empty Markdown document field.

WHEN the spec has accepted rewrites THE System SHALL reflect those rewrites in the certified spec text section of the exported document.

WHEN the spec has unresolved findings THE System SHALL list each unresolved finding with line number, check identifier, severity, and message in the unresolved questions section.

WHEN all findings have accepted rewrites THE System SHALL include an unresolved questions section stating no open questions remain.

WHEN the spec contains EARS-formatted requirements THE System SHALL list each requirement statement in the acceptance criteria section grouped by section.

WHEN the spec has requirements THE System SHALL produce one implementation task per requirement ordered by line number.

WHEN the spec identifier does not match any stored spec THE System SHALL return status code 404.

WHEN any coding agent receives the exported Markdown THE System SHALL have produced a document parseable as standard Markdown with no proprietary blocks or formatting.

WHEN the System returns the response THE System SHALL include spec identifier, filename, score, verdict, and exported-at timestamp in the response metadata.

---

## Interface Notes

This section documents technical routing and protocol details referenced by the
requirements above. These notes are not requirements.

- HTTP method: POST
- Route path: /api/specs/{spec_id}/handoff-export
- The route router uses prefix "/api", so the decorator path is
  /specs/{spec_id}/handoff-export within that router.
- Request model: HandoffExportRequest (empty body accepted)
- Response model: HandoffExportResponse (fields: spec_id, filename, score,
  verdict, exported_at, markdown_document)
- Status codes: 200 on success, 404 for missing spec_id

---

## Out of Scope

- AI or LLM-generated summaries or task descriptions (future work).
- Frontend UI for the handoff export (separate spec).
- Authentication or authorization on the export endpoint.
- Cloud deployment or external storage of exported documents.
- Batch export of multiple specs in one request.
- Modification of any clarify-related logic.
- Custom export templates or user-configurable section ordering.
