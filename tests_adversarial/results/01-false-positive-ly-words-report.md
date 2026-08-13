# SpecBuddy Quality Report

## Scan Metadata

- Source: `tests_adversarial/briefs/01-false-positive-ly-words.md`
- Scanned at: 2026-08-12T10:19:25+00:00
- Requirement lines: 15
- Verdict: **CERTIFIED**
- Agent Readiness Score: **64/100** (At Risk)

## Summary

- Findings: 5
- Defects: 4
- Clarifications: 1
- Info: 0

## Findings

| Line | Check | Category | Severity | Type | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | --- |
| 7 | AMB-PASSIVE | syntactical | defect | passive_voice | Passive voice hides the actor responsible for the behavior. | Rewrite in active voice with an explicit actor: 'THE System SHALL ...'. |
| 11 | AMB-VAGUE-VERB | lexical | defect | vague_verb | Vague verb 'support' has no observable output. | Replace it with a measurable behavior, e.g. 'THE System SHALL display the order status within 2 seconds.' |
| 15 | AMB-ADVERB | lexical | defect | unquantified_adverb | Adverb 'automatically' should be replaced with a measurable criterion. | Replace the adverb with an observable threshold or acceptance test. |
| 15 | AMB-PASSIVE | syntactical | defect | passive_voice | Passive voice hides the actor responsible for the behavior. | Rewrite in active voice with an explicit actor: 'THE System SHALL ...'. |
| 5 | COMP-HAPPY-PATH | completeness | clarification | missing_unwanted_behavior | Feature description contains nominal behavior but no Unwanted Behavior IF-THEN requirement. | Add an IF <failure condition>, THEN THE System SHALL <recovery action> requirement. |

## Clarification Queue

1. Line 5: Feature description contains nominal behavior but no Unwanted Behavior IF-THEN requirement. A) Keep as-is and accept coding-agent drift risk; B) Add an IF <failure condition>, THEN THE System SHALL <recovery action> requirement.
