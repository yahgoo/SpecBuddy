"""Oxylabs google_search scraping for WorkBuddy deny-list and test cases."""
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

USERNAME = os.getenv("OXYLABS_USERNAME")
PASSWORD = os.getenv("OXYLABS_PASSWORD")
API_URL = "https://realtime.oxylabs.io/v1/queries"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "oxylabs_raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

QUERIES = [
    ("ambiguous_requirements", "examples of ambiguous software requirements"),
    ("vague_acceptance_criteria", "vague acceptance criteria examples bad PRD"),
    ("ears_mistakes", "EARS requirements syntax common mistakes"),
    ("poor_user_stories", "poorly written user story examples product management"),
]


def run_query(slug: str, query: str, retries: int = 3) -> dict | None:
    payload = {
        "source": "google_search",
        "query": query,
        "geo_location": "United States",
        "parse": True,
    }
    for attempt in range(1, retries + 1):
        print(f"  [{slug}] attempt {attempt}/{retries} ...", end=" ", flush=True)
        try:
            resp = requests.post(
                API_URL,
                auth=(USERNAME, PASSWORD),
                json=payload,
                timeout=60,
            )
            if resp.status_code == 429:
                wait = 10 * attempt
                print(f"429 rate-limited, waiting {wait}s ...")
                time.sleep(wait)
                continue
            if resp.status_code == 200:
                data = resp.json()
                out_path = OUTPUT_DIR / f"{slug}.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                n_results = len(data.get("results", []))
                print(f"OK ({n_results} result pages, saved to {out_path.name})")
                return data
            else:
                print(f"HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"ERROR: {e}")
        if attempt < retries:
            time.sleep(5)
    return None


def main():
    print("=== Oxylabs Google Search Scraping ===")
    print(f"User: {USERNAME[:4]}...{USERNAME[-3:]}")
    print(f"Queries: {len(QUERIES)}")
    print()

    results_summary = {}
    for slug, query in QUERIES:
        print(f"Query: \"{query}\"")
        data = run_query(slug, query)
        if data:
            organic = []
            for page in data.get("results", []):
                content = page.get("content", {})
                parsed = content.get("results", {})
                organic.extend(parsed.get("organic", []))
            results_summary[slug] = {
                "query": query,
                "status": "success",
                "organic_count": len(organic),
            }
        else:
            results_summary[slug] = {
                "query": query,
                "status": "failed",
                "organic_count": 0,
            }
        print()
        time.sleep(2)  # respect rate limits between queries

    print("=== Summary ===")
    for slug, info in results_summary.items():
        print(f"  {slug}: {info['status']} ({info['organic_count']} organic results)")

    # Save summary for Step 4
    summary_path = OUTPUT_DIR.parent / "oxylabs_scrape_meta.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    print(f"\nMeta saved: {summary_path}")


if __name__ == "__main__":
    main()
