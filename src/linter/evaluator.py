"""Evaluator stage: aggregate findings into readiness, tiers, and exit codes."""

from __future__ import annotations

from collections import Counter

from .models import EvaluationResult, Finding, RequirementRecord


REFUSAL_TYPES = {
    "lowercase_ears_keyword",
    "missing_ears_keyword",
    "ears_pattern_violation",
    "implementation_leakage",
    "singularity_violation",
}


def evaluate(records: list[RequirementRecord], findings: list[Finding]) -> EvaluationResult:
    """Compute an agent-readiness score and verdict from findings."""

    score = max(0, 100 - sum(_deduction(finding) for finding in findings))
    has_refusal = any(finding.type in REFUSAL_TYPES for finding in findings)
    verdict = "REFUSED" if has_refusal else "CERTIFIED"
    counts = Counter(finding.severity for finding in findings)

    return EvaluationResult(
        score=score,
        tier=_tier(score),
        verdict=verdict,
        exit_code=2 if has_refusal else 0,
        findings=tuple(findings),
        requirement_count=len(records),
        defects=counts["defect"],
        clarifications=counts["clarification"],
        infos=counts["info"],
    )


def _deduction(finding: Finding) -> int:
    if finding.severity == "defect":
        return 8
    if finding.severity == "clarification":
        return 4
    return 1


def _tier(score: int) -> str:
    if score >= 90:
        return "Agent Ready"
    if score >= 75:
        return "Needs Light Cleanup"
    if score >= 50:
        return "At Risk"
    return "Rewrite Required"
