# SKILL — SpecBuddy Requirements Engineering Linter

This file is an IDE-agnostic instruction set for reviewing or authoring
coding-agent-ready requirements.

## Purpose

SpecBuddy is an automated quality gateway that catches requirement defects before
they propagate to design, implementation, and testing. By enforcing structured
EARS syntax and flagging linguistic smells, it reduces AI drift: the tendency for
coding agents to fill ambiguity with inconsistent assumptions.

The agent using this skill acts as an intent clarifier. Every requirement must be
a testable constraint on observable behavior, not a vague thesis statement.

## When To Use

- At the start of a spec-driven workflow session.
- Before generating implementation plans, designs, or tasks from requirements.
- Whenever a PM, BA, engineer, or AI-assisted builder modifies a requirement.
- When moving from a prototype sketch to a production-ready specification.

## Review Checklist

1. **EARS compliance**: Does every acceptance criterion follow one of the six
   canonical EARS patterns?
2. **Imperative usage**: Is `SHALL` used for mandatory requirements, with
   `should`, `must`, `may`, and `will` rejected?
3. **Measurable metrics**: Are performance and success criteria quantifiable?
4. **Error path coverage**: Does each nominal path have an unwanted-behavior
   `IF ... THEN` requirement where appropriate?
5. **Ambiguity scan**: Is the requirement free of lexical, referential, and
   syntactical ambiguity?

## Ambiguity Rules

Flag the following as defects:

- **Vague verbs**: `handle`, `provide`, `support`, `optimize`, `manage`.
- **Unquantified adjectives**: `fast`, `scalable`, `timely`, `user-friendly`,
  `appropriate`.
- **Passive voice**: requirements must make the actor explicit.
- **Pronoun ambiguity**: `it`, `this`, or `they` without a clear noun in the same
  statement.
- **Oblique symbols**: `/` used to combine synonyms, such as `symbol/sign`.
- **Escape clauses**: `as appropriate`, `if necessary`, `where possible`.

## EARS Enforcement Rules

Every requirement SHALL conform to one of the six EARS patterns:

1. **Ubiquitous**: `THE System SHALL <behavior>`
2. **Event-driven**: `WHEN <trigger> THE System SHALL <response>`
3. **State-driven**: `WHILE <state> THE System SHALL <behavior>`
4. **Unwanted behavior**: `IF <condition> THEN THE System SHALL <recovery action>`
5. **Optional feature**: `WHERE <feature> is included THE System SHALL <behavior>`
6. **Complex**: `<precondition(s)> <trigger> THE System SHALL <response>`

Grammar rules:

- EARS keywords must be uppercase.
- Use one `SHALL` per requirement to preserve singularity and traceability.
- A requirement with no EARS keyword is non-compliant and must be rewritten.

## Required Output Format

Findings should be delivered as a clarification queue using simple two-option
questions:

- **Ambiguity question**: "The phrase 'remove the record' could mean hard-delete
  or soft-delete. Which did you mean? A) Keep as-is; B) Change to soft-delete."
- **Conflict question**: "Rule R1 and R2 fire in the same situation but demand
  incompatible outcomes. Which one takes priority?"
- **Surprising scenario**: Present a concrete behavior the requirements accept or
  reject and ask whether it is intended.

## Refusal Conditions

Refuse to proceed to implementation planning if any of the following are present:

1. Thesis-level requirements, such as "The system shall be user-friendly".
2. Implementation leakage, such as "The system shall use an SQL database".
3. Missing or lowercase EARS keywords.
4. Untestable statements that cannot be mapped to observable inputs or outputs.
