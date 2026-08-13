"""Reporter stage: emit Markdown quality reports and stdout summaries."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from .models import EvaluationResult, Finding, ReportResult, RequirementRecord


def write_report(
    source_path: str | Path,
    records: list[RequirementRecord],
    evaluation: EvaluationResult,
    out_path: str | Path = "specbuddy-report.md",
) -> ReportResult:
    """Write a human-readable Markdown Quality Report."""

    if len(records) > 20:
        print(f"Scanning {len(records)} requirement lines...", file=sys.stderr)

    destination = Path(out_path)
    markdown = render_report(source_path, records, evaluation)
    destination.write_text(markdown, encoding="utf-8")
    return ReportResult(path=destination, markdown=markdown)


def render_report(
    source_path: str | Path,
    records: list[RequirementRecord],
    evaluation: EvaluationResult,
) -> str:
    lines = [
        "# SpecBuddy Quality Report",
        "",
        "## Scan Metadata",
        "",
        f"- Source: `{source_path}`",
        f"- Scanned at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Requirement lines: {len(records)}",
        f"- Verdict: **{evaluation.verdict}**",
        f"- Agent Readiness Score: **{evaluation.score}/100** ({evaluation.tier})",
        "",
        "## Summary",
        "",
        f"- Findings: {len(evaluation.findings)}",
        f"- Defects: {evaluation.defects}",
        f"- Clarifications: {evaluation.clarifications}",
        f"- Info: {evaluation.infos}",
        "",
        "## Findings",
        "",
    ]

    if evaluation.findings:
        lines.extend(
            [
                "| Line | Check | Category | Severity | Type | Message | Suggestion |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for finding in evaluation.findings:
            lines.append(_finding_row(finding))
    else:
        lines.append("No findings. The spec is ready for coding-agent handoff.")

    clarifications = [finding for finding in evaluation.findings if finding.severity == "clarification"]
    lines.extend(["", "## Clarification Queue", ""])
    if clarifications:
        for index, finding in enumerate(clarifications, start=1):
            lines.append(
                f"{index}. Line {finding.line_number}: {finding.message} "
                f"A) Keep as-is and accept coding-agent drift risk; B) {finding.suggested_rewrite}"
            )
    else:
        lines.append("No clarification questions.")

    return "\n".join(lines) + "\n"


def print_summary(report: ReportResult, evaluation: EvaluationResult) -> None:
    """Print the required stdout scan summary."""

    print("SpecBuddy scan complete")
    print(f"Requirements scanned: {evaluation.requirement_count}")
    print(f"Findings: {len(evaluation.findings)}")
    print(f"Defects: {evaluation.defects}")
    print(f"Clarifications: {evaluation.clarifications}")
    print(f"Agent Readiness Score: {evaluation.score}/100 ({evaluation.tier})")
    print(f"Verdict: {evaluation.verdict}")
    print(f"Report: {report.path}")


def _finding_row(finding: Finding) -> str:
    values = (
        str(finding.line_number),
        finding.check_id,
        finding.category,
        finding.severity,
        finding.type,
        finding.message,
        finding.suggested_rewrite,
    )
    return "| " + " | ".join(_escape_cell(value) for value in values) + " |"


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
