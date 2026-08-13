# Adversarial Test Briefs — Manifest

This directory contains adversarial requirements documents designed to
stress-test SpecBuddy's deterministic linter (`src/linter/`) for crashes,
false positives, and graceful degradation.

## Briefs

| # | File | Target Weakness | Expected Behavior |
|---|------|-----------------|-------------------|
| 1 | `01-false-positive-ly-words.md` | AMB-ADVERB rule uses `\b[A-Za-z]+ly\b` which matches non-adverb words ending in -ly (family, supply, assembly, monthly, early, only, apply, quarterly, natively, belly, yearly) | **Should NOT flag** these words as adverbs. Currently expected to produce **false positives** on: supply, family, assembly, monthly, early, only, quarterly, natively, belly, yearly. |
| 2 | `02-ears-unusual-positions.md` | EARS pattern matcher expects keywords at line start; multiple WHEN/WHILE/IF conditions and nested subordinate clauses may confuse pattern recognition | **Should not crash.** May flag EARS-PATTERN violations on compound conditions that are arguably valid. Tests whether singularity check (EARS-SINGULARITY) triggers correctly. |
| 3 | `03-minimal-input.md` | Parser, evaluator, and reporter handling of a single requirement — division-by-zero risks in scoring, empty-list edge cases | **Should not crash.** Should produce a valid score and report for 1 requirement. |
| 4 | `04-extremely-long-lines.md` | Regex performance on 300+ word lines — potential catastrophic backtracking in passive-voice pattern `\b(is\|are\|…)\s+\w+(ed\|en)\b` or adverb pattern on very long tokens | **Should not crash or hang.** Should complete analysis within a reasonable time (<5 seconds). May flag legitimate findings. |
| 5 | `05-unicode-multilingual.md` | Encoding handling — regex patterns assume ASCII word boundaries; Chinese/Tamil/emoji characters may cause `re` module failures or incorrect word-boundary matching | **Should not crash.** May produce unexpected findings on Unicode content but must not raise exceptions. |
| 6 | `06-malformed-ears-syntax.md` | Graceful degradation on incomplete EARS constructs — dangling WHEN with no SHALL, SHALL with no subject, doubled keywords, empty clauses | **Should not crash.** Should flag defects (EARS-PATTERN, EARS-MISSING, etc.) but must not raise unhandled exceptions on malformed input. |
| 7 | `07-mixed-markdown-structures.md` | Parser robustness with tables, fenced code blocks, nested lists, blockquotes, and horizontal rules mixed with real requirements | **Should not crash.** Parser should ideally skip code block contents (text inside ``` fences is not a requirement). Tables and blockquotes should not produce parser errors. |
| 8 | `08-empty-file.md` | Empty file (single newline) — tests that parser returns empty list without error, evaluator handles zero records, reporter handles empty findings | **Should not crash.** Should produce a valid (trivial) report with score 100 or equivalent "no requirements found" result. |
| 9 | `09-whitespace-only.md` | Whitespace-only file (spaces, tabs, blank lines) — similar to empty but non-zero byte count; tests `.strip()` and empty-check logic | **Should not crash.** Should produce same behavior as empty file. |
| 10 | `10-regex-adversarial-patterns.md` | Regex metacharacters in requirement text, catastrophic backtracking patterns (e.g., `a{1000}`), boundary abuse (`ly` repeated without word separation), extreme single-token length (1000 chars) | **Should not crash or hang.** Regex engine should handle metacharacters in input without treating them as pattern syntax. Performance must remain bounded. |

## Running These Tests

From the repo root:

```bash
# Run each brief through the CLI and verify no crash (exit code 0 or 2, not 1):
for f in tests_adversarial/briefs/*.md; do
  echo "--- $f ---"
  python3 -m linter.claritygate "$f" --out /dev/null
  echo "Exit code: $?"
  echo
done
```

A test passes if:
- Exit code is `0` (certified) or `2` (refused) — never `1` (unhandled exception).
- No Python traceback is printed to stderr.
- Execution completes within 10 seconds per file.

## Known False-Positive Vectors

The following words in brief 01 are expected to be **incorrectly flagged** by
the current AMB-ADVERB rule (`\b[A-Za-z]+ly\b`), confirming the false-positive
weakness:

- `supply` — noun/verb, not an adverb
- `family` — noun
- `assembly` — noun
- `monthly` — adjective (used attributively before "report")
- `early` — adjective (before "registration")
- `only` — adjective/adverb of exclusion, not vagueness
- `quarterly` — adjective
- `natively` — legitimate technical adverb (debatable whether vague)
- `belly` — noun (belly band)
- `yearly` — adjective

These demonstrate that the regex `\b[A-Za-z]+ly\b` needs a whitelist or
part-of-speech awareness to avoid false positives on common English words.
