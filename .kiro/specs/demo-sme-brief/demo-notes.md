# Demo Notes — Ah Huat Nasi Lemak Online Ordering

## (a) Clarify-Loop Demo Candidates

These 3 findings are designed for the AI Clarification feature's bounded A/B
question format. Each has a genuinely vague term with two clear, mutually
exclusive interpretations.

### Candidate 1 — Line 9: "Orders should be confirmed via notification"

**Ambiguity:** "notification" — what channel?

- **Option A:** SMS notification (sent to the customer's registered mobile number)
- **Option B:** In-app push notification (sent via the PWA / mobile app)

**Why it's good for demo:** Singapore hawkers have customers who range from
elderly SMS-only users to younger app-savvy ones. Both options are plausible and
the business must decide.

---

### Candidate 2 — Line 19: "orders cancelled if unpaid"

**Ambiguity:** "cancelled if unpaid" — when exactly?

- **Option A:** Auto-cancel immediately if PayNow payment is not received within
  60 seconds of QR code generation
- **Option B:** Hold the order for a 10-minute grace period, then auto-cancel
  (allowing customers to retry payment)

**Why it's good for demo:** Real hawker systems face this tradeoff — aggressive
cancellation keeps queues fast but frustrates customers with slow phones;
generous grace periods risk ghost orders blocking the queue during peak lunch.

---

### Candidate 3 — Line 13: "delivery within a reasonable radius"

**Ambiguity:** "reasonable radius" — what's the boundary?

- **Option A:** Fixed 3 km radius from the stall's registered address
- **Option B:** Dynamic radius based on postal code district (e.g. same
  2-digit postal sector only — covers the HDB estate and adjacent blocks)

**Why it's good for demo:** "Reasonable" is subjective and the business needs to
commit to a rule the system can enforce programmatically.

---

## (b) Expected Finding-Category Breakdown

| Category | Expected Count | Key Check IDs |
|----------|---------------|---------------|
| Syntactical (EARS) | ~40–45 | EARS-IMPERATIVE, EARS-MISSING, EARS-KEYWORD, EARS-PATTERN |
| Lexical | ~25–30 | AMB-VAGUE-VERB, AMB-VAGUE-ADJ, AMB-ADVERB, AMB-ESCAPE |
| Syntactical (passive) | ~7–8 | AMB-PASSIVE |
| Referential | ~4–5 | AMB-OBLIQUE, AMB-PRONOUN |
| Tacit | ~4–5 | TACIT-UNREC, LEAK-IMPLEMENTATION |
| Completeness | 1 | COMP-HAPPY-PATH |

**Actual first-run result:** 85 findings, 81 defects, 4 clarifications, score
0/100, verdict REFUSED.

---

## (c) Suggested Demo Narration Beats (3–5 minutes)

### Beat 1: The Problem (30s)
"Here's a real-world spec — a Singapore hawker stall wants online ordering.
A junior PM wrote this first draft. It looks reasonable, covers menu, payment,
delivery. Let's see what SpecBuddy thinks."

### Beat 2: Show REFUSED (45s)
Paste the requirements into SpecBuddy. Show the immediate result:
- Score: 0/100
- Verdict: REFUSED
- 85 findings across 23 requirement lines

"The coding agent would build *something* from this, but we'd have no idea if
it matches what Ah Huat actually needs. SpecBuddy catches the ambiguity before
code is written."

### Beat 3: Category Breakdown (30s)
Show the finding categories: EARS violations (no testable structure), vague
verbs and adjectives (handle, manage, fast, appropriate), passive voice (hides
who is responsible), implementation leakage (frontend, backend, API).

### Beat 4: Clarify 2–3 Findings (90s)
Walk through the Clarify feature on:
1. **"notification"** → pick SMS vs push → watch the rewrite suggestion update
2. **"cancelled if unpaid"** → pick grace period vs immediate → show the
   clarified requirement with an explicit timeout
3. **"reasonable radius"** → pick fixed 3km vs postal sector → requirement now
   has a testable boundary

"Each clarification turns a vague intent into something a coding agent can
implement deterministically."

### Beat 5: Apply Fixes & Rescore (45s)
Apply the deterministic rewrites suggested by SpecBuddy (EARS patterns, remove
vague adjectives, explicit actors). Rescore live — show the score climbing
toward CERTIFIED.

### Beat 6: Show CERTIFIED (30s)
After fixes and clarifications, show:
- Score: 85+ /100
- Verdict: CERTIFIED
- Remaining findings are advisory only

### Beat 7: Export Handoff Pack (30s)
Export the Markdown report. Show it contains:
- Original vs. rewritten requirements
- Audit trail of which findings were resolved
- Clarification decisions recorded

"This is what CodeBuddy or any coding agent receives. Clear specs in → better
software out."

### Beat 8: Evidence Panel (15s)
Show the evidence panel with timestamps and decision log. "Every clarification
is traceable — the PM, the stall owner, and the developer can all see why the
spec says what it says."

---

## File Locations

- **Requirements brief:** `.kiro/specs/demo-sme-brief/requirements.md`
- **This notes file:** `.kiro/specs/demo-sme-brief/demo-notes.md`
- **Linter report output:** run `python3 -m linter.claritygate .kiro/specs/demo-sme-brief/requirements.md --out /tmp/specbuddy-demo-report.md`
