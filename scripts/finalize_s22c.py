#!/usr/bin/env python3
"""Blocked historical entry point; do not restore a superseded promotion claim.

The original source is immutable at
 evidence/snapshots/pre_s23_finalize_s22c.py.
S23 proves a literal registry duplicate, independently of format validity.
"""
from __future__ import annotations

import json


def main() -> int:
    print(json.dumps({
        "status": "BLOCKED_HISTORICAL_DUPLICATE",
        "submission_ready": False,
        "slot_selected": False,
        "new_tiff_generated": False,
        "reason": "S22C fails the any-registry overlap rule; never regenerate its old promote claim.",
        "current_evidence": "evidence/s23_registry_feasibility.json",
        "original_source": "evidence/snapshots/pre_s23_finalize_s22c.py",
    }, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
