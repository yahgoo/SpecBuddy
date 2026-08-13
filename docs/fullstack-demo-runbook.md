# SpecBuddy Full-Stack Demo Runbook

Recording guide for the local SpecBuddy demo.

## Prerequisites

- Backend dependencies installed: `pip install -r requirements-backend.txt`
- Frontend dependencies installed: `cd frontend && npm install`
- Local ports `8000` and `5173` available

## Startup Commands

Backend, from the repo root:

```bash
python3 -m uvicorn backend.main:create_app --factory --host 127.0.0.1 --port 8000
```

Frontend, from `frontend/`:

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

## Demo Input

Paste this into the textarea:

```markdown
# Demo Requirements

The system should support login quickly.
The system shall handle user data.
If needed, the system may notify users.
THE System SHALL display the dashboard.
```

## Demo Flow

1. Open the app and show the default `requirements.md` input.
2. Paste the demo input.
3. Click **Analyze**.
4. Show the **REFUSED** verdict and low readiness score.
5. Show line-level findings, check IDs, and deterministic rewrite suggestions.
6. Click **Apply fix** on a supported finding.
7. Confirm the score and findings update.
8. Show **Accepted Rewrites**.
9. Expand **Parsed Requirements**.
10. Expand **Full Report (Markdown)**.
11. Show the **Mission Board** progress.

## Suggested Voiceover Beats

- "SpecBuddy is a deterministic requirements quality gate: no AI scoring, no
  hallucinated rewrites."
- "It checks the spec before the coding agent starts building."
- "The rewrite loop lets a user accept suggested single-line fixes and rescore
  immediately."
- "Mission Board progress is derived from the current score, verdict, and
  findings."
- "SpecBuddy currently accepts Markdown requirements. Notes from meetings,
  PRDs, whiteboards, and collaboration tools can be converted into Markdown
  upstream; direct integrations are future work."

## Expected Values

Exact values depend on the input, but the demo should show:

- A rough spec starts with a **REFUSED** verdict.
- Findings include ambiguity, EARS, and unverifiable-language issues.
- Applying a supported fix reduces findings and improves the score.
- Accepted rewrites appear without mutating the stored raw spec.

## Pre-Recording Verification

```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```
