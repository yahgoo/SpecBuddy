# SpecBuddy Quality Report

## Scan Metadata

- Source: `tests_adversarial/briefs/04-extremely-long-lines.md`
- Scanned at: 2026-08-12T10:19:25+00:00
- Requirement lines: 2
- Verdict: **REFUSED**
- Agent Readiness Score: **40/100** (Rewrite Required)

## Summary

- Findings: 8
- Defects: 7
- Clarifications: 1
- Info: 0

## Findings

| Line | Check | Category | Severity | Type | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | EARS-IMPERATIVE | syntactical | defect | non_mandatory_imperative | 'must' weakens the requirement; mandatory requirements must use SHALL. | Rewrite the statement with 'THE System SHALL ...' and an observable outcome. |
| 5 | AMB-ADVERB | lexical | defect | unquantified_adverb | Adverb 'finally' should be replaced with a measurable criterion. | Replace the adverb with an observable threshold or acceptance test. |
| 5 | AMB-PASSIVE | syntactical | defect | passive_voice | Passive voice hides the actor responsible for the behavior. | Rewrite in active voice with an explicit actor: 'THE System SHALL ...'. |
| 5 | EARS-KEYWORD | syntactical | defect | lowercase_ears_keyword | EARS keywords must be UPPERCASE. Required keywords: WHEN, WHILE, WHERE, IF, THEN, SHALL. | Rewrite lowercase keywords as: WHEN, WHILE, WHERE, IF, THEN, SHALL. |
| 7 | AMB-ADVERB | lexical | defect | unquantified_adverb | Adverb 'continuously' should be replaced with a measurable criterion. | Replace the adverb with an observable threshold or acceptance test. |
| 7 | AMB-OBLIQUE | referential | defect | oblique_symbol | A slash combines alternatives or synonyms and creates referential ambiguity. | Choose one term or split the alternatives into separate requirements. |
| 7 | LEAK-IMPLEMENTATION | tacit | defect | implementation_leakage | Implementation term 'database' leaks design choices into requirements. | State the observable behavior without naming implementation technology. |
| 5 | COMP-HAPPY-PATH | completeness | clarification | missing_unwanted_behavior | Feature description contains nominal behavior but no Unwanted Behavior IF-THEN requirement. | Add an IF <failure condition>, THEN THE System SHALL <recovery action> requirement. |

## Clarification Queue

1. Line 5: Feature description contains nominal behavior but no Unwanted Behavior IF-THEN requirement. A) Keep as-is and accept coding-agent drift risk; B) Add an IF <failure condition>, THEN THE System SHALL <recovery action> requirement.
