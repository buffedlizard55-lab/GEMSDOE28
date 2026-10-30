#!/usr/bin/env python3
"""Publish the S30 fail-closed review and locked submission state.

Standard-library only, offline, and negative-only. This builder never reads/writes a raster, performs
network requests, selects a slot, or enables a GeoTIFF download. It renders the checked-in S30 run
card and nine-site scorecard, then puts a conspicuous decision banner on every entry/executive route.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "evidence/s30_run_card.json"
SCORECARD = ROOT / "evidence/s30_scorecard.json"
PANEL_ID = "s30-current-decision"
SITE_ID = "gemsdoe28-s30-review"

PAGES = {
    ROOT / "docs/index.html": ("data/s30_run_card.json", "data/s30_scorecard.json", "s30-review.html"),
    ROOT / "docs/executive-summary.html": ("data/s30_run_card.json", "data/s30_scorecard.json", "s30-review.html"),
    ROOT / "docs/current-review.html": ("data/s30_run_card.json", "data/s30_scorecard.json", "s30-review.html"),
    ROOT / "index.html": ("docs/data/s30_run_card.json", "docs/data/s30_scorecard.json", "docs/s30-review.html"),
    ROOT / "executive-summary.html": ("docs/data/s30_run_card.json", "docs/data/s30_scorecard.json", "docs/s30-review.html"),
    ROOT / "current-review.html": ("docs/data/s30_run_card.json", "docs/data/s30_scorecard.json", "docs/s30-review.html"),
}
EXPECTED_SITES = [
    "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
    "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
]


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str):
    raise ValueError(f"Invalid JSON constant: {value}")


def load_json(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs,
                        parse_constant=_reject_constant)
    if not isinstance(result, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return result


def escape(value) -> str:
    return html.escape(str(value), quote=True)


def validate_records(card: dict, scorecard: dict) -> None:
    if card.get("schema") != "gemsdoe28-s30-blocked-repository-review-v1":
        raise ValueError("Unexpected S30 card schema")
    if card.get("branch") != "arena/6aaf0523-gemsdoe28":
        raise ValueError("S30 card is not for the active branch")
    if (card.get("verdict") != "negative" or card.get("new_tiff_generated") is not False
            or card.get("submission_ready") is not False
            or card.get("ok_to_download_and_submit") is not False
            or card.get("slot_selected") is not False):
        raise ValueError("S30 publisher accepts only a negative, no-file, no-slot card")
    if card.get("raster_sha256") is not None or card.get("submission_name") is not None:
        raise ValueError("S30 must not identify an uploadable raster or submission name")
    if len(card.get("submission_note", "")) > 140:
        raise ValueError("Submission note exceeds the 140-character limit")
    if card.get("submission_note_character_count") != len(card.get("submission_note", "")):
        raise ValueError("Submission note length does not match its recorded count")
    holdout = card.get("holdout", {})
    if (holdout.get("label") != "HOLDOUT-DTI" or holdout.get("status", "").startswith("NOT RUN") is False
            or holdout.get("dti") is not None or holdout.get("ci95") is not None
            or holdout.get("withheld_positives") is not None):
        raise ValueError("S30 must label the holdout as NOT RUN, without a fabricated score")
    validator = card.get("validator", {})
    if (validator.get("status", "").startswith("NOT RUN") is False
            or any(validator.get(key) is not None for key in
                   ("no_nan_inside_footprint", "values_in_0_1", "crs_shape_transform_match", "single_band"))):
        raise ValueError("S30 validator must remain NOT RUN for a nonexistent candidate")
    if card.get("experiments_run") != 0 or card.get("slot_selected") is not False:
        raise ValueError("S30 cannot claim a scientific experiment or weekly slot")
    slate = card.get("candidate_slate")
    if not isinstance(slate, list) or not 3 <= len(slate) <= 5:
        raise ValueError("S30 must publish three to five ranked hypothesis proposals")
    required_hypothesis_fields = {
        "rank", "id", "name", "layers", "physical_signature",
        "why_it_may_find_catalogue_missing_faults", "difference_from_repo",
        "non_fault_mimic", "expected_holdout_dti_improvement", "implementation_cost",
        "data_obtainability",
    }
    for rank, idea in enumerate(slate, start=1):
        if not isinstance(idea, dict) or not required_hypothesis_fields <= set(idea) or idea.get("rank") != rank:
            raise ValueError("S30 hypothesis slate is incomplete or not ranked sequentially")

    if card.get("preflight", {}).get("status") != "BLOCKED":
        raise ValueError("S30 must remain blocked until its assigned lane and inputs pass preflight")
    if card.get("download_validation", {}).get("status", "").startswith("FAIL CLOSED") is False:
        raise ValueError("S30 must preserve the missing-template fail-closed result")

    if scorecard.get("schema") != "gemsdoe28-s30-nine-site-scorecard-v1":
        raise ValueError("Unexpected S30 scorecard schema")
    rows = scorecard.get("rows")
    if not isinstance(rows, list) or [row.get("site") for row in rows] != EXPECTED_SITES:
        raise ValueError("S30 scorecard must contain each requested site exactly once and in order")
    if (scorecard.get("all_nine_historical_files_flagged_duplicate_under_70_percent_3px_rule") is not True
            or scorecard.get("complete_global_registry") is not False
            or scorecard.get("current_submission_file") is not None
            or scorecard.get("estimated_leaderboard_scores_available") is not False):
        raise ValueError("S30 scorecard must preserve its bounded, negative-only scope")
    for row in rows:
        if (row.get("score_estimate") is not None or row.get("duplicate_under_requested_rule") is not True
                or row.get("current_file_to_download") is not None
                or row.get("current_ok_to_download_and_submit") is not False
                or not re.fullmatch(r"[0-9a-f]{64}", row.get("historical_artifact_sha256", ""))):
            raise ValueError(f"Unsafe or incomplete historical row: {row.get('site')}")


def render_panel(card_href: str, scorecard_href: str, review_href: str, card: dict) -> str:
    blockers = card.get("preflight", {}).get("blockers", [])
    blocker_text = " · ".join(escape(item) for item in blockers[:5])
    return f'''<section class="section callout-danger" id="{PANEL_ID}" aria-label="Current S30 automated submission decision" data-submission-ready="false">
<p class="eyebrow">S30 · {escape(card['observed_utc'])} · AUTOMATED FAIL-CLOSED REVIEW · NO HUMAN GEOLOGICAL INSPECTOR</p>
<h1>NO FILE APPROVED · OK TO DOWNLOAD AND SUBMIT: NO</h1>
<p><strong>No new TIFF was generated or approved; no weekly slot was selected.</strong> Do not upload any historical research raster. The GEMSDOE32 claim of 0.2778 is user-reported, not an organizer receipt; no calibrated score estimate is available.</p>
<div class="download-actions"><button class="button" type="button" disabled aria-disabled="true">Submission download locked</button><a class="button quiet" href="{escape(card_href)}" download>Download S30 run card</a><a class="button quiet" href="{escape(scorecard_href)}" download>Download nine-site scorecard</a><a class="button quiet" href="{escape(review_href)}">Open S30 executive review</a></div>
<p><strong>No approved TIFF to download.</strong> <strong>Blocking preflight:</strong> {blocker_text}. The complete record and exact-file audit are linked in the S30 review. Archived S29 TIFFs are research-only and failed the promotion gate.</p>
<p><strong>Archive warning:</strong> Older S28/S29 cards and any historical TIFF links below are retained as dated evidence only. They do not supersede this S30 decision and are not approved for download or upload.</p>
</section>'''


def _row_html(row: dict) -> str:
    claim = f"{float(row['historical_score_claim']):.4f}"
    source = escape(row["historical_artifact_source"])
    filename = escape(row["historical_artifact_filename_audit_snapshot"])
    overlap = float(row["candidate_within_3px_fraction"]) * 100.0
    peer = escape(row["max_overlap_reference"])
    format_status = escape(row["audit_format_status"])
    return f'''<tr><th scope="row">{escape(row['site'])}</th>
<td><a href="{source}" rel="noopener noreferrer"><code>{filename}</code></a><br><small>Historical owner-mirror audit snapshot · {escape(row['historical_artifact_sha256'][:16])}… · format audit {format_status}</small></td>
<td><strong>{claim}</strong><br><small>USER-REPORTED / UNVERIFIED</small></td>
<td>Unavailable<br><small>No calibrated estimate</small></td>
<td><strong>NO</strong><br>{overlap:.2f}% within 3 px of {peer}</td>
<td><strong>None · NO</strong><br>No S30 file is approved</td></tr>'''


def _hypothesis_html(idea: dict) -> str:
    layers = ", ".join(idea.get("layers", []))
    sources = "".join(
        f'<li><a href="{escape(url)}" rel="noopener noreferrer">{escape(url)}</a></li>'
        for url in idea.get("required_free_official_sources", [idea.get("official_source", "")])
        if url
    )
    return f'''<article class="card">
<p class="eyebrow">RANK {int(idea['rank'])} · {escape(idea['id'])}</p><h3>{escape(idea['name'])}</h3>
<p><strong>Layers:</strong> {escape(layers)}.</p>
<p><strong>Physical signature:</strong> {escape(idea['physical_signature'])}</p>
<p><strong>Why a catalogue-missing fault:</strong> {escape(idea['why_it_may_find_catalogue_missing_faults'])}</p>
<p><strong>Different from this repository:</strong> {escape(idea['difference_from_repo'])}</p>
<p><strong>Named non-fault mimic:</strong> {escape(idea['non_fault_mimic'])}</p>
<p><strong>Expected HOLDOUT-DTI improvement:</strong> {escape(idea['expected_holdout_dti_improvement'])}<br><strong>Cost:</strong> {escape(idea['implementation_cost'])}</p>
<p><strong>Availability:</strong> {escape(idea['data_obtainability'])}</p>
<ul>{sources}</ul>
</article>'''


def render_page(card: dict, scorecard: dict) -> str:
    rows = "\n".join(_row_html(row) for row in scorecard["rows"])
    hypotheses = "\n".join(_hypothesis_html(item) for item in card["candidate_slate"])
    blockers = "".join(f"<li>{escape(item)}</li>" for item in card["preflight"]["blockers"])
    sources = "".join(
        f'<li><a href="{escape(source["url"])}" rel="noopener noreferrer">{escape(source["label"])}</a>'
        f' — {"freshly checked in S30" if source["freshly_checked_in_S30"] else "manual review link; not freshly checked in S30"}</li>'
        for source in card["official_manual_review_links"]
    )
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="S30 fail-closed executive summary, nine-site scorecard, ranked geological hypotheses, and automated submission guide.">
  <title>S30 executive review | GEMSDOE28</title>
  <link rel="stylesheet" href="assets/site.css">
</head>
<body>
<header class="site-header"><div class="header-inner">
  <a class="brand" href="index.html">GEMSDOE28 <small>DOE GEMS · Auditable research</small></a>
  <nav aria-label="Main navigation"><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary</a><a href="s30-review.html" aria-current="page">Current review</a><a href="research.html">Research</a><a href="sources.html">Sources</a></nav>
</div></header>
<main>
<section class="section callout-danger" id="{SITE_ID}" aria-label="S30 automated submission decision" data-submission-ready="false">
  <p class="eyebrow">S30 · {escape(card['observed_utc'])} · AUTOMATED FAIL-CLOSED REVIEW · NO HUMAN GEOLOGICAL INSPECTOR</p>
  <h1>NO FILE APPROVED · OK TO DOWNLOAD AND SUBMIT: NO</h1>
  <p><strong>No new TIFF was generated or approved; no weekly slot was selected.</strong> The historical S29 candidate remains archived for research only. This page deliberately provides no TIFF download.</p>
  <p><strong>Leaderboard score estimate:</strong> unavailable for all nine sites—not zero and not a projection. All historical scores below are user-supplied claims without organizer receipts.</p>
  <div class="download-actions"><button class="button" type="button" disabled aria-disabled="true">No approved TIFF to download</button><a class="button quiet" href="data/s30_run_card.json" download>Download S30 run card</a><a class="button quiet" href="data/s30_scorecard.json" download>Download nine-site scorecard</a></div>
</section>
<section class="section"><p class="eyebrow">EXECUTIVE SUMMARY · NINE REQUESTED SITES</p><h2>Historical claims, novelty and current download decision</h2>
<p>All artifact links are pinned owner-repository mirrors used for audit/learning only; they are not authenticated competition uploads. “Unique?” applies only to the nine selected historical files in the inherited 2026-10-29 geometry audit, not a complete global registry. No S30 file was emitted or compared.</p>
<div class="table-wrap"><table><caption>None of these historical files is approved for S30 submission.</caption><thead><tr><th>Site</th><th>Historical artifact — audit only</th><th>Supplied claim</th><th>Estimated leaderboard score</th><th>Unique among nine?</th><th>Download / submit now?</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>The inherited audit computed 72 ordered comparisons among the nine selected files. Every selected file exceeded the requested 70% within-3-pixel overlap threshold against at least one peer. That audit is not a complete synchronized registry check.</p>
</section>
<section class="section"><h2>Why the GEMSDOE32 0.2778 claim may be the top of this nine-site list</h2>
<p>The inherited pixel forensic record finds the 37,654-dot GEMSDOE32 placement is exactly the H27-4 solo set minus 2,545 catalogue-adjacent dots (distance ≤2 pixels), with zero additions. Its supplied historical score is 0.2778 versus 0.2708 for the related solo claim. One plausible explanation is more efficient emission: removing redundant or low-marginal-credit points can reduce weighted false-positive mass while retaining useful coverage. The DTI metric weights false negatives more heavily than false positives (beta 0.8, alpha 0.2), so pruning can also hurt; benefit depends on hidden-truth coverage that is unavailable here. This construction is not a causal explanation of a receipt-confirmed result, and the user-supplied scores are unverified.</p>
<p><strong>No numeric leaderboard estimate follows from this forensic relationship.</strong> Internal catalogue holdouts do not identify hidden-label scores without a separately validated transfer calibration.</p>
</section>
<section class="section"><h2>Ranked hypotheses — proposals only; no lane assigned or test run</h2>
<p>Ranks are qualitative expected research value, not measured improvement. Every HOLDOUT-DTI delta is unknown. MCR is first because it uses existing competition bands in principle; all other rows require external files whose current availability was not verified. The prompt’s reference to a single assigned method paragraph cannot be resolved from the request or current manifest; therefore none is authorized.</p>
<div class="grid">{hypotheses}</div></section>
<section class="section callout-warning"><h2>Why no test or TIFF was produced</h2>
<p>The fail-closed preflight at {escape(card['observed_utc'])} returned <strong>BLOCKED</strong>. It found no explicit assigned lane, no complete synchronized registry, no frozen same-protocol best, an expired inherited two-hour clock, absent prepared features, and all pinned shared evaluator/writer files missing. The exact sample template and labels are also absent. Do not reset the timer, infer a lane, build a private evaluator, or expose a research TIFF as uploadable.</p>
<ul>{blockers}</ul>
<p>Software tests and static-site checks do not count as geological experiments or HOLDOUT-DTI measurements. No weekly cap was checked; no selector decision or slot occurred.</p>
</section>
<section class="section"><h2>Existing archived TIFF — not a S30 submission</h2>
<p>The repository already contains <code>gems29-s29-hole-k20000-20261029-b68117a828cc-nan.tif</code> (SHA-256 <code>{escape(card['validator']['archived_s29_candidate']['sha256'])}</code>). Local read-only inspection found one float32 band, EPSG:32611, 3730×3292, values 0–1 in its finite cells, and 20,000 positive cells. Exact comparison to the official sample template could not be repeated because the template is absent. Inherited S29 HOLDOUT-DTI was <strong>0.0295</strong> (95% CI 0.0234–0.0360; 60,988 withheld positives), below its matched random-K and comparable best. It is a negative research artifact and is **NOT OK TO DOWNLOAD AND SUBMIT**.</p>
</section>
<section class="section"><h2>How to submit an approved file later</h2>
<ol>
<li>Wait for a separate positive same-protocol holdout, passing pre-placement and final-dot registry uniqueness gates, exact format validation, and a separate selector authorization. S30 has no approved file.</li>
<li>For the exact approved GeoTIFF only, validate one float32 band; matching template CRS, shape and geotransform; every in-footprint value finite and in [0,1]; no infinities; and the required outside-footprint mask. Use the hash-pinned shared writer/validator, not a private fork.</li>
<li>On the competition’s New submission form, choose the approved .tif (or one-file .zip) and enter its short unique note (≤140 characters). Do not upload any historical artifact from the table above.</li>
<li>Bind the organizer’s returned receipt to that exact file SHA-256. Only that receipt can establish ORGANIZER-CONFIRMED score attribution.</li>
</ol>
<p>The project’s fault/hypothesis inspection is automated; a human geological inspection is not a substitute for the buffered holdout, leakage canaries, novelty checks, or exact-file validator. No DrivenData login/receipt or upload was accessed in S30.</p>
</section>
<section class="section"><h2>Official-source links for manual review</h2>
<p>These are references from the prompt and checked-in source ledger. Non-GitHub official hosts were not contacted in this S30 runtime, so current availability is not asserted.</p><ul>{sources}</ul>
<p><a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/77_s30_repository_review_2026-10-30.md">Read the full S30 research and repository review</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/s30_preflight.json">Preflight evidence</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/s30_download_audit.json">Exact-file audit failure</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/s30_archived_candidate_inspection.json">Archived TIFF inspection</a></p>
</section>
</main>
<footer class="site-footer"><p>GEMSDOE28 · S30 negative review · No TIFF approved · Scores are not receipts.</p></footer>
</body></html>
'''


def inject(page_path: Path, panel: str, card_href: str, scorecard_href: str) -> None:
    text = page_path.read_text(encoding="utf-8")
    marker = f'id="{PANEL_ID}"'
    if marker in text:
        pos = text.index(marker)
        start = text.rfind("<section", 0, pos)
        end_tag = text.find("</section>", pos)
        if start < 0 or end_tag < 0:
            raise ValueError(f"Malformed existing S30 panel in {page_path}")
        text = text[:start] + text[end_tag + len("</section>"):]
    if "<main>" not in text:
        raise ValueError(f"Missing main element in {page_path}")
    text = text.replace("<main>", "<main>" + panel, 1)
    text = text.replace('href="s29-review.html">Current review', 'href="s30-review.html">Current review')
    text = text.replace('href="docs/s29-review.html">Current review', 'href="docs/s30-review.html">Current review')
    text = text.replace('href="s29-review.html" aria-current="page">Current review',
                        'href="s30-review.html" aria-current="page">Current review')
    text = text.replace('href="docs/s29-review.html" aria-current="page">Current review',
                        'href="docs/s30-review.html" aria-current="page">Current review')
    if panel not in text:
        raise ValueError(f"S30 panel insertion failed for {page_path}")
    if 'data-submission-ready="false"' not in text or 'No approved TIFF to download' not in text:
        raise ValueError(f"S30 page does not visibly lock the TIFF download: {page_path}")
    if ".tif" in panel.lower():
        raise ValueError("The current decision panel must not contain an actionable TIFF link")
    page_path.write_text(text, encoding="utf-8")


def main() -> int:
    card = load_json(CARD)
    scorecard = load_json(SCORECARD)
    validate_records(card, scorecard)
    published_card = ROOT / "docs/data/s30_run_card.json"
    published_scorecard = ROOT / "docs/data/s30_scorecard.json"
    published_card.parent.mkdir(parents=True, exist_ok=True)
    published_card.write_bytes(CARD.read_bytes())
    published_scorecard.write_bytes(SCORECARD.read_bytes())
    standalone = ROOT / "docs/s30-review.html"
    standalone.write_text(render_page(card, scorecard), encoding="utf-8")

    updated = []
    for page_path, (card_href, scorecard_href, review_href) in PAGES.items():
        if not page_path.is_file():
            raise FileNotFoundError(f"Expected public entry page is missing: {page_path}")
        section = render_panel(card_href, scorecard_href, review_href, card)
        inject(page_path, section, card_href, scorecard_href)
        updated.append(page_path.relative_to(ROOT).as_posix())

    output = {
        "status": "built",
        "schema": card["schema"],
        "panel": PANEL_ID,
        "pages": updated + [standalone.relative_to(ROOT).as_posix()],
        "run_card_sha256": hashlib.sha256(CARD.read_bytes()).hexdigest(),
        "scorecard_sha256": hashlib.sha256(SCORECARD.read_bytes()).hexdigest(),
        "network_requests": 0,
        "new_tiff_generated": False,
        "download_enabled": False,
        "ok_to_submit": False,
    }
    print(json.dumps(output, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
