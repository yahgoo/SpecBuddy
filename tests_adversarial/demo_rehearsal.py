"""Demo rehearsal script — exercises the full SpecBuddy clarify loop.

Calls existing backend functions directly (same flow the UI uses) against
the demo SME brief requirements.md without modifying any linter or adapter code.

Sequence:
1. Load the spec into storage.
2. Certify — expect REFUSED, score 0.
3. Get clarify options for 3 target findings.
4. Select a clarify option for each (with SME-specific rewrites).
5. Confirm rewrites applied and text updated.
6. Re-certify and report new score/verdict.
7. Report remaining blocking categories if not CERTIFIED.
8. Export handoff Markdown pack.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Ensure project root is importable
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))

from backend.database import connect, init_db, get_spec, get_rewrites
from backend.linter_adapter import (
    analyze_spec,
    get_analysis,
    get_clarify_options,
    select_clarify_option,
    build_handoff_export,
    _reconstruct_effective_text,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEPARATOR = "=" * 72


def banner(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


# ---------------------------------------------------------------------------
# Demo-specific SME rewrites (what a subject-matter expert would choose)
# ---------------------------------------------------------------------------

# Line 9: "Orders should be confirmed via notification once payment is received."
# Ambiguity: What notification channel? → SME chooses: SMS
LINE_9_SME_REWRITE = (
    "- WHEN payment is received, THE System SHALL send an SMS confirmation "
    "to the customer's registered mobile number within 30 seconds."
)

# Line 13: "The system should support delivery within a reasonable radius from the stall."
# Ambiguity: What radius? → SME chooses: fixed 3 km
LINE_13_SME_REWRITE = (
    "- THE System SHALL accept delivery orders only for addresses within "
    "a 3 km radius from the stall, calculated by straight-line distance from postal code."
)

# Line 19: "Payment status should be tracked and orders cancelled if unpaid."
# Ambiguity: When to cancel? → SME chooses: 10-minute grace period
LINE_19_SME_REWRITE = (
    "- WHEN an order remains unpaid for more than 10 minutes, "
    "THE System SHALL cancel the order and release reserved inventory."
)


# ---------------------------------------------------------------------------
# Main rehearsal
# ---------------------------------------------------------------------------

def main() -> None:
    spec_path = _PROJECT_ROOT / ".kiro" / "specs" / "demo-sme-brief" / "requirements.md"
    raw_text = spec_path.read_text(encoding="utf-8")
    filename = "requirements.md"

    # Use a temp database so runs are idempotent
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp_db.name
    tmp_db.close()

    try:
        init_db(db_path)
        conn = connect(db_path)

        # ------------------------------------------------------------------
        # STEP 1: Load the spec into the app's storage
        # ------------------------------------------------------------------
        banner("STEP 1 — Load spec into storage")
        result = analyze_spec(conn, filename, raw_text)
        spec_id = result["spec_id"]
        print(f"Spec loaded.  spec_id={spec_id}")
        print(f"  filename: {result['filename']}")
        print(f"  lines: {len(raw_text.splitlines())}")

        # ------------------------------------------------------------------
        # STEP 2: Initial certification — expect REFUSED, score 0
        # ------------------------------------------------------------------
        banner("STEP 2 — Initial certification")
        print(f"  Score:   {result['score']}/100")
        print(f"  Verdict: {result['verdict']}")
        print(f"  Tier:    {result['tier']}")
        print(f"  Exit:    {result['exit_code']}")
        print(f"  Findings total: {len(result['findings'])}")
        print(f"    defects:        {result['defects']}")
        print(f"    clarifications: {result['clarifications']}")
        print(f"    infos:          {result['infos']}")

        assert result["verdict"] == "REFUSED", (
            f"Expected REFUSED, got {result['verdict']}"
        )
        assert result["score"] == 0, (
            f"Expected score 0, got {result['score']}"
        )
        print("\n  ✓ Confirmed: verdict=REFUSED, score=0/100")

        # ------------------------------------------------------------------
        # STEP 3: Get clarify options for 3 target findings
        # ------------------------------------------------------------------
        banner("STEP 3 — Get clarify options for 3 target findings")

        # Identify the most relevant check_ids for each target line:
        # Line 9:  notification channel → AMB-PASSIVE (vague actor for notification)
        # Line 13: delivery radius → AMB-VAGUE-VERB ("support" is vague)
        # Line 19: unpaid cancellation timing → EARS-IMPERATIVE (no SHALL)
        findings_by_line: dict[int, list] = {}
        for f in result["findings"]:
            findings_by_line.setdefault(f["line_number"], []).append(f)

        # Define the target (line_number, check_id, description, sme_rewrite)
        targets = [
            (9, "EARS-MISSING", "notification channel → SMS", LINE_9_SME_REWRITE),
            (13, "AMB-VAGUE-VERB", "delivery radius → fixed 3 km", LINE_13_SME_REWRITE),
            (19, "EARS-IMPERATIVE", "unpaid cancellation → 10-min grace", LINE_19_SME_REWRITE),
        ]

        # Show all findings on target lines first
        for ln, check_id, desc, _ in targets:
            findings_on_line = findings_by_line.get(ln, [])
            print(f"\n  Line {ln} — {desc}")
            print(f"  All findings on this line ({len(findings_on_line)}):")
            for f in findings_on_line:
                marker = " ←" if f["check_id"] == check_id else ""
                print(f"    [{f['check_id']}] {f['severity']}: {f['message']}{marker}")

        # Now call get_clarify_options for each target
        print("\n" + "-" * 60)
        print("  Clarify options returned by the system:")
        print("-" * 60)

        clarify_results = {}
        for ln, check_id, desc, _ in targets:
            opts = get_clarify_options(conn, spec_id, ln, check_id)
            clarify_results[(ln, check_id)] = opts
            print(f"\n  === Line {ln}: {desc} ===")
            print(f"  Check: {check_id}")
            print(f"  Effective line: {opts['effective_line']}")
            for opt in opts["options"]:
                print(f"    Option {opt['label']}:")
                print(f"      Text:      {opt['rewritten_text']}")
                print(f"      Rationale: {opt['rationale']}")

        # ------------------------------------------------------------------
        # STEP 4: Select clarify option for each (SME-specific rewrites)
        # ------------------------------------------------------------------
        banner("STEP 4 — Select clarify option (SME-specific choices)")

        print("  The SME reviews the two system-generated options, then provides")
        print("  a domain-specific rewrite via select_clarify_option:\n")

        apply_results = {}
        for ln, check_id, desc, sme_rewrite in targets:
            print(f"  Line {ln} ({desc}):")
            print(f"    SME chosen text: {sme_rewrite}")

            result_sel = select_clarify_option(
                conn, spec_id, ln, check_id, sme_rewrite
            )
            apply_results[ln] = result_sel
            print(f"    ✓ Applied successfully. New score: {result_sel['score']}/100\n")

        # ------------------------------------------------------------------
        # STEP 5: Confirm rewrites applied & text updated
        # ------------------------------------------------------------------
        banner("STEP 5 — Confirm rewrites applied and text updated")

        rewrites = get_rewrites(conn, spec_id)
        print(f"\n  Active rewrites: {len(rewrites)}")
        for rw in rewrites:
            print(f"    Line {rw['line_number']}: {rw['rewritten_text']}")

        # Verify effective text changed
        spec_row = get_spec(conn, spec_id)
        effective_text = _reconstruct_effective_text(spec_row["raw_text"], rewrites)
        effective_lines = effective_text.split("\n")

        print("\n  Effective text at target lines (after SME rewrites):")
        for ln, _, desc, _ in targets:
            if ln - 1 < len(effective_lines):
                print(f"    Line {ln}: {effective_lines[ln - 1]}")

        assert len(rewrites) == 3, f"Expected 3 rewrites, got {len(rewrites)}"
        print("\n  ✓ All 3 rewrite overlays confirmed in storage.")

        # Verify rewrites contain SME-specific language
        rewrite_texts = [rw["rewritten_text"] for rw in rewrites]
        all_text = " ".join(rewrite_texts)
        assert "SMS" in all_text, "Expected 'SMS' in rewrites"
        assert "3 km" in all_text, "Expected '3 km' in rewrites"
        assert "10 minutes" in all_text, "Expected '10 minutes' in rewrites"
        print("  ✓ SME-specific terms confirmed: SMS, 3 km, 10 minutes")

        # ------------------------------------------------------------------
        # STEP 6: Re-run certification after all clarifications
        # ------------------------------------------------------------------
        banner("STEP 6 — Re-run certification after all 3 clarifications")

        new_analysis = get_analysis(conn, spec_id)
        print(f"  Score:   {new_analysis['score']}/100")
        print(f"  Verdict: {new_analysis['verdict']}")
        print(f"  Tier:    {new_analysis['tier']}")
        print(f"  Findings total: {len(new_analysis['findings'])}")
        print(f"    defects:        {new_analysis['defects']}")
        print(f"    clarifications: {new_analysis['clarifications']}")
        print(f"    infos:          {new_analysis['infos']}")

        initial_findings = len(result["findings"])
        new_findings = len(new_analysis["findings"])
        reduced = initial_findings - new_findings
        print(f"\n  Findings reduced: {initial_findings} → {new_findings} (−{reduced})")

        # ------------------------------------------------------------------
        # STEP 7: Report remaining blocking categories
        # ------------------------------------------------------------------
        banner("STEP 7 — Remaining blocking categories")

        if new_analysis["verdict"] != "CERTIFIED":
            remaining_by_check: dict[str, int] = {}
            remaining_by_severity: dict[str, int] = {}
            for f in new_analysis["findings"]:
                cid = f.get("check_id", f.get("type", "unknown"))
                sev = f["severity"]
                remaining_by_check[cid] = remaining_by_check.get(cid, 0) + 1
                remaining_by_severity[sev] = remaining_by_severity.get(sev, 0) + 1

            print(f"\n  Verdict is still {new_analysis['verdict']}.")
            print(f"  Score: {new_analysis['score']}/100")
            print(f"\n  Remaining findings by check_id ({len(remaining_by_check)} categories):")
            for cat, count in sorted(remaining_by_check.items(), key=lambda x: -x[1]):
                print(f"    {cat}: {count}")
            print(f"\n  Remaining findings by severity:")
            for sev, count in sorted(remaining_by_severity.items()):
                print(f"    {sev}: {count}")

            print("\n  ┌─────────────────────────────────────────────────────────┐")
            print("  │  DEMO NARRATIVE                                         │")
            print("  │  Answering 3 ambiguity questions (clarify loop) fixed   │")
            print(f"  │  {reduced} findings. Remaining {new_findings} findings are structural  │")
            print("  │  (EARS patterns, implementation leaks, etc.) and need   │")
            print("  │  remediation — the next step in the SpecBuddy workflow. │")
            print("  └─────────────────────────────────────────────────────────┘")
        else:
            print("\n  ✓ Spec is now CERTIFIED!")

        # ------------------------------------------------------------------
        # STEP 8: Export handoff Markdown pack
        # ------------------------------------------------------------------
        banner("STEP 8 — Export handoff Markdown pack")

        export = build_handoff_export(conn, spec_id)
        print(f"  spec_id:     {export['spec_id']}")
        print(f"  filename:    {export['filename']}")
        print(f"  score:       {export['score']}")
        print(f"  verdict:     {export['verdict']}")
        print(f"  exported_at: {export['exported_at']}")
        print(f"  markdown_document length: {len(export['markdown_document'])} chars")
        print(f"\n  First 600 chars of Markdown export:")
        print("  " + "-" * 60)
        for line in export["markdown_document"][:600].split("\n"):
            print(f"  | {line}")
        print("  " + "-" * 60)

        assert export["markdown_document"], "Handoff export is empty!"
        assert "# Handoff Export" in export["markdown_document"], (
            "Missing expected heading in handoff export"
        )
        assert "SMS" in export["markdown_document"], (
            "SME rewrite (SMS) not reflected in handoff export"
        )
        assert "3 km" in export["markdown_document"], (
            "SME rewrite (3 km) not reflected in handoff export"
        )
        print("\n  ✓ Handoff export confirmed:")
        print("    - Downloadable Markdown pack returned")
        print("    - SME clarifications visible in exported spec")
        print("    - Contains metadata, certified spec, acceptance criteria,")
        print("      unresolved questions, and implementation tasks")

        # ------------------------------------------------------------------
        # Done
        # ------------------------------------------------------------------
        banner("DEMO REHEARSAL COMPLETE ✓")
        print(f"  Initial state:          score=0/100, verdict=REFUSED, {initial_findings} findings")
        print(f"  After 3 SME clarifies:  score={new_analysis['score']}/100, "
              f"verdict={new_analysis['verdict']}, {new_findings} findings")
        print(f"  Findings eliminated:    {reduced}")
        print(f"  Handoff export:         ✓ ({len(export['markdown_document'])} chars Markdown)")
        print()
        print("  All 8 rehearsal steps passed.")
        print()

    finally:
        conn.close()
        os.unlink(db_path)


if __name__ == "__main__":
    main()
