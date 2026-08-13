"""Linter adapter: wraps the frozen src.linter pipeline for the backend.

All linter behavior is imported from src.linter.* — never reimplemented.
Scores, tiers, and verdicts are derived fresh on every call by invoking the
frozen evaluator.  They are never persisted in the database.

Transaction ownership: public functions in this module own the transaction
boundary (commit on success, rollback on failure).  The database helper
functions they call never commit or roll back independently.
"""

from __future__ import annotations

import re as _re
import sqlite3
from datetime import datetime, timezone
from typing import Any

from src.linter.evaluator import evaluate
from src.linter.models import EvaluationResult, Finding, RequirementRecord
from src.linter.parser import parse_requirements
from src.linter.reporter import render_report
from src.linter.rule_engine import run_checks

from backend.database import (
    delete_all_rewrites,
    delete_rewrite,
    get_rewrites,
    get_spec,
    insert_spec,
    replace_findings,
    replace_requirements,
    upsert_rewrite,
)

# ---------------------------------------------------------------------------
# Clarify helpers
# ---------------------------------------------------------------------------


def _clarify_option_a(check_id: str, effective_line: str, suggested_rewrite: str) -> tuple[str, str]:
    """Return (rewritten_text, rationale) for option A (minimal targeted fix)."""
    if suggested_rewrite:
        return suggested_rewrite, "Applies the targeted rewrite suggested by the linter."
    return effective_line, "No change — already conforms to this rule."


def _clarify_option_b(check_id: str, effective_line: str, suggested_rewrite: str) -> tuple[str, str]:
    """Return (rewritten_text, rationale) for option B (EARS pattern rewrite)."""
    stmt = effective_line.strip()
    # Strip leading Markdown bullet/numbering
    stmt_clean = _re.sub(r"^[-*\d]+[.)]\s*", "", stmt).strip()

    if check_id in ("EARS-MISSING", "EARS-PATTERN", "EARS-IMPERATIVE"):
        text = f"WHEN <trigger>, THE System SHALL {stmt_clean.rstrip('.')}."
        return text, "Rewrites using the canonical WHEN/SHALL EARS pattern with an explicit trigger."

    if check_id == "EARS-SINGULAR":
        text = f"THE System SHALL {stmt_clean.rstrip('.')}."
        return text, "Extracts the first behavior as a standalone, singular SHALL requirement."

    if check_id in ("AMB-VAGUE-VERB", "AMB-VAGUE-ADJ", "AMB-ADVERB"):
        text = f"THE System SHALL {stmt_clean.rstrip('.')} within [measurable threshold]."
        return text, "Anchors the requirement to a measurable, observable threshold."

    if check_id == "AMB-PASSIVE":
        text = f"THE System SHALL [explicit action on] {stmt_clean.rstrip('.')}."
        return text, "Converts to active voice with THE System as the explicit actor."

    if check_id == "AMB-PRONOUN":
        text = f"THE System SHALL [action on] [explicit noun]."
        return text, "Replaces the ambiguous pronoun with an explicit named actor or object."

    if check_id == "AMB-ESCAPE":
        text = f"THE System SHALL {stmt_clean.rstrip('.')} under [specific condition]."
        return text, "Replaces the escape clause with a concrete, testable condition."

    if check_id == "AMB-OBLIQUE":
        text = f"THE System SHALL {_re.sub(r'[A-Za-z]+/[A-Za-z]+', '[chosen term]', stmt_clean).rstrip('.')}."
        return text, "Eliminates the slash ambiguity by selecting one explicit term."

    if check_id == "EARS-KEYWORD":
        text = _re.sub(
            r"\b(when|while|where|if|then|shall)\b",
            lambda m: m.group(0).upper(),
            stmt_clean,
            flags=_re.IGNORECASE,
        )
        return text, "Uppercases all EARS keywords to meet the keyword-casing rule."

    if check_id == "LEAK-IMPLEMENTATION":
        text = f"THE System SHALL {stmt_clean.rstrip('.')} without specifying implementation technology."
        return text, "Removes implementation details and focuses on observable behavior."

    if check_id == "TACIT-UNREC":
        text = f"THE System SHALL {stmt_clean.rstrip('.')} [explicit assumption stated here]."
        return text, "Makes the assumed domain knowledge explicit and verifiable."

    if check_id == "COMP-HAPPY-PATH":
        text = f"IF <failure condition>, THEN THE System SHALL <recovery action>."
        return text, "Adds an Unwanted Behavior pattern to cover the missing error path."

    # Generic fallback
    text = f"THE System SHALL {stmt_clean.rstrip('.')}."
    return text, "Rewrites as a minimal ubiquitous EARS requirement."


