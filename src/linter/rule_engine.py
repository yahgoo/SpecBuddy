"""Rule Engine stage: run deterministic ambiguity and EARS checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from .models import EARS_KEYWORDS, Finding, RequirementRecord


VAGUE_VERBS = ("handle", "provide", "support", "optimize", "manage")
VAGUE_ADJECTIVES = ("fast", "scalable", "timely", "user-friendly", "appropriate")
NON_MANDATORY_IMPERATIVES = ("should", "must", "may", "will")
ESCAPE_CLAUSES = ("as appropriate", "if necessary", "where possible", "if needed")
TACIT_PHRASES = ("obviously", "simply", "just", "as usual")
IMPLEMENTATION_TERMS = ("sql", "database", "react", "kafka", "aws", "http", "api", "frontend", "backend")
BE_FORMS = ("is", "are", "was", "were", "be", "been", "being")
PRONOUNS = ("it", "this", "they")


@dataclass(frozen=True)
class Check:
    id: str
    description: str
    run: Callable[[RequirementRecord], list[Finding]]


def run_checks(records: list[RequirementRecord]) -> list[Finding]:
    """Run per-record checks and document-level checks."""

    findings: list[Finding] = []
    for record in records:
        for check in CHECKS:
            findings.extend(check.run(record))
    findings.extend(_check_happy_path_only(records))
    return findings


def _finding(
    record: RequirementRecord,
    check_id: str,
    type_: str,
    severity: str,
    category: str,
    message: str,
    suggested_rewrite: str,
) -> Finding:
    return Finding(
        line_number=record.line_number,
        type=type_,
        severity=severity,
        message=message,
        suggested_rewrite=suggested_rewrite,
        check_id=check_id,
        category=category,
    )


def check_vague_verbs(record: RequirementRecord) -> list[Finding]:
    hits = _term_hits(record.statement, VAGUE_VERBS)
    return [
        _finding(
            record,
            "AMB-VAGUE-VERB",
            "vague_verb",
            "defect",
            "lexical",
            f"Vague verb '{hit}' has no observable output.",
            "Replace it with a measurable behavior, e.g. 'THE System SHALL display the order status within 2 seconds.'",
        )
        for hit in hits
    ]


def check_vague_adjectives(record: RequirementRecord) -> list[Finding]:
    findings: list[Finding] = []
    for hit in _term_hits(record.statement, VAGUE_ADJECTIVES):
        findings.append(
            _finding(
                record,
                "AMB-VAGUE-ADJ",
                "unverifiable_adjective",
                "defect",
                "lexical",
                f"Unquantified adjective '{hit}' is unverifiable.",
                _metric_suggestion(hit),
            )
        )
    return findings


def check_non_mandatory_imperatives(record: RequirementRecord) -> list[Finding]:
    return [
        _finding(
            record,
            "EARS-IMPERATIVE",
            "non_mandatory_imperative",
            "defect",
            "syntactical",
            f"'{hit}' weakens the requirement; mandatory requirements must use SHALL.",
            "Rewrite the statement with 'THE System SHALL ...' and an observable outcome.",
        )
        for hit in _term_hits(record.statement, NON_MANDATORY_IMPERATIVES)
    ]



# Curated exclusion list: common -ly words that are NOT vague adverbs.
# Includes nouns, adjectives, verbs, and domain-specific terms that end in -ly.
_ADVERB_EXCLUSIONS: set[str] = {
    # Nouns
    "supply", "family", "assembly", "belly", "bully", "tally", "rally",
    "ally", "anomaly", "jelly", "lily", "monopoly", "homily", "italy",
    "july", "fly", "reply", "comply", "multiply", "imply",
    # Adjectives (often used attributively, not as vague adverbs)
    "early", "monthly", "quarterly", "yearly", "daily", "weekly", "hourly",
    "only", "lonely", "friendly", "costly", "deadly", "elderly", "ghastly",
    "holy", "likely", "unlikely", "lively", "lovely", "manly", "orderly",
    "silly", "ugly", "unruly", "woolly", "timely", "scholarly", "worldly",
    "comely", "cowardly", "curly", "hilly", "jolly", "melancholy", "oily",
    "surly", "bubbly", "chilly", "grisly", "heavenly", "homely", "kindly",
    "lowly", "princely", "sickly", "stately", "wily",
    # Verbs
    "apply", "rely", "comply", "imply", "multiply", "reply", "supply",
    "bully", "rally", "tally", "fly",
    # Technical/domain terms unlikely to be vague adverbs in specs
    "natively", "locally", "internally", "externally",
}


def check_adverbs(record: RequirementRecord) -> list[Finding]:
    findings: list[Finding] = []
    for match in re.finditer(r"\b[A-Za-z]+ly\b", record.statement):
        word = match.group(0)
        if word.lower() in _ADVERB_EXCLUSIONS:
            continue
        findings.append(
            _finding(
                record,
                "AMB-ADVERB",
                "unquantified_adverb",
                "defect",
                "lexical",
                f"Adverb '{word}' should be replaced with a measurable criterion.",
                "Replace the adverb with an observable threshold or acceptance test.",
            )
        )
    return findings


def check_passive_voice(record: RequirementRecord) -> list[Finding]:
    # This intentionally catches common MVP cases, not the full complexity of English grammar.
    pattern = rf"\b({'|'.join(BE_FORMS)})\s+\w+(ed|en)\b"
    if not re.search(pattern, record.statement, re.IGNORECASE):
        return []
    return [
        _finding(
            record,
            "AMB-PASSIVE",
            "passive_voice",
            "defect",
            "syntactical",
            "Passive voice hides the actor responsible for the behavior.",
            "Rewrite in active voice with an explicit actor: 'THE System SHALL ...'.",
        )
    ]


def check_pronouns(record: RequirementRecord) -> list[Finding]:
    findings: list[Finding] = []
    tokens = re.findall(r"[A-Za-z][A-Za-z-]*", record.statement)
    for index, token in enumerate(tokens):
        if token.lower() not in PRONOUNS:
            continue
        prior_tokens = [item for item in tokens[:index] if item.lower() not in EARS_STOPWORDS]
        # Heuristic: very short prior context usually leaves no reliable antecedent.
        if len(prior_tokens) < 2:
            findings.append(
                _finding(
                    record,
                    "AMB-PRONOUN",
                    "pronoun_antecedent",
                    "clarification",
                    "referential",
                    f"Pronoun '{token}' may not have a clear antecedent in the same statement.",
                    "Name the referenced actor or object explicitly.",
                )
            )
    return findings


def check_oblique_symbols(record: RequirementRecord) -> list[Finding]:
    if not re.search(r"\b[A-Za-z][A-Za-z-]*/[A-Za-z-]*[A-Za-z]\b", record.statement):
        return []
    return [
        _finding(
            record,
            "AMB-OBLIQUE",
            "oblique_symbol",
            "defect",
            "referential",
            "A slash combines alternatives or synonyms and creates referential ambiguity.",
            "Choose one term or split the alternatives into separate requirements.",
        )
    ]


def check_escape_clauses(record: RequirementRecord) -> list[Finding]:
    return [
        _finding(
            record,
            "AMB-ESCAPE",
            "escape_clause",
            "defect",
            "lexical",
            f"Escape clause '{hit}' permits non-conformance.",
            "Replace the escape clause with a specific condition and expected behavior.",
        )
        for hit in _phrase_hits(record.statement, ESCAPE_CLAUSES)
    ]


def check_ears_keyword_casing(record: RequirementRecord) -> list[Finding]:
    if not record.lowercase_keywords:
        return []
    required = ", ".join(EARS_KEYWORDS)
    return [
        _finding(
            record,
            "EARS-KEYWORD",
            "lowercase_ears_keyword",
            "defect",
            "syntactical",
            f"EARS keywords must be UPPERCASE. Required keywords: {required}.",
            f"Rewrite lowercase keywords as: {required}.",
        )
    ]


def check_ears_missing_keyword(record: RequirementRecord) -> list[Finding]:
    if record.has_ears_keyword:
        return []
    return [
        _finding(
            record,
            "EARS-MISSING",
            "missing_ears_keyword",
            "defect",
            "syntactical",
            "Requirement has no EARS keyword and is not testable enough for handoff.",
            "Rewrite using one EARS pattern, e.g. 'WHEN <trigger>, THE System SHALL <response>'.",
        )
    ]


def check_ears_singularity(record: RequirementRecord) -> list[Finding]:
    if len(re.findall(r"\bSHALL\b", record.statement)) <= 1:
        return []
    return [
        _finding(
            record,
            "EARS-SINGULAR",
            "singularity_violation",
            "defect",
            "syntactical",
            "Requirement contains more than one SHALL statement.",
            "Split the behavior into one requirement per SHALL for traceability.",
        )
    ]


def check_ears_pattern(record: RequirementRecord) -> list[Finding]:
    if "SHALL" not in record.uppercase_keywords or record.lowercase_keywords:
        return []
    if _matches_ears_pattern(record.statement):
        return []
    return [
        _finding(
            record,
            "EARS-PATTERN",
            "ears_pattern_violation",
            "defect",
            "syntactical",
            "Requirement does not match one of the six accepted EARS patterns.",
            "Use 'THE System SHALL ...', 'WHEN ... THE System SHALL ...', or another canonical EARS pattern.",
        )
    ]


def check_tacit_knowledge(record: RequirementRecord) -> list[Finding]:
    return [
        _finding(
            record,
            "TACIT-UNREC",
            "tacit_knowledge",
            "clarification",
            "tacit",
            f"Phrase '{hit}' suggests unstated domain knowledge.",
            "Make the assumed rule explicit as an observable requirement.",
        )
        for hit in _phrase_hits(record.statement, TACIT_PHRASES)
    ]


def check_implementation_leakage(record: RequirementRecord) -> list[Finding]:
    return [
        _finding(
            record,
            "LEAK-IMPLEMENTATION",
            "implementation_leakage",
            "defect",
            "tacit",
            f"Implementation term '{hit}' leaks design choices into requirements.",
            "State the observable behavior without naming implementation technology.",
        )
        for hit in _term_hits(record.statement, IMPLEMENTATION_TERMS)
    ]


def _check_happy_path_only(records: list[RequirementRecord]) -> list[Finding]:
    nominal_records = [record for record in records if _is_nominal(record.statement)]
    has_unwanted_behavior = any(_is_unwanted_behavior(record.statement) for record in records)
    if not nominal_records or has_unwanted_behavior:
        return []
    first = nominal_records[0]
    return [
        _finding(
            first,
            "COMP-HAPPY-PATH",
            "missing_unwanted_behavior",
            "clarification",
            "completeness",
            "Feature description contains nominal behavior but no Unwanted Behavior IF-THEN requirement.",
            "Add an IF <failure condition>, THEN THE System SHALL <recovery action> requirement.",
        )
    ]


def _term_hits(statement: str, terms: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for term in terms:
        if re.search(rf"\b{re.escape(term)}\b", statement, re.IGNORECASE):
            hits.append(term)
    return hits


def _phrase_hits(statement: str, phrases: tuple[str, ...]) -> list[str]:
    lowered = statement.lower()
    return [phrase for phrase in phrases if phrase in lowered]


def _metric_suggestion(term: str) -> str:
    if term == "fast":
        return "Replace 'fast' with a threshold, e.g. 'within 2 seconds for 95% of requests'."
    if term == "user-friendly":
        return "Replace 'user-friendly' with a measurable usability criterion, e.g. 'new users complete checkout without help in under 3 minutes'."
    if term == "scalable":
        return "Replace 'scalable' with a load target, e.g. 'support 1,000 concurrent users with p95 latency under 500ms'."
    if term == "timely":
        return "Replace 'timely' with an explicit deadline or latency threshold."
    return "Replace the subjective adjective with an observable metric or threshold."


def _matches_ears_pattern(statement: str) -> bool:
    normalized = re.sub(r"\s+", " ", statement.strip())
    patterns = (
        r"^THE\s+System\s+SHALL\s+.+$",
        r"^WHEN\s+.+,?\s+THE\s+System\s+SHALL\s+.+$",
        r"^WHILE\s+.+,?\s+THE\s+System\s+SHALL\s+.+$",
        r"^IF\s+.+,?\s+THEN\s+THE\s+System\s+SHALL\s+.+$",
        r"^WHERE\s+.+,?\s+THE\s+System\s+SHALL\s+.+$",
    )
    if any(re.match(pattern, normalized) for pattern in patterns):
        return True
    # MVP-light Complex pattern: an uppercase condition appears before THE System SHALL.
    return bool(re.match(r"^(WHEN|WHILE|WHERE|IF)\s+.+\s+THE\s+System\s+SHALL\s+.+$", normalized))


def _is_nominal(statement: str) -> bool:
    normalized = statement.strip()
    if _is_unwanted_behavior(normalized):
        return False
    return bool(
        re.search(r"\b(THE\s+System\s+SHALL|WHEN|WHILE|WHERE)\b", normalized)
        or re.search(r"\b(the system|users?|admins?)\s+(should|must|may|will|can)\b", normalized, re.IGNORECASE)
    )


def _is_unwanted_behavior(statement: str) -> bool:
    return bool(re.search(r"\bIF\b.+\bTHEN\b.+\bTHE\s+System\s+SHALL\b", statement))


EARS_STOPWORDS = {
    "a",
    "an",
    "and",
    "if",
    "shall",
    "system",
    "the",
    "then",
    "when",
    "where",
    "while",
}


CHECKS = (
    Check("AMB-VAGUE-VERB", "Vague verbs", check_vague_verbs),
    Check("AMB-VAGUE-ADJ", "Unquantified adjectives", check_vague_adjectives),
    Check("EARS-IMPERATIVE", "Non-mandatory imperatives", check_non_mandatory_imperatives),
    Check("AMB-ADVERB", "Unquantified adverbs", check_adverbs),
    Check("AMB-PASSIVE", "Passive voice", check_passive_voice),
    Check("AMB-PRONOUN", "Pronoun antecedents", check_pronouns),
    Check("AMB-OBLIQUE", "Oblique symbols", check_oblique_symbols),
    Check("AMB-ESCAPE", "Escape clauses", check_escape_clauses),
    Check("EARS-KEYWORD", "EARS keyword casing", check_ears_keyword_casing),
    Check("EARS-MISSING", "Missing EARS keyword", check_ears_missing_keyword),
    Check("EARS-SINGULAR", "EARS singularity", check_ears_singularity),
    Check("EARS-PATTERN", "EARS pattern", check_ears_pattern),
    Check("TACIT-UNREC", "Tacit knowledge", check_tacit_knowledge),
    Check("LEAK-IMPLEMENTATION", "Implementation leakage", check_implementation_leakage),
)

