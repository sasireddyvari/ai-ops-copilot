from __future__ import annotations

import sys
from pathlib import Path
import unittest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_ops_copilot.data_store import load_articles, load_incidents
from agentic_ops_copilot.retrieval import (
    detect_service,
    estimate_sla_risk,
    rank_articles,
    rank_similar_incidents,
)


class RetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.incidents = load_incidents()
        self.articles = load_articles()

    def test_detect_service_for_5g(self) -> None:
        service = detect_service("5G handover failures after radio refresh")
        self.assertEqual(service, "5g ran")

    def test_rank_similar_incidents_prioritizes_5g_case(self) -> None:
        matches = rank_similar_incidents("5G handover failures after radio refresh", self.incidents, limit=2)
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0].item_id, "INC-10421")

    def test_rank_articles_prioritizes_matching_runbook(self) -> None:
        matches = rank_articles("alarm flood after maintenance", self.articles, limit=2)
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0].item_id, "KB-2001")

    def test_estimate_sla_risk_increases_for_sev1(self) -> None:
        score, label = estimate_sla_risk("SEV1", age_hours=3.0, sla_hours=1, similar_open_count=2)
        self.assertGreater(score, 0.7)
        self.assertIn(label, {"high", "critical"})


if __name__ == "__main__":
    unittest.main()
