"""Benchmark runner: executes the frozen linter against test case files and
computes precision/recall metrics.

Callable as a standalone script: python3 -m tests_benchmark.runner

Logic:
- Loads cases from distillation and adversarial JSON files.
- Invokes the frozen linter pipeline per case.
- Compares reported findings to expected_flags.
- Classifies TP, FP, FN per case.
- For control cases: pass if zero findings, fail with FP if findings present.
- Returns structured results with aggregate ratios.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path
from typing import Any

from src.linter.parser import parse_requirements
from src.linter.rule_engine import run_checks
from src.linter.evaluator import evaluate

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
_DISTILLATION_PATH = _DATA_DIR / "distillation-test-cases.json"
_ADVERSARIAL_PATH = _DATA_DIR / "adversarial-sg-sme-cases.json"


def _load_cases(path: Path) -> list[dict[str, Any]]:
    """Load test cases from a JSON file. Returns empty list with warning if missing."""
    if not path.exists():
        warnings.warn(f"Case file not found: {path}")
        return []
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, list):
        warnings.warn(f"Case file is not a JSON array: {path}")
        return []
    return data


def _validate_case(case: Any) -> bool:
    """Return True if case has required fields."""
    if not isinstance(case, dict):
        return False
    required = ("id", "title", "requirement_text", "expected_flags", "difficulty")
    return all(k in case for k in required)


def _parse_expected_flags(expected_flags: str) -> list[str]:
    """Parse semicolon-separated expected flags into a list of lowercase tokens."""
    if not expected_flags.strip():
        return []
    return [f.strip().lower() for f in expected_flags.split(";") if f.strip()]


def _finding_matches_flag(finding_msg: str, finding_check_id: str, flag: str) -> bool:
    """Check if a linter finding matches an expected flag (fuzzy keyword match)."""
    flag_lower = flag.lower()
    msg_lower = finding_msg.lower()
    check_lower = finding_check_id.lower()

    # Direct check_id match
    if check_lower and check_lower in flag_lower:
        return True

    # Keyword overlap: extract meaningful words from the flag
    flag_words = [w for w in flag_lower.replace("(", " ").replace(")", " ").split() if len(w) > 2]
    for word in flag_words:
        if word in msg_lower or word in check_lower:
            return True

    return False


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    """Run the frozen linter on a single case and return per-case result."""
    case_id = case["id"]
    title = case["title"]
    requirement_text = case["requirement_text"]
    expected_flags_raw = case["expected_flags"]
    difficulty = case.get("difficulty", "unknown")
    is_control = difficulty == "control"

    result: dict[str, Any] = {
        "id": case_id,
        "title": title,
        "difficulty": difficulty,
        "status": "passed",
        "detected_flags": [],
        "missed_flags": [],
        "false_positives": [],
        "error": None,
    }

    try:
        records = parse_requirements(requirement_text)
        findings = run_checks(records)
    except Exception as exc:
        result["status"] = "errored"
        result["error"] = str(exc)
        return result

    finding_descriptors = [
        {"message": f.message, "check_id": f.check_id, "severity": f.severity}
        for f in findings
    ]

    # Control case: expect zero findings
    if is_control:
        if len(findings) == 0:
            result["status"] = "passed"
        else:
            result["status"] = "failed"
            result["false_positives"] = [
                f"{fd['check_id']}: {fd['message']}" for fd in finding_descriptors
            ]
        return result

    # Normal case: compare findings to expected flags
    expected_flags = _parse_expected_flags(expected_flags_raw)

    # Skip flags that indicate "none expected" for non-control cases
    expected_flags = [
        f for f in expected_flags
        if not f.startswith("none expected")
    ]

    detected: list[str] = []
    missed: list[str] = []
    matched_finding_indices: set[int] = set()

    for flag in expected_flags:
        found = False
        for idx, fd in enumerate(finding_descriptors):
            if idx in matched_finding_indices:
                continue
            if _finding_matches_flag(fd["message"], fd["check_id"], flag):
                detected.append(flag)
                matched_finding_indices.add(idx)
                found = True
                break
        if not found:
            missed.append(flag)

    # False positives: findings that didn't match any expected flag
    fps = []
    for idx, fd in enumerate(finding_descriptors):
        if idx not in matched_finding_indices:
            fps.append(f"{fd['check_id']}: {fd['message']}")

    result["detected_flags"] = detected
    result["missed_flags"] = missed
    result["false_positives"] = fps
    result["status"] = "passed" if not missed else "partial"

    return result


def run_benchmark(
    distillation_path: Path | None = None,
    adversarial_path: Path | None = None,
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the full benchmark and return structured results.

    Args:
        distillation_path: Override path for distillation cases.
        adversarial_path: Override path for adversarial cases.
        cases: If provided, use these cases directly (skip file loading).

    Returns:
        Dictionary with per_case results and aggregate metrics.
    """
    if cases is not None:
        all_cases = cases
    else:
        dist_path = distillation_path or _DISTILLATION_PATH
        adv_path = adversarial_path or _ADVERSARIAL_PATH
        all_cases = _load_cases(dist_path) + _load_cases(adv_path)

    if not all_cases:
        warnings.warn("No test cases loaded — returning zero totals.")
        return {
            "total_cases": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "true_positive_ratio": 0.0,
            "detection_coverage_ratio": 0.0,
            "per_case": [],
            "warnings": ["No test cases loaded."],
        }

    per_case: list[dict[str, Any]] = []
    total_tp = 0
    total_fp = 0
    total_fn = 0
    run_warnings: list[str] = []

    for case in all_cases:
        if not _validate_case(case):
            run_warnings.append(f"Skipping malformed entry: {case.get('id', '<no id>')}")
            continue

        case_result = _run_case(case)
        per_case.append(case_result)

        if case_result["status"] == "errored":
            continue

        tp = len(case_result["detected_flags"])
        fp = len(case_result["false_positives"])
        fn = len(case_result["missed_flags"])

        total_tp += tp
        total_fp += fp
        total_fn += fn

    # Aggregate ratios
    tp_ratio = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    coverage_ratio = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0

    return {
        "total_cases": len(per_case),
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "true_positive_ratio": round(tp_ratio, 4),
        "detection_coverage_ratio": round(coverage_ratio, 4),
        "per_case": per_case,
        "warnings": run_warnings,
    }


