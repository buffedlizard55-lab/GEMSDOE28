#!/usr/bin/env python3
"""Add the dated S28 decision after the historical overlays, without authorizing uploads."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = (ROOT / "docs/index.html", ROOT / "docs/executive-summary.html",
         ROOT / "index.html", ROOT / "executive-summary.html")


def main():
    for path in PAGES:
        page = path.read_text(encoding="utf-8")
        marker = 'id="s28-current-decision"'
        if marker in page:
            before, after = page.split(marker, 1)
            start, end = before.rfind("<section"), after.find("</section>")
            if start < 0 or end < 0:
                raise ValueError(f"Malformed S28 panel: {path}")
            page = before[:start] + after[end + len("</section>"):]
        if "<main>" not in page:
            raise ValueError(f"Missing main element: {path}")
        report = "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/73_s28_checkout_review_2026-10-29.md"
        panel = f'''<section class="section callout-danger" id="s28-current-decision" data-submission-ready="false">
<p class="eyebrow">S28 · 2026-10-29 UTC · CHECKOUT REVIEW</p>
<h2>NO NEW TIFF · OK TO SUBMIT: NO</h2>
<p>No new candidate has been validated, and no leaderboard score estimate is available. Archived TIFFs are for research, not upload. No slot was selected.</p>
<p>Owner-mirror core inputs, pinned shared tools and the feature cache were restored for this checkout; mirrors are not organizer-authenticated and ignored data do not persist in a new checkout. The latest preflight is blocked by the unassigned method lane, incomplete synchronized registry, literal overlap bound, missing comparable baseline and expired prior clock.</p>
<p>The dated exact-file audit found two historical all-finite variants with NaN nodata tags. Passing format checks alone does not prove uniqueness or high performance, and the cause of the portal error is unconfirmed. <a href="{report}">Read the full review, prior nine-site table and next steps</a>.</p>
</section>'''
        path.write_text(page.replace("<main>", "<main>" + panel, 1), encoding="utf-8")


if __name__ == "__main__":
    main()
