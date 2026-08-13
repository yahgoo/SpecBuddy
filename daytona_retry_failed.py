"""Retry failed evaluations from the batch run with extended timeout."""

import json
import os
import sys
import time
from pathlib import Path

from daytona import Daytona, DaytonaConfig

# Import shared config and logic from the main batch script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from daytona_grillmode_batch import (
    COACH_ORDER,
    COACH_PROMPTS,
    DAYTONA_API_KEY,
    LLM_API_KEY,
    LLM_API_URL,
    LLM_MODEL,
    OUTPUT_PATH,
    load_test_cases,
)

TIMEOUT = 120  # extended from 60s
MAX_TOKENS = 8192  # Kimi K2.6 needs room for reasoning + content


def run_eval_with_retry(sandbox, coach_name, coach_prompt, tc):
    """Same as main batch but with extended timeout."""
    prompt_escaped = json.dumps(coach_prompt)
    req_escaped = json.dumps(tc["requirement_text"])

    code = f"""\
import json, urllib.request, sys

api_key = {json.dumps(LLM_API_KEY)}
api_url = {json.dumps(LLM_API_URL)}
model = {json.dumps(LLM_MODEL)}

system_prompt = {prompt_escaped}
requirement = {req_escaped}
tc_id = {json.dumps(tc["id"])}
coach_name = {json.dumps(coach_name)}

user_msg = f"Evaluate this requirement (id={{tc_id}}):\\n\\n{{requirement}}"

payload = json.dumps({{
    "model": model,
    "messages": [
        {{"role": "system", "content": system_prompt}},
        {{"role": "user", "content": user_msg}}
    ],
    "temperature": 0.1,
    "max_tokens": {MAX_TOKENS}
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
    with urllib.request.urlopen(req, timeout={TIMEOUT}) as resp:
        body = json.loads(resp.read().decode())
    choice = body["choices"][0]
    msg = choice["message"]
    # Kimi K2.6 reasoning model: content may be None, answer in reasoning
    content = msg.get("content") or ""
    if not content:
        # Try reasoning field and extract JSON from it
        reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
        # Look for JSON object in reasoning
        import re
        json_match = re.search(r'\\{{[^{{}}]*"coach"[^{{}}]*\\}}', reasoning, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        else:
            # Try to find any JSON block
            start = reasoning.find('{{"coach')
            if start >= 0:
                content = reasoning[start:]
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\\n")
        content = "\\n".join(lines[1:])
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    if not content:
        print(json.dumps({{"error": "empty response (reasoning model token exhaustion)", "coach": coach_name, "requirement_id": tc_id, "finish_reason": choice.get("finish_reason", "unknown")}}))
        sys.exit(1)
    print(content)
except Exception as e:
    print(json.dumps({{"error": str(e), "coach": coach_name, "requirement_id": tc_id}}))
    sys.exit(1)
"""

    response = sandbox.process.code_run(code, timeout=TIMEOUT + 30)

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


def main():
    # Load existing results
    with open(OUTPUT_PATH, encoding="utf-8") as f:
        results = json.load(f)

    # Find failed entries
    failed_indices = [
        i for i, r in enumerate(results) if r.get("severity") == "error"
    ]
    print(f"Found {len(failed_indices)} failed evaluations to retry.")
    if not failed_indices:
        print("Nothing to retry — all 50 are clean.")
        return

    # Load all test cases for lookup
    all_tcs = {tc["id"]: tc for tc in load_test_cases()}

    # Create sandbox
    config = DaytonaConfig(api_key=DAYTONA_API_KEY)
    daytona = Daytona(config)
    sandbox = None
    t_start = time.time()

    try:
        print("Creating sandbox for retry...")
        sandbox = daytona.create()
        print(f"Sandbox ready: {sandbox.id}")

        for count, idx in enumerate(failed_indices, 1):
            entry = results[idx]
            coach_name = entry["coach"]
            tc_id = entry["requirement_id"]
            tc = all_tcs[tc_id]

            print(f"  [{count}/{len(failed_indices)}] {coach_name} -> {tc_id} ...", end=" ", flush=True)
            t0 = time.time()

            new_result = run_eval_with_retry(sandbox, coach_name, COACH_PROMPTS[coach_name], tc)
            elapsed = time.time() - t0

            if new_result.get("severity") != "error":
                results[idx] = new_result
                n_flags = len(new_result.get("flags", []))
                print(f"OK ({n_flags} flags, {elapsed:.1f}s)")
            else:
                print(f"STILL FAILED ({elapsed:.1f}s): {new_result.get('error', '')[:80]}")

    finally:
        if sandbox:
            print("\nDeleting sandbox...")
            try:
                daytona.delete(sandbox)
                print("Sandbox deleted.")
            except Exception as e:
                print(f"Cleanup warning: {e}")

    retry_elapsed = time.time() - t_start

    # Save merged results
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Final validation
    total = len(results)
    errors_remaining = sum(1 for r in results if r.get("severity") == "error")
    ids = [(r["coach"], r["requirement_id"]) for r in results]
    duplicates = len(ids) - len(set(ids))

    print(f"\n=== FINAL VALIDATION ===")
    print(f"Total entries: {total}")
    print(f"Errors remaining: {errors_remaining}")
    print(f"Duplicates: {duplicates}")
    print(f"Retry elapsed: {retry_elapsed:.1f}s")
    print(f"Results saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
