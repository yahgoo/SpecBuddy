# SpecBuddy — Requirements Quality Gate

## Problem Statement

Poorly written requirements are expensive to fix when discovered late. In
AI-assisted delivery, the problem compounds: when a requirement is vague, a coding
agent fills the gap with assumptions that may vary across runs.

SpecBuddy provides a requirements quality gate before implementation starts. It
checks Markdown requirements, flags ambiguity, scores readiness, suggests
deterministic rewrites, and produces a cleaner handoff for coding agents.

## Goals

- Validate EARS-style requirement structure.
- Detect ambiguous, unverifiable, passive, or non-mandatory language.
- Surface missing error paths and tacit assumptions.
- Provide deterministic line-level rewrite suggestions.
- Preserve raw input immutably while applying rewrite overlays.
- Export a Markdown report for coding-agent handoff.

## Non-Goals

- Generating application code.
- Making AI or network calls for rewrites.
- Adding auth, cloud deployment, collaboration, or multi-user editing.
- Implementing live imports from DingTalk, Zoom, Teams, OCR, speech-to-text, or
  whiteboards in the first version.

## Target Users

- Business Analysts
- Product Managers
- Engineering Managers
- Vibe coders and AI-assisted builders
- Delivery teams working with coding agents

## Functional Requirements

- **FR1**: The system SHALL accept pasted Markdown requirements text.
- **FR2**: The system SHALL store the original raw Markdown text immutably.
- **FR3**: The system SHALL parse requirement lines and detect EARS keywords.
- **FR4**: The system SHALL flag non-mandatory imperatives such as `should`,
  `must`, `may`, and `will` when used in place of `SHALL`.
- **FR5**: The system SHALL flag ambiguous or unverifiable language.
- **FR6**: The system SHALL calculate a readiness score, tier, verdict, and
  severity counts.
- **FR7**: The system SHALL provide deterministic rewrite suggestions where a
  finding has a supported single-line fix.
- **FR8**: The system SHALL apply rewrite overlays without mutating the original
  raw Markdown text.
- **FR9**: The system SHALL reanalyze the effective spec after a rewrite is
  applied, removed, or reset.
- **FR10**: The system SHALL generate a Markdown quality report.

## Non-Functional Requirements

- **NFR1 (Determinism)**: The same input SHALL produce the same findings, score,
  verdict, and report except for timestamp metadata.
- **NFR2 (Local-first)**: The first version SHALL run locally without external
  services.
- **NFR3 (Portability)**: The core linter SHALL run from the command line using
  Python standard-library behavior.
- **NFR4 (Safety)**: Backend tests SHALL use temporary SQLite databases.

## Acceptance Criteria

- **AC1**: WHEN the user analyzes rough requirements, THE SYSTEM SHALL display
  score, verdict, tier, findings, parsed requirements, and report Markdown.
- **AC2**: WHEN a finding has a supported rewrite, THE SYSTEM SHALL display an
  **Apply fix** action.
- **AC3**: WHEN the user applies a fix, THE SYSTEM SHALL store a line-level
  rewrite overlay and update the analysis result.
- **AC4**: WHEN the user removes or resets rewrites, THE SYSTEM SHALL reanalyze
  using the remaining overlays.
- **AC5**: WHEN the user opens Mission Board, THE SYSTEM SHALL show progress
  derived from current findings, score, and verdict.

## Open Questions

- Should the internal compatibility command `linter.claritygate` be renamed in a
  later version?
- Which upstream source integration should be built first after the Markdown-only
  submission version?
