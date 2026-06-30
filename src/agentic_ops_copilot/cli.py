from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import build_engine
from .data_store import load_sample_requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI Operations Copilot demo")
    parser.add_argument("--sample", type=int, default=None, help="1-based index of the demo sample to analyze")
    parser.add_argument("--text", type=str, default=None, help="Custom incident text")
    parser.add_argument("--backend", type=str, default=None, help="rules or transformers")
    args = parser.parse_args()

    samples = load_sample_requests()
    if args.text:
        text = args.text
    elif args.sample:
        text = samples[max(0, args.sample - 1) % len(samples)]["text"]
    else:
        text = samples[0]["text"]

    engine = build_engine(backend=args.backend)
    result = engine.analyze(text)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
