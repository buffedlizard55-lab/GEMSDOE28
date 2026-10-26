#!/usr/bin/env python3
"""Safety block for the historical S22-SIGN runner.

The exact code merged in PR 57 is preserved at
``evidence/snapshots/pr57_run_s22_candidate.py``. Its canary may be empty but
reported as passing, and its local quadrant proxy is not the shared required
holdout. It must not be rerun or used to promote a submission. Any new work
requires the assigned lane, complete registry, cached features, shared
whole-segment evaluator and the independent promotion gate.
"""


def main() -> None:
    raise SystemExit("BLOCKED: historical S22-SIGN runner is not the shared protocol; "
                     "see evidence/s22_sign_audit.json. No experiment was run.")


if __name__ == "__main__":
    main()
