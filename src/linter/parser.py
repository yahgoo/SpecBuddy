"""Parser stage: extract requirement-like Markdown lines."""

from __future__ import annotations

import re

from .models import EARS_KEYWORDS, RequirementRecord


REQUIREMENT_SECTIONS = {
    "functional requirements",
    "non-functional requirements",
    "acceptance criteria",
    "user stories",
    "requirements",
    "test data",
}

LOWERCASE_EARS = tuple(keyword.lower() for keyword in EARS_KEYWORDS)


def parse_requirements(text: str) -> list[RequirementRecord]:
    """Extract requirement-like lines while preserving source line numbers."""

    records: list[RequirementRecord] = []
    current_section: str | None = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue

        heading = _heading_text(stripped)
        if heading is not None:
            current_section = heading
            continue

        statement = _clean_markdown_line(stripped)
        if not statement:
            continue

        uppercase = _find_keywords(statement, EARS_KEYWORDS)
        lowercase = _find_lowercase_keywords(statement)
        if _is_requirement_like(statement, current_section, uppercase, lowercase):
            records.append(
                RequirementRecord(
                    line_number=line_number,
                    raw_text=raw_line,
                    statement=statement,
                    section=current_section,
                    uppercase_keywords=tuple(uppercase),
                    lowercase_keywords=tuple(lowercase),
                )
            )

    return records


def _heading_text(line: str) -> str | None:
    match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
    if not match:
        return None
    return match.group(1).strip().lower()


def _clean_markdown_line(line: str) -> str:
    cleaned = re.sub(r"^\s*[-*+]\s+", "", line)
    cleaned = re.sub(r"^\s*\d+[.)]\s+", "", cleaned)
    cleaned = re.sub(r"^\*\*[^*]+:\*\*\s*", "", cleaned)
    cleaned = re.sub(r"^\*\*[^*]+?\*\*:\s*", "", cleaned)
    cleaned = cleaned.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] == '"':
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _find_keywords(statement: str, keywords: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for keyword in keywords:
        if re.search(rf"\b{re.escape(keyword)}\b", statement):
            found.append(keyword)
    return found


def _find_lowercase_keywords(statement: str) -> list[str]:
    found: list[str] = []
    for keyword in LOWERCASE_EARS:
        if re.search(rf"\b{re.escape(keyword)}\b", statement):
            found.append(keyword)
    return found


def _is_requirement_like(
    statement: str,
    section: str | None,
    uppercase_keywords: list[str],
    lowercase_keywords: list[str],
) -> bool:
    if uppercase_keywords or lowercase_keywords:
        return True
    if section in REQUIREMENT_SECTIONS and _looks_like_list_item(statement):
        return True
    if re.search(r"\b(the system|users?|admins?)\s+(should|must|may|will|can)\b", statement, re.IGNORECASE):
        return True
    return False


def _looks_like_list_item(statement: str) -> bool:
    return bool(re.search(r"\b(shall|should|must|may|will|can|want to|need to)\b", statement, re.IGNORECASE))

