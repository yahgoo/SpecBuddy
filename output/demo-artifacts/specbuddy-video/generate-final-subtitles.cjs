const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const enPath = path.join(root, 'specbuddy-demo-final.srt');

const cues = [
  { start: 0, end: 1.687, en: ['"Just add PayNow."'] },
  { start: 1.687, end: 5.93, en: ['That was a real hawker-stall', 'requirements brief.'] },
  { start: 5.93, end: 7.704, en: ['A coding agent will build it'] },
  { start: 7.704, end: 10.453, en: ['and guess what happens', 'when payment fails.'] },

  { start: 12, end: 16.66, en: ['SpecBuddy is the quality gate', 'before your coding agent.'] },
  { start: 16.66, end: 17.733, en: ['It scores.'] },
  { start: 17.733, end: 19.626, en: ['It refuses ambiguity.'] },
  { start: 19.626, end: 21.706, en: ['Only the deterministic linter'] },
  { start: 21.706, end: 24.672, en: ['decides when a spec is ready.'] },

  { start: 26, end: 28.11, en: ['Four layers, one invariant.'] },
  { start: 28.11, end: 31.111, en: ['A React frontend for review', 'and clarification.'] },
  { start: 31.111, end: 35.585, en: ['A FastAPI and SQLite backend', 'for transactional rewrites.'] },
  { start: 35.585, end: 39.962, en: ['A deterministic Python linter', 'enforces EARS and scores.'] },
  { start: 39.962, end: 42.11, en: ['Only the linter can certify.'] },
  { start: 42.11, end: 44.443, en: ['The AI layer only proposes:'] },
  { start: 44.443, end: 48.333, en: ['exactly two mutually exclusive', 'rewrites, never a verdict.'] },
  { start: 48.333, end: 52.355, en: ['That separation is', 'the core architecture.'] },
  { start: 52.355, end: 56.485, en: ['People review tradeoffs;', 'AI drafts bounded options.'] },
  { start: 56.485, end: 58.363, en: ['SpecBuddy gives', 'the final yes or no.'] },

  { start: 60, end: 65.077, en: ['SpecBuddy catches weak requirements', 'before a coding agent starts building.'] },
  { start: 68, end: 74.293, en: ['Here is a real heartland brief,', 'written like clients really write.'] },
  { start: 78, end: 83.277, en: ['SpecBuddy refuses it immediately:', 'score zero, twenty-two findings.'] },
  { start: 83.277, end: 87.024, en: ['It flags PayNow retry gaps', 'and missing PDPA consent.'] },
  { start: 90, end: 94.885, en: ['The Mission Board turns issues', 'into a visible checklist.'] },
  { start: 102, end: 107.461, en: ['Each finding has an exact line,', 'plus a fix or question.'] },
  { start: 115, end: 119.949, en: ['Apply one fix and one answer;', 'the findings count drops.'] },
  { start: 128, end: 133.163, en: ['Accepted rewrites stay visible', 'and reversible.'] },
  { start: 138, end: 142.267, en: ['Resolve the rest, and the spec', 'reaches CERTIFIED state.'] },
  { start: 150, end: 154.949, en: ['One hundred out of one hundred:', 'CERTIFIED for agent handoff.'] },

  { start: 160, end: 162.398, en: ['This is not marketing.', 'It is measured.'] },
  { start: 162.398, end: 165.425, en: ['Twenty-one adversarial', 'benchmark cases.'] },
  { start: 165.425, end: 168.24, en: ['Ten hostile briefs tested.', 'Zero crashes.'] },
  { start: 168.24, end: 171.373, en: ['False positives dropped', 'from sixteen down to one.'] },
  { start: 171.373, end: 172.587, en: ['Zero regressions.'] },

  { start: 174, end: 177.06, en: ['We built SpecBuddy using', 'a spec-driven workflow.'] },
  { start: 177.06, end: 182.34, en: ['Every new feature started', 'as a requirements document.'] },
  { start: 182.34, end: 185.108, en: ['We ran each one through', 'SpecBuddy until it certified.'] },
  { start: 185.108, end: 189.927, en: ['The Clarify interaction', 'came from a certified spec.'] },
  { start: 189.927, end: 193.934, en: ['Tencent CodeBuddy implemented', 'the reserved frontend slice.'] },
  { start: 193.934, end: 197.109, en: ['The rule was explicit:', 'AI proposes.'] },
  { start: 197.109, end: 202.817, en: ['Only the deterministic linter', 'certifies.'] },
  { start: 202.817, end: 207.123, en: ['The practical lesson:', 'make the handoff measurable.'] },
  { start: 207.123, end: 211.549, en: ['Review means changed files,', 'tests, and the gate.'] },
  { start: 211.549, end: 215.728, en: ['Accepted rewrites stay visible', 'for human review.'] },

  { start: 217, end: 219.299, en: ['Built for Singapore agencies'] },
  { start: 219.299, end: 222.412, en: ['and SMEs commissioning', 'agent-built software.'] },
  { start: 222.412, end: 225.886, en: ['Also for BAs and PMs', 'writing their briefs.'] },
  { start: 225.886, end: 228.598, en: ['As a per-seat gate', 'with CI integration,'] },
  { start: 228.598, end: 233.123, en: ['deterministic verdicts are', 'what a CI pipeline can trust.'] },
  { start: 233.123, end: 235.448, en: ['The buyer does not need', 'another chatbot.'] },
  { start: 235.448, end: 237.907, en: ['They need an auditable', 'checkpoint before build.'] },

  { start: 239, end: 239.904, en: ['Next:'] },
  { start: 239.904, end: 242.761, en: ['specs directly from docs', 'and meeting notes,'] },
  { start: 242.761, end: 244.433, en: ['a CI gate mode,'] },
  { start: 244.433, end: 248.35, en: ['expanded rule packs for', 'PDPA and payments.'] },
  { start: 248.35, end: 251.928, en: ['SpecBuddy moves into', 'daily delivery.'] },

  { start: 253, end: 254.523, en: ['Same coding agent.'] },
  { start: 254.523, end: 255.631, en: ['Clearer specs in.'] },
  { start: 255.631, end: 256.951, en: ['Better software out.'] },
  { start: 256.951, end: 257.779, en: ['SpecBuddy.'] },
];

function timestamp(seconds) {
  const ms = Math.round(seconds * 1000);
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  const r = ms % 1000;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(r).padStart(3, '0')}`;
}

function validate() {
  const failures = [];
  cues.forEach((cue, index) => {
    const duration = cue.end - cue.start;
    if (cue.en.length > 2) failures.push(`cue ${index + 1}: ${cue.en.length} lines`);
    if (duration > 7) failures.push(`cue ${index + 1}: duration ${duration.toFixed(3)}s`);
    cue.en.forEach((line, lineIndex) => {
      if ([...line].length > 42) failures.push(`cue ${index + 1}: line ${lineIndex + 1} length ${[...line].length}`);
    });
  });
  return failures;
}

const failures = validate();
if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}

const body = cues.map((cue, index) => {
  return `${index + 1}\n${timestamp(cue.start)} --> ${timestamp(cue.end)}\n${cue.en.join('\n')}\n`;
}).join('\n');

fs.writeFileSync(enPath, body);
console.log(`wrote ${enPath}`);
console.log(`cue_count=${cues.length}`);
