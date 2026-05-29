"""
server.py — FastAPI server for Deconstruct Studio AI Engine.
Uses configurable DB (SQLite dev / PostgreSQL prod).
"""
import os, logging, urllib.request, json
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
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

# --- Fallback data for dev/demo mode (no API key) ---
FALLBACK = {
    "deep_read": {
        "summary": "本文讲述了一个出身卑微的年轻人，在历经家族覆灭、挚爱离世等重大打击后，凭借坚韧意志一步步崛起，最终在乱世中建立新秩序的故事。核心立意是：在极端逆境中，人性的选择比能力更能决定命运走向。",
        "emotion_curve": [
            {"position": 0, "valence": 0.3, "arousal": 0.4},
            {"position": 500, "valence": -0.6, "arousal": 0.7},
            {"position": 1000, "valence": 0.1, "arousal": 0.5},
            {"position": 1500, "valence": -0.8, "arousal": 0.9},
            {"position": 2000, "valence": -0.3, "arousal": 0.6},
            {"position": 2500, "valence": 0.5, "arousal": 0.5},
            {"position": 3000, "valence": 0.8, "arousal": 0.3},
        ],
        "hooks": [
            {"position": 50, "type": "悬念"},
            {"position": 800, "type": "冲突爆发"},
            {"position": 1500, "type": "情感冲击"},
            {"position": 2800, "type": "反转"},
        ],
    },
    "deconstruct": {
        "intent": "通过极端逆境中的人性选择，探讨命运走向的核心驱动力",
        "structure": "起（家族荣耀）→ 承（突遭变故）→ 转（绝境崛起）→ 合（新秩序建立）",
        "portable_logic": [
            "主角遭受不公后奋起反抗",
            "误会经过多重铺垫后解除",
            "底层人物通过坚持获得认可",
            "绝境中遇到关键导师",
        ],
        "specific_elements": [
            "在玄武门之变当天被赐婚",
            "用ChatGPT生成一封分手信",
            "在末日前夜收到母亲的信",
            "穿越到唐朝成为御厨",
        ],
    },
    "skeleton": {
        "text_skeleton": "触发（家族被灭）→ 逃亡（遇到导师）→ 隐忍修炼（3年）→ 首次反击（失败受重伤）→ 低谷（挚爱离世）→ 觉醒（发现真相）→ 决战（推翻旧秩序）→ 闭环（建立新秩序）",
        "mermaid_code": "graph TD\n  A[家族被灭] --> B[逃亡遇导师]\n  B --> C[隐忍修炼3年]\n  C --> D[首次反击失败]\n  D --> E[挚爱离世低谷]\n  E --> F[觉醒发现真相]\n  F --> G[决战推翻旧秩序]\n  G --> H[建立新秩序闭环]",
    },
    "strip_test": {
        "test_cases": [
            {"genre": "科幻", "rewritten": "宇航员在量子传送失败后，发现自己被困在时间裂缝中，每次醒来都是同一天的不同版本。"},
            {"genre": "校园", "rewritten": "高三学生在模拟考作弊被发现后，面临退学处分。班主任给了他一张空白答题卡，让他用一个月重新证明自己。"},
            {"genre": "宫廷", "rewritten": "宫女因在御前打碎茶杯被贬入冷宫，却在冷宫中发现了一道密道，通向先皇的秘密档案室。"},
        ],
    },
    "map_skeleton": {
        "text_skeleton": "触发（家族被灭）→ 逃亡（遇到导师）→ 隐忍修炼（3年）→ 首次反击（失败受重伤）→ 低谷（挚爱离世）→ 觉醒（发现真相）→ 决战（推翻旧秩序）→ 闭环（建立新秩序）",
        "mermaid_code": "graph TD\n  A[家族被灭] --> B[逃亡遇导师]\n  B --> C[隐忍修炼3年]\n  C --> D[首次反击失败]\n  D --> E[挚爱离世低谷]\n  E --> F[觉醒发现真相]\n  F --> G[决战推翻旧秩序]\n  G --> H[建立新秩序闭环]",
    },
}


def _run_ai_task(task_name: str, ctx: dict) -> dict:
    """Try LLM call; return fallback data if unavailable."""
    if llm is None:
        return dict(FALLBACK.get(task_name, {}))
    try:
        return llm.call(task_name, ctx)
    except Exception as e:
        _log.warning("LLM %s failed (%s), using fallback", task_name, e)
        return dict(FALLBACK.get(task_name, {}))

# --- Serve frontend SPA at /app ---
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    _log.info("Frontend mounted at /app from %s", frontend_dir)

# --- Dependencies (lazy-init LLM to allow graceful fallback) ---
db = db_from_config()
try:
    llm = LLM()
except Exception as e:
    _log.warning("LLM not available (%s), using fallback data for all AI tasks", e)
    llm = None
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


# --- AI task endpoints ---

@app.post("/api/deep-read")
def api_deep_read(req: TaskRequest):
    """Node 2: AI deep reading analysis."""
    ctx = {"original_text": req.original_text, "stage": req.stage}
    return _run_ai_task("deep_read", ctx)


@app.post("/api/deconstruct")
def api_deconstruct(req: TaskRequest):
    """Node 3: Layered deconstruction."""
    ctx = {"original_text": req.original_text, "stage": req.stage}
    return _run_ai_task("deconstruct", ctx)


@app.post("/api/map-skeleton")
def api_map_skeleton(req: TaskRequest):
    """Node 5: Generate narrative skeleton."""
    ctx = {
        "original_text": req.original_text,
        "user_answers": req.user_answers,
    }
    result = _run_ai_task("map_skeleton", ctx)
    return result


@app.post("/api/strip-test")
def api_strip_test(req: TaskRequest):
    """Node 4: Cross-genre strip test for a specific element."""
    ctx = {"specific_element": req.specific_element}
    return _run_ai_task("strip_test", ctx)


class FetchURLRequest(BaseModel):
    url: str


@app.post("/api/fetch-url")
def api_fetch_url(req: FetchURLRequest):
    """Fetch text content from a URL (CORS proxy for frontend)."""
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("utf-8", errors="replace")
            # Strip HTML tags for HTML content
            if "text/html" in content_type:
                import re
                text = re.sub(r"<[^>]+>", "", text)
                text = re.sub(r"\s+", " ", text).strip()
            return {"url": url, "content": text[:50000], "truncated": len(text) > 50000}
    except Exception as e:
        raise HTTPException(400, f"Failed to fetch URL: {e}")


@app.get("/")
def root():
    return {
        "service": "Deconstruct Studio AI Engine",
        "version": "0.2.0",
        "frontend": "/app",
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
