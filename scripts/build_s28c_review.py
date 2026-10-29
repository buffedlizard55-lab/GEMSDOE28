#!/usr/bin/env python3
"""Publish the S28C evidence snapshot offline; never authorize an upload."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL_ID = "s28c-current-decision"


def load(path):
    return json.loads((ROOT / path).read_text())


def render_panel(prefix=""):
    return f'''<section class="section callout-danger" id="{PANEL_ID}" data-submission-ready="false" aria-label="Latest evidence snapshot">
<p class="eyebrow">S28C · 2026-10-29 UTC · supersedes earlier current-status notices below</p>
<h2>OK TO SUBMIT: NO — no new TIFF generated</h2>
<p>The pinned inputs, 32-band cache and shared tools are restored. All nine historical leaders fail the final-dot uniqueness rule within the audited nine-leader subset. No new holdout experiment or weekly slot was used. Earlier missing-data notices below are historical, not this checkout's current state.</p>
<p><strong>Download for submission: none approved. Estimated leaderboard score: unavailable.</strong> A format pass alone is not a performance or uniqueness pass.</p>
<p><a href="{prefix}s28c-review.html">Latest executive summary: nine-site file table, evidence and submission guide</a> · <a href="{prefix}data/s28c_run_card.json" download>Download JSON run card</a></p></section>'''


def inject(page, panel):
    marker = f'id="{PANEL_ID}"'
    if marker in page:
        start = page.rfind("<section", 0, page.index(marker))
        end = page.index("</section>", page.index(marker)) + len("</section>")
        page = page[:start] + page[end:]
    if "<main>" not in page:
        raise ValueError("Missing main element")
    return page.replace("<main>", "<main>" + panel, 1)


def main():
    audit = load("evidence/s28c_priority_novelty.json")
    preflight = load("evidence/s28c_preflight.json")
    card = load("evidence/s28c_run_card.json")
    if card["verdict"] != "negative" or card["ok_to_submit"] is not False:
        raise ValueError("Snapshot builder cannot publish promotion")
    rows = []
    for leader in audit["leaders"]:
        raster = leader["raster"]
        check = leader["final_dots"]
        rows.append(f'''<tr><td>{html.escape(leader['site'])}</td><td><a href="{html.escape(raster['source'], quote=True)}">{html.escape(raster['file'])}</a><br>Historical source only — do not submit</td><td>USER-REPORTED / UNVERIFIED {leader['reported_score']:.4f}</td><td>Unavailable</td><td>{'PASS' if raster['hard_checks_passed'] else 'FAIL'} local format</td><td>NO: max 3 px overlap {check['max_dot_overlap']:.4f}; max |raw rho| {check['max_abs_rank_correlation']:.4f}</td><td>NO</td></tr>''')
    hypotheses = load("registry/s26_hypotheses.json")["hypotheses"]
    hypothesis_rows = []
    for item in hypotheses:
        hypothesis_rows.append("<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in (
            item['rank'], item['name'], ', '.join(item['layers']), item['physical_signature'],
            item['why_it_may_find_catalogue-missing_faults'], item['differs_from_repo'],
            item['non_fault_mimic'], item['implementation_cost'], item['data_obtainability'])) + "</tr>")
    blockers = "".join(f"<li>{html.escape(reason)}</li>" for reason in preflight["failures"])
    body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>S28C executive review | GEMSDOE28</title><link rel="stylesheet" href="assets/site.css"></head>
<body><header class="site-header"><div class="header-inner"><a class="brand" href="index.html">GEMSDOE28</a><nav><a href="executive-summary.html">Executive summary</a> · <a href="cross-site-review.html">Historical cross-site review</a></nav></div></header><main>{render_panel()}
<section class="section"><h2>Nine-site executive table</h2><p>These are the highest artifacts in the supplied result list, not an organizer-verified ranking. Links identify the exact pinned source files for education, not approved uploads. No original pre-placement surface is available. Geometry statistics are not HOLDOUT-DTI. No calibrated hidden-score estimate exists for any row.</p>
<div style="overflow-x:auto"><table><thead><tr><th>Site</th><th>Exact historical file / audit link</th><th>Historical claim (not a receipt)</th><th>Estimated leaderboard score</th><th>Format</th><th>Unique vs other eight leaders?</th><th>OK to submit?</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
<section class="section"><h2>Why GEMSDOE32 appeared best</h2><p>Fresh exact pixel-set forensics establish that its 37,654 dots equal the GEMSDOE28 solo prediction after removing 2,545 dots within 2 pixels of the catalogue. No dots were added. GEMSDOE25 and GEMSDOE30 have identical footprint predictions; GEMSDOE28 solo and GEMSDOE31 solo also match exactly.</p><p>Removing redundant catalogue-adjacent predictions could reduce false-positive cost without losing much withheld-fault coverage. That is a testable metric explanation, not proven causation. A catalogue-dependent operator must be rebuilt using only visible faults in each buffered holdout fold. Scoring a historical full-catalogue raster on hidden catalogue segments would leak information. We cannot establish that a new submission will beat the reported 0.2778.</p><p>The task predicts faults associated with geothermal exploration; it does not verify geothermal vents, flow rates or commercial productivity. The quoted leaderboard anchors conflict. A prior branch recorded a public-board observation, but no current organizer page or submission receipt was fetched in S28C.</p></section>
<section class="section"><h2>Ranked, untested geological hypotheses</h2><p>Reuse the four existing untried proposals rather than rename them as new discoveries. Ranking is qualitative expected complementarity adjusted for cost, not a numerical DTI forecast. No hypothesis was implemented or validated in this review. External-data proposals remain non-viable here until their official bytes and coverage can be checked. The availability text below is the dated S26 proposal record; S28C restored the existing-data cache, not the external USGS/GDR layers.</p><div style="overflow-x:auto"><table><thead><tr><th>Rank</th><th>Hypothesis</th><th>Layers</th><th>Physical signature</th><th>Missing-fault rationale</th><th>Difference from existing work</th><th>Non-fault mimic</th><th>Cost</th><th>Data limitations (S26 record)</th></tr></thead><tbody>{''.join(hypothesis_rows)}</tbody></table></div></section>
<section class="section"><h2>What blocks a new submission</h2><ul>{blockers}</ul><p>Neither a fresh session timestamp nor a new filename resolves the absent lane, registry or paired baseline. A dense lattice registry control also makes the declared dot budget incompatible with the literal overlap rule; do not relocate dots merely to evade it. No feature canaries or new holdout run were performed.</p><p>Existing S25 PCSE evidence: HOLDOUT-DTI (gems-segment-pooled-v1), 60,988 withheld positives, 0.0450, 95% CI [0.0380, 0.0525]. Same-fold random-K: HOLDOUT-DTI 0.0699, 95% CI [0.0667, 0.0731]. These are historical local results, not score estimates, and are not newly reproduced in S28C.</p><p>An independent parallel audit on main also found that every S25 PCSE dot lies within 3 px of the shared calibration lattice; its earlier limited-registry uniqueness claim is superseded. It is not unique under the literal global rule. The current exact-file audit contains 869 checks and two failures: archived H40 vent and H41 spring all-finite variants retain NaN nodata tags. Historical hash-bound files are flagged, not silently rewritten.</p></section>
<section class="section"><h2>Exactly how submission will work once approved</h2><ol><li>Generate a genuinely new lane-specific surface using the shared cached stack. Run per-feature leakage canaries; AUC above 0.90 blocks trust until explained. Check registry similarity before placing dots; stop on duplicates.</li><li>Hide whole fault segments with a buffer; rebuild catalogue features from visible faults only and mask visible faults pixel-exactly. Use the shared evaluator (alpha 0.2, beta 0.8, 300 m triangular kernel). Beat the frozen comparable best under the predeclared paired gate.</li><li>Check final-dot uniqueness, then use the shared writer and validate the exact final bytes: one band, finite inside footprint, values in [0,1], matching CRS, shape and transform. Check actual values as well as nodata metadata; never use numeric missing-value sentinels as probabilities.</li><li>Publish a content-addressed TIFF link, SHA-256, unique submission name and note of at most 140 characters only after all required gates pass. Currently no such file is approved.</li><li>A separate selector checks the authenticated weekly allowance. Upload the approved TIFF (or a ZIP containing only that TIFF), paste its identifying note, and retain the submission-page receipt. Only that receipt can link a raster to an ORGANIZER-CONFIRMED score. This review did not log in, upload or spend a slot.</li></ol></section>
<section class="section"><h2>Evidence and official sources</h2><p><a href="data/s28c_priority_novelty.json">Fresh shared-comparator output and forensics</a> · <a href="data/s28c_run_card.json">Run card</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/s28c_priority_repository_audit.json">Pinned nine-repository inventory</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/s28c_download_audit.json">Exact-file audit</a></p><ul><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official task, metric and format</a></li><li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference code</a></li><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Official public leaderboard</a></li><li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a></li><li><a href="https://gdr.openei.org/submissions/1391">Official INGENIOUS data source</a></li></ul><p>Official non-GitHub hosts are outside this runtime's outbound allowlist. Links are provided for source review, not claimed as freshly verified. Owner GitHub mirrors are hash-verified but not organizer-authenticated. No manual inspection is substituted for project validation.</p></section></main></body></html>'''
    (ROOT / "docs/s28c-review.html").write_text(body)
    for name in ("s28c_run_card.json", "s28c_priority_novelty.json"):
        (ROOT / "docs/data" / name).write_text((ROOT / "evidence" / name).read_text())
    for path in ("docs/index.html", "docs/executive-summary.html", "index.html", "executive-summary.html"):
        target = ROOT / path
        page = inject(target.read_text(), render_panel("" if path.startswith("docs/") else "docs/"))
        for prefix in ("", "docs/"):
            page = page.replace(f'href="{prefix}session24-review.html">Latest review',
                                f'href="{prefix}s28c-review.html">Latest review')
        target.write_text(page)
    print("S28C review published offline; no file approved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
