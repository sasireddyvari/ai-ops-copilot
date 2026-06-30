from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .schemas import IncidentRecord, KnowledgeArticle


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"


def _load_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_incidents() -> list[IncidentRecord]:
    raw = _load_json(DATA_DIR / "incidents.json")
    return [IncidentRecord(**item) for item in raw]


def load_articles() -> list[KnowledgeArticle]:
    raw = _load_json(DATA_DIR / "kb_articles.json")
    return [KnowledgeArticle(**item) for item in raw]


def load_sample_requests() -> list[dict]:
    return _load_json(DATA_DIR / "sample_requests.json")


def find_incident(incident_id: str) -> IncidentRecord | None:
    for incident in load_incidents():
        if incident.incident_id == incident_id:
            return incident
    return None


def incident_to_dict(incident: IncidentRecord) -> dict:
    return asdict(incident)


def article_to_dict(article: KnowledgeArticle) -> dict:
    return asdict(article)
