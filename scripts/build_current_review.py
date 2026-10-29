#!/usr/bin/env python3
"""Publish the dated checkout decision and canonical current card, preserving dated history.

Offline and deliberately negative-only: this reporting tool cannot approve a TIFF.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL_ID = "current-checkout-decision"


def text(value):
    return html.escape(str(value), quote=True)


def render(card, scorecard, hypotheses, *, prefix=""):
    if (card.get("submission_ready") is not False or card.get("ok_to_submit") is not False
            or card.get("slot_selected") is not False or card.get("new_tiff_generated") is not False
            or card.get("raster_sha256") is not None or card.get("verdict") != "negative"):
        raise ValueError("This review renderer accepts only a negative, no-new-raster decision")
    if (card.get("experiments_run") != 0 or card["holdout"].get("dti") is not None
            or card["restoration"].get("cache_missingness_passed") is not True
            or card["restoration"].get("shared_assets_passed") is not True):
        raise ValueError("Review narrative requires restored inputs and no new experiment result")
    if len(scorecard["sites"]) != 9 or len({row["site"] for row in scorecard["sites"]}) != 9:
        raise ValueError("Nine distinct site rows required")
    rows = []
    for site in scorecard["sites"]:
        # User claims are never upgraded to organizer-confirmed by a build.
        if (site["estimated_leaderboard_score"] is not None or site["ok_to_submit"] is not False
                or site["unique_under_requested_rule"] is not False):
            raise ValueError("Historical reference cannot supply a score estimate or upload approval")
        rows.append(f'''<tr><th scope="row">{text(site['site'])}</th>
<td><a href="{text(site['source'])}">{text(site['file'])}</a></td>
<td>{site['highest_supplied_score']:.4f}<br>USER-REPORTED / UNVERIFIED</td>
<td>Unavailable</td><td>No — historical geometry audit</td><td><strong>NO</strong></td></tr>''')
    proposals = []
    for idea in hypotheses["hypotheses"]:
        proposals.append(f'''<li><strong>{text(idea['id'])}: {text(idea['name'])}</strong>
<p>Layers: {text(', '.join(idea['layers']))}. Signature: {text(idea['physical_signature'])}</p>
<p>Missing-fault rationale (hypothesis, not discovery): {text(idea['why_it_may_find_catalogue-missing_faults'])}</p>
<p>Difference from prior implementation: {text(idea['differs_from_repo'])}</p>
<p>Non-fault mimic: {text(idea['non_fault_mimic'])}. Cost: {text(idea['implementation_cost'])}</p></li>''')
    prior = card["prior_holdout_not_current"]
    ci = prior["ci95"]
    blockers = "".join(f"<li>{text(value)}</li>" for value in card["preflight"]["failures"])
    return f'''<section class="section callout-danger" id="{PANEL_ID}" data-submission-ready="false" aria-label="Latest checkout decision">
<p class="eyebrow">CURRENT REVIEW · {text(card['observed_utc'])} · {text(card['branch'])}</p>
<h1>No new submission approved</h1><h2>Submission download locked · OK TO SUBMIT: NO</h2>
<p><strong>No new TIFF was generated and no weekly slot was used.</strong> Inputs and shared tools are now restored and hash-verified from owner GitHub mirrors; they are not organizer-authenticated. The cached feature stack passes its missingness contract. Older checkout-specific banners below are historical, not current input status.</p>
<p><a href="{prefix}current-review.html">Current executive summary, nine-site table and submission guide</a> · <a href="{prefix}data/current_run_card.json" download>Download current JSON run card</a></p>
<h2>Best historical file by site — not recommended uploads</h2>
<p>The values below are supplied historical claims, <strong>not ORGANIZER-CONFIRMED scores</strong>. Linked files are for audit/learning, not new submissions. Uniqueness refers to the inherited nine-file geometry audit, not merely different file hashes; the registry is not globally synchronized. Today's GitHub head refresh is metadata-only and does not prove these remain the latest best files.</p>
<div class="table-wrap"><table><thead><tr><th>Site</th><th>Historical reference file (audit only)</th><th>Reported claim</th><th>Estimated leaderboard score</th><th>Unique under your rule?</th><th>Submit?</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>Why GEMSDOE32 may have improved</h2>
<p>The inherited pixel audit reconstructs H33-2-B2 by removing 2,545 catalogue-adjacent dots from a 40,199-dot H27-4 parent, leaving 37,654 dots with no additions. That is emission pruning, not evidence of a new fault-discovery model. Under distance-tolerant DTI, redundant predictions can add false-positive mass without additional recovery credit; pruning can help. Removing a uniquely useful prediction can instead harm recall. Neither the construction nor the supplied 0.2778 claim establishes causation without hidden truth and a file-bound organizer receipt.</p>
<p><strong>Can we exceed it?</strong> Possibly, but no calibrated hidden-score estimate is available. The prompt's leaderboard anchors conflict. This review did not fetch the live DrivenData board and does not treat an older parallel-session observation as today's verification.</p>
<h2>Measured evidence, not a leaderboard projection</h2>
<p>Prior S25 PCSE: <strong>HOLDOUT-DTI ({text(prior['evaluator_version'])}) {prior['dti']:.4f}</strong>, 95% CI {ci[0]:.4f}–{ci[1]:.4f}, {prior['withheld_positives']:,} withheld positive pixels. Same-fold random-K: <strong>HOLDOUT-DTI ({text(prior['evaluator_version'])}) {prior['control_dti']:.4f}</strong>, 95% CI {prior['control_ci95'][0]:.4f}–{prior['control_ci95'][1]:.4f}, same withheld positives. This is inherited evidence, not a new experiment or expected leaderboard result. The S25 research TIFF fails the literal shared-registry novelty rule (100% dot overlap with the registered calibration raster, per the parallel audit) and remains <strong>NOT OK to submit</strong>.</p>
<h2>Fresh automated validation</h2>
<p>The archive audit performed {card['archive_audit']['check_count']} checks and failed on {len(card['archive_audit']['failures'])} historical checks. Research sibling-manifest files now receive actual raster/ZIP inspection, not hash-only registration. Existing archive defects are flagged, not silently rewritten or approved. Local format validation cannot prove portal acceptance or determine the cause of the earlier range error.</p>
<h2>What blocks the next experiment?</h2><ul>{blockers}</ul>
<p>No method paragraph was supplied; no exclusive lane was invented. No canary, surface, final dots or new HOLDOUT-DTI was run. The stale experiment clock was not reset. A complete synchronized registry and frozen comparable best remain missing. Do not change the dot budget to exploit registry holes.</p>
<h2>Ranked untried hypotheses retained from the prior session</h2>
<p>This is the existing preregistered slate, not four newly discovered ideas. Qualitative order balances plausible complementarity and cost; numerical DTI improvement is unknown for each. TCB and MCR use locally restored bands. HFR2M needs official USGS heat-flow and DOE GDR temperature-probe bytes; DNT needs official USGS 3DEP tiles. Those raw external layers are not currently obtainable through this sandbox's allowed hosts and are <strong>not viable for the present run</strong>.</p><ol>{''.join(proposals)}</ol>
<h2>Exactly how a future approved submission is made</h2><ol>
<li>Pass the explicit lane/registry/budget preflight; reuse the pinned shared feature stack, evaluator and writer. Run individual-feature leakage canaries; AUC above 0.90 blocks reliance until resolved.</li>
<li>Use buffered whole-segment hide-and-recover folds, visible-only catalogue features, exact visible-fault masking and pooled HOLDOUT-DTI (alpha 0.2, beta 0.8, 300 m triangular kernel), with withheld-positive count and 95% CI. Beat the frozen same-protocol best; no ratio projection is a score.</li>
<li>Check surface rank correlation before placement and final-dot overlap against the complete registry. Stop on duplication. Independently reopen the exact TIFF/ZIP: single band, matching CRS/shape/transform, finite footprint values in [0,1], valid nodata convention and SHA-256. Never silently clamp a bad file.</li>
<li>A separate selector verifies the authenticated weekly allowance and authorizes one file. Only then may the site show an approved one-click download, unique submission name and note of at most 140 characters. None exists in this review.</li>
<li>On DrivenData's New submission form choose that exact .tif (or .zip containing only it), paste the note, and submit. Bind the returned receipt to the file SHA-256 before labeling a result ORGANIZER-CONFIRMED. This project did not access or submit through the portal.</li></ol>
<p><a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/74_s28_validation_review_2026-10-29.md">Full review, sources and next steps</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem/format</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b">Official reference snapshot</a></p>
</section>'''


def inject(page, section):
    marker = f'id="{PANEL_ID}"'
    if marker in page:
        start = page.rfind("<section", 0, page.index(marker))
        end = page.index("</section>", page.index(marker)) + len("</section>")
        if start < 0:
            raise ValueError("Malformed current-review section")
        page = page[:start] + page[end:]
    if "<main>" not in page:
        raise ValueError("Missing main element")
    return page.replace("<main>", "<main>" + section, 1)


def main():
    card_bytes = (ROOT / "evidence/s28_validation_run_card.json").read_bytes()
    card = json.loads(card_bytes)
    scorecard = json.loads((ROOT / "evidence/s23_scorecard.json").read_text())
    hypotheses = json.loads((ROOT / "registry/s26_hypotheses.json").read_text())
    docs_section = render(card, scorecard, hypotheses)
    root_section = render(card, scorecard, hypotheses, prefix="docs/")
    for filename, section in (("docs/index.html", docs_section),
                              ("docs/executive-summary.html", docs_section),
                              ("index.html", root_section), ("executive-summary.html", root_section)):
        path = ROOT / filename
        path.write_text(inject(path.read_text(), section))
    standalone = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Current executive summary | GEMSDOE28</title>
<link rel="stylesheet" href="assets/site.css"></head><body><header class="site-header"><nav aria-label="Main navigation"><a href="index.html">GEMSDOE28 overview</a> · <a href="executive-summary.html">Executive summary</a></nav></header><main>{docs_section}</main></body></html>'''
    (ROOT / "docs/current-review.html").write_text(standalone)
    # Advance only generic aliases; dated cards retain the exact historical bytes.
    for filename in ("docs/data/current_run_card.json", "data/current_run_card.json"):
        (ROOT / filename).write_bytes(card_bytes)
    print(json.dumps({"current_card": "evidence/s28_validation_run_card.json", "submission_ready": False,
                      "dated_history_preserved": True, "network_requests": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
