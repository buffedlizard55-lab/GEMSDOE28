#!/usr/bin/env python3
"""S25 add-on: publish the PCSE decision panel and its standalone page. Standard library only.

Runs from ``scripts/build_active_review.py`` after the generated site is built, so CI's clean-diff
check still holds. It reads the S25 card and ablation plus the S28 shared-registry audit; it performs no network requests and never changes a
hash-bound historical file. The panel reports the historical limited comparison, superseded by the S28 shared-registry
control audit. The file is a duplicate under the literal rule and is not OK to submit.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CARD = ROOT / "evidence" / "s25_pcse_run_card.json"
ABLATION = ROOT / "evidence" / "s25_pcse_ablation.json"
AUDIT = ROOT / "evidence" / "s28_pcse_lattice_audit.json"
REPO_BLOB = "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/"
STANDALONE = DOCS / "s25" / "index.html"
PANEL_ID = "s25-pcse-decision"
# Page -> relative prefix to docs/downloads
PAGES = {
    DOCS / "index.html": "downloads/",
    DOCS / "executive-summary.html": "downloads/",
    ROOT / "index.html": "docs/downloads/",
    ROOT / "executive-summary.html": "docs/downloads/",
}


def _ci(pair: list[float]) -> str:
    return f"{pair[0]:.4f} to {pair[1]:.4f}"


def _load() -> tuple[dict, dict]:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    abl = json.loads(ABLATION.read_text(encoding="utf-8"))
    sub = card["submission"]
    if card["validator"].get("hard_checks_passed") is not True:
        raise ValueError("S25 panel refuses to render: validator hard checks did not pass")
    if sub["sha256_tif"] is None or len(sub["sha256_tif"]) != 64:
        raise ValueError("S25 panel refuses to render: missing TIFF SHA-256")
    return card, abl


def panel(prefix: str) -> str:
    card, abl = _load()
    sub = card["submission"]
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    candidate = audit["inherited_candidate"]
    if (audit.get("status") != "DUPLICATE_STOP"
            or candidate.get("sha256") != sub["sha256_tif"]
            or candidate.get("duplicate_under_literal_rule") is not True
            or not 0.70 < candidate["final_dot_comparison"]["max_dot_overlap"] <= 1):
        raise ValueError("Missing or inconsistent S25 shared-registry duplicate audit")
    name = html.escape(sub["name"], quote=True)
    dti = card["holdout_dti"]["value"]
    ci = card["holdout_dti"]["ci95"]["interval"]
    ctrl = card["control_random_k_holdout_dti"]["value"]
    paired = card["paired_vs_random_k"]
    overlap = card["novelty"]["max_dot_overlap_within_3px_candidate_side"]
    rho = card["novelty"]["max_abs_surface_spearman"]
    ab_step = abl["results"]["phase_stepfrac_only"]["dti"]
    ab_energy = abl["results"]["energy_only"]["dti"]
    return f'''<section class="section callout-danger" id="{PANEL_ID}" aria-label="S25 PCSE submission decision">
<p class="eyebrow">S25 · 2026-10-28 UTC · AUTOMATED DECISION · NO HUMAN INSPECTOR</p>
<h2>S25 research TIFF: DUPLICATE + HOLDOUT-NEGATIVE · OK TO SUBMIT: NO</h2>
<p><strong>Download (review only):</strong> <a href="{prefix}{name}">{name}</a> (<a href="{prefix}{html.escape(sub["zip"], quote=True)}">ZIP</a>)</p>
<table>
<thead><tr><th>Question</th><th>Answer</th></tr></thead>
<tbody>
<tr><td>Uniqueness under the literal shared-registry rule</td><td><strong>NO.</strong> All candidate dots (100%) are within 3 px of the registered calibration lattice. A prior comparison of 51 local TIFFs reported {overlap:.4f} overlap and {rho:.4f} max |surface Spearman| but omitted that control; it does not establish global uniqueness. The original surface was not checked against this control.</td></tr>
<tr><td>Format checks</td><td>PASS in the prior S25 exact validation; current basic Rasterio inspection agrees on band, CRS, shape, transform, mask, and [0,1]. A fresh check against the hash-pinned owner-mirror template also passes the local format checks; this does not guarantee portal acceptance.</td></tr>
<tr><td>Fresh exact-file audit (S26 checkout)</td><td><strong>FAIL CLOSED</strong> at the time (sample and labels were missing). Historical; superseded by the S27 row below.</td></tr>
<tr><td>Exact-file audit (S27, restored inputs)</td><td>Run against the restored sample template (owner mirror, SHA-256 pinned, not organizer-authenticated). The S25 file passes every check: EPSG:32611 grid, single float32 band, 37,654 dots, NaN outside footprint, values in [0,1], no catalogue overlap, registered in manifest. Audit overall: <strong>FAIL on two historical archive variants</strong> (H40/H41 all-finite files carry a NaN nodata tag). Those are archive-only, DO NOT SUBMIT, and were not rewritten.</td></tr>
<tr><td>HOLDOUT-DTI (evaluator gems-segment-pooled-v1)</td><td><strong>{dti:.4f}</strong> (95% CI {_ci(ci)}); {card["holdout_dti"]["n_withheld_positive_pixels"]:,} withheld positives.</td></tr>
<tr><td>Random-placement control, same folds</td><td>{ctrl:.4f}. PCSE minus control: {paired["paired_delta_dti"]:+.4f} (95% CI {_ci(paired["paired_delta_ci95"])}); PCSE wins {paired["fold_wins"]} of {paired["n_folds"]} folds.</td></tr>
<tr><td>Ablation (diagnostic only)</td><td>Step-polarity term alone {ab_step:.4f}; energy term alone {ab_energy:.4f}.</td></tr>
<tr><td>Organizer score</td><td>None. Not organizer-confirmed.</td></tr>
<tr><td><strong>OK to download?</strong></td><td>Yes, for review and audit only.</td></tr>
<tr><td><strong>OK to submit?</strong></td><td><strong>NO.</strong> It fails the literal registry overlap rule and scores below a random-placement control on the shared holdout.</td></tr>
</tbody>
</table>
<p>No upload note: this file is not eligible for submission.</p>
<p>Full record: <a href="{REPO_BLOB}knowledge/69_s25_pcse_result.md">S25 PCSE result</a> · <a href="{REPO_BLOB}evidence/s25_pcse_run_card.json">run card</a> · <a href="{REPO_BLOB}evidence/s25_pcse_ablation.json">ablation</a> · <a href="{REPO_BLOB}evidence/s25_pcse_novelty.json">historical limited novelty</a> · <a href="{REPO_BLOB}evidence/s28_pcse_lattice_audit.json">superseding lattice audit</a>. <a href="{REPO_BLOB}knowledge/71_s26_review_2026-10-28.md">Historical S26 review and candidate hypotheses</a> · <a href="{REPO_BLOB}registry/s26_hypotheses.json">machine-readable hypothesis ranking</a>. Official public leaderboard observed 2026-10-28: #1 0.4544; #26 0.3195; the prompt's 0.4413 is not on the board. Public-board rank is not the private prize score.</p>
</section>'''


def standalone() -> str:
    body = panel("../downloads/")
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>S25 PCSE result | GEMSDOE28</title>
<link rel="stylesheet" href="../assets/site.css">
</head>
<body>
<header class="topbar"><div class="wrap">
  <a class="brand" href="../index.html">GEMSDOE28 <small>DOE GEMS · Auditable research</small></a>
  <nav aria-label="Main navigation"><a href="../index.html">Overview</a><a href="../executive-summary.html">Executive summary</a><a href="index.html">S25 result</a></nav>
</div></header>
<main>{body}</main>
</body>
</html>
'''


def inject(path: Path, prefix: str) -> bool:
    page = path.read_text(encoding="utf-8")
    if f'id="{PANEL_ID}"' in page:
        start = page.index(f'<section class="section callout-danger" id="{PANEL_ID}"')
        end = page.index("</section>", start) + len("</section>")
        page = page[:start] + page[end:]
    if "<main>" not in page:
        raise ValueError(f"Missing main element in {path}")
    page = page.replace("<main>", "<main>" + panel(prefix), 1)
    path.write_text(page, encoding="utf-8")
    return True


def main() -> int:
    STANDALONE.parent.mkdir(parents=True, exist_ok=True)
    STANDALONE.write_text(standalone(), encoding="utf-8")
    for path, prefix in PAGES.items():
        inject(path, prefix)
    print(json.dumps({"status": "built", "standalone": STANDALONE.relative_to(ROOT).as_posix(),
                      "panel_pages": [p.relative_to(ROOT).as_posix() for p in PAGES],
                      "network_requests": 0, "ok_to_submit": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
