from __future__ import annotations

import sys
from pathlib import Path
import unittest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_ops_copilot.engine import build_engine


class EngineTests(unittest.TestCase):
    def test_analyze_returns_expected_sections(self) -> None:
        engine = build_engine(backend="rules")
        result = engine.analyze("Alarm flood after planned maintenance in NMS")
        self.assertEqual(result.detected_service, "nms")
        self.assertTrue(result.similar_incidents)
        self.assertTrue(result.knowledge_articles)
        self.assertIn("Recommended actions", result.executive_summary)
        self.assertTrue(result.agentic_ai_tips)

    def test_failure_case_escalates_when_evidence_is_weak(self) -> None:
        engine = build_engine(backend="rules")
        result = engine.analyze("Not enough data. A few users report intermittent issues.", prefer_graph=False)
        self.assertIn(result.sla_risk, {"medium", "high", "critical"})
        self.assertTrue(result.escalation_guidance)


if __name__ == "__main__":
    unittest.main()