def get_clarify_options(
    conn: sqlite3.Connection,
    spec_id: int,
    line_number: int,
    check_id: str,
) -> dict[str, Any]:
    """Return two A/B clarify options for a finding without mutating the database.

    Raises:
        KeyError: if spec_id not found.
        ValueError: if line_number is out of range or finding not found.
    """
    spec_row = get_spec(conn, spec_id)
    if spec_row is None:
        raise KeyError(f"spec_id {spec_id} not found")

    rewrites = get_rewrites(conn, spec_id)
    effective_text = _reconstruct_effective_text(spec_row["raw_text"], rewrites)
    lines = effective_text.split("\n")

    if line_number < 1 or line_number > len(lines):
        raise ValueError(f"line_number {line_number} out of range (1-{len(lines)})")

    effective_line = lines[line_number - 1]

    # Find the matching finding to get suggested_rewrite
    records = parse_requirements(effective_text)
    findings = run_checks(records)
    matching = [f for f in findings if f.line_number == line_number and f.check_id == check_id]
    suggested_rewrite = matching[0].suggested_rewrite if matching else ""

    option_a_text, option_a_rationale = _clarify_option_a(check_id, effective_line, suggested_rewrite)
    option_b_text, option_b_rationale = _clarify_option_b(check_id, effective_line, suggested_rewrite)

    return {
        "spec_id": spec_id,
        "line_number": line_number,
        "check_id": check_id,
        "effective_line": effective_line,
        "options": [
            {
                "label": "A",
                "rewritten_text": option_a_text,
                "rationale": option_a_rationale,
            },
            {
                "label": "B",
                "rewritten_text": option_b_text,
                "rationale": option_b_rationale,
            },
        ],
    }


def select_clarify_option(
    conn: sqlite3.Connection,
    spec_id: int,
    line_number: int,
    check_id: str,
    chosen_text: str,
) -> dict[str, Any]:
    """Apply the chosen clarify option as a rewrite and re-analyze.

    Raises 409-equivalent ConflictError if the line has changed since the options
    were generated (i.e. no finding with that check_id on that line exists).

    Raises:
        KeyError: if spec_id not found.
        ValueError: for out-of-range line numbers.
        ConflictError: if finding is no longer present (line changed).
    """
    spec_row = get_spec(conn, spec_id)
    if spec_row is None:
        raise KeyError(f"spec_id {spec_id} not found")

    rewrites = get_rewrites(conn, spec_id)
    effective_text = _reconstruct_effective_text(spec_row["raw_text"], rewrites)
    raw_lines = spec_row["raw_text"].split("\n")

    if line_number < 1 or line_number > len(raw_lines):
        raise ValueError(f"line_number {line_number} out of range (1-{len(raw_lines)})")

    # Conflict check: verify the finding still exists
    records_now = parse_requirements(effective_text)
    findings_now = run_checks(records_now)
    still_present = any(f.line_number == line_number and f.check_id == check_id for f in findings_now)
    if not still_present:
        raise ConflictError(f"Finding {check_id} on line {line_number} no longer exists — line has changed.")

    # Delegate to apply_rewrite which owns the transaction
    return apply_rewrite(conn, spec_id, line_number, chosen_text)


