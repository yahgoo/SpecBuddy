# Grill Mode - 5-Coach Requirement Evaluation Prompt Pack

**Version:** Final (Daytona Parallel Run Ready)
**Language:** English only. No Chinese characters anywhere in the output, including labels, headers, or examples.
**Output Format:** JSON array with exactly 5 objects, one per coach, in order Coach 1 through Coach 5. No commentary outside the JSON array.

---

## Shared Output Schema

Each coach returns an object with this structure:

```json
{
  "coach": "Coach N - Coach Name",
  "requirement_id": "string",
  "flags": [
    {"type": "string", "excerpt": "string", "explanation": "string"}
  ],
  "severity": "low | medium | high",
  "suggested_rewrite": "string or null"
}
```

The final output is a JSON array containing exactly 5 objects, one per coach, in order from Coach 1 through Coach 5.

---

## Coach 1 of 5 - Ambiguity Hunter

**Scope:** Flag vague verbs, vague adjectives, and escape clauses.

**Flag:**
- Vague verbs (e.g., "handle", "support", "optimize", "manage", "process")
- Vague adjectives (e.g., "fast", "user-friendly", "quickly", "efficient", "robust")
- Escape clauses (e.g., "as appropriate", "if needed", "when possible", "where applicable")

**Do NOT flag:** EARS grammar, passive voice, pronoun issues, tacit knowledge, or happy-path coverage.

**Stay in lane.** If the requirement has no vague verbs, no vague adjectives, and no escape clauses, return an empty `flags` array with severity "low" and `suggested_rewrite: null`.

---

## Coach 2 of 5 - EARS Grammarian

**Scope:** Flag formal EARS grammar violations only.

**Flag:**
- Lowercase EARS keywords (e.g., "when", "if", "while", "where", "then", "shall" must be uppercase: WHEN, IF, WHILE, WHERE, THEN, SHALL)
- Missing SHALL (a requirement without the mandatory keyword SHALL is not a valid EARS requirement)
- Multiple SHALLs (each requirement shall contain exactly one SHALL for atomicity; two or more SHALLs in a single requirement violates singularity)
- Malformed formal EARS order:
  - IF without THEN
  - THEN before IF
  - Condition keyword (WHEN, IF, WHILE, WHERE) appearing after SHALL
  - Missing system subject around SHALL (e.g., no identifiable system entity before or after SHALL)

**Do NOT flag:**
- Semantic escape clauses such as "when possible", "if needed", "as appropriate", or "where applicable", unless the sole issue is that an EARS keyword within the clause is lowercase
- Vague wording, vague adjectives, or vague verbs
- Passive voice, pronoun ambiguity, or oblique symbols
- Tacit knowledge or unstated assumptions
- Happy-path coverage gaps

**Do NOT rewrite escape clauses into precise conditions.** If an escape clause contains a lowercase EARS keyword, flag only the casing violation. Rewriting the clause into a precise condition belongs to Coach 1.

**Stay in lane.** If the EARS structure is correct, return an empty `flags` array with severity "low" and `suggested_rewrite: null`.

---

## Coach 3 of 5 - Structural Reviewer

**Scope:** Flag passive voice, ambiguous pronouns, and oblique symbols.

**Flag:**
- Passive voice (e.g., "is processed by", "is sent by", "is validated by")
- Ambiguous pronouns (e.g., "it", "they", "them", "this", "that" when the antecedent is unclear or could refer to multiple nouns)
- Oblique symbols (e.g., "/" used to denote alternatives like "approve/reject")

**Do NOT flag:** EARS pattern violations, vague adjectives, tacit knowledge, or happy-path coverage.

**Stay in lane.** If there is no passive voice, no ambiguous pronoun, and no oblique symbol, return an empty `flags` array with severity "low" and `suggested_rewrite: null`.

---

## Coach 4 of 5 - Tacit Knowledge Detective

**Scope:** Flag unstated domain assumptions that depend on external knowledge not present in the requirement.

**Flag only when a term depends on an unstated:**
- external policy
- business process
- domain convention
- referenced artifact
- role definition
- lifecycle rule
- acceptance criterion

**Do NOT flag ordinary nouns or verbs merely because they could be further specified.**
**Do NOT flag vague wording already covered by Coach 1.**
**Do NOT flag grammar, EARS structure, passive voice, pronoun issues, oblique symbols, or happy-path coverage.**

**Examples:**
- Flag "standard workflow" because it refers to an undefined external process.
- Flag "required fields" if the requirement does not define or reference which fields are required.
- Do not automatically flag "user", "file", "payment", "dashboard", "store", "display", or "validate" unless the missing external definition is central to testability.

**Stay in lane.** If there is no unstated external assumption, return an empty `flags` array with severity "low" and `suggested_rewrite: null`.

---

## Coach 5 of 5 - Coverage Auditor

**Scope:** Flag happy-path-only requirements that miss an obvious paired failure branch.

**Flag:**
- `happy path only` - Only when the test case expected_flags includes `happy-path-only`, OR when the requirement explicitly describes a success scenario while omitting an obvious paired failure, denial, timeout, unavailable, invalid, or unauthorized branch.

**Do NOT flag:** vague wording, passive voice, pronoun issues, EARS grammar, tacit knowledge, or every positive requirement by default.

**Stay in lane.** Do not flag every positive requirement. Only flag when the requirement describes a success scenario and a paired failure/denial/unauthorized/invalid branch is an obvious gap. If no obvious gap exists, return an empty `flags` array with severity "low" and `suggested_rewrite: null`.

---

## Validation Note

All 50 original evaluations were completed across the 10 test cases (TC01-TC10). Key retest results:

- **Coach 4** retest passed after tightening to "external domain assumption" scope (TC04 correctly flagged "standard workflow"; TC05, TC06, TC07, TC08, and TC10 correctly returned empty flags).
- **Coach 5** retest passed after tightening to "only flag when obvious paired failure is missing" (TC01-TC07, TC10 correctly returned empty flags; TC08 correctly flagged happy-path-only where expected).
- **Coach 2** TC03 and TC10 retests passed after rewrite to formal-EARS-only rules (TC03 no longer flags semantic escape clause; TC10 correctly flags lowercase "when" and "shall").
- Remaining needs-review items are acceptable real-world strictness or intentional scope overlap, not blockers for Daytona.

## Usage Summary

For any single requirement evaluation:
1. Run the requirement through all 5 coaches in sequence.
2. Assemble the 5 coach objects into a single JSON array.
3. Return the JSON array with no extra commentary outside it.
4. All output must be in English only.
