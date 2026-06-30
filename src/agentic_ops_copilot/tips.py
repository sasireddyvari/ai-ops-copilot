from __future__ import annotations


AGENTIC_AI_TIPS = [
    {
        "title": "Keep tools narrow",
        "tip": "Each tool should do one thing well: search, score, summarize, or validate.",
        "why": "Smaller tools are easier to test, observe, and swap out later.",
    },
    {
        "title": "Separate retrieval from reasoning",
        "tip": "Gather evidence first, then draft the answer from the evidence bundle.",
        "why": "This reduces hallucination and makes the workflow easier to debug.",
    },
    {
        "title": "Use graph stages for control",
        "tip": "Model the agent as a graph so you can add checkpoints, retries, and gates.",
        "why": "A graph is easier to evolve than a single giant prompt.",
    },
    {
        "title": "Return structured outputs",
        "tip": "Have the model emit sections or JSON that downstream code can validate.",
        "why": "Structured outputs are safer for automation than free-form prose.",
    },
    {
        "title": "Design for fallback",
        "tip": "If the evidence is weak, the system should escalate rather than invent details.",
        "why": "Good agents know when to stop and ask for help.",
    },
    {
        "title": "Measure latency and cost",
        "tip": "Track time and token budget per step, not just final answer quality.",
        "why": "Agentic systems fail from slow or expensive loops as often as from bad answers.",
    },
    {
        "title": "Add human review on high-risk paths",
        "tip": "Make escalation explicit when SLA risk or confidence thresholds are high.",
        "why": "Enterprise workflows need an approval layer for sensitive actions.",
    },
    {
        "title": "Plan for local model swaps",
        "tip": "Start with a small Transformers model for demos and leave a clean adapter for vLLM later.",
        "why": "That gives you a low-friction demo path and a scale path for production.",
    },
]
