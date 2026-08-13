"""Run Daytona Grill Mode batch against TC11-TC20 (Oxylabs test cases).

Reuses the same 5 frozen coach prompts, JSON schema, and sandbox pattern.
Uses max_tokens=8192 from the start to avoid Kimi K2.6 reasoning truncation.
"""
import json
import os
import sys
import time
from pathlib import Path

from daytona import Daytona, DaytonaConfig

# Reuse coach prompts from the main batch script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from daytona_grillmode_batch import COACH_ORDER, COACH_PROMPTS

DAYTONA_API_KEY = os.environ.get("DAYTONA_API_KEY", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_API_URL = os.environ.get("LLM_API_URL", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "")

PROJECT_ROOT = Path(__file__).resolve().parent
TEST_CASES_PATH = PROJECT_ROOT / "data" / "samples" / "distillation-test-cases-tc11-20.json"
OUTPUT_PATH = PROJECT_ROOT / "output" / "daytona_grillmode_results_tc11_20.json"

MAX_TOKENS = 8192
TIMEOUT = 120


def run_evaluation(sandbox, coach_name, coach_prompt, tc):
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

req = urllib.request.Request(api_url, data=payload, headers={{"Content-Type": "application/json", "Authorization": f"Bearer {{api_key}}"}})

try:
    with urllib.request.urlopen(req, timeout={TIMEOUT}) as resp:
        body = json.loads(resp.read().decode())
    choice = body["choices"][0]
    msg = choice["message"]
    content = msg.get("content") or ""
    if not content:
        reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
        import re
        start = reasoning.find('{{"coach')
        if start >= 0:
            end = reasoning.rfind('}}')
            if end > start:
                content = reasoning[start:end+1]
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\\n")
        content = "\\n".join(lines[1:])
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    if not content:
        print(json.dumps({{"error": "empty response", "coach": coach_name, "requirement_id": tc_id, "finish_reason": choice.get("finish_reason", "unknown")}}))
        sys.exit(1)
    print(content)
except Exception as e:
    print(json.dumps({{"error": str(e), "coach": coach_name, "requirement_id": tc_id}}))
    sys.exit(1)
"""

    for attempt in range(3):
        try:
            response = sandbox.process.code_run(code, timeout=TIMEOUT + 30)
            break
        except Exception as conn_err:
            if attempt < 2:
                print(f"[retry {attempt+1}] ", end="", flush=True)
                time.sleep(5)
            else:
                return {
                    "coach": coach_name,
                    "requirement_id": tc["id"],
                    "flags": [],
                    "severity": "error",
                    "suggested_rewrite": None,
                    "error": f"Connection error after 3 attempts: {conn_err}",
                }

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
    if not DAYTONA_API_KEY or not LLM_API_KEY:
        print("ERROR: Missing DAYTONA_API_KEY or LLM_API_KEY")
        sys.exit(1)

    with open(TEST_CASES_PATH, encoding="utf-8") as f:
        test_cases = json.load(f)

    total = len(test_cases) * len(COACH_ORDER)
    print(f"=== Daytona Grill Mode — TC11-TC20 Batch ===")
    print(f"Test cases: {len(test_cases)} (TC11-TC20)")
    print(f"Coaches: {len(COACH_ORDER)}")
    print(f"Total evaluations: {total}")
    print(f"max_tokens: {MAX_TOKENS}")
    print()

    config = DaytonaConfig(api_key=DAYTONA_API_KEY)
    daytona = Daytona(config)
    sandbox = None
    results = []
    t_start = time.time()

    try:
        print("Creating sandbox...")
        sandbox = daytona.create()
        print(f"Sandbox ready: {sandbox.id}")
        try:
            sandbox.set_auto_delete_interval(1800)
        except Exception:
            pass

        completed = 0
        for tc in test_cases:
            for coach_name in COACH_ORDER:
                completed += 1
                label = f"[{completed}/{total}] {coach_name.split(' - ')[0]} -> {tc['id']}"
                print(f"  {label} ...", end=" ", flush=True)
                t0 = time.time()
                result = run_evaluation(sandbox, coach_name, COACH_PROMPTS[coach_name], tc)
                elapsed = time.time() - t0
                results.append(result)
                status = "OK" if result.get("severity") != "error" else "ERR"
                n_flags = len(result.get("flags", []))
                print(f"{status} ({n_flags} flags, {elapsed:.1f}s)")

    except Exception as exc:
        print(f"\nFATAL: {type(exc).__name__}: {exc}")
        sys.exit(1)
    finally:
        if sandbox:
            print("\nDeleting sandbox...")
            try:
                daytona.delete(sandbox)
                print("Sandbox deleted.")
            except Exception as e:
                print(f"Cleanup warning: {e}")

    total_elapsed = time.time() - t_start

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    errors = [r for r in results if r.get("severity") == "error"]
    print(f"\n=== RESULTS ===")
    print(f"Total: {len(results)}")
    print(f"Success: {len(results) - len(errors)}")
    print(f"Errors: {len(errors)}")
    print(f"Elapsed: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"Saved: {OUTPUT_PATH}")
    if errors:
        print("\nFailed evaluations:")
        for e in errors:
            print(f"  - {e['coach']} / {e['requirement_id']}: {e.get('error', '')[:80]}")


if __name__ == "__main__":
    main()
