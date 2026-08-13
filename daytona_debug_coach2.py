"""Debug: check raw LLM response for Coach 2 / TC01."""
import json
import os
from daytona import Daytona, DaytonaConfig

DAYTONA_API_KEY = os.environ["DAYTONA_API_KEY"]
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_API_URL = os.environ["LLM_API_URL"]
LLM_MODEL = os.environ["LLM_MODEL"]

config = DaytonaConfig(api_key=DAYTONA_API_KEY)
daytona = Daytona(config)
sandbox = daytona.create()
print(f"Sandbox: {sandbox.id}")

code = f"""\
import json, urllib.request

api_key = {json.dumps(LLM_API_KEY)}
api_url = {json.dumps(LLM_API_URL)}
model = {json.dumps(LLM_MODEL)}

system_prompt = "You are Coach 2 of 5 - EARS Grammarian. Scope: Flag formal EARS grammar violations only. Flag: Lowercase EARS keywords, Missing SHALL, Multiple SHALLs, Malformed formal EARS order. Do NOT flag: semantic escape clauses, vague wording, passive voice, pronoun ambiguity, oblique symbols, tacit knowledge, or happy-path coverage gaps. Output ONLY a single JSON object (no markdown fences, no commentary) with this exact schema: {{\\"coach\\": \\"Coach 2 - EARS Grammarian\\", \\"requirement_id\\": \\"<ID>\\", \\"flags\\": [{{\\"type\\": \\"string\\", \\"excerpt\\": \\"string\\", \\"explanation\\": \\"string\\"}}], \\"severity\\": \\"low | medium | high\\", \\"suggested_rewrite\\": \\"string or null\\"}}"

user_msg = "Evaluate this requirement (id=TC01):\\n\\nThe system should be fast when processing orders."

payload = json.dumps({{
    "model": model,
    "messages": [
        {{"role": "system", "content": system_prompt}},
        {{"role": "user", "content": user_msg}}
    ],
    "temperature": 0.1,
    "max_tokens": 2048
}}).encode()

req = urllib.request.Request(api_url, data=payload, headers={{"Content-Type": "application/json", "Authorization": f"Bearer {{api_key}}"}})
with urllib.request.urlopen(req, timeout=120) as resp:
    body = json.loads(resp.read().decode())

choice = body["choices"][0]
msg = choice["message"]
print("KEYS:", list(msg.keys()))
print("CONTENT_REPR:", repr(msg.get("content")))
print("REASONING_REPR:", repr(msg.get("reasoning_content", "NOT_PRESENT")[:300]))
print("FINISH_REASON:", choice.get("finish_reason"))
"""

resp = sandbox.process.code_run(code, timeout=150)
print(f"Exit: {resp.exit_code}")
print(f"Output:\n{resp.result}")

daytona.delete(sandbox)
print("Sandbox deleted.")
