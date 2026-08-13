STEP 3b (Screenshot capture — SpecBuddy demo video):

Backend confirmed running on http://127.0.0.1:8000 (200 on /docs).
Frontend confirmed running on http://127.0.0.1:5173 (200).
Playwright 1.62.1 with Chromium confirmed installed.

Do not modify product code except to smoke-test the app if absolutely
required.

1. Check if the SpecBuddy repo has an existing demo/fixture requirements
   file (search specs/, demo-ui/, data/samples/, tests_adversarial/ for
   something resembling a "rough requirements" sample — data/samples/
   already has several candidates like ambiguous-requirements.md). If
   an existing sample fits well, use it; otherwise create one at
   output/demo-artifacts/specbuddy-video/demo-input.md with this content:

   # Demo Requirements
   The system should support login quickly.
   The system shall handle user data.
   If needed, the system may notify users.
   THE System SHALL display the dashboard.

2. Write a Playwright script (headless Chromium, viewport 1440x900,
   full_page: false) that drives the REAL running SpecBuddy app at
   http://127.0.0.1:5173 through these 8 scenes, saving PNGs to
   output/demo-artifacts/specbuddy-video/assets/screenshots/:

   scene-01-empty-app.png       — app loaded before any input
   scene-02-demo-input.png      — demo requirements pasted into the app
   scene-03-refused-result.png  — after clicking Analyze; score/verdict/findings summary visible
   scene-04-mission-board.png   — Mission Board or progress panel visible
   scene-05-findings.png        — findings list with line numbers, check IDs, Apply fix buttons
   scene-06-after-apply-rewrite.png — after clicking one Apply fix; score/findings updated
   scene-07-accepted-rewrites.png   — Accepted Rewrites section visible
   scene-08-report-preview.png      — full Markdown report or export/report preview visible

   Hard rules:
   - Do NOT use small MCP/browser screenshots (e.g. ~394x425).
   - Every screenshot must be at least 1280x720; target 1440x900.
   - Interact with the real UI (paste text, click Analyze, scroll,
     click Apply fix, expand report) — no mocked/static HTML.

3. Run the script.

4. Verify every PNG's dimensions:
   for f in output/demo-artifacts/specbuddy-video/assets/screenshots/*.png; do
     python3 -c "from PIL import Image; im=Image.open('$f'); print('$f', im.size)"
   done

Stop conditions:
- Stop if any screenshot is below 1280x720.
- Stop if any screenshot is blank, cropped, or doesn't show real app UI.

Report: fixture file used/created, list of 8 screenshot paths with
exact dimensions, and confirmation each shows the real running app.
Do not touch the 7 deferred untracked files from earlier (README
screenshot replacement will be a separate, later step using scaled-down
crops of these same captures).
</content>