from __future__ import annotations

from dataclasses import dataclass
from textwrap import indent


@dataclass
class ResponseContext:
    input_text: str
    service: str
    severity: str
    risk_label: str
    risk_score: float
    similar_incidents: list[dict]
    knowledge_articles: list[dict]
    likely_root_causes: list[str]
    recommended_actions: list[str]
    escalation_guidance: str


class RuleBasedResponder:
    """Deterministic fallback that keeps the demo reliable without a model."""

    backend_name = "rules"

    def generate(self, context: ResponseContext) -> str:
        incident_lines = []
        for item in context.similar_incidents:
            incident_lines.append(f"- {item['item_id']}: {item['title']} ({item['reason']})")
        article_lines = []
        for item in context.knowledge_articles:
            article_lines.append(f"- {item['item_id']}: {item['title']} ({item['reason']})")

        root_causes = context.likely_root_causes or ["Insufficient evidence yet; treat as a human-review case."]
        actions = context.recommended_actions or [
            "Collect missing evidence from logs and alarms.",
            "Confirm the exact blast radius and impacted customers.",
            "Escalate to the owning team with the evidence bundle.",
        ]

        return f"""## Executive summary
Service: {context.service}
Severity: {context.severity}
Risk: {context.risk_label} ({context.risk_score:.2f})

## Similar incidents
{chr(10).join(incident_lines) if incident_lines else '- No strong similar incidents found.'}

## Knowledge articles
{chr(10).join(article_lines) if article_lines else '- No strong knowledge-base match found.'}

## Likely root causes
{chr(10).join(f'- {item}' for item in root_causes)}

## Recommended actions
{chr(10).join(f'- {item}' for item in actions)}

## Escalation guidance
{context.escalation_guidance}
"""


class TransformersResponder:
    """Optional demo backend using Hugging Face Transformers.

    If you have a GPU, this is the place to swap in a larger model or point the app
    to a vLLM-served endpoint for higher throughput.
    """

    backend_name = "transformers"

    def __init__(self, model_name: str = "distilgpt2"):
        try:
            from transformers import pipeline
        except Exception as exc:  # pragma: no cover - dependency optional
            raise RuntimeError("transformers is not installed") from exc

        self.model_name = model_name
        # For demos this keeps the dependency lightweight.
        # If you have a GPU, you can change this to device_map='auto' or use a vLLM server.
        self.generator = pipeline(
            "text-generation",
            model=model_name,
            max_new_tokens=220,
            do_sample=False,
        )

    def generate(self, context: ResponseContext) -> str:
        prompt = f"""
You are an enterprise AI operations copilot.
Write a concise incident analysis with these sections:
Executive summary, Likely root causes, Recommended actions, Escalation guidance.

Incident:
{context.input_text}

Evidence:
{context}
"""
        try:
            output = self.generator(prompt)[0]["generated_text"]
        except Exception:
            return RuleBasedResponder().generate(context)
        return output.split("Incident:")[-1].strip() if "Incident:" in output else output.strip()


def get_responder(backend: str, model_name: str = "distilgpt2"):
    backend = (backend or "rules").strip().lower()
    if backend == "transformers":
        try:
            return TransformersResponder(model_name=model_name)
        except Exception:
            return RuleBasedResponder()
    return RuleBasedResponder()


def summarize_context(context: ResponseContext) -> str:
    similar = "\n".join(f"- {item['item_id']}: {item['title']}" for item in context.similar_incidents) or "- None"
    articles = "\n".join(f"- {item['item_id']}: {item['title']}" for item in context.knowledge_articles) or "- None"
    return f"""Service: {context.service}
Severity: {context.severity}
Risk: {context.risk_label} ({context.risk_score:.2f})

Similar incidents:
{indent(similar, '  ')}

Articles:
{indent(articles, '  ')}
"""
