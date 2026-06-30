from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    backend: str = "rules"
    transformers_model: str = "distilgpt2"
    use_graph: bool = True
    max_similar_incidents: int = 3
    max_articles: int = 3


def load_config() -> AppConfig:
    backend = os.getenv("COPILOT_BACKEND", "rules").strip().lower()
    transformers_model = os.getenv("COPILOT_TRANSFORMERS_MODEL", "distilgpt2").strip()
    use_graph = os.getenv("COPILOT_USE_GRAPH", "1").strip() not in {"0", "false", "False"}
    return AppConfig(
        backend=backend,
        transformers_model=transformers_model,
        use_graph=use_graph,
        max_similar_incidents=3,
        max_articles=3,
    )