class ConflictError(Exception):
    """Raised when a clarify selection conflicts with the current spec state."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _reconstruct_effective_text(raw_text: str, rewrites: list[sqlite3.Row]) -> str:
    """Apply single-line rewrite overlays to the raw text.

    Each overlay replaces the physical line at its 1-based line_number.
    No prefix reconstruction, fuzzy matching, or Markdown AST editing.
    """
    lines = raw_text.split("\n")
    for rw in rewrites:
        idx = rw["line_number"] - 1
        if 0 <= idx < len(lines):
            lines[idx] = rw["rewritten_text"]
    return "\n".join(lines)


def _run_pipeline(effective_text: str) -> tuple[list[RequirementRecord], list[Finding], EvaluationResult]:
    """Run the frozen parse → check → evaluate pipeline."""
    records = parse_requirements(effective_text)
    findings = run_checks(records)
    evaluation = evaluate(records, findings)
    return records, findings, evaluation


def _records_to_dicts(records: list[RequirementRecord]) -> list[dict[str, Any]]:
    """Convert RequirementRecord dataclasses to storage dicts."""
    return [
        {
            "line_number": r.line_number,
            "raw_text": r.raw_text,
            "statement": r.statement,
            "section": r.section,
            "uppercase_keywords": list(r.uppercase_keywords),
            "lowercase_keywords": list(r.lowercase_keywords),
        }
        for r in records
    ]


def _findings_to_dicts(findings: list[Finding]) -> list[dict[str, Any]]:
    """Convert Finding dataclasses to storage dicts."""
    return [
        {
            "line_number": f.line_number,
            "type": f.type,
            "severity": f.severity,
            "message": f.message,
            "suggested_rewrite": f.suggested_rewrite,
            "check_id": f.check_id,
            "category": f.category,
        }
        for f in findings
    ]


def _findings_to_response(findings: list[Finding]) -> list[dict[str, Any]]:
    """Convert Finding dataclasses to API response dicts."""
    return [
        {
            "line_number": f.line_number,
            "type": f.type,
            "severity": f.severity,
            "message": f.message,
            "suggested_rewrite": f.suggested_rewrite,
            "check_id": f.check_id,
            "category": f.category,
        }
        for f in findings
    ]


def _requirements_to_response(records: list[RequirementRecord]) -> list[dict[str, Any]]:
    """Convert RequirementRecord dataclasses to API response dicts."""
    return [
        {
            "line_number": r.line_number,
            "raw_text": r.raw_text,
            "statement": r.statement,
            "section": r.section,
            "uppercase_keywords": list(r.uppercase_keywords),
            "lowercase_keywords": list(r.lowercase_keywords),
        }
        for r in records
    ]


def _rewrites_to_response(rewrites: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert rewrite rows to API response dicts."""
    return [
        {
            "line_number": rw["line_number"],
            "rewritten_text": rw["rewritten_text"],
            "applied_at": rw["applied_at"],
        }
        for rw in rewrites
    ]


