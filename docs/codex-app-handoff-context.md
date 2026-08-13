# Handoff Context for Codex App — SpecBuddy Git Setup + Demo Video

## Situation
Working directory:
`/Users/kmsum/Downloads/AI Tinkerers x Tencent Cloud Hackathon - Agent Development Challenge/SpecBuddy`

This is the **SpecBuddy** project (renamed/rebranded from an earlier
prototype called ClarityGate). A prior Codex CLI session, running in a
restricted sandbox mode, could create ordinary files/directories but
was blocked from running `git init` ("Operation not permitted"), even
though the filesystem itself is writable and not read-only. This looks
like a sandbox/approval-mode restriction on git operations specifically,
not a real macOS permission problem. You are running with full git
access, so take over from here.

## What's already done (do not redo)
1. **Branding cleanup complete**: 8 obsolete ClarityGate artifacts
   (pitch decks, .key/.pptx/.pdf files, ~25.6 MB total) were deleted.
   `__pycache__` cleaned. Verified via full test suite: 36/36 core
   tests, 73/73 backend tests, 18/18 benchmark tests, frontend build
   passing.
2. **Remaining known issue (not yet fixed)**: 6 screenshots in
   `docs/assets/screenshots/` (`01-import.png` through `06-report.png`)
   still visually show old ClarityGate branding in the UI itself.
   They're referenced only in `README.md` lines 59, 64, 69, 74, 79, 84.
   Plan is to replace them with fresh SpecBuddy screenshots (same
   filenames, so README needs no edits) — this has NOT been done yet.
3. `demo-ui/index.html` confirmed clean of ClarityGate branding.
4. No video files exist in the repo yet.
5. Technical files intentionally kept as-is (do not touch/rename):
   `linter/claritygate.py`, `src/linter/claritygate.py`,
   `specs/claritygate-mvp/`, `claritygate-report.md`.

## What's blocked and needs you to take over now

### 1. Git initialization + remote
```
cd "/Users/kmsum/Downloads/AI Tinkerers x Tencent Cloud Hackathon - Agent Development Challenge/SpecBuddy"
git init
git branch -m main
git remote add origin https://github.com/yahgoo/SpecBuddy.git
git remote -v
git ls-remote origin
```
Report `git ls-remote origin` output before doing anything else — if
`yahgoo/SpecBuddy` already has commits on GitHub, histories need to be
reconciled (fetch + rebase, or confirm it's genuinely empty) before any
push, rather than force-pushing over existing content.

### 2. First commit
Once the remote is confirmed, stage and commit everything **except**
build artifacts:
```
git status --short
git add -A
git commit -m "Initial commit: SpecBuddy"
```
Do not push yet — confirm with the user first.

### 3. Demo video creation (queued, separate task)
There is a full 8-step Codex CLI prompt sequence already prepared
(Steps 3a–3h) covering: preflight/server health checks, Playwright
screenshot capture (8 real-app scenes at 1440x900+), a source contact
sheet, HyperFrames composition (1920x1080, 8 scenes, ~75-90s), TTS
voiceover (Kokoro-82M `af_heart` preferred, silent+captions fallback if
unavailable), SRT captions, final MP4 render, and ffprobe + final
contact-sheet verification. Output targets:
`output/demo-artifacts/specbuddy-demo-final.mp4`
`output/demo-artifacts/specbuddy-demo-final.srt`

Hard constraints carried over: no screenshots under 1280x720, no
`.clip { opacity: 0 }` in HyperFrames CSS, no robotic TTS fallback, MP4
and SRT must share exact basename, no product code changes, no commits
without explicit user instruction.

## Ground rules for this handoff
- Do not modify product code unless required to start/smoke-test the app.
- Do not push or force-push without explicit user confirmation.
- Do not overwrite an existing remote history without confirming it's safe.
- Do not touch the 4 accepted `claritygate`-named technical files.
- Report back after git init/remote/ls-remote before proceeding further.
</content>