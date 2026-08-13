"""Shared data models for the SpecBuddy linter pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


EARS_KEYWORDS = ("WHEN", "WHILE", "WHERE", "IF", "THEN", "SHALL")


@dataclass(frozen=True)
class RequirementRecord:
    """A requirement-like line extracted from a Markdown requirements file."""

    line_number: int
    raw_text: str
    statement: str
    section: str | None = None
    uppercase_keywords: tuple[str, ...] = field(default_factory=tuple)
    lowercase_keywords: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_ears_keyword(self) -> bool:
        return bool(self.uppercase_keywords or self.lowercase_keywords)


@dataclass(frozen=True)
class Finding:
    """A single issue or clarification produced by a linter check."""

    line_number: int
    type: str
    severity: str
    message: str
    suggested_rewrite: str
    check_id: str = ""
    category: str = ""


@dataclass(frozen=True)
class EvaluationResult:
    """Aggregated linter outcome for a scan."""

    score: int
    tier: str
    verdict: str
    exit_code: int
    findings: tuple[Finding, ...]
    requirement_count: int
    defects: int
    clarifications: int
    infos: int


@dataclass(frozen=True)
class ReportResult:
    """Result of writing a quality report."""

    path: Path
    markdown: str
