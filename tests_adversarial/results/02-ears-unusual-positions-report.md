# SpecBuddy Quality Report

## Scan Metadata

- Source: `tests_adversarial/briefs/02-ears-unusual-positions.md`
- Scanned at: 2026-08-12T10:19:25+00:00
- Requirement lines: 10
- Verdict: **REFUSED**
- Agent Readiness Score: **60/100** (At Risk)

## Summary

- Findings: 5
- Defects: 5
- Clarifications: 0
- Info: 0

## Findings

| Line | Check | Category | Severity | Type | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | AMB-PASSIVE | syntactical | defect | passive_voice | Passive voice hides the actor responsible for the behavior. | Rewrite in active voice with an explicit actor: 'THE System SHALL ...'. |
| 6 | LEAK-IMPLEMENTATION | tacit | defect | implementation_leakage | Implementation term 'database' leaks design choices into requirements. | State the observable behavior without naming implementation technology. |
| 8 | AMB-PASSIVE | syntactical | defect | passive_voice | Passive voice hides the actor responsible for the behavior. | Rewrite in active voice with an explicit actor: 'THE System SHALL ...'. |
| 11 | AMB-PASSIVE | syntactical | defect | passive_voice | Passive voice hides the actor responsible for the behavior. | Rewrite in active voice with an explicit actor: 'THE System SHALL ...'. |
| 12 | AMB-ADVERB | lexical | defect | unquantified_adverb | Adverb 'immediately' should be replaced with a measurable criterion. | Replace the adverb with an observable threshold or acceptance test. |

## Clarification Queue

No clarification questions.
