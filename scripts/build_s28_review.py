#!/usr/bin/env python3
"""Publish a fail-closed correction to the S25 novelty claim; no network access."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "evidence/s28_run_card.json"
AUDIT = ROOT / "evidence/s28_pcse_lattice_audit.json"
PANEL_ID = "s28-current-decision"
PAGES = [ROOT / "index.html", ROOT / "executive-summary.html",
         ROOT / "docs/index.html", ROOT / "docs/executive-summary.html"]


def render(card: dict, audit: dict) -> str:
    candidate = audit["inherited_candidate"]
    overlap = candidate["final_dot_comparison"]["max_dot_overlap"]
    if (card.get("submission_ready") is not False or card.get("slot_selected") is not False
            or card.get("verdict") != "negative" or audit.get("status") != "DUPLICATE_STOP"
            or candidate.get("sha256") != card.get("historical_s25_sha256")
            or candidate.get("duplicate_under_literal_rule") is not True
            or not isinstance(overlap, (int, float)) or not 0.70 < overlap <= 1):
        raise ValueError("Inconsistent negative review or duplicate evidence")
    return f'''<section class="section callout-danger" id="{PANEL_ID}" aria-label="Latest submission decision" data-submission-ready="false">
<p class="eyebrow">29 OCT 2026 · CURRENT CHECKOUT REVIEW</p>
<h2>NO FILE APPROVED · OK TO SUBMIT: NO</h2>
<p>No new TIFF, score estimate, geological experiment, or submission slot. An explicit parallel lane, synchronized registry and comparable frozen baseline are missing. A separate selector must decide any future submission.</p>
<p><strong>Correction:</strong> the old S25 PCSE TIFF is a duplicate under the literal shared-registry rule: {overlap:.1%} of its dots are within 3 pixels of a registered calibration raster. Its earlier “unique” claim applied only to a limited local comparison and is superseded. It also failed its prior holdout. Do not submit it.</p>
<p>The nine-site historical scorecard below reports user-supplied scores, not organizer-confirmed receipts. A reliable hidden-score estimate is unavailable. <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/73_s28_review_2026-10-29.md">Full review and nine-site decision</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/s28_pcse_lattice_audit.json">Exact duplicate audit</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/s28_run_card.json">JSON run card</a>.</p>
</section>'''


def main() -> int:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    panel = render(card, audit)
    for path in PAGES:
        page = path.read_text(encoding="utf-8")
        marker = f'id="{PANEL_ID}"'
        if marker in page:
            start = page.rfind("<section", 0, page.index(marker))
            end = page.index("</section>", page.index(marker)) + len("</section>")
            if start < 0:
                raise ValueError(f"Malformed prior panel: {path}")
            page = page[:start] + page[end:]
        if "<main>" not in page:
            raise ValueError(f"Missing main element: {path}")
        path.write_text(page.replace("<main>", "<main>" + panel, 1), encoding="utf-8")
    print(json.dumps({"status": "built", "submission_ready": False, "network_requests": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
