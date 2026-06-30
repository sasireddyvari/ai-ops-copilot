from __future__ import annotations

import sys
from pathlib import Path
import unittest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agentic_ops_copilot.tips import AGENTIC_AI_TIPS


class TipsTests(unittest.TestCase):
    def test_tips_include_vllm_swaps(self) -> None:
        combined = " ".join(item["tip"] for item in AGENTIC_AI_TIPS).lower()
        self.assertIn("vllm", combined)


if __name__ == "__main__":
    unittest.main()
