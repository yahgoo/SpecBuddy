# SpecBuddy Quality Report

## Scan Metadata

- Source: `tests_adversarial/briefs/05-unicode-multilingual.md`
- Scanned at: 2026-08-12T10:19:25+00:00
- Requirement lines: 10
- Verdict: **CERTIFIED**
- Agent Readiness Score: **84/100** (Needs Light Cleanup)

## Summary

- Findings: 2
- Defects: 2
- Clarifications: 0
- Info: 0

## Findings

| Line | Check | Category | Severity | Type | Message | Suggestion |
| --- | --- | --- | --- | --- | --- | --- |
| 6 | AMB-VAGUE-VERB | lexical | defect | vague_verb | Vague verb 'support' has no observable output. | Replace it with a measurable behavior, e.g. 'THE System SHALL display the order status within 2 seconds.' |
| 8 | AMB-ADVERB | lexical | defect | unquantified_adverb | Adverb 'correctly' should be replaced with a measurable criterion. | Replace the adverb with an observable threshold or acceptance test. |

## Clarification Queue

No clarification questions.
