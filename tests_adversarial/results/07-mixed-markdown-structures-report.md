# SpecBuddy Quality Report

## Scan Metadata

- Source: `tests_adversarial/briefs/07-mixed-markdown-structures.md`
- Scanned at: 2026-08-12T10:19:26+00:00
- Requirement lines: 9
- Verdict: **REFUSED**
- Agent Readiness Score: **44/100** (Rewrite Required)

## Summary

- Findings: 7
- Defects: 7
- Clarifications: 0
- Info: 0

## Findings

| Line | Check | Category | Severity | Type | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | --- |
| 13 | AMB-PASSIVE | syntactical | defect | passive_voice | Passive voice hides the actor responsible for the behavior. | Rewrite in active voice with an explicit actor: 'THE System SHALL ...'. |
| 13 | LEAK-IMPLEMENTATION | tacit | defect | implementation_leakage | Implementation term 'http' leaks design choices into requirements. | State the observable behavior without naming implementation technology. |
| 19 | EARS-PATTERN | syntactical | defect | ears_pattern_violation | Requirement does not match one of the six accepted EARS patterns. | Use 'THE System SHALL ...', 'WHEN ... THE System SHALL ...', or another canonical EARS pattern. |
| 33 | AMB-PASSIVE | syntactical | defect | passive_voice | Passive voice hides the actor responsible for the behavior. | Rewrite in active voice with an explicit actor: 'THE System SHALL ...'. |
| 47 | AMB-VAGUE-VERB | lexical | defect | vague_verb | Vague verb 'support' has no observable output. | Replace it with a measurable behavior, e.g. 'THE System SHALL display the order status within 2 seconds.' |
| 47 | EARS-PATTERN | syntactical | defect | ears_pattern_violation | Requirement does not match one of the six accepted EARS patterns. | Use 'THE System SHALL ...', 'WHEN ... THE System SHALL ...', or another canonical EARS pattern. |
| 55 | AMB-VAGUE-VERB | lexical | defect | vague_verb | Vague verb 'handle' has no observable output. | Replace it with a measurable behavior, e.g. 'THE System SHALL display the order status within 2 seconds.' |

## Clarification Queue

No clarification questions.
