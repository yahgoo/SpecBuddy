# SpecBuddy Quality Report

## Scan Metadata

- Source: `tests_adversarial/briefs/06-malformed-ears-syntax.md`
- Scanned at: 2026-08-12T10:19:26+00:00
- Requirement lines: 12
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
| 6 | EARS-PATTERN | syntactical | defect | ears_pattern_violation | Requirement does not match one of the six accepted EARS patterns. | Use 'THE System SHALL ...', 'WHEN ... THE System SHALL ...', or another canonical EARS pattern. |
| 9 | EARS-PATTERN | syntactical | defect | ears_pattern_violation | Requirement does not match one of the six accepted EARS patterns. | Use 'THE System SHALL ...', 'WHEN ... THE System SHALL ...', or another canonical EARS pattern. |
| 10 | EARS-SINGULAR | syntactical | defect | singularity_violation | Requirement contains more than one SHALL statement. | Split the behavior into one requirement per SHALL for traceability. |
| 11 | EARS-PATTERN | syntactical | defect | ears_pattern_violation | Requirement does not match one of the six accepted EARS patterns. | Use 'THE System SHALL ...', 'WHEN ... THE System SHALL ...', or another canonical EARS pattern. |
| 14 | EARS-SINGULAR | syntactical | defect | singularity_violation | Requirement contains more than one SHALL statement. | Split the behavior into one requirement per SHALL for traceability. |
| 14 | EARS-PATTERN | syntactical | defect | ears_pattern_violation | Requirement does not match one of the six accepted EARS patterns. | Use 'THE System SHALL ...', 'WHEN ... THE System SHALL ...', or another canonical EARS pattern. |

## Clarification Queue

No clarification questions.
