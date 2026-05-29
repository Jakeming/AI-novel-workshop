"""
server.py — FastAPI server for Deconstruct Studio AI Engine.
Uses configurable DB (SQLite dev / PostgreSQL prod).
"""
import os, logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from models.schemas import Stage, SimilarityInput
from validation.service import ValidationService
from core.llm import LLM
from core.db import db_from_config
from probe.context import ProbeContextLoader, ProbeContext
from probe.context import RejectionLoopProbe, InspirationPollutionProbe
from probe.context import SkeletonDiversityProbe, AbuseProbe, RateLimitProbe

_log = logging.getLogger(__name__)
app = FastAPI(title="Deconstruct Studio AI Engine", version="0.2.0")

# --- Dependencies ---
db = db_from_config()
llm = LLM()
val_service = ValidationService()
probe_loader = ProbeContextLoader(db)
_probes = [
    RejectionLoopProbe(), InspirationPollutionProbe(),
    SkeletonDiversityProbe(), AbuseProbe(), RateLimitProbe(),
]

def get_db():
    return db

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
    user_id: int = 1
    session_id: int = 0
    source_title: str = ""

class TaskResponse(BaseModel):
    task: str
    status: str
    data: dict
    elapsed_ms: float = 0
    session_id: int = 0


# --- DB-backed endpoints ---

@app.post("/session/start")
def start_session(req: TaskRequest, db=Depends(get_db)):
    """Start a new deconstruction session."""
    user = db.get_user(req.user_id)
    if not user:
        db.create_user(f"user_{req.user_id}")
    sid = db.create_session(req.user_id, req.source_title)
    return {"session_id": sid, "status": "created"}


@app.post("/session/{session_id}/node/{node}")
def complete_node(session_id: int, node: int, db=Depends(get_db)):
    """Mark a workflow node as complete."""
    if node < 1 or node > 7:
        raise HTTPException(400, "Node must be 1-7")
    db.update_session_node(session_id, node)
    return {"session_id": session_id, "node": node, "status": "completed"}


@app.post("/validate", response_model=dict)
def validate(req: TaskRequest, db=Depends(get_db)):
    """Run similarity validation. Saves result to DB."""
    sim_input = SimilarityInput(
        original_text=req.original_text,
        imitation_text=req.imitation_text,
        user_answers=req.user_answers,
        stage=Stage(req.stage),
        previous_failures=req.previous_failures,
        allow_threshold_relaxation=req.allow_threshold_relaxation,
    )
    result = val_service.check(sim_input)
    # Persist
    session = db.get_session(req.session_id) if req.session_id else None
    if session:
        db.update_session_verdict(req.session_id, result.verdict.value)
        db.save_draft(req.session_id, req.imitation_text[:500], result.verdict.value)
    return result.__dict__


@app.post("/probe/run")
def run_probes(user_id: int = 1, db=Depends(get_db)):
    """Run all guardian probes for a user."""
    ctx = probe_loader.load(str(user_id))
    alerts = []
    for probe in _probes:
        alert = probe.run(ctx)
        if alert:
            alerts.append({"probe": alert.probe, "severity": alert.severity, "message": alert.message})
    return {"user_id": user_id, "alerts": alerts, "context": {
        "consecutive_failures_2h": ctx.consecutive_failures_2h,
    }}


@app.get("/session/{session_id}")
def get_session(session_id: int, db=Depends(get_db)):
    """Get full session details."""
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    drafts = db.get_drafts(session_id)
    return {"session": session, "drafts": drafts}


@app.get("/")
def root():
    return {
        "service": "Deconstruct Studio AI Engine",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-engine", "version": "0.2.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
