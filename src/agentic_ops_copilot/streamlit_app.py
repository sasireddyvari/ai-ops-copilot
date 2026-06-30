from __future__ import annotations

try:
    import streamlit as st
except Exception as exc:  # pragma: no cover - optional until deps are installed
    raise RuntimeError("Install dependencies from requirements.txt before running the UI.") from exc

from .engine import build_engine
from .data_store import load_sample_requests


engine = build_engine()


def render_sidebar() -> None:
    st.sidebar.title("Agentic AI tips")
    st.sidebar.caption("Practical guidance from this repo")
    for item in engine.analyze("demo").agentic_ai_tips:
        with st.sidebar.expander(item["title"], expanded=False):
            st.write(item["tip"])
            st.caption(item["why"])


def main() -> None:
    st.set_page_config(page_title="AI Operations Copilot", page_icon="🧭", layout="wide")
    render_sidebar()

    st.title("AI Operations Copilot")
    st.write(
        "An enterprise incident triage demo that searches similar cases, grounds the response in evidence, "
        "and recommends next steps."
    )

    samples = load_sample_requests()
    sample_lookup = {item["name"]: item["text"] for item in samples}
    selected_sample = st.selectbox("Load a sample incident", ["Custom"] + [item["name"] for item in samples])
    default_text = sample_lookup.get(selected_sample, "")
    incident_text = st.text_area("Incident / ticket text", value=default_text, height=220)

    col1, col2 = st.columns([2, 1])
    with col2:
        backend = st.selectbox("Backend", ["rules", "transformers"], index=0)
        incident_id = st.text_input("Optional incident ID", value="")
        analyze_button = st.button("Analyze incident", type="primary")

    if analyze_button and incident_text.strip():
        local_engine = build_engine(backend=backend)
        result = local_engine.analyze(
            incident_text.strip(),
            incident_id=incident_id.strip() or None,
            prefer_graph=True,
        )
        st.success(f"Analysis complete using {result.backend_used} backend")
        left, right = st.columns([1, 1])
        with left:
            st.subheader("Operational summary")
            st.metric("Service", result.detected_service)
            st.metric("Severity", result.detected_severity)
            st.metric("SLA risk", result.sla_risk)
            st.metric("Risk score", f"{result.risk_score:.2f}")
            st.markdown("### Likely root causes")
            for item in result.likely_root_causes:
                st.write(f"- {item}")
            st.markdown("### Recommended actions")
            for item in result.recommended_actions:
                st.write(f"- {item}")
        with right:
            st.subheader("Grounded evidence")
            st.markdown("### Similar incidents")
            for item in result.similar_incidents:
                st.write(f"- {item.item_id}: {item.title} ({item.reason})")
            st.markdown("### Knowledge articles")
            for item in result.knowledge_articles:
                st.write(f"- {item.item_id}: {item.title} ({item.reason})")

        st.markdown("## Report")
        st.markdown(result.executive_summary)
    elif analyze_button:
        st.warning("Please enter some incident text before running the copilot.")


if __name__ == "__main__":
    main()
