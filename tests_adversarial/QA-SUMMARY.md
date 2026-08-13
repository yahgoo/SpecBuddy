# Adversarial QA Summary

## Test Campaign

- **Date:** 2026-08-12
- **Scope:** 10 adversarial briefs targeting crash vectors, false positives,
  regex performance, encoding edge cases, and graceful degradation
- **Linter under test:** `src/linter/` deterministic core (Python 3.11+,
  stdlib only)

## Results At A Glance

| Metric | Result |
|--------|--------|
| Briefs tested | 10 |
| Crashes | 0 |
| Hangs / timeouts | 0 |
| Unhandled exceptions | 0 |
| Bugs found | 1 |
| Test regressions after fix | 0 |

## Bug Found And Fixed

### AMB-ADVERB False Positives

- **Root cause:** The `\b[A-Za-z]+ly\b` regex in the AMB-ADVERB check matched
  common English words ending in `-ly` that are not vague adverbs (e.g.
  `supply`, `family`, `assembly`, `monthly`, `early`, `only`, `quarterly`,
  `natively`, `belly`, `yearly`).
- **Impact:** Brief 01 (`01-false-positive-ly-words.md`) originally produced
  16 AMB-ADVERB findings; 15 were false positives.
- **Fix:** Added a whitelist of non-adverb `-ly` words to the AMB-ADVERB rule.
  The rule now skips known nouns, adjectives, and technical terms before
  flagging.
- **After fix:** Brief 01 produces 1 AMB-ADVERB finding (`automatically` on
  line 15), which is a legitimate flag. False positives reduced from 16 to 1.

## Test Regression Check

After the AMB-ADVERB whitelist fix:

- Core test suite (`tests/`): **36 tests passed** — 0 failures
- Backend test suite (`tests_backend/`): **73 tests passed** — 0 failures
- All 10 adversarial briefs: exit code 0 or 2 (no crashes)

## Certification Status Across All Specs

| Spec | Score | Verdict |
|------|-------|---------|
| `clarification-loop-backend/requirements.md` | 100/100 | CERTIFIED |
| `clarification-loop-frontend/requirements.md` | 100/100 | CERTIFIED |
| `evidence-benchmark/requirements.md` | 100/100 | CERTIFIED |
| `handoff-export-backend/requirements.md` | 100/100 | CERTIFIED |
| `handoff-export-frontend/requirements.md` | 100/100 | CERTIFIED |

**All 5 project specs achieve 100/100 Agent Ready — CERTIFIED.**

## Brief-Level Results

| # | Brief | Exit | Score | Verdict | Notes |
|---|-------|------|-------|---------|-------|
| 1 | `01-false-positive-ly-words.md` | 0 | 64/100 | CERTIFIED | 1 AMB-ADVERB (legitimate), 2 AMB-PASSIVE, 1 AMB-VAGUE-VERB, 1 COMP-HAPPY-PATH |
| 2 | `02-ears-unusual-positions.md` | 2 | 60/100 | REFUSED | 5 defects on compound EARS conditions — expected |
| 3 | `03-minimal-input.md` | 0 | 96/100 | CERTIFIED | 1 clarification — no scoring edge case |
| 4 | `04-extremely-long-lines.md` | 2 | 40/100 | REFUSED | 8 findings on 300+ word lines — no hang |
| 5 | `05-unicode-multilingual.md` | 0 | 84/100 | CERTIFIED | Emoji, CJK, Tamil handled without crash |
| 6 | `06-malformed-ears-syntax.md` | 2 | 52/100 | REFUSED | Graceful degradation on dangling keywords |
| 7 | `07-mixed-markdown-structures.md` | 2 | 44/100 | REFUSED | Tables/code fences handled without crash |
| 8 | `08-empty-file.md` | 0 | 100/100 | CERTIFIED | Zero requirements — trivial pass |
| 9 | `09-whitespace-only.md` | 0 | 100/100 | CERTIFIED | Whitespace-only — trivial pass |
| 10 | `10-regex-adversarial-patterns.md` | 2 | 52/100 | REFUSED | Metacharacters in input — no crash or backtrack |

## Conclusion

The deterministic linter core is stable under adversarial input. The single
bug discovered (AMB-ADVERB false positives) was a precision issue, not a
safety issue. The whitelist fix resolved it with zero regressions. All project
specifications pass at 100/100 CERTIFIED and are ready for coding-agent
handoff.
