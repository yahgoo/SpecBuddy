# SpecBuddy Social Post Draft

I am building **SpecBuddy**, a requirements quality gate for AI-assisted software
delivery.

The idea is simple: coding agents are only as good as the specifications they
receive.

SpecBuddy checks Markdown requirements before implementation starts. It flags
ambiguous, unverifiable, and non-testable language; scores readiness; suggests
deterministic rewrites; and helps teams export a cleaner handoff for coding
agents.

Bad requirements often fail quietly later as bugs, rework, inconsistent agent
behavior, missed edge cases, and features no one can trace back to the original
intent. SpecBuddy catches that drift at the source.

Current scope:

- Markdown requirements in
- deterministic Python linter
- FastAPI backend
- SQLite rewrite overlays
- React/Vite review UI
- Mission Board progress
- Markdown report export

Future work includes source imports from meeting notes, PRDs, whiteboards, and
collaboration tools.

Same coding agent. Clearer specs in. Better software out.
