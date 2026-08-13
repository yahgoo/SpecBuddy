# SpecBuddy Submission Checklist

Submission deadline: **August 14, 2026 at 6:00 PM Singapore time**.

## Required Form Fields

- [ ] Project title: `SpecBuddy`
- [ ] Team name
- [ ] Team members
- [ ] Contact email
- [ ] Public repository URL, optional
- [ ] Project image: 16:9 cover, about `380x216px`, under 5 MB
- [ ] Short blurb: under 10 words
- [ ] Demo video link: YouTube, Google Drive, or Loom
- [ ] Product sharing paragraph
- [ ] Product used: CodeBuddy
- [ ] Project description
- [ ] Demo/project link, optional bonus

## Suggested Short Blurb

Clearer specs for better agent-built software.

## Product Sharing Draft

SpecBuddy is being prepared for the AI Tinkerers x Tencent Cloud Agent
Development Challenge with CodeBuddy as the hackathon coding-agent context. The
project focuses on a practical CodeBuddy handoff problem: before a coding agent
starts building, teams need requirements that are specific, testable, and free of
silent ambiguity. This first version preserves a deterministic Python linter,
FastAPI backend, SQLite rewrite overlay flow, and React/Vite review UI so users
can paste Markdown requirements, analyze them, apply deterministic fixes, and
export a cleaner specification for coding-agent implementation.

## Project Description Draft

SpecBuddy is a requirements quality gate for AI-assisted software delivery. It
helps business analysts, product managers, engineering leads, and AI-assisted
builders turn rough requirements into coding-agent-ready specifications before
implementation begins.

The product accepts Markdown requirements, stores the raw text immutably, runs a
deterministic Python linter, and returns a readiness score, verdict, severity
counts, line-level findings, suggested deterministic rewrites, parsed
requirements, accepted rewrite overlays, Mission Board progress, and a full
Markdown quality report.

The core insight is that coding agents are only as good as the specifications
they receive. Weak requirements create downstream bugs, rework, inconsistent
agent behavior, missed edge cases, and features that cannot be traced back to the
original intent. SpecBuddy catches that ambiguity before coding starts.

SpecBuddy currently accepts Markdown requirements. In real delivery, that
Markdown can come from BA notes, PRDs, meeting minutes, whiteboards, or
collaboration tools. Source integrations such as DingTalk, Zoom, Teams, OCR,
speech-to-text, and whiteboard import are future work, not current
implementation.

## Demo Video Checklist

- [ ] Shows paste/import of rough Markdown requirements
- [ ] Shows Analyze
- [ ] Shows REFUSED result with low score
- [ ] Shows ambiguity and rewrite suggestions
- [ ] Shows Apply fix
- [ ] Shows score/findings update
- [ ] Shows accepted rewrite
- [ ] Shows Mission Board update
- [ ] Shows full Markdown report

## Verification

```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests_backend
cd frontend && npm run build
```
