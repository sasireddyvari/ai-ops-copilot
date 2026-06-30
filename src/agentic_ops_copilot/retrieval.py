from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict
from typing import Callable, Iterable

from .schemas import IncidentRecord, KnowledgeArticle, RankedMatch


SERVICE_KEYWORDS = {
    "5g ran": ["5g", "handover", "radio", "du", "rrc", "attach"],
    "messaging": ["sms", "smpp", "queue", "delivery", "broker"],
    "billing": ["billing", "invoice", "usage", "etl", "retry"],
    "nms": ["alarm", "nms", "maintenance", "suppression", "dedup"],
    "crm": ["crm", "auth", "token", "login", "timeout"],
    "customer portal": ["portal", "latency", "api", "cpu", "traffic"],
}

SEVERITY_ORDER = {"sev1": 1, "sev2": 2, "sev3": 3, "sev4": 4}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", normalize(text)) if len(token) > 1]


def score_overlap(query: str, candidate: str) -> float:
    q_tokens = Counter(tokens(query))
    c_tokens = Counter(tokens(candidate))
    if not q_tokens or not c_tokens:
        return 0.0
    overlap = 0.0
    for token, q_count in q_tokens.items():
        if token in c_tokens:
            overlap += min(q_count, c_tokens[token])
    coverage = overlap / max(1.0, sum(q_tokens.values()))
    phrase = 0.15 if normalize(query) in normalize(candidate) else 0.0
    return round(coverage + phrase, 4)


def detect_service(text: str) -> str:
    lowered = normalize(text)
    best_service = "unknown"
    best_score = 0
    for service, keywords in SERVICE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_service = service
            best_score = score
    return best_service


def detect_severity(text: str) -> str:
    lowered = normalize(text)
    for severity in ("sev1", "sev2", "sev3", "sev4"):
        if severity in lowered:
            return severity.upper()
    if any(keyword in lowered for keyword in ("mass outage", "customers are unable", "flood", "critical")):
        return "SEV1"
    if any(
        keyword in lowered
        for keyword in (
            "dropped sessions",
            "handover failures",
            "failed handovers",
            "outage",
            "delay",
            "timeouts",
            "degradation",
            "spike",
            "slow",
            "failure",
        )
    ):
        return "SEV2"
    return "SEV3"


def infer_age_hint_hours(text: str) -> float:
    lowered = normalize(text)
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:h|hour|hours)", lowered)
    if matches:
        return float(matches[-1])
    if any(keyword in lowered for keyword in ("after shift change", "evening", "night", "month-end")):
        return 4.0
    return 1.5


def estimate_sla_risk(severity: str, age_hours: float, sla_hours: int, similar_open_count: int = 0) -> tuple[float, str]:
    sev_rank = SEVERITY_ORDER.get(severity.lower(), 3)
    sev_weight = {1: 1.0, 2: 0.72, 3: 0.45, 4: 0.25}.get(sev_rank, 0.45)
    age_factor = min(1.0, age_hours / max(1.0, float(sla_hours)))
    repeat_factor = min(0.2, similar_open_count * 0.05)
    score = min(0.99, sev_weight * 0.55 + age_factor * 0.35 + repeat_factor)
    if score >= 0.8:
        label = "critical"
    elif score >= 0.6:
        label = "high"
    elif score >= 0.35:
        label = "medium"
    else:
        label = "low"
    return round(score, 3), label


def _build_reason(query: str, candidate_text: str, score: float) -> str:
    query_tokens = set(tokens(query))
    candidate_tokens = set(tokens(candidate_text))
    overlap = sorted(query_tokens.intersection(candidate_tokens))
    if overlap:
        return f"shared terms: {', '.join(overlap[:4])}"
    return f"semantic similarity score {score:.2f}"


def rank_records(
    query: str,
    records: Iterable[IncidentRecord | KnowledgeArticle],
    text_getter: Callable[[IncidentRecord | KnowledgeArticle], str],
    id_getter: Callable[[IncidentRecord | KnowledgeArticle], str],
    title_getter: Callable[[IncidentRecord | KnowledgeArticle], str],
    limit: int = 3,
) -> list[RankedMatch]:
    scored: list[RankedMatch] = []
    for record in records:
        text = text_getter(record)
        score = score_overlap(query, text)
        if score <= 0.0:
            continue
        scored.append(
            RankedMatch(
                item_id=id_getter(record),
                title=title_getter(record),
                score=score,
                reason=_build_reason(query, text, score),
            )
        )
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]


def rank_similar_incidents(query: str, incidents: list[IncidentRecord], limit: int = 3) -> list[RankedMatch]:
    return rank_records(
        query=query,
        records=incidents,
        text_getter=lambda item: f"{item.title} {item.description} {' '.join(item.tags)} {item.root_cause}",
        id_getter=lambda item: item.incident_id,
        title_getter=lambda item: item.title,
        limit=limit,
    )


def rank_articles(query: str, articles: list[KnowledgeArticle], limit: int = 3) -> list[RankedMatch]:
    return rank_records(
        query=query,
        records=articles,
        text_getter=lambda item: f"{item.title} {item.body} {' '.join(item.tags)} {' '.join(item.services)}",
        id_getter=lambda item: item.article_id,
        title_getter=lambda item: item.title,
        limit=limit,
    )


def top_root_cause_candidates(query: str, incidents: list[IncidentRecord], limit: int = 3) -> list[str]:
    ranked = rank_similar_incidents(query, incidents, limit=limit)
    causes: list[str] = []
    for match in ranked:
        incident = next((item for item in incidents if item.incident_id == match.item_id), None)
        if incident and incident.root_cause not in causes:
            causes.append(incident.root_cause)
    return causes


def infer_service_from_matches(matches: list[RankedMatch], incidents: list[IncidentRecord]) -> str:
    if not matches:
        return "unknown"
    top = next((item for item in incidents if item.incident_id == matches[0].item_id), None)
    return top.service if top else "unknown"
