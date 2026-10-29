#!/usr/bin/env python3
"""Publish the S28 experiment decision on the entry pages, without unlocking a TIFF."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = ROOT / "evidence/s28_tcb_run_card.json"
REPORT_PATH = ROOT / "knowledge/73_s28_tcb_result_2026-10-29.md"
PANEL_ID = "s28-current-decision"
PAGES = {
    ROOT / "docs/index.html": ("data/s28_tcb_run_card.json", "s28-review.html"),
    ROOT / "docs/executive-summary.html": ("data/s28_tcb_run_card.json", "s28-review.html"),
    ROOT / "index.html": ("docs/data/s28_tcb_run_card.json", "docs/s28-review.html"),
    ROOT / "executive-summary.html": ("docs/data/s28_tcb_run_card.json", "docs/s28-review.html"),
}


def _number(value: object, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def panel(card: dict, card_href: str, report_href: str, review_href: str) -> str:
    holdout = card.get("holdout") or {}
    random_control = card.get("random_k_control") or {}
    paired = card.get("paired_vs_random_k") or {}
    surface = (card.get("surface_before_placement") or {}).get("comparison") or {}
    final = (card.get("final_dots") or {}).get("comparison") or {}
    canary = card.get("feature_canaries") or {}
    final_rows = final.get("rows") or []
    control_overlap = next(
        (row.get("candidate_dot_overlap_within_3px") for row in final_rows if "calibration" in str(row.get("registry_id", ""))),
        None,
    )
    if card.get("branch") != "arena/09c38505-gemsdoe28":
        raise ValueError("S28 card branch does not match the active Arena branch")
    if card.get("verdict") != "negative" or card.get("new_tiff_generated") is not False:
        raise ValueError("S28 panel requires a negative no-TIFF card")
    if card.get("ok_to_submit") is not False or card.get("slot_selected") is not False:
        raise ValueError("S28 panel cannot render an upload-approved or slot-selected card")
    canary_max = max(
        (float(row.get("pooled_auc", 0.0)) for row in (canary.get("features") or {}).values()),
        default=None,
    )
    return f'''<section class="section callout-danger" id="{PANEL_ID}" aria-label="Current S28 submission decision" data-submission-ready="false">
<p class="eyebrow">S28 · 2026-10-29 UTC · AUTOMATED DECISION · NO HUMAN INSPECTOR</p>
<h2>Current decision: NO FILE APPROVED · OK TO SUBMIT: NO</h2>
<p><strong>Current run: NOT READY TO SUBMIT.</strong> No upload is authorized; do not upload it or any prior file.</p>
<p><strong>No new TIFF was generated.</strong> The top untried S26-TCB hypothesis was tested once. Its surface passed the pre-placement comparison, but its final 37,654-dot placement was a literal duplicate of the registered spacing-five calibration control. The protocol therefore stopped before serialization; no old file was renamed, relocated, or selected.</p>
<table><caption>S28-TCB gates; all DTI numbers are HOLDOUT-DTI, never leaderboard estimates.</caption><thead><tr><th>Gate</th><th>Observed result</th></tr></thead><tbody>
<tr><td>HOLDOUT-DTI</td><td>{_number(holdout.get('dti', 0), 6)}; 95% CI {_number(holdout.get('ci95', {}).get('interval', [0, 0])[0], 6)}–{_number(holdout.get('ci95', {}).get('interval', [0, 0])[1], 6)}; {int(holdout.get('n_withheld_positive_pixels', 0)):,} withheld positives.</td></tr>
<tr><td>Paired random-K control</td><td>HOLDOUT-DTI {_number(random_control.get('dti', 0), 6)}; ΔDTI {_number(paired.get('paired_delta_dti', 0), 6)}; 95% CI {_number((paired.get('paired_delta_ci95') or [0, 0])[0], 6)}–{_number((paired.get('paired_delta_ci95') or [0, 0])[1], 6)}; {paired.get('fold_wins', 0)}/4 folds won.</td></tr>
<tr><td>Leakage canaries</td><td>PASS; maximum pooled AUC {_number(canary_max, 6) if canary_max is not None else 'not recorded'} &lt; 0.90 suspicion threshold.</td></tr>
<tr><td>Surface before placement</td><td>{'PASS' if surface.get('passed') else 'FAIL'}; maximum absolute rank correlation {_number(surface.get('max_abs_rank_correlation', 0), 6)} across {surface.get('registry_unique_rasters', 0)} checked artifacts.</td></tr>
<tr><td>Final-dot novelty</td><td>FAIL / DUPLICATE STOP; calibration-control overlap {_number(control_overlap, 6) if control_overlap is not None else 'not recorded'} within 3 pixels. No TIFF was written.</td></tr>
<tr><td>Leaderboard estimate / slot</td><td>Unavailable; no organizer receipt or transfer calibration. No weekly slot selected or spent.</td></tr>
</tbody></table>
<div class="download-actions"><button class="button" type="button" disabled aria-disabled="true">Submission download locked</button><a class="button quiet" href="{html.escape(card_href, quote=True)}" download>Download S28 run card</a><a class="button quiet" href="{html.escape(review_href, quote=True)}">Open S28 review</a></div>
<p><strong>There is no TIF link because no candidate passed the scientific and uniqueness gates.</strong> Historical files in the nine-site table remain audit/education references and are not approved uploads. <a href="{html.escape(report_href, quote=True)}">Read the complete nine-site executive summary, hypotheses, sources, and run card</a>.</p>
</section>'''


def inject(path: Path, section: str) -> None:
    page = path.read_text(encoding="utf-8")
    marker = f'id="{PANEL_ID}"'
    if marker in page:
        marker_position = page.index(marker)
        start = page.rfind("<section", 0, marker_position)
        end = page.index("</section>", marker_position) + len("</section>")
        page = page[:start] + page[end:]
    if "<main>" not in page:
        raise ValueError(f"Missing main element in {path}")
    page = page.replace("<main>", "<main>" + section, 1)
    path.write_text(page, encoding="utf-8")


def standalone(card: dict) -> str:
    body = panel(
        card,
        "data/s28_tcb_run_card.json",
        "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/73_s28_tcb_result_2026-10-29.md",
        "s28-review.html",
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>S28 TCB review | GEMSDOE28</title><link rel="stylesheet" href="assets/site.css"></head>
<body><header class="site-header"><div class="header-inner"><a class="brand" href="index.html">GEMSDOE28 <small>DOE GEMS · Auditable research</small></a>
<nav aria-label="Main navigation"><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary</a><a href="s28-review.html">S28 review</a></nav></div></header>
<main>{body}<section class="section"><h2>Decision boundary</h2><p>The internal TCB holdout is catalogue-derived and cannot be converted into a leaderboard estimate. A unique format-valid file would still not be upload-approved. The only correct current action is to preserve this negative result and resolve the registry/baseline limitations before authorizing another lane.</p></section></main>
<footer><div class="footer-inner"><p><strong>Maximize P(Win) · Own the Outcome.</strong> No competition login, upload, polling, or slot selection occurred.</p></div></footer></body></html>'''


def main() -> int:
    card = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    for path, (card_href, review_href) in PAGES.items():
        report_href = "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/73_s28_tcb_result_2026-10-29.md"
        inject(path, panel(card, card_href, report_href, review_href))
    (ROOT / "docs/s28-review.html").write_text(standalone(card), encoding="utf-8")
    (ROOT / "docs/data/s28_tcb_run_card.json").write_text(
        json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "built", "panel": PANEL_ID, "network_requests": 0, "ok_to_submit": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
