#!/usr/bin/env python3
"""Publish the current S27 fail-closed decision on site entry points; no network or upload calls."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = ROOT / "evidence/s27_run_card.json"
REPORT_PATH = ROOT / "knowledge/72_s27_active_branch_review_2026-10-28.md"
PANEL_ID = "s27-current-decision"
PAGES = {
    ROOT / "docs/index.html": ("downloads/", "data/s27_run_card.json"),
    ROOT / "docs/executive-summary.html": ("downloads/", "data/s27_run_card.json"),
    ROOT / "index.html": ("docs/downloads/", "docs/data/s27_run_card.json"),
    ROOT / "executive-summary.html": ("docs/downloads/", "docs/data/s27_run_card.json"),
}


def panel(card: dict, report_href: str, card_href: str, artifact_prefix: str, review_page_href: str) -> str:
    prior = card["holdout"]["prior_result_not_current"]
    archive = html.escape(card["raster"]["existing_research_artifact"].split("/")[-1], quote=True)
    score = float(prior["dti"])
    ci = prior["ci95"]
    return f'''<section class="section callout-danger" id="{PANEL_ID}" aria-label="Historical S27 submission decision" data-submission-ready="false">
<p class="eyebrow">S27 · 2026-10-28 UTC · PRIOR BRANCH REVIEW · NO NEW TIFF</p>
<h2>S27 decision (historical): NO FILE APPROVED · OK TO SUBMIT: NO</h2>
<p><strong>No new submission was generated.</strong> S26-TCB is only a ranked, untested hypothesis; preflight was blocked and exact-file validation failed closed in the S27 checkout. The archived S25 PCSE TIFF is <strong>research/audit only, not submission-ready</strong>; do not upload it.</p>
<table><thead><tr><th>Gate</th><th>Current result</th></tr></thead><tbody>
<tr><td>Current candidate HOLDOUT-DTI</td><td>Not run; no S27 candidate exists.</td></tr>
<tr><td>Prior S25 PCSE</td><td>HOLDOUT-DTI (gems-segment-pooled-v1) {score:.4f}; 95% CI {ci[0]:.4f}–{ci[1]:.4f}; {prior['withheld_positives']:,} withheld positives. Below same-fold random-K HOLDOUT-DTI {prior['random_k_control_dti']:.4f}; this is not a leaderboard score.</td></tr>
<tr><td>S27 exact validator</td><td>FAIL CLOSED in that historical checkout: local sample submission and labels were absent. No approval.</td></tr>
<tr><td>Unique new raster / upload</td><td>No new raster; no novelty result; no slot selected.</td></tr>
</tbody></table>
<p><strong>Research-only archive:</strong> <a href="{artifact_prefix}{archive}">{archive}</a>. Existing artifact link is provided for audit, not upload.</p>
<p><a href="{html.escape(review_page_href, quote=True)}">Open the S27 review page</a> · <a href="{html.escape(report_href, quote=True)}">Read the full report and nine-site table</a> · <a href="{html.escape(card_href, quote=True)}" download>Download S27 JSON run card</a></p>
</section>'''


def standalone(card: dict) -> str:
    body = panel(card,
                 "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/72_s27_active_branch_review_2026-10-28.md",
                 "data/s27_run_card.json", "downloads/", "s27-review.html")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>S27 active-branch review | GEMSDOE28</title><link rel="stylesheet" href="assets/site.css"></head>
<body><header class="site-header"><div class="header-inner"><a class="brand" href="index.html">GEMSDOE28 <small>DOE GEMS · Auditable research</small></a>
<nav aria-label="Main navigation"><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary</a><a href="s27-review.html">Current review</a></nav></div></header>
<main>{body}<section class="section"><h2>Historical decision boundary</h2><p>This review did not fit a model, run holdout DTI, emit a candidate raster, or select a submission slot. The S25 holdout value above is inherited historical evidence. The companion report documents the experiment blockers, four preregistered hypothesis choices, source limitations, validation passes, and exact nine-site historical scorecard.</p>
<p>The 0.2778 / 0.3195 / 0.4413 claims are not freshly confirmed from an organizer page. Score estimates remain unavailable rather than invented.</p></section></main></body></html>'''


def inject(path: Path, section: str) -> None:
    page = path.read_text(encoding="utf-8")
    marker = f'id="{PANEL_ID}"'
    if marker in page:
        start = page.rfind("<section", 0, page.index(marker))
        end = page.index("</section>", page.index(marker)) + len("</section>")
        page = page[:start] + page[end:]
    if "<main>" not in page:
        raise ValueError(f"Missing main element in {path}")
    page = page.replace("<main>", "<main>" + section, 1)
    path.write_text(page, encoding="utf-8")


def main() -> int:
    card = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    if card.get("branch") != "arena/265e6e24-gemsdoe28" or card.get("verdict") != "negative":
        raise ValueError("Refusing to publish a run card for a different branch or non-negative disposition")
    if card["submission"]["ok_to_submit"] is not False or card["submission"]["slot_selected"] is not False:
        raise ValueError("Refusing to render a card that selects or authorizes a submission")
    if not REPORT_PATH.is_file():
        raise FileNotFoundError(REPORT_PATH)
    report_href = "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/72_s27_active_branch_review_2026-10-28.md"
    for path, (artifact_prefix, card_href) in PAGES.items():
        review_page_href = "s27-review.html" if path.parent == ROOT / "docs" else "docs/s27-review.html"
        section = panel(card, report_href, card_href, artifact_prefix, review_page_href)
        inject(path, section)
    (ROOT / "docs/s27-review.html").write_text(standalone(card), encoding="utf-8")
    (ROOT / "docs/data/s27_run_card.json").write_text(
        json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "built", "pages": [p.relative_to(ROOT).as_posix() for p in PAGES],
                      "standalone": "docs/s27-review.html", "network_requests": 0,
                      "ok_to_submit": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
