#!/usr/bin/env python3
"""Check a run-card evidence schema without selecting or spending a submission slot.

Exit 0: evidence schema passes (NOT upload authorization); 1: negative; 2: unreadable/invalid JSON.
This does not authenticate evidence or replace raster/evaluator execution.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27.evidence_json import loads  # noqa: E402
from gems27.promotion import promotion_gate  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path)
    args = parser.parse_args(argv)
    try:
        card = loads(args.card.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"verdict": "negative", "evidence_schema_passed": False, "promotion_eligible": False, "submission_ready": False,
                          "slot_selected": False, "failures": [str(exc)]}), file=sys.stdout)
        return 2
    result = promotion_gate(card)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["verdict"] == "promote" else 1


if __name__ == "__main__":
    raise SystemExit(main())
