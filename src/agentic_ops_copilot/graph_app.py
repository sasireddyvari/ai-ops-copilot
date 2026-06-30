from __future__ import annotations

from typing import Any, TypedDict


class AnalysisState(TypedDict, total=False):
    text: str
    incident_id: str | None
    context: dict[str, Any]
    report: str


def build_compiled_graph(engine):
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception:
        return None

    graph = StateGraph(AnalysisState)

    def prepare(state: AnalysisState) -> AnalysisState:
        return {"context": engine.build_context(state["text"], state.get("incident_id"))}

    def draft(state: AnalysisState) -> AnalysisState:
        context = state["context"]
        report = engine.draft_report(context)
        return {"report": report}

    def finalize(state: AnalysisState) -> AnalysisState:
        context = state["context"]
        if context["risk_label"] in {"high", "critical"} and "Escalate" not in state["report"]:
            state["report"] += "\n\n## Safety note\nEscalate to the owning team before taking disruptive action."
        return state

    graph.add_node("prepare", prepare)
    graph.add_node("draft", draft)
    graph.add_node("finalize", finalize)
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "draft")
    graph.add_edge("draft", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()
