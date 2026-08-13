# SpecBuddy Demo Handoff

## Core Story

"Bad spec in, bad AI build out." SpecBuddy catches requirement defects before a
coding agent starts implementation.

## Local Demo Commands

Run the backend:

```bash
python3 -m uvicorn backend.main:create_app --factory --host 127.0.0.1 --port 8000
```

Run the frontend:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

## CLI Backup Commands

```bash
python3 -m linter.claritygate data/samples/ambiguous-requirements.md --out /tmp/specbuddy-ambiguous-report.md
python3 -m linter.claritygate data/samples/clean-ears-requirements.md --out /tmp/specbuddy-clean-report.md
```

The command path still uses the preserved internal compatibility module
`linter.claritygate`; public product naming is SpecBuddy.

## Demo Beats

1. Paste rough requirements.
2. Analyze.
3. Show REFUSED verdict and low score.
4. Show line-level ambiguity findings.
5. Apply one deterministic fix.
6. Show score and findings update.
7. Show accepted rewrite.
8. Show Mission Board progress.
9. Open full Markdown report.

## Scope Note

SpecBuddy currently accepts Markdown requirements. Upstream sources such as
DingTalk, Zoom/Teams minutes, whiteboards, scribbles, BRDs, PRDs, and meeting
notes can be converted into Markdown before analysis. Live imports are future
work.
