from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .config import load_config
from .data_store import load_articles, load_incidents, load_sample_requests
from .llm_backends import ResponseContext, get_responder
from .retrieval import (
    detect_severity,
    detect_service,
    estimate_sla_risk,
    infer_age_hint_hours,
    infer_service_from_matches,
    rank_articles,
    rank_similar_incidents,
    top_root_cause_candidates,
)
from .schemas import AnalysisResult
from .tips import AGENTIC_AI_TIPS


class IncidentCopilotEngine:
    def __init__(self, backend: str | None = None, model_name: str | None = None):
        self.config = load_config()
        self.backend = backend or self.config.backend
        self.model_name = model_name or self.config.transformers_model
        self.incidents = load_incidents()
        self.articles = load_articles()
        self.responder = get_responder(self.backend, self.model_name)

    def build_context(self, text: str, incident_id: str | None = None) -> dict[str, Any]:
        source_text = text
        primary_incident = None
        if incident_id:
            primary_incident = next((item for item in self.incidents if item.incident_id == incident_id), None)
            if primary_incident:
                source_text = f"{primary_incident.title}. {primary_incident.description}"

        similar_incidents = rank_similar_incidents(source_text, self.incidents, limit=self.config.max_similar_incidents)
        knowledge_articles = rank_articles(source_text, self.articles, limit=self.config.max_articles)
        service = detect_service(source_text)
        if service == "unknown" and similar_incidents:
            service = infer_service_from_matches(similar_incidents, self.incidents)
        if service == "unknown" and primary_incident:
            service = primary_incident.service
        severity = detect_severity(source_text)
        age_hours = infer_age_hint_hours(source_text)
        sla_hours = primary_incident.sla_hours if primary_incident else 4
        risk_score, risk_label = estimate_sla_risk(severity, age_hours, sla_hours, similar_open_count=len(similar_incidents))
        root_causes = top_root_cause_candidates(source_text, self.incidents, limit=3)

        actions = [
            "Validate the impacted service and confirm the blast radius.",
            "Compare the current symptom pattern with the top similar incidents.",
            "Use the most relevant KB article as the runbook starting point.",
        ]
        if risk_label in {"high", "critical"}:
            actions.insert(0, "Escalate the incident to the owning team and start a recovery bridge.")
        if service == "5g ran":
            actions.append("Check radio parameter changes, neighbor relations, and DU health before making changes.")
        elif service == "messaging":
            actions.append("Inspect queue depth, connector throttling, and broker utilization.")
        elif service == "billing":
            actions.append("Inspect ETL retries, partition pruning, and month-end data skew.")
        elif service == "nms":
            actions.append("Verify maintenance windows and apply alarm suppression rules.")
        elif service == "crm":
            actions.append("Review auth cache saturation and token validation latency.")
        elif service == "customer portal":
            actions.append("Check API cluster saturation, hot partitions, and cache hit ratio.")

        escalation = (
            "Confidence is high enough to propose a playbook-based response."
            if risk_label in {"high", "critical"}
            else "Use this as a triage assist and confirm the findings with an operator before any major change."
        )

        return {
            "source_text": source_text,
            "primary_incident": primary_incident,
            "similar_incidents": similar_incidents,
            "knowledge_articles": knowledge_articles,
            "service": service,
            "severity": severity,
            "age_hours": age_hours,
            "sla_hours": sla_hours,
            "risk_score": risk_score,
            "risk_label": risk_label,
            "likely_root_causes": root_causes,
            "recommended_actions": actions,
            "escalation_guidance": escalation,
        }

    def draft_report(self, context: dict[str, Any]) -> str:
        responder_context = ResponseContext(
            input_text=context["source_text"],
            service=context["service"],
            severity=context["severity"],
            risk_label=context["risk_label"],
            risk_score=context["risk_score"],
            similar_incidents=[item.__dict__ for item in context["similar_incidents"]],
            knowledge_articles=[item.__dict__ for item in context["knowledge_articles"]],
            likely_root_causes=context["likely_root_causes"],
            recommended_actions=context["recommended_actions"],
            escalation_guidance=context["escalation_guidance"],
        )
        return self.responder.generate(responder_context)

    def analyze(self, text: str, incident_id: str | None = None, prefer_graph: bool | None = None) -> AnalysisResult:
        prefer_graph = self.config.use_graph if prefer_graph is None else prefer_graph
        graph_result = None
        graph_used = False
        if prefer_graph:
            try:
                from .graph_app import build_compiled_graph

                compiled = build_compiled_graph(self)
                if compiled is not None:
                    graph_result = compiled.invoke({"text": text, "incident_id": incident_id})
                    graph_used = True
            except Exception:
                graph_result = None
                graph_used = False

        if graph_result is None:
            context = self.build_context(text, incident_id)
            report = self.draft_report(context)
        else:
            context = graph_result["context"]
            report = graph_result["report"]
            graph_used = True

        return AnalysisResult(
            input_text=text,
            detected_service=context["service"],
            detected_severity=context["severity"],
            age_hint_hours=context["age_hours"],
            sla_risk=context["risk_label"],
            risk_score=context["risk_score"],
            similar_incidents=context["similar_incidents"],
            knowledge_articles=context["knowledge_articles"],
            likely_root_causes=context["likely_root_causes"],
            recommended_actions=context["recommended_actions"],
            escalation_guidance=context["escalation_guidance"],
            executive_summary=report,
            agentic_ai_tips=AGENTIC_AI_TIPS,
            backend_used=self.responder.backend_name,
            graph_used=graph_used,
        )

    def sample_requests(self) -> list[dict]:
        return load_sample_requests()


def build_engine(backend: str | None = None, model_name: str | None = None) -> IncidentCopilotEngine:
    return IncidentCopilotEngine(backend=backend, model_name=model_name)
