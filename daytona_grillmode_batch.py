"""Daytona Grill Mode Batch Runner.

Runs 5 AI coach prompts against 10 distillation test cases (50 evaluations)
inside a single Daytona sandbox.  Results are saved to
output/daytona_grillmode_results.json in the shared coach JSON schema.

Architecture: ONE sandbox, sequential execution.
Justification: Each evaluation is a lightweight LLM API call (~1-5s).
50 sequential calls take ~2-4 min.  No CPU/memory isolation needed between
coaches.  Single sandbox = simpler cleanup, lower cost, one auto-delete timer.

Usage:
    # Smoke test (TC01 only, all 5 coaches):
    python3 daytona_grillmode_batch.py --smoke

    # Full batch (all 10 test cases x 5 coaches):
    python3 daytona_grillmode_batch.py
"""

import json
import os
import sys
import textwrap
import time
from pathlib import Path

from daytona import Daytona, DaytonaConfig

# ---------------------------------------------------------------------------
# Configuration (all from environment — never hardcoded)
# ---------------------------------------------------------------------------
DAYTONA_API_KEY = os.environ.get("DAYTONA_API_KEY", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_API_URL = os.environ.get("LLM_API_URL", "https://api.doubleword.ai/v1/chat/completions")
LLM_MODEL = os.environ.get("LLM_MODEL", "moonshotai/Kimi-K2.6")

PROJECT_ROOT = Path(__file__).resolve().parent
TEST_CASES_PATH = PROJECT_ROOT / "data" / "samples" / "distillation-test-cases.json"
OUTPUT_PATH = PROJECT_ROOT / "output" / "daytona_grillmode_results.json"

# ---------------------------------------------------------------------------
# Coach prompt definitions (from grill-mode-final-prompt-pack.md / SKILL.md)
# ---------------------------------------------------------------------------
COACH_PROMPTS = {
    "Coach 1 - Ambiguity Hunter": textwrap.dedent("""\
        You are Coach 1 of 5 - Ambiguity Hunter.

        Scope: Flag vague verbs, vague adjectives, and escape clauses.

        Flag:
        - Vague verbs (e.g., "handle", "support", "optimize", "manage", "process")
        - Vague adjectives (e.g., "fast", "user-friendly", "quickly", "efficient", "robust")
        - Escape clauses (e.g., "as appropriate", "if needed", "when possible", "where applicable")

        Do NOT flag: EARS grammar, passive voice, pronoun issues, tacit knowledge, or happy-path coverage.

        Stay in lane. If the requirement has no vague verbs, no vague adjectives, and no escape clauses, return an empty flags array with severity "low" and suggested_rewrite: null.

        Output ONLY a single JSON object (no markdown fences, no commentary) with this exact schema:
        {"coach": "Coach 1 - Ambiguity Hunter", "requirement_id": "<ID>", "flags": [{"type": "string", "excerpt": "string", "explanation": "string"}], "severity": "low | medium | high", "suggested_rewrite": "string or null"}
    """),
    "Coach 2 - EARS Grammarian": textwrap.dedent("""\
        You are Coach 2 of 5 - EARS Grammarian.

        Scope: Flag formal EARS grammar violations only.

        Flag:
        - Lowercase EARS keywords (e.g., "when", "if", "while", "where", "then", "shall" must be uppercase: WHEN, IF, WHILE, WHERE, THEN, SHALL)
        - Missing SHALL (a requirement without the mandatory keyword SHALL is not a valid EARS requirement)
        - Multiple SHALLs (each requirement shall contain exactly one SHALL for atomicity)
        - Malformed formal EARS order: IF without THEN, THEN before IF, condition keyword after SHALL, missing system subject around SHALL

        Do NOT flag: semantic escape clauses, vague wording, passive voice, pronoun ambiguity, oblique symbols, tacit knowledge, or happy-path coverage gaps.
        Do NOT rewrite escape clauses into precise conditions.

        Stay in lane. If the EARS structure is correct, return an empty flags array with severity "low" and suggested_rewrite: null.

        Output ONLY a single JSON object (no markdown fences, no commentary) with this exact schema:
        {"coach": "Coach 2 - EARS Grammarian", "requirement_id": "<ID>", "flags": [{"type": "string", "excerpt": "string", "explanation": "string"}], "severity": "low | medium | high", "suggested_rewrite": "string or null"}
    """),
    "Coach 3 - Structural Reviewer": textwrap.dedent("""\
        You are Coach 3 of 5 - Structural Reviewer.

        Scope: Flag passive voice, ambiguous pronouns, and oblique symbols.

        Flag:
        - Passive voice (e.g., "is processed by", "is sent by", "is validated by")
        - Ambiguous pronouns (e.g., "it", "they", "them", "this", "that" when the antecedent is unclear)
        - Oblique symbols (e.g., "/" used to denote alternatives like "approve/reject")

        Do NOT flag: EARS pattern violations, vague adjectives, tacit knowledge, or happy-path coverage.

        Stay in lane. If there is no passive voice, no ambiguous pronoun, and no oblique symbol, return an empty flags array with severity "low" and suggested_rewrite: null.

        Output ONLY a single JSON object (no markdown fences, no commentary) with this exact schema:
        {"coach": "Coach 3 - Structural Reviewer", "requirement_id": "<ID>", "flags": [{"type": "string", "excerpt": "string", "explanation": "string"}], "severity": "low | medium | high", "suggested_rewrite": "string or null"}
    """),
    "Coach 4 - Tacit Knowledge Detective": textwrap.dedent("""\
        You are Coach 4 of 5 - Tacit Knowledge Detective.

        Scope: Flag unstated domain assumptions that depend on external knowledge not present in the requirement.

        Flag only when a term depends on an unstated: external policy, business process, domain convention, referenced artifact, role definition, lifecycle rule, or acceptance criterion.

        Do NOT flag ordinary nouns or verbs merely because they could be further specified.
        Do NOT flag vague wording already covered by Coach 1.
        Do NOT flag grammar, EARS structure, passive voice, pronoun issues, oblique symbols, or happy-path coverage.

        Examples:
        - Flag "standard workflow" because it refers to an undefined external process.
        - Flag "required fields" if the requirement does not define which fields are required.
        - Do not automatically flag "user", "file", "payment", "dashboard" unless the missing external definition is central to testability.

        Stay in lane. If there is no unstated external assumption, return an empty flags array with severity "low" and suggested_rewrite: null.

        Output ONLY a single JSON object (no markdown fences, no commentary) with this exact schema:
        {"coach": "Coach 4 - Tacit Knowledge Detective", "requirement_id": "<ID>", "flags": [{"type": "string", "excerpt": "string", "explanation": "string"}], "severity": "low | medium | high", "suggested_rewrite": "string or null"}
    """),
    "Coach 5 - Coverage Auditor": textwrap.dedent("""\
        You are Coach 5 of 5 - Coverage Auditor.

        Scope: Flag happy-path-only requirements that miss an obvious paired failure branch.

        Flag:
        - happy path only: Only when the requirement explicitly describes a success scenario while omitting an obvious paired failure, denial, timeout, unavailable, invalid, or unauthorized branch.

        Do NOT flag: vague wording, passive voice, pronoun issues, EARS grammar, tacit knowledge, or every positive requirement by default.

        Stay in lane. Do not flag every positive requirement. Only flag when the requirement describes a success scenario and a paired failure/denial/unauthorized/invalid branch is an obvious gap. If no obvious gap exists, return an empty flags array with severity "low" and suggested_rewrite: null.

        Output ONLY a single JSON object (no markdown fences, no commentary) with this exact schema:
        {"coach": "Coach 5 - Coverage Auditor", "requirement_id": "<ID>", "flags": [{"type": "string", "excerpt": "string", "explanation": "string"}], "severity": "low | medium | high", "suggested_rewrite": "string or null"}
    """),
}

COACH_ORDER = [
    "Coach 1 - Ambiguity Hunter",
    "Coach 2 - EARS Grammarian",
    "Coach 3 - Structural Reviewer",
    "Coach 4 - Tacit Knowledge Detective",
    "Coach 5 - Coverage Auditor",
]


def load_test_cases(limit_tc: str | None = None) -> list[dict]:
    """Load test cases from JSON. Optionally filter to a single TC id."""
    with open(TEST_CASES_PATH, encoding="utf-8") as f:
        cases = json.load(f)
    if limit_tc:
        cases = [tc for tc in cases if tc["id"] == limit_tc]
    return cases


def build_sandbox_eval_code(coach_name: str, coach_prompt: str,
                            tc_id: str, requirement_text: str) -> str:
    """Build self-contained Python code to run INSIDE the Daytona sandbox.

    Uses only stdlib (urllib) to call the LLM API.  Prints raw JSON to stdout.
    """
    # Escape for embedding in triple-quoted string
    prompt_escaped = coach_prompt.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    req_escaped = requirement_text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')

    return f'''\
import json, urllib.request, os, sys

api_key = os.environ.get("LLM_API_KEY", "")
api_url = os.environ.get("LLM_API_URL", "")
model = os.environ.get("LLM_MODEL", "")

system_prompt = """{prompt_escaped}"""
requirement = """{req_escaped}"""
tc_id = "{tc_id}"

user_msg = f"Evaluate this requirement (id={{tc_id}}):\\n\\n{{requirement}}"

payload = json.dumps({{
    "model": model,
    "messages": [
        {{"role": "system", "content": system_prompt}},
        {{"role": "user", "content": user_msg}}
    ],
    "temperature": 0.1,
    "max_tokens": 2048
}}).encode()

req = urllib.request.Request(
    api_url,
    data=payload,
    headers={{
        "Content-Type": "application/json",
        "Authorization": f"Bearer {{api_key}}"
    }}
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode())
    content = body["choices"][0]["message"]["content"].strip()
    # Strip markdown fences if present
    if content.startswith("```"):
        content = content.split("\\n", 1)[1] if "\\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    print(content)
except Exception as e:
    print(json.dumps({{"error": str(e), "coach": "{coach_name}", "requirement_id": tc_id}}))
    sys.exit(1)
'''


def run_evaluation(sandbox, coach_name: str, coach_prompt: str,
                   tc: dict) -> dict:
    """Run a single coach evaluation inside the sandbox."""
    code = build_sandbox_eval_code(
        coach_name, coach_prompt, tc["id"], tc["requirement_text"]
    )
    response = sandbox.process.code_run(code, timeout=90)

    if response.exit_code != 0:
        return {
            "coach": coach_name,
            "requirement_id": tc["id"],
            "flags": [],
            "severity": "error",
            "suggested_rewrite": None,
            "error": response.result.strip() if response.result else "non-zero exit",
        }

    raw = response.result.strip()
    try:
        result = json.loads(raw)
        # Ensure required fields
        result.setdefault("coach", coach_name)
        result.setdefault("requirement_id", tc["id"])
        result.setdefault("flags", [])
        result.setdefault("severity", "low")
        result.setdefault("suggested_rewrite", None)
        return result
    except json.JSONDecodeError:
        return {
            "coach": coach_name,
            "requirement_id": tc["id"],
            "flags": [],
            "severity": "error",
            "suggested_rewrite": None,
            "error": f"JSON parse failed: {raw[:200]}",
        }


def main() -> None:
    # Parse args
    smoke_test = "--smoke" in sys.argv

    # Validate config
    if not DAYTONA_API_KEY:
        print("ERROR: DAYTONA_API_KEY not set.")
        sys.exit(1)
    if not LLM_API_KEY:
        print("ERROR: LLM_API_KEY not set.")
        sys.exit(1)

    # Load test cases
    limit_tc = "TC01" if smoke_test else None
    test_cases = load_test_cases(limit_tc)
    total = len(test_cases) * len(COACH_ORDER)
    mode_label = "SMOKE TEST (TC01 x 5 coaches)" if smoke_test else f"FULL BATCH ({len(test_cases)} TCs x 5 coaches)"
    print(f"=== Daytona Grill Mode Batch Runner ===")
    print(f"Mode: {mode_label}")
    print(f"Total evaluations: {total}")
    print(f"LLM: {LLM_MODEL} @ {LLM_API_URL}")
    print()

    # Initialize Daytona
    config = DaytonaConfig(api_key=DAYTONA_API_KEY)
    daytona = Daytona(config)

    sandbox = None
    results = []

    try:
        print("Creating sandbox...")
        sandbox = daytona.create()
        print(f"Sandbox ready: {sandbox.id}")

        # Set auto-delete safety net (30 min) in case script crashes
        try:
            sandbox.set_auto_delete_interval(1800)
        except Exception:
            pass  # non-critical

        # Set LLM env vars inside sandbox
        sandbox.process.exec(
            f'export LLM_API_KEY="{LLM_API_KEY}" && '
            f'export LLM_API_URL="{LLM_API_URL}" && '
            f'export LLM_MODEL="{LLM_MODEL}" && '
            f'echo "env set"'
        )
        # Note: env vars set via exec don't persist across code_run calls.
        # We pass them via the code itself using os.environ — but code_run
        # doesn't inherit shell env.  So we inject them into the code.
        # Actually, let's use update_env if available, or embed in code.

        # Run evaluations
        completed = 0
        for tc in test_cases:
            for coach_name in COACH_ORDER:
                completed += 1
                label = f"[{completed}/{total}] {coach_name} -> {tc['id']}"
                print(f"  {label} ...", end=" ", flush=True)
                t0 = time.time()

                result = run_evaluation_in_sandbox(
                    sandbox, coach_name, COACH_PROMPTS[coach_name], tc
                )
                elapsed = time.time() - t0
                results.append(result)

                status = "OK" if result.get("severity") != "error" else "ERR"
                n_flags = len(result.get("flags", []))
                print(f"{status} ({n_flags} flags, {elapsed:.1f}s)")

    except Exception as exc:
        print(f"\nFATAL: {type(exc).__name__}: {exc}")
        sys.exit(1)

    finally:
        if sandbox is not None:
            print("\nDeleting sandbox...")
            try:
                daytona.delete(sandbox)
                print("Sandbox deleted.")
            except Exception as e:
                print(f"Cleanup warning: {e}")

    # Save results
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved: {OUTPUT_PATH}")
    print(f"Total: {len(results)} evaluations")

    # Summary
    errors = [r for r in results if r.get("severity") == "error"]
    if errors:
        print(f"WARNING: {len(errors)} evaluations had errors.")
        for e in errors:
            print(f"  - {e['coach']} / {e['requirement_id']}: {e.get('error', 'unknown')}")


def run_evaluation_in_sandbox(sandbox, coach_name: str, coach_prompt: str,
                              tc: dict) -> dict:
    """Run evaluation with LLM env vars embedded in the code."""
    # Build code with env vars baked in (since code_run doesn't inherit shell)
    prompt_escaped = json.dumps(coach_prompt)
    req_escaped = json.dumps(tc["requirement_text"])
    tc_id = tc["id"]

    code = f"""\
import json, urllib.request, sys

api_key = {json.dumps(LLM_API_KEY)}
api_url = {json.dumps(LLM_API_URL)}
model = {json.dumps(LLM_MODEL)}

system_prompt = {prompt_escaped}
requirement = {req_escaped}
tc_id = {json.dumps(tc_id)}
coach_name = {json.dumps(coach_name)}

user_msg = f"Evaluate this requirement (id={{tc_id}}):\\n\\n{{requirement}}"

payload = json.dumps({{
    "model": model,
    "messages": [
        {{"role": "system", "content": system_prompt}},
        {{"role": "user", "content": user_msg}}
    ],
    "temperature": 0.1,
    "max_tokens": 2048
}}).encode()

req = urllib.request.Request(
    api_url,
    data=payload,
    headers={{
        "Content-Type": "application/json",
        "Authorization": f"Bearer {{api_key}}"
    }}
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode())
    content = body["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        lines = content.split("\\n")
        content = "\\n".join(lines[1:])
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    print(content)
except Exception as e:
    print(json.dumps({{"error": str(e), "coach": coach_name, "requirement_id": tc_id}}))
    sys.exit(1)
"""

    response = sandbox.process.code_run(code, timeout=90)

    if response.exit_code != 0:
        return {
            "coach": coach_name,
            "requirement_id": tc["id"],
            "flags": [],
            "severity": "error",
            "suggested_rewrite": None,
            "error": (response.result or "").strip()[:300],
        }

    raw = (response.result or "").strip()
    try:
        result = json.loads(raw)
        result.setdefault("coach", coach_name)
        result.setdefault("requirement_id", tc["id"])
        result.setdefault("flags", [])
        result.setdefault("severity", "low")
        result.setdefault("suggested_rewrite", None)
        return result
    except json.JSONDecodeError:
        return {
            "coach": coach_name,
            "requirement_id": tc["id"],
            "flags": [],
            "severity": "error",
            "suggested_rewrite": None,
            "error": f"JSON parse failed: {raw[:200]}",
        }


if __name__ == "__main__":
    main()