def main() -> None:
    """CLI entry point for standalone execution."""
    result = run_benchmark()

    print("=" * 60)
    print("SpecBuddy Benchmark Results")
    print("=" * 60)
    print(f"Total cases:              {result['total_cases']}")
    print(f"True positives:           {result['true_positives']}")
    print(f"False positives:          {result['false_positives']}")
    print(f"False negatives:          {result['false_negatives']}")
    print(f"True-positive ratio:      {result['true_positive_ratio']:.4f}")
    print(f"Detection-coverage ratio: {result['detection_coverage_ratio']:.4f}")
    print("-" * 60)

    if result["warnings"]:
        print("Warnings:")
        for w in result["warnings"]:
            print(f"  ⚠ {w}")
        print("-" * 60)

    for case in result["per_case"]:
        status_icon = {"passed": "✓", "partial": "△", "failed": "✗", "errored": "⚠"}.get(
            case["status"], "?"
        )
        print(f"  {status_icon} [{case['id']}] {case['title']} ({case['status']})")
        if case["error"]:
            print(f"      Error: {case['error']}")
        if case["missed_flags"]:
            print(f"      Missed: {', '.join(case['missed_flags'])}")
        if case["false_positives"]:
            print(f"      FP: {', '.join(case['false_positives'][:3])}")

    print("=" * 60)
    print(json.dumps({
        "total_cases": result["total_cases"],
        "true_positives": result["true_positives"],
        "false_positives": result["false_positives"],
        "false_negatives": result["false_negatives"],
        "true_positive_ratio": result["true_positive_ratio"],
        "detection_coverage_ratio": result["detection_coverage_ratio"],
    }, indent=2))


if __name__ == "__main__":
    main()