def _build_analysis_response(
    conn: sqlite3.Connection,
    spec_row: sqlite3.Row,
    records: list[RequirementRecord],
    findings: list[Finding],
    evaluation: EvaluationResult,
    effective_text: str,
) -> dict[str, Any]:
    """Build the full analysis response dict."""
    rewrites = get_rewrites(conn, spec_row["id"])
    report_md = render_report(spec_row["filename"], records, evaluation)
    return {
        "spec_id": spec_row["id"],
        "filename": spec_row["filename"],
        "raw_text": spec_row["raw_text"],
        "effective_markdown": effective_text,
        "created_at": spec_row["created_at"],
        "requirements": _requirements_to_response(records),
        "findings": _findings_to_response(findings),
        "rewrites": _rewrites_to_response(rewrites),
        "score": evaluation.score,
        "tier": evaluation.tier,
        "verdict": evaluation.verdict,
        "exit_code": evaluation.exit_code,
        "requirement_count": evaluation.requirement_count,
        "defects": evaluation.defects,
        "clarifications": evaluation.clarifications,
        "infos": evaluation.infos,
        "report_markdown": report_md,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_spec(conn: sqlite3.Connection, filename: str, raw_text: str) -> dict[str, Any]:
    """Insert a new spec, run the frozen linter, store results, return analysis.

    Owns the transaction: commits on success, rolls back on failure.
    """
    try:
        spec_id = insert_spec(conn, filename, raw_text)
        records, findings, evaluation = _run_pipeline(raw_text)
        replace_requirements(conn, spec_id, _records_to_dicts(records))
        replace_findings(conn, spec_id, _findings_to_dicts(findings))
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    spec_row = get_spec(conn, spec_id)
    return _build_analysis_response(conn, spec_row, records, findings, evaluation, raw_text)


def get_analysis(conn: sqlite3.Connection, spec_id: int) -> dict[str, Any] | None:
    """Return the current analysis for a spec using its rewrite overlays.

    Does not mutate the database.  Returns None if spec_id is not found.
    """
    spec_row = get_spec(conn, spec_id)
    if spec_row is None:
        return None

    rewrites = get_rewrites(conn, spec_id)
    effective_text = _reconstruct_effective_text(spec_row["raw_text"], rewrites)
    records, findings, evaluation = _run_pipeline(effective_text)
    return _build_analysis_response(conn, spec_row, records, findings, evaluation, effective_text)


def apply_rewrite(
    conn: sqlite3.Connection,
    spec_id: int,
    line_number: int,
    rewritten_text: str,
) -> dict[str, Any]:
    """Apply a single-line rewrite overlay and re-analyze.

    Validates that line_number exists in the raw text and is a parsed
    requirement line.  Owns the transaction.

    Raises:
        KeyError: if spec_id not found.
        ValueError: if line_number is out of range or not a requirement line.
    """
    spec_row = get_spec(conn, spec_id)
    if spec_row is None:
        raise KeyError(f"spec_id {spec_id} not found")

    raw_lines = spec_row["raw_text"].split("\n")
    if line_number < 1 or line_number > len(raw_lines):
        raise ValueError(f"line_number {line_number} out of range (1-{len(raw_lines)})")

    # Verify line_number is a parsed requirement line
    rewrites = get_rewrites(conn, spec_id)
    effective_text = _reconstruct_effective_text(spec_row["raw_text"], rewrites)
    records = parse_requirements(effective_text)
    requirement_lines = {r.line_number for r in records}
    if line_number not in requirement_lines:
        raise ValueError(f"line_number {line_number} is not a parsed requirement line")

    try:
        upsert_rewrite(conn, spec_id, line_number, rewritten_text)
        # Re-analyze with the new overlay
        new_rewrites = get_rewrites(conn, spec_id)
        new_effective = _reconstruct_effective_text(spec_row["raw_text"], new_rewrites)
        records, findings, evaluation = _run_pipeline(new_effective)
        replace_requirements(conn, spec_id, _records_to_dicts(records))
        replace_findings(conn, spec_id, _findings_to_dicts(findings))
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return _build_analysis_response(conn, spec_row, records, findings, evaluation, new_effective)


def remove_rewrite(
    conn: sqlite3.Connection,
    spec_id: int,
    line_number: int,
) -> dict[str, Any]:
    """Remove one rewrite overlay and re-analyze.

    Owns the transaction.

    Raises:
        KeyError: if spec_id not found.
    """
    spec_row = get_spec(conn, spec_id)
    if spec_row is None:
        raise KeyError(f"spec_id {spec_id} not found")

    try:
        delete_rewrite(conn, spec_id, line_number)
        rewrites = get_rewrites(conn, spec_id)
        effective_text = _reconstruct_effective_text(spec_row["raw_text"], rewrites)
        records, findings, evaluation = _run_pipeline(effective_text)
        replace_requirements(conn, spec_id, _records_to_dicts(records))
        replace_findings(conn, spec_id, _findings_to_dicts(findings))
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return _build_analysis_response(conn, spec_row, records, findings, evaluation, effective_text)


def reset_rewrites(conn: sqlite3.Connection, spec_id: int) -> dict[str, Any]:
    """Delete all rewrite overlays for a spec and re-analyze.

    Owns the transaction.

    Raises:
        KeyError: if spec_id not found.
    """
    spec_row = get_spec(conn, spec_id)
    if spec_row is None:
        raise KeyError(f"spec_id {spec_id} not found")

    try:
        delete_all_rewrites(conn, spec_id)
        records, findings, evaluation = _run_pipeline(spec_row["raw_text"])
        replace_requirements(conn, spec_id, _records_to_dicts(records))
        replace_findings(conn, spec_id, _findings_to_dicts(findings))
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return _build_analysis_response(conn, spec_row, records, findings, evaluation, spec_row["raw_text"])


def build_handoff_export(conn: sqlite3.Connection, spec_id: int) -> dict[str, Any]:
    """Build a Markdown handoff export document for a spec.

    Read-only: no database writes.

    Raises:
        KeyError: if spec_id not found.
    """
    spec_row = get_spec(conn, spec_id)
    if spec_row is None:
        raise KeyError(f"spec_id {spec_id} not found")

    rewrites = get_rewrites(conn, spec_id)
    effective_text = _reconstruct_effective_text(spec_row["raw_text"], rewrites)
    records, findings, evaluation = _run_pipeline(effective_text)

    filename = spec_row["filename"]
    score = evaluation.score
    verdict = evaluation.verdict
    tier = evaluation.tier
    exported_at = datetime.now(timezone.utc).isoformat()

    # --- Build Markdown document ---
    sections: list[str] = []

    # Metadata header
    sections.append(f"# Handoff Export: {filename}")
    sections.append("")
    sections.append(f"- **Filename:** {filename}")
    sections.append(f"- **Score:** {score}")
    sections.append(f"- **Verdict:** {verdict}")
    sections.append(f"- **Tier:** {tier}")
    sections.append(f"- **Exported at:** {exported_at}")
    sections.append("")

    # Section 1: Certified Spec
    sections.append("## Certified Spec")
    sections.append("")
    sections.append(effective_text)
    sections.append("")

    # Section 2: Acceptance Criteria
    sections.append("## Acceptance Criteria")
    sections.append("")
    if records:
        # Group by section
        by_section: dict[str, list] = {}
        for r in records:
            sec = r.section or "General"
            by_section.setdefault(sec, []).append(r)
        for sec_name, reqs in by_section.items():
            sections.append(f"### {sec_name}")
            sections.append("")
            for r in reqs:
                sections.append(f"- {r.statement}")
            sections.append("")
    else:
        sections.append("No parseable requirements found.")
        sections.append("")

    # Section 3: Unresolved Questions
    sections.append("## Unresolved Questions")
    sections.append("")
    rewrite_lines = {rw["line_number"] for rw in rewrites}
    unresolved = [
        f for f in findings
        if f.severity in ("defect", "clarification") and f.line_number not in rewrite_lines
    ]
    if unresolved:
        for f in unresolved:
            sections.append(
                f"- **Line {f.line_number}** [{f.check_id}] ({f.severity}): {f.message}"
            )
        sections.append("")
    else:
        sections.append("All questions resolved — no open questions remain.")
        sections.append("")

    # Section 4: Implementation Tasks
    sections.append("## Implementation Tasks")
    sections.append("")
    if records:
        sorted_records = sorted(records, key=lambda r: r.line_number)
        for i, r in enumerate(sorted_records, 1):
            sections.append(f"{i}. [Line {r.line_number}] {r.statement}")
        sections.append("")
    else:
        sections.append("No implementation tasks — no requirements parsed.")
        sections.append("")

    markdown_document = "\n".join(sections)

    return {
        "spec_id": spec_id,
        "filename": filename,
        "score": score,
        "verdict": verdict,
        "exported_at": exported_at,
        "markdown_document": markdown_document,
    }
