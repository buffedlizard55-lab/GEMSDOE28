#!/usr/bin/env python3
"""Publish the active-branch review without mutating S23 hash-bound generators.

Run after scripts/build_site.py. This add-on keeps the historical S23 source
bytes intact while exposing the newest checkout-level decision on key pages.
It performs no network requests and never unlocks a TIFF download.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REVIEW = ROOT / "evidence/active_checkout_review_2026-10-27.json"
PAGES = {
    DOCS / "index.html": "data/active_checkout_review_2026-10-27.json",
    DOCS / "executive-summary.html": "data/active_checkout_review_2026-10-27.json",
    DOCS / "cross-site-review.html": "data/active_checkout_review_2026-10-27.json",
    DOCS / "session23-result.html": "data/active_checkout_review_2026-10-27.json",
    ROOT / "index.html": "docs/data/active_checkout_review_2026-10-27.json",
    ROOT / "executive-summary.html": "docs/data/active_checkout_review_2026-10-27.json",
}


def render(review: dict, card_link: str) -> str:
    checked = html.escape(str(review.get("observed_utc", "not recorded")))
    branch = html.escape(str(review.get("branch", "unknown")))
    blockers = review.get("preflight", {}).get("blockers", [])
    if not isinstance(blockers, list):
        raise ValueError("Review preflight blockers must be a list")
    blocker_text = " ".join(html.escape(str(item)) for item in blockers)
    review_page = "docs/session24-review.html" if card_link.startswith("docs/") else "session24-review.html"
    safe_review_page = html.escape(review_page, quote=True)
    holdout = review.get("holdout", {})
    if not isinstance(holdout, dict) or holdout.get("dti") is not None:
        raise ValueError("Current review must not claim an unrun HOLDOUT-DTI")
    if review.get("executive_decision", {}).get("submission_ready") is not False:
        raise ValueError("Active review is not a negative fail-closed decision")
    return f'''<section class="section callout-warning" id="active-checkout-review" aria-label="Prior parallel checkout review">
<p class="eyebrow">PRIOR PARALLEL-CHECKOUT RECORD · {checked} · {branch}</p>
<h2>Prior checkout status: NO — no new TIFF was generated</h2>
<p>This immutable review belongs to a different branch and is retained as parallel-session provenance; its data/cache and shared-tool state do not describe the active checkout. That review recorded a blocked preflight and no HOLDOUT-DTI. For the current repository-review disposition, open <a href="{safe_review_page}">the S24 review for this branch</a>.</p>
<p><strong>Blockers recorded by the prior checkout:</strong> {blocker_text}</p>
<p><a href="{html.escape(card_link, quote=True)}">Open the prior checkout's JSON record</a> · <a href="{safe_review_page}">Current S24 repository review</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/68_active_checkout_review_2026-10-27.md">Read the prior detailed review</a>. No score estimate, weekly slot, or upload authorization is asserted.</p>
</section>'''


def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    if not isinstance(review, dict):
        raise ValueError("Active checkout review must be a JSON object")
    output_json = DOCS / "data/active_checkout_review_2026-10-27.json"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(review, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    updated = []
    for path, card_link in PAGES.items():
        page = path.read_text(encoding="utf-8")
        marker = 'id="active-checkout-review"'
        if marker in page:
            before, after = page.split(marker, 1)
            end = after.find("</section>")
            if end < 0:
                raise ValueError(f"Malformed previous active-review panel in {path}")
            section_start = before.rfind("<section")
            if section_start < 0:
                raise ValueError(f"Missing previous section opener in {path}")
            page = before[:section_start] + after[end + len("</section>"):]
        if "<main>" not in page:
            raise ValueError(f"Missing main element in generated page {path}")
        panel = render(review, card_link)
        page = page.replace("<main>", "<main>" + panel, 1)
        path.write_text(page, encoding="utf-8")
        updated.append(path.relative_to(ROOT).as_posix())
    # S25 add-on: the newest decision panel is inserted above the historical panel (same CI pass).
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    import build_s25_page  # noqa: PLC0415

    build_s25_page.main()
    import build_s27_review  # noqa: PLC0415

    build_s27_review.main()
    import build_s28_review  # noqa: PLC0415

    build_s28_review.main()
    print(json.dumps({"status": "built", "pages": updated,
                      "review_card": "docs/data/active_checkout_review_2026-10-27.json",
                      "network_requests": 0, "submission_ready": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
