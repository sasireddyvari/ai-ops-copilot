from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class IncidentRecord:
    incident_id: str
    title: str
    description: str
    service: str
    severity: str
    status: str
    created_at: str
    sla_hours: int
    owner_team: str
    tags: list[str]
    resolution_summary: str
    root_cause: str


@dataclass(frozen=True)
class KnowledgeArticle:
    article_id: str
    title: str
    body: str
    tags: list[str]
    services: list[str]


@dataclass
class AnalysisRequest:
    text: str
    incident_id: str | None = None
    backend: str | None = None


@dataclass
class RankedMatch:
    item_id: str
    title: str
    score: float
    reason: str


@dataclass
class AnalysisResult:
    input_text: str
    detected_service: str
    detected_severity: str
    age_hint_hours: float
    sla_risk: str
    risk_score: float
    similar_incidents: list[RankedMatch] = field(default_factory=list)
    knowledge_articles: list[RankedMatch] = field(default_factory=list)
    likely_root_causes: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    escalation_guidance: str = ""
    executive_summary: str = ""
    agentic_ai_tips: list[dict[str, Any]] = field(default_factory=list)
    backend_used: str = "rules"
    graph_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["similar_incidents"] = [asdict(item) for item in self.similar_incidents]
        payload["knowledge_articles"] = [asdict(item) for item in self.knowledge_articles]
        return payload
