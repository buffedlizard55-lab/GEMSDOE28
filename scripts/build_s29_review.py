#!/usr/bin/env python3
"""Overlay the current fail-closed S29 decision on public entry pages.

Standard-library only. It never reads rasters or performs network requests; a missing/invalid run
card fails closed rather than exposing a submission download.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "evidence/s29_run_card.json"
PAGES = {
    ROOT / "docs/index.html": ("data/s29_run_card.json", "s29-review.html"),
    ROOT / "docs/executive-summary.html": ("data/s29_run_card.json", "s29-review.html"),
    ROOT / "index.html": ("docs/data/s29_run_card.json", "docs/s29-review.html"),
    ROOT / "executive-summary.html": ("docs/data/s29_run_card.json", "docs/s29-review.html"),
}
PANEL_ID = "s29-current-decision"


def panel(card_href: str, review_href: str) -> str:
    return f'''<section class="section callout-danger" id="{PANEL_ID}" aria-label="Current S29 submission decision" data-submission-ready="false">
<p class="eyebrow">S29 · 2026-10-29 UTC · AUTOMATED REVIEW</p>
<h2>NO FILE APPROVED · OK TO DOWNLOAD AND SUBMIT: NO</h2>
<p><strong>No new TIFF was generated.</strong> This checkout has no assigned method lane, restored cache/shared template, complete synchronized registry, frozen comparable baseline, or fresh experiment authorization. No score estimate is defensible.</p>
<div class="download-actions"><button class="button" type="button" disabled aria-disabled="true">No approved TIFF to download</button><a class="button quiet" href="{card_href}" download>Download S29 run card</a><a class="button quiet" href="{review_href}">Nine-site executive review</a></div>
<p>Historical TIFFs are audit-only and must not be submitted. <a href="{review_href}">See the nine-site table, candidate slate, source links and limitations.</a></p>
</section>'''


def inject(path: Path, section: str) -> None:
    text = path.read_text(encoding="utf-8")
    marker = f'id="{PANEL_ID}"'
    if marker in text:
        marker_position = text.index(marker)
        start = text.rfind("<section", 0, marker_position)
        end = text.index("</section>", marker_position) + len("</section>")
        text = text[:start] + text[end:]
    if "<main>" not in text:
        raise ValueError(f"Missing main element in {path}")
    text = text.replace("<main>", "<main>" + section, 1)
    text = text.replace('href="s28c-review.html">Latest review',
                        'href="s29-review.html">Current review')
    text = text.replace('href="docs/s28c-review.html">Latest review',
                        'href="docs/s29-review.html">Current review')
    path.write_text(text, encoding="utf-8")


def validate_card(card: dict) -> None:
    required_false = ("new_tiff_generated", "submission_ready", "ok_to_download_and_submit", "slot_selected")
    if card.get("schema") != "gemsdoe28-s29-repository-review-v1":
        raise ValueError("Unexpected S29 run-card schema")
    if card.get("verdict") != "negative" or any(card.get(key) is not False for key in required_false):
        raise ValueError("S29 publisher accepts only a negative, no-download, no-slot run card")
    if card.get("raster_sha256") is not None or card.get("submission_name") is not None:
        raise ValueError("A negative review must not name or link a candidate TIFF")


def main() -> int:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    validate_card(card)
    published_card = ROOT / "docs/data/s29_run_card.json"
    published_card.parent.mkdir(parents=True, exist_ok=True)
    published_card.write_bytes(CARD.read_bytes())
    for path, (card_href, review_href) in PAGES.items():
        inject(path, panel(card_href, review_href))
    print(json.dumps({"status": "built", "panel": PANEL_ID, "pages": [p.relative_to(ROOT).as_posix() for p in PAGES],
                      "network_requests": 0, "new_tiff": False, "ok_to_submit": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
