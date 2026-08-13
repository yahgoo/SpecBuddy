# SpecBuddy Quality Report

## Scan Metadata

- Source: `tests_adversarial/briefs/10-regex-adversarial-patterns.md`
- Scanned at: 2026-08-12T10:19:26+00:00
- Requirement lines: 10
- Verdict: **REFUSED**
- Agent Readiness Score: **52/100** (At Risk)

## Summary

- Findings: 6
- Defects: 6
- Clarifications: 0
- Info: 0

## Findings

| Line | Check | Category | Severity | Type | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | AMB-PASSIVE | syntactical | defect | passive_voice | Passive voice hides the actor responsible for the behavior. | Rewrite in active voice with an explicit actor: 'THE System SHALL ...'. |
| 10 | AMB-ADVERB | lexical | defect | unquantified_adverb | Adverb 'exactly' should be replaced with a measurable criterion. | Replace the adverb with an observable threshold or acceptance test. |
| 11 | AMB-VAGUE-VERB | lexical | defect | vague_verb | Vague verb 'handle' has no observable output. | Replace it with a measurable behavior, e.g. 'THE System SHALL display the order status within 2 seconds.' |
| 11 | AMB-ADVERB | lexical | defect | unquantified_adverb | Adverb 'exactly' should be replaced with a measurable criterion. | Replace the adverb with an observable threshold or acceptance test. |
| 11 | EARS-KEYWORD | syntactical | defect | lowercase_ears_keyword | EARS keywords must be UPPERCASE. Required keywords: WHEN, WHILE, WHERE, IF, THEN, SHALL. | Rewrite lowercase keywords as: WHEN, WHILE, WHERE, IF, THEN, SHALL. |
| 13 | AMB-VAGUE-VERB | lexical | defect | vague_verb | Vague verb 'support' has no observable output. | Replace it with a measurable behavior, e.g. 'THE System SHALL display the order status within 2 seconds.' |

## Clarification Queue

No clarification questions.
