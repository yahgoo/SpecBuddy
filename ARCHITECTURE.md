# SpecBuddy Architecture

SpecBuddy is a local-first, three-layer full-stack application:

```text
Frontend (React + Vite + TypeScript)
  Import -> Analyze -> Review -> Apply Fix -> Report
        |
        | HTTP/JSON
        v
Backend (FastAPI + sqlite3)
  API routes -> database transactions -> linter adapter
        |
        | direct Python imports
        v
Frozen deterministic linter (src/linter/)
  loader -> parser -> rule_engine -> evaluator -> reporter
        |
        v
SQLite rewrite overlays + Markdown report
```

## Core Invariant

The backend does not reimplement linter logic. It imports the existing
`src/linter/` pipeline, persists raw Markdown immutably, applies single-line
rewrite overlays, reruns the same deterministic analysis, and returns the result
to the frontend.

For a given effective spec text, backend analysis must match the direct linter
pipeline for requirements, findings, score, tier, verdict, and report content.

## Data Flow

1. User pastes Markdown requirements.
2. Backend stores the original raw text.
3. Backend parses and analyzes the effective text.
4. Findings, score, verdict, parsed requirements, and report Markdown are
   returned to the frontend.
5. User may apply a deterministic single-line rewrite.
6. Backend stores the rewrite overlay in one transaction and reanalyzes.
7. Mission Board state is derived in the frontend from the current result.

## Persistence Rules

- Raw spec text remains immutable after insertion.
- SQLite rewrites are overlays keyed by original physical Markdown line number.
- Rewrite mutation and reanalysis happen in one transaction with rollback on
  failure.
- Every SQLite connection enables `PRAGMA foreign_keys = ON`.
- Tests use temporary SQLite databases, never the development database.
- Mission state is not persisted in the backend.

## Technology Choices

- **Python deterministic linter**: stable, inspectable, no AI/network dependency.
- **FastAPI**: small HTTP wrapper with automatic local API docs.
- **sqlite3**: standard-library persistence for local demo reliability.
- **React/Vite/TypeScript**: responsive interactive review UI.
- **stdlib unittest**: preserves the existing backend/core test approach.

## Current Boundaries

SpecBuddy currently accepts Markdown requirements. Upstream content may come from
BA notes, PRDs, meeting minutes, whiteboards, or collaboration tools after being
converted into Markdown. Live DingTalk, Zoom, Teams, OCR, speech-to-text,
whiteboard, and file-import integrations are future work.
