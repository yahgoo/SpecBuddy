---
name: specbuddy-demo-video
description: Create or update SpecBuddy demo videos with real app screenshots, HyperFrames compositions, per-scene Kokoro voiceover, scene-aligned SRT captions, MP4 rendering, ffprobe checks, and contact-sheet visual QA. Use when preparing hackathon/demo video assets, refreshing screenshots, adding voiceover, diagnosing HyperFrames output, or verifying final SpecBuddy demo media.
---

# SpecBuddy Demo Video

## Overview

Use this skill to produce demo-grade SpecBuddy videos from the real running app. Keep product code unchanged unless the user explicitly asks for product changes; demo work belongs under `output/demo-artifacts/` or another user-approved artifact path.

For HyperFrames commands, also load the `hyperframes`, `hyperframes-core`, `hyperframes-cli`, and `media-use` skills. For voiceover, read `references/kokoro-hyperframes.md`.

## Required Gates

Stop and report before continuing when any gate fails:

- The screenshot shows a blank page, error page, loading spinner, or mocked/static UI.
- A source or verification screenshot is below 1280x720.
- HyperFrames `check` reports lint/runtime/layout/motion/contrast errors.
- Kokoro TTS is unavailable or produces silence; do not use macOS robotic voices.
- Any voice WAV runs longer than its scene duration minus 1.5 seconds.
- The rendered MP4 has no audio stream when voiceover was requested.
- The final contact sheet contains blank, broken, cropped, or wrong-app frames.

## Workflow

1. Confirm scope and state:
   - Check git status and avoid committing/pushing unless explicitly asked.
   - Confirm backend/frontend startup commands from repo docs or package files.
   - Start the real app only when screenshots or UI smoke tests require it.
   - Health-check backend and frontend before browser automation.

2. Capture real app screenshots:
   - Use Playwright with Chromium, normally viewport 1440x900.
   - Interact with the real UI: paste requirements, click Analyze, apply one rewrite, scroll to findings, accepted rewrites, and report/export views.
   - Save source screenshots under `output/demo-artifacts/specbuddy-video/assets/screenshots/`.
   - Verify each screenshot's exact dimensions and visually inspect at least one contact sheet.

3. Build or update the HyperFrames composition:
   - Use screenshots inside a browser frame; the app UI remains the hero.
   - Keep resolution 1920x1080.
   - Use subtle zoom/pan toward the important UI region for each scene.
   - Use concise lower-thirds that do not cover important product UI.
   - Never set a static `.clip { opacity: 0 }`; if fading is needed, use timeline/keyframed opacity while clips remain visible over their active range.
   - Declare seek-safe animation with one paused timeline and, when possible, an `index.motion.json` sidecar.

4. Generate voiceover one scene at a time:
   - Do not synthesize one full-length narration file for the full video; it can compress timing and drift against captions.
   - Write one text file per scene and generate one WAV per scene with Kokoro `af_heart`, speed about `0.95`.
   - Measure each WAV with `ffprobe`.
   - Mount each WAV as a separate `<audio>` element with `data-start = scene start + 1s` and `data-duration = measured duration`.
   - Use a dedicated audio track index that does not overlap visual clips.

5. Generate SRT captions:
   - Use the exact voiceover line per scene.
   - Match each caption start and end to the WAV start and measured duration.
   - Save the SRT next to the MP4 with the same basename.

6. Validate and render:
   - Run `npx hyperframes check` from the composition directory and fix blocking findings.
   - Render with pinned project scripts or the same HyperFrames version already used in the project.
   - Verify MP4 streams with `ffprobe`; require video dimensions, duration, and audio codec when voiceover is expected.

7. Final visual QA:
   - Extract one rendered frame per scene from the final MP4.
   - Build a labeled final contact sheet from those extracted frames.
   - Inspect the contact sheet before declaring complete.
   - Report output paths, durations, stream metadata, check result, and visual assessment.

## Scene Pattern

For the main SpecBuddy walkthrough, this structure works well:

| Scene | Focus | Typical duration |
| --- | --- | --- |
| 1 | Empty/import state | 8s |
| 2 | Rough requirements pasted | 10s |
| 3 | REFUSED score and findings summary | 12s |
| 4 | Mission Board or evidence/readiness panel | 12s |
| 5 | Findings list with line numbers and actions | 13s |
| 6 | Score/findings after applying one rewrite | 13s |
| 7 | Accepted rewrites or export controls | 10s |
| 8 | Markdown report or handoff pack preview | 12s |

Adapt scene labels to the actual product state. Keep source screenshots real; do not recreate the UI as motion graphics.

## Reporting Format

Finish with:

- Final MP4 path and SRT path.
- HyperFrames check result.
- WAV durations and whether any scene timing changed.
- `ffprobe` video/audio metadata.
- Contact sheet path and visual assessment.
- Any skipped step, blocker, or non-product artifact created.
