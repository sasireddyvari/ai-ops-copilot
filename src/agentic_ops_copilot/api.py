from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover - optional until deps are installed
    FastAPI = None  # type: ignore
    HTTPException = RuntimeError  # type: ignore
    BaseModel = object  # type: ignore

    def Field(*args, **kwargs):  # type: ignore
        return None

from .engine import build_engine
from .data_store import load_articles, load_incidents


class AnalyzeRequest(BaseModel):  # type: ignore[misc]
    text: str = Field(..., description="Incident or ticket text")
    incident_id: str | None = Field(default=None, description="Optional demo incident ID")
    backend: str | None = Field(default=None, description="rules or transformers")


if FastAPI is not None:
    app = FastAPI(title="AI Operations Copilot", version="0.1.0")
    engine = build_engine()

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "backend": engine.responder.backend_name,
            "graph_enabled": engine.config.use_graph,
            "incidents": len(load_incidents()),
            "knowledge_articles": len(load_articles()),
        }

    @app.get("/demo/incidents")
    def demo_incidents() -> list[dict[str, Any]]:
        return [item.__dict__ for item in load_incidents()]

    @app.get("/demo/articles")
    def demo_articles() -> list[dict[str, Any]]:
        return [item.__dict__ for item in load_articles()]

    @app.post("/analyze")
    def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
        local_engine = build_engine(backend=payload.backend)
        result = local_engine.analyze(payload.text, incident_id=payload.incident_id)
        return result.to_dict()

    @app.get("/tips")
    def tips() -> dict[str, Any]:
        return {"tips": engine.analyze("demo").agentic_ai_tips}

else:  # pragma: no cover
    app = None


def run_server() -> None:
    if app is None:
        raise RuntimeError("Install dependencies from requirements.txt before running the API.")
    import uvicorn

    uvicorn.run("agentic_ops_copilot.api:app", host="0.0.0.0", port=8000, reload=True)
