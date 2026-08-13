# SpecBuddy — Design

This design preserves the existing deterministic linter behavior and describes
the local full-stack wrapper used for the first SpecBuddy version.

## Pipeline

```text
Markdown requirements
  -> loader
  -> parser
  -> rule engine
  -> evaluator
  -> reporter
  -> frontend review loop
```

The linter pipeline is deterministic. It does not call an LLM, use network
services, or generate probabilistic rewrites.

## Backend

The FastAPI backend exposes endpoints for:

- creating a spec from raw Markdown
- retrieving a stored spec
- analyzing effective text
- applying one line-level rewrite overlay
- removing a rewrite overlay
- resetting all rewrites

SQLite stores raw spec text, parsed requirements, findings, score snapshots, and
rewrite overlays. The original raw text remains immutable after insertion.

## Frontend

The React/Vite frontend provides:

- Markdown input
- score/verdict summary
- severity counts
- findings filters
- deterministic rewrite actions
- accepted rewrite display
- parsed requirement display
- Mission Board
- full Markdown report preview

Mission Board state is derived from the current analysis response. It is not
persisted by the backend.

## Rewrite Overlay Rules

- A rewrite targets one original physical Markdown line.
- Applying a rewrite and reanalysis occurs in one transaction.
- Failure rolls back the rewrite.
- Removing or resetting rewrites reanalyzes the effective spec.

## Report

The report uses the public SpecBuddy product name and an agent-readiness score.
The internal CLI compatibility command remains `python3 -m linter.claritygate`
for this first rebrand.

## Future Work

Source integrations are intentionally out of scope for the first SpecBuddy
version. Later versions may import or normalize notes from DingTalk, Zoom, Teams,
whiteboards, BRDs, PRDs, and meeting transcripts into Markdown before analysis.
