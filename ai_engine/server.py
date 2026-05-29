"""
server.py — FastAPI server for Deconstruct Studio AI Engine.
Exposes 7 AI tasks + validation as HTTP endpoints.
"""
import os, json, logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models.schemas import (
    Stage, Verdict, SimilarityInput, SimilarityOutput,
)
from validation.service import ValidationService
from core.llm import LLM

_log = logging.getLogger(__name__)
app = FastAPI(title="Deconstruct Studio AI Engine", version="0.1.0")
llm = LLM()
val_service = ValidationService()

# --- Request schemas ---

class TaskRequest(BaseModel):
    task: str
    stage: str = "novice"
    original_text: str = ""
    imitation_text: str = ""
    specific_element: str = ""
    user_answers: dict = {}
    previous_failures: int = 0
    allow_threshold_relaxation: bool = False

class TaskResponse(BaseModel):
    task: str
    status: str
    data: dict
    elapsed_ms: float = 0

# --- AI tasks ---

def _run_task(task_name: str, ctx: dict) -> dict:
    """Run a single AI task via LLM client."""
    start = datetime.utcnow()
    try:
        result = llm.call(task_name, ctx)
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        return {"task": task_name, "status": "ok", "data": result, "elapsed_ms": round(elapsed, 1)}
    except Exception as e:
        _log.error("Task %s failed: %s", task_name, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/task", response_model=TaskResponse)
def run_task(req: TaskRequest):
    """Run any AI task by name. Stateless — no DB writes."""
    ctx = {
        "original_text": req.original_text,
        "imitation_text": req.imitation_text,
        "specific_element": req.specific_element,
        "stage": req.stage,
        "user_answers": req.user_answers,
        "previous_failures": req.previous_failures,
        "warnings": [],
    }
    return _run_task(req.task, ctx)


@app.post("/validate", response_model=SimilarityOutput)
def validate(req: TaskRequest):
    """
    Run similarity validation. Returns verdict + warnings.
    Does NOT output cooldown fields (rule-engine's job).
    """
    sim_input = SimilarityInput(
        original_text=req.original_text,
        imitation_text=req.imitation_text,
        user_answers=req.user_answers,
        stage=Stage(req.stage),
        previous_failures=req.previous_failures,
        allow_threshold_relaxation=req.allow_threshold_relaxation,
    )
    return val_service.check(sim_input)


@app.post("/orchestrate")
def orchestrate(req: TaskRequest):
    """
    Run the full task chain for a deconstruction session.
    Task chain: deep_read -> deconstruct -> map_skeleton -> check_similarity.
    Returns all intermediate results.
    """
    chain = ["deep_read", "deconstruct", "map_skeleton"]
    results = {}
    for task_name in chain:
        ctx = {
            "original_text": req.original_text,
            "stage": req.stage,
            "user_answers": req.user_answers,
        }
        if task_name == "map_skeleton":
            ctx["deep_read_result"] = results.get("deep_read", {}).get("data", {})
            ctx["deconstruct_result"] = results.get("deconstruct", {}).get("data", {})
        resp = _run_task(task_name, ctx)
        results[task_name] = resp
    return {"tasks": results, "ecosystem": "complete"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-engine", "llm_stats": llm.stats()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
