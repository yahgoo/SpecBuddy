"""API routes for SpecBuddy backend.

All routes derive scores, tiers, and verdicts fresh from the frozen evaluator.
No mission state is returned.  No score/tier/verdict is persisted.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, field_validator

from backend.database import (
    connect,
    get_latest_benchmark_run,
    insert_benchmark_run,
    is_benchmark_running,
)
from backend.linter_adapter import (
    ConflictError,
    analyze_spec,
    apply_rewrite,
    build_handoff_export,
    get_analysis,
    get_clarify_options,
    remove_rewrite,
    reset_rewrites,
    select_clarify_option,
)
from tests_benchmark.runner import run_benchmark

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class CreateSpecRequest(BaseModel):
    filename: str
    raw_text: str

    @field_validator("filename")
    @classmethod
    def filename_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("filename must not be empty")
        return v

    @field_validator("raw_text")
    @classmethod
    def raw_text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("raw_text must not be empty")
        return v


class ApplyRewriteRequest(BaseModel):
    line_number: int
    rewritten_text: str

    @field_validator("rewritten_text")
    @classmethod
    def rewritten_text_valid(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("rewritten_text must not be empty")
        return v


class ClarifyOptionsRequest(BaseModel):
    line_number: int
    check_id: str

    @field_validator("check_id")
    @classmethod
    def check_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("check_id must not be empty")
        return v


class SelectClarifyOptionRequest(BaseModel):
    line_number: int
    check_id: str
    chosen_text: str

    @field_validator("chosen_text")
    @classmethod
    def chosen_text_valid(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("chosen_text must not be empty")
        return v


class HandoffExportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")


class HandoffExportResponse(BaseModel):
    spec_id: int
    filename: str
    score: int
    verdict: str
    exported_at: str
    markdown_document: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_conn(request: Request):
    """Open a database connection from the app-level db_path."""
    return connect(request.app.state.db_path)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/specs", status_code=201)
def create_spec(body: CreateSpecRequest, request: Request):
    """Create a new spec and run the frozen linter analysis."""
    conn = _get_conn(request)
    try:
        result = analyze_spec(conn, body.filename, body.raw_text)
        return result
    finally:
        conn.close()


@router.get("/specs/{spec_id}")
def get_spec_analysis(spec_id: int, request: Request):
    """Return the current analysis for a spec using its rewrite overlays."""
    conn = _get_conn(request)
    try:
        result = get_analysis(conn, spec_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"spec_id {spec_id} not found")
        return result
    finally:
        conn.close()


@router.post("/specs/{spec_id}/rewrites")
def create_rewrite(spec_id: int, body: ApplyRewriteRequest, request: Request):
    """Apply a single-line rewrite overlay and re-analyze."""
    # Reject multi-line content at the route level (400)
    if "\n" in body.rewritten_text or "\r" in body.rewritten_text:
        raise HTTPException(
            status_code=400,
            detail="rewritten_text must be a single physical line (no \\n or \\r)",
        )

    conn = _get_conn(request)
    try:
        result = apply_rewrite(conn, spec_id, body.line_number, body.rewritten_text)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"spec_id {spec_id} not found")
    except ValueError as exc:
        msg = str(exc)
        if "out of range" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=422, detail=msg)
    finally:
        conn.close()


@router.delete("/specs/{spec_id}/rewrites/{line_number}")
def delete_one_rewrite(spec_id: int, line_number: int, request: Request):
    """Delete one rewrite overlay and re-analyze."""
    conn = _get_conn(request)
    try:
        result = remove_rewrite(conn, spec_id, line_number)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"spec_id {spec_id} not found")
    finally:
        conn.close()


@router.delete("/specs/{spec_id}/rewrites")
def delete_all_spec_rewrites(spec_id: int, request: Request):
    """Delete all rewrite overlays for a spec and re-analyze."""
    conn = _get_conn(request)
    try:
        result = reset_rewrites(conn, spec_id)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"spec_id {spec_id} not found")
    finally:
        conn.close()


@router.post("/specs/{spec_id}/clarify")
def get_clarify_options_route(spec_id: int, body: ClarifyOptionsRequest, request: Request):
    """Return two A/B clarify options for a finding without mutating state."""
    conn = _get_conn(request)
    try:
        result = get_clarify_options(conn, spec_id, body.line_number, body.check_id)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"spec_id {spec_id} not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        conn.close()


@router.post("/specs/{spec_id}/clarify/select")
def select_clarify_option_route(spec_id: int, body: SelectClarifyOptionRequest, request: Request):
    """Apply the chosen clarify option and return the updated analysis."""
    if "\n" in body.chosen_text or "\r" in body.chosen_text:
        raise HTTPException(
            status_code=400,
            detail="chosen_text must be a single physical line (no \\n or \\r)",
        )

    conn = _get_conn(request)
    try:
        result = select_clarify_option(conn, spec_id, body.line_number, body.check_id, body.chosen_text)
        return result
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"spec_id {spec_id} not found")
    except ValueError as exc:
        msg = str(exc)
        if "out of range" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=422, detail=msg)
    finally:
        conn.close()


@router.post("/specs/{spec_id}/handoff-export")
def export_handoff_pack(spec_id: int, body: HandoffExportRequest, request: Request):
    """Export a Markdown handoff document for a spec."""
    conn = _get_conn(request)
    try:
        result = build_handoff_export(conn, spec_id)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"spec_id {spec_id} not found")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Evidence Panel Route
# ---------------------------------------------------------------------------


@router.get("/specs/{spec_id}/evidence")
def get_spec_evidence(spec_id: int, request: Request):
    """Return evidence metrics for a spec.

    Computes initial_score from raw_text (no rewrites), current_score from
    effective text (with rewrites), findings resolved count, and benchmark
    metrics from the latest run.
    """
    conn = _get_conn(request)
    try:
        from backend.database import get_rewrites, get_spec
        from src.linter.evaluator import evaluate
        from src.linter.parser import parse_requirements
        from src.linter.rule_engine import run_checks

        spec_row = get_spec(conn, spec_id)
        if spec_row is None:
            raise HTTPException(status_code=404, detail=f"spec_id {spec_id} not found")

        raw_text = spec_row["raw_text"]

        # Initial score: run pipeline on raw_text (no rewrites)
        initial_records = parse_requirements(raw_text)
        initial_findings = run_checks(initial_records)
        initial_eval = evaluate(initial_records, initial_findings)
        initial_score = initial_eval.score

        # Current score: run pipeline on effective text (with rewrites)
        rewrites = get_rewrites(conn, spec_id)
        from backend.linter_adapter import _reconstruct_effective_text
        effective_text = _reconstruct_effective_text(raw_text, rewrites)
        current_records = parse_requirements(effective_text)
        current_findings = run_checks(current_records)
        current_eval = evaluate(current_records, current_findings)
        current_score = current_eval.score

        # Findings resolved: initial finding count minus current finding count
        findings_resolved = max(0, len(initial_findings) - len(current_findings))

        # Questions answered: count of clarification findings resolved via rewrites
        initial_clarifications = [f for f in initial_findings if f.severity == "clarification"]
        current_clarification_lines = {
            (f.line_number, f.check_id) for f in current_findings if f.severity == "clarification"
        }
        questions_answered = sum(
            1 for f in initial_clarifications
            if (f.line_number, f.check_id) not in current_clarification_lines
        )

        # Benchmark metrics
        latest_benchmark = get_latest_benchmark_run(conn)
        if latest_benchmark and latest_benchmark["completed_at"]:
            true_positive_ratio_pct = round(latest_benchmark["true_positive_ratio"] * 100, 2)
            detection_coverage_ratio_pct = round(latest_benchmark["detection_coverage_ratio"] * 100, 2)
            benchmark_available = True
        else:
            true_positive_ratio_pct = None
            detection_coverage_ratio_pct = None
            benchmark_available = False

        return {
            "spec_id": spec_id,
            "initial_score": initial_score,
            "current_score": current_score,
            "findings_resolved": findings_resolved,
            "questions_answered": questions_answered,
            "true_positive_ratio_pct": true_positive_ratio_pct,
            "detection_coverage_ratio_pct": detection_coverage_ratio_pct,
            "benchmark_available": benchmark_available,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Benchmark Routes
# ---------------------------------------------------------------------------


@router.post("/benchmark/run", status_code=200)
def run_benchmark_route(request: Request):
    """Trigger a benchmark execution, store results, return structured result.

    If a run is in progress, return 202 Accepted with a message.
    """
    conn = _get_conn(request)
    try:
        if is_benchmark_running(conn):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=202,
                content={"detail": "A benchmark run is already in progress."},
            )

        # Mark as in-progress
        started_at = datetime.now(timezone.utc).isoformat()
        in_progress_data = {
            "started_at": started_at,
            "completed_at": "",
            "total_cases": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "true_positive_ratio": 0.0,
            "detection_coverage_ratio": 0.0,
            "per_case_json": "[]",
        }
        run_id = insert_benchmark_run(conn, in_progress_data)
        conn.commit()

        # Execute the benchmark
        result = run_benchmark()

        # Update the run with results
        completed_at = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            UPDATE benchmark_runs
            SET completed_at = ?, total_cases = ?, true_positives = ?,
                false_positives = ?, false_negatives = ?,
                true_positive_ratio = ?, detection_coverage_ratio = ?,
                per_case_json = ?
            WHERE id = ?
            """,
            (
                completed_at,
                result["total_cases"],
                result["true_positives"],
                result["false_positives"],
                result["false_negatives"],
                result["true_positive_ratio"],
                result["detection_coverage_ratio"],
                json.dumps(result["per_case"]),
                run_id,
            ),
        )
        conn.commit()

        return {
            "id": run_id,
            "started_at": started_at,
            "completed_at": completed_at,
            "total_cases": result["total_cases"],
            "true_positives": result["true_positives"],
            "false_positives": result["false_positives"],
            "false_negatives": result["false_negatives"],
            "true_positive_ratio": result["true_positive_ratio"],
            "detection_coverage_ratio": result["detection_coverage_ratio"],
            "per_case": result["per_case"],
            "warnings": result.get("warnings", []),
        }
    finally:
        conn.close()


@router.get("/benchmark/results")
def get_benchmark_results(request: Request):
    """Return the latest stored benchmark result."""
    conn = _get_conn(request)
    try:
        latest = get_latest_benchmark_run(conn)
        if latest is None:
            return {"result": None}
        # Parse per_case_json back to list
        per_case = json.loads(latest["per_case_json"]) if latest["per_case_json"] else []
        return {
            "result": {
                "id": latest["id"],
                "started_at": latest["started_at"],
                "completed_at": latest["completed_at"],
                "total_cases": latest["total_cases"],
                "true_positives": latest["true_positives"],
                "false_positives": latest["false_positives"],
                "false_negatives": latest["false_negatives"],
                "true_positive_ratio": latest["true_positive_ratio"],
                "detection_coverage_ratio": latest["detection_coverage_ratio"],
                "per_case": per_case,
            }
        }
    finally:
        conn.close()
