#!/usr/bin/env python3
"""Build the S30 fail-closed review page and status overlays from committed evidence.

This builder is offline and deterministic. It validates the blocked run card, copies JSON evidence
for the static site, and never reads/writes a raster, contacts a competition site, or approves a file.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CARD_PATH = ROOT / "evidence/s30_run_card.json"
PREFLIGHT_PATH = ROOT / "evidence/s30_preflight.json"
SOURCE_REFRESH_PATH = ROOT / "evidence/s30_source_refresh.json"
HYPOTHESES_PATH = ROOT / "registry/s30_hypotheses.json"
SCORECARD_PATH = ROOT / "evidence/s23_scorecard.json"
OVERLAP_PATH = ROOT / "evidence/s24_nine_site_overlap.json"
FORENSIC_PATH = ROOT / "evidence/s15_champion_forensic.json"
REPORT_PATHS = {
    "GEMSDOE24": "docs/executive-summary-9sites.html",
    "GEMSDOE25": "docs/current-review.html",
    "GEMSDOE27": "docs/executive-summary.html",
    "GEMSDOE28": "docs/executive-summary.html",
    "GEMSDOE30": "docs/executive-summary.html",
    "GEMSDOE31": "docs/executive-summary.html",
    "GEMSDOE32": "docs/nine-site-executive-summary.html",
    "GEMSDOE33": "docs/executive-summary.html",
    "GEMSDOE36": "docs/executive-summary.html",
}
PAGES = {
    ROOT / "docs/index.html": ("data/s30_run_card.json", "s30-review.html", "data/s30_hypotheses.json"),
    ROOT / "docs/executive-summary.html": (
        "data/s30_run_card.json", "s30-review.html", "data/s30_hypotheses.json"),
    ROOT / "docs/current-review.html": (
        "data/s30_run_card.json", "s30-review.html", "data/s30_hypotheses.json"),
    ROOT / "docs/cross-site-review.html": (
        "data/s30_run_card.json", "s30-review.html", "data/s30_hypotheses.json"),
    ROOT / "index.html": ("docs/data/s30_run_card.json", "docs/s30-review.html",
                           "docs/data/s30_hypotheses.json"),
    ROOT / "executive-summary.html": ("docs/data/s30_run_card.json", "docs/s30-review.html",
                                      "docs/data/s30_hypotheses.json"),
    ROOT / "current-review.html": ("docs/data/s30_run_card.json", "docs/s30-review.html",
                                   "docs/data/s30_hypotheses.json"),
}
PANEL_ID = "s30-current-decision"
PUBLISHED_EVIDENCE = {
    PREFLIGHT_PATH: DOCS / "data/s30_preflight.json",
    SOURCE_REFRESH_PATH: DOCS / "data/s30_source_refresh.json",
    HYPOTHESES_PATH: DOCS / "data/s30_hypotheses.json",
    SCORECARD_PATH: DOCS / "data/s30_scorecard.json",
    OVERLAP_PATH: DOCS / "data/s30_overlap_audit.json",
    FORENSIC_PATH: DOCS / "data/s30_gemsdoe32_forensic.json",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def fmt_score(value: Any) -> str:
    return f"{float(value):.4f}"


def validate_records(card: dict, preflight: dict, source: dict, hypotheses: dict,
                     scorecard: dict, overlap: dict, forensic: dict) -> None:
    if card.get("schema") != "gemsdoe28-s30-repository-review-v1":
        raise ValueError("Unexpected S30 run-card schema")
    if card.get("branch") != "arena/5a9fd894-gemsdoe28":
        raise ValueError("S30 run card is not bound to the active session branch")
    if card.get("submission_verdict") != "negative":
        raise ValueError("S30 publisher accepts only a negative decision")
    if card.get("experiment_budget", {}).get("experiments_run") != 0:
        raise ValueError("A repository-review-only S30 card must record zero experiments")
    if card.get("experiment_budget", {}).get("holdouts_run") != 0:
        raise ValueError("A repository-review-only S30 card must record zero holdouts")
    if card.get("raster", {}).get("new_tiff_generated") is not False:
        raise ValueError("S30 must not claim a new TIFF")
    if card.get("raster", {}).get("sha256") is not None:
        raise ValueError("A no-TIFF S30 run card must not publish a raster hash")
    if card.get("approval", {}).get("ok_to_download") is not False:
        raise ValueError("No S30 download may be approved")
    if card.get("approval", {}).get("ok_to_submit") is not False:
        raise ValueError("No S30 submission may be approved")
    if card.get("approval", {}).get("weekly_slot_selected") is not False:
        raise ValueError("S30 must not select a weekly slot")
    note = card.get("approval", {}).get("submission_note", "")
    if not isinstance(note, str) or len(note) > 140:
        raise ValueError("S30 submission note must be a single-line string of at most 140 characters")
    if card.get("approval", {}).get("submission_note_characters") != len(note):
        raise ValueError("S30 submission-note character count does not match its text")
    if preflight.get("status") != "BLOCKED" or preflight.get("experiment_allowed") is not False:
        raise ValueError("S30 run card and preflight disagree; refuse publication")
    if preflight.get("submission_ready") is not False or preflight.get("slot_selected") is not False:
        raise ValueError("S30 preflight must remain fail-closed")
    if source.get("freshly_observed_count") != 10 or source.get("source_count") != 18:
        raise ValueError("Source refresh count changed; review feed before publishing")
    if source.get("drivendata_contacted") is not False:
        raise ValueError("S30 report must not claim or perform competition-site contact")
    if len(source.get("focus_site_owner_repositories", [])) != 9:
        raise ValueError("The S30 source snapshot must cover the nine requested sites")
    slate = hypotheses.get("hypotheses", [])
    if len(slate) < 3 or len(slate) > 5:
        raise ValueError("The S30 preregistered slate must contain 3–5 hypotheses")
    if [item.get("rank") for item in slate] != list(range(1, len(slate) + 1)):
        raise ValueError("S30 hypothesis ranking must be consecutive and deterministic")
    if len(scorecard.get("sites", [])) != 9:
        raise ValueError("Historical scorecard must contain all nine requested sites")
    if overlap.get("pairs_total") != 72 or overlap.get("pairs_over_0_70") != 72:
        raise ValueError("The pinned nine-site overlap audit changed; re-review before publishing")
    if any(value <= 0.70 for value in overlap.get("pairwise_overlap", {}).values()):
        raise ValueError("S30 requires a directed-pair duplicate review at the literal 70% threshold")
    if forensic.get("champion_subset_of_solo") is not True:
        raise ValueError("GEMSDOE32 forensic relation no longer matches the pinned audit")
    if forensic.get("champion_equals_solo_minus_dcat_le2_exact") is not True:
        raise ValueError("GEMSDOE32 deletion-only reconstruction no longer matches the pinned audit")
    if forensic.get("symdiff_champion_vs_solo_minus_dcat_le2") != 0:
        raise ValueError("GEMSDOE32 reconstruction has a non-zero symmetric difference")
    if card.get("holdout", {}).get("dti") is not None or card.get("holdout", {}).get("ci95") is not None:
        raise ValueError("No S30 HOLDOUT-DTI can be published")
    passes = card.get("verification_passes", [])
    if len(passes) != 3 or any(item.get("pass") != index for index, item in enumerate(passes, 1)):
        raise ValueError("S30 card must record exactly three ordered verification passes")
    if any(not str(item.get("status", "")).startswith("PASS") for item in passes):
        raise ValueError("A verification pass is incomplete; refuse to publish the S30 closeout")


def panel(card_href: str, review_href: str, slate_href: str) -> str:
    return f'''<section class="section callout-danger readiness-banner" id="{PANEL_ID}" aria-label="Current S30 decision" data-submission-ready="false">
<p class="eyebrow">S30 · 2026-10-30 UTC · ACTIVE BRANCH REVIEW</p>
<h2>NO NEW TIFF · DOWNLOAD: NO FILE EXISTS · SUBMIT: NO</h2>
<p><strong>No new GeoTIFF was generated, no holdout was run, and no weekly slot was selected or spent.</strong> The automated preflight is BLOCKED. The current branch has no assigned geological lane, complete parallel registry, comparable frozen baseline, feature cache, or available pinned shared evaluator/writer. Its recorded two-hour clock is expired; it was not reset.</p>
<p><strong>Do not download or submit any historical raster from the nine-site archive.</strong> No unique S30 submission artifact exists. The literal 70%/3 px registry rule is binding; S29's earlier request for a human waiver is superseded and must not be reopened.</p>
<div class="download-actions"><button class="button" type="button" disabled aria-disabled="true">No approved TIFF to download</button><a class="button quiet" href="{esc(card_href)}" download>Download S30 run card (JSON)</a><a class="button quiet" href="{esc(slate_href)}" download>Download preregistered slate (JSON)</a><a class="button secondary" href="{esc(review_href)}">Open full S30 review</a></div>
<p class="small">This S30 banner is the current status. All S29/S28 panels below are archived snapshots and do not authorize an exception or a submission.</p>
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
    header_end = page.find("</header>")
    if header_end >= 0:
        header = page[:header_end]
        tail = page[header_end:]
        header = header.replace('href="s29-review.html">Current review',
                                'href="s30-review.html">Current review')
        header = header.replace('href="docs/s29-review.html">Current review',
                                'href="docs/s30-review.html">Current review')
        page = header + tail
    path.write_text(page, encoding="utf-8")


def retarget_current_nav(path: Path) -> None:
    page = path.read_text(encoding="utf-8")
    header_end = page.find("</header>")
    if header_end < 0:
        return
    header, tail = page[:header_end], page[header_end:]
    root_link = path.parent == ROOT
    if root_link:
        header = header.replace('href="docs/s29-review.html">Current review',
                                'href="docs/s30-review.html">Current review')
        header = header.replace('href="docs/session24-review.html">Latest review',
                                'href="docs/s30-review.html">Current review')
    else:
        header = header.replace('href="s29-review.html">Current review',
                                'href="s30-review.html">Current review')
        header = header.replace('href="session24-review.html">Latest review',
                                'href="s30-review.html">Current review')
    updated = header + tail
    if updated != page:
        path.write_text(updated, encoding="utf-8")


def score_table(scorecard: dict, overlap: dict) -> str:
    rows = []
    for site in scorecard["sites"]:
        directed = [
            value for pair, value in overlap["pairwise_overlap"].items()
            if pair.split("->", 1)[0] == site["site"] or pair.split("->", 1)[1] == site["site"]
        ]
        max_overlap = max(directed) if directed else site.get("max_overlap_vs_other_eight")
        rows.append(f'''<tr>
<th scope="row">{esc(site["site"])}</th>
<td>{fmt_score(site["highest_supplied_score"])}<br><span class="status holdout">USER-REPORTED / UNVERIFIED</span></td>
<td><code class="file-name">{esc(site["file"])}</code></td>
<td>{max_overlap:.1%}<br><span class="small">max directional overlap within 3 px</span></td>
<td>NOT ESTIMABLE</td>
<td>NO — historical reference only</td>
</tr>''')
    return "\n".join(rows)


def source_table(source: dict) -> str:
    rows = []
    for item in source["focus_site_owner_repositories"]:
        site = item["site"]
        commit = item["default_branch_head"]
        report = REPORT_PATHS[site]
        report_url = f"https://github.com/buffedlizard55-lab/{site}/blob/{commit}/{report}"
        rows.append(f'''<tr><th scope="row">{esc(site)}</th>
<td><a href="{esc(item["pinned_tree_url"])}"><code>{esc(commit[:12])}</code></a></td>
<td><a href="{esc(report_url)}">Pinned owner report</a><br><code>{esc(report)}</code></td>
<td>Owner-reported material only; no organizer receipt verified</td></tr>''')
    return "\n".join(rows)


def hypothesis_table(hypotheses: dict) -> str:
    rows = []
    for item in hypotheses["hypotheses"]:
        layers = ", ".join(item["layers"])
        availability = item["data_obtainability_check"].get("current_status", "Status not recorded")
        rows.append(f'''<tr><th scope="row">{item["rank"]}. {esc(item["name"])}<br><span class="small">{esc(item["id"])}</span></th>
<td>{esc(layers)}</td>
<td>{esc(item["physical_signature"])}<br><strong>Why:</strong> {esc(item["why_it_may_find_catalogue_missing_faults"])}</td>
<td>{esc(item["named_non_fault_mimic"])}</td>
<td>{esc(item["difference_from_implemented_repo_work"])}</td>
<td>{esc(item["implementation_cost"])}<br><strong>Expected ΔDTI:</strong> unknown</td>
<td>{esc(item["data_required"])}<br><strong>Availability:</strong> {esc(availability)}</td></tr>''')
    return "\n".join(rows)


def official_links(hypotheses: dict) -> str:
    items = list(hypotheses.get("official_manual_review_links", []))
    items.append("https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/")
    return "\n".join(f'<li><a href="{esc(url)}">{esc(url)}</a></li>' for url in items)


def standalone(card: dict, preflight: dict, source: dict, hypotheses: dict,
               scorecard: dict, overlap: dict, forensic: dict) -> str:
    report_panel = panel("data/s30_run_card.json", "s30-review.html", "data/s30_hypotheses.json")
    failures = "\n".join(f"<li>{esc(item)}</li>" for item in preflight["failures"])
    repository_rows = source_table(source)
    hypotheses_rows = hypothesis_table(hypotheses)
    scores = score_table(scorecard, overlap)
    official = official_links(hypotheses)
    historical_card = card["score_claim_hygiene"]["latest_saved_public_board_observation"]
    current_sources = len(source["focus_site_owner_repositories"])
    changed = source["checked_at_utc"]
    solo_key = "solo_r1_8acb75e1f2cc_owner_reported_0.2708"
    removed = forensic["removed_solo_to_champion"]
    solo_count = forensic["counts"][solo_key]
    removal_pct = 100 * removed / solo_count
    score_delta = card["gemdoe32_0_2778_analysis"]["score_difference_vs_0_2708_claim"]
    pair_count = overlap["pairs_total"]
    duplicated = overlap["pairs_over_0_70"]
    max_overlap = overlap["max_pairwise_overlap"]["value"]
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="GEMSDOE28 S30 fail-closed review: nine-site score claims, GEMSDOE32 forensic analysis, ranked hypotheses, preflight and submission status.">
<title>S30 current review | GEMSDOE28</title><link rel="stylesheet" href="assets/site.css"></head>
<body><header class="site-header"><div class="header-inner"><a class="brand" href="index.html">GEMSDOE28 <small>DOE GEMS · Auditable research</small></a>
<nav aria-label="Main navigation"><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary</a><a href="s30-review.html">Current review</a><a href="cross-site-review.html">Nine-site review</a><a href="sources.html">Sources</a></nav></div></header>
<main><section class="hero"><div class="hero-content"><p class="eyebrow">S30 · {esc(card["observed_utc"])} · {esc(card["branch"])}</p>
<h1>No new submission is authorized.</h1><p class="lead">The correct outcome is a documented stop, not a guessed method lane, an improvised score, or a reused historical raster. The automated preflight blocks experiments and submission.</p>
<div class="value-line"><span class="value-pill">DOWNLOAD: NO NEW FILE EXISTS</span><span class="value-pill">SUBMIT: NO</span><span class="value-pill">SCORE ESTIMATE: NOT ESTIMABLE</span><span class="value-pill">WEEKLY SLOT: NONE SELECTED</span></div>
<p>Scope: GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. This is a review of repository evidence and owner-reported claims, not a new official leaderboard audit.</p></div></section>
{report_panel}
<section class="section" id="scorecard"><h2>Nine-site executive summary</h2>
<p>These are the highest historical claims supplied in the pinned S23 scorecard, not a live leaderboard ranking. Every number is <strong>USER-REPORTED / UNVERIFIED</strong>; none has an archived organizer receipt tied to the raster. The “leaderboard estimate” is deliberately <strong>NOT ESTIMABLE</strong> for every row.</p>
<div class="table-wrap"><table id="s30-nine-site-scorecard"><caption>Historical score claims and status. No direct TIFF download links are provided; filenames identify audit-only artifacts.</caption><thead><tr><th>Site</th><th>Highest supplied claim</th><th>Historical artifact name</th><th>Max overlap within 3 px</th><th>Leaderboard estimate</th><th>Download / submit</th></tr></thead><tbody>{scores}</tbody></table></div>
<p><strong>Literal duplicate result:</strong> {duplicated}/{pair_count} directed comparisons among the nine selected historical artifacts exceed 70% within 3 px; maximum directional overlap is {max_overlap:.1%}. This is a historical nine-file subset, not the missing complete registry. Surface rank-correlation against the complete current registry cannot be checked because that registry is absent.</p>
<p>Machine-readable records: <a href="data/s30_scorecard.json">S30 scorecard snapshot</a> · <a href="data/s30_overlap_audit.json">historical overlap audit</a> · <a href="data/s30_source_refresh.json">pinned owner-repository heads</a>.</p></section>
<section class="section" id="gemsdoe32"><h2>What the GEMSDOE32 “0.2778” claim does—and does not—show</h2>
<div class="callout"><strong>Claim status: OWNER-REPORTED / UNVERIFIED.</strong> The local forensic record found no organizer receipt. The number is not a current confirmed leaderboard score, and no hidden-score estimate is inferred from it.</div>
<p>The pinned forensic record confirms that the 37,654-dot B2 pattern is an exact subset of GEMSDOE31 H27-4 solo: it removes {removed:,} dots (about {removal_pct:.2f}% of the parent set) and adds none. The removed dots are those within 2 px of the published USGS/INGENIOUS catalogue. The reported difference from the GEMSDOE31 0.2708 claim is +{score_delta:.4f}.</p>
<p>A plausible metric mechanism is that removing low-credit predictions can lower the false-positive contribution. That is only a hypothesis about the reported difference—not a verified causal explanation, not proof that every removed dot was a false positive, and not evidence of a new geological detector. The raster remains geometrically non-unique under the requested 70%/3 px rule. Do not copy, relabel, download for submission, or resubmit it.</p>
<p>Evidence: <a href="data/s30_gemsdoe32_forensic.json">pinned subset forensic</a> · <a href="data/s30_scorecard.json">score claim record</a>. The artifact filename is recorded in the JSON for audit only; this page provides no TIFF download link.</p></section>
<section class="section" id="hypotheses"><h2>Ranked, untried geological hypotheses</h2>
<p>Three candidates are preregistered before implementation. Rank is a qualitative balance of expected potential and cost, <strong>not a numerical DTI forecast</strong>. The top MCR idea is local-data-only in principle, but cannot run because the feature cache, assigned lane and shared evaluator are missing. The external-data proposals are not called viable: their required bytes were not freshly obtained or checked.</p>
<div class="table-wrap"><table><caption>Physical signature, repository differentiation, non-fault mimic, cost and actual data availability.</caption><thead><tr><th>Rank / candidate</th><th>Specific layers</th><th>Transform and rationale</th><th>Named non-fault mimic</th><th>Difference from repo work</th><th>Cost / expected ΔDTI</th><th>Required data / availability</th></tr></thead><tbody>{hypotheses_rows}</tbody></table></div>
<p>Full preregistration: <a href="data/s30_hypotheses.json">download JSON hypothesis slate</a>. No hypothesis was fit, tested on holdout, or selected as the active lane.</p></section>
<section class="section" id="preflight"><h2>Automated gate result: BLOCKED</h2>
<p>Preflight checked {esc(preflight["checked_at_utc"])}. It records {float(preflight["elapsed_seconds"]):,.3f} elapsed seconds against a {int(preflight["time_cap_seconds"]):,}-second cap. The clock was not reset.</p>
<ul>{failures}</ul>
<p>No S30 surface correlation or final-dot overlap can be reported: no candidate surface, final dots, or raster exists, and the full synchronized registry is missing. No feature-alone AUC, HOLDOUT-DTI, confidence interval, or validator output was generated.</p>
<p>The required holdout protocol remains fixed: whole buffered fault-segment holdout; catalogue features from visible faults only; pixel-exact visible-fault mask; pooled DTI with α=0.2, β=0.8 and a 300 m triangular kernel; report evaluator version, withheld-positive count, and 95% CI. This run has no holdout measurement.</p>
<p><a href="data/s30_preflight.json">Preflight JSON</a> · <a href="data/s30_run_card.json">S30 run card JSON</a>.</p></section>
<section class="section" id="source-review"><h2>Fresh source review and provenance limits</h2>
<p>The source feed was refreshed at {esc(changed)} using a GitHub/API-only allowlist. {current_sources} of {current_sources} focus-site repository heads were observed; 10/18 total metadata sources were fresh. DrivenData, USGS, ScienceBase and GDR pages were not contacted in this runtime. No competition leaderboard, portal receipt, or current account allowance was checked. The 2026-10-29 public-board numbers below are only the latest saved repository observation.</p>
<div class="table-wrap"><table><caption>Commit-pinned owner summaries fetched through GitHub for review; these are not official competition evidence.</caption><thead><tr><th>Site</th><th>Observed head</th><th>Review page</th><th>Evidence class</th></tr></thead><tbody>{repository_rows}</tbody></table></div>
<p>Saved board observation ({esc(historical_card["observed_date"])}): #1 {fmt_score(historical_card["rank_1"])}; #26 {fmt_score(historical_card["rank_26"])}. It is not current as of S30 and does not prove any local raster's score. The user-supplied 0.4413 and 0.3195 anchors remain unresolved as current standings; the prior observation is not substituted for a fresh official check.</p>
<div class="callout"><strong>Official, trusted manual source links (not freshly verified in this run):</strong><ul>{official}</ul><p>Fresh official-source verification is incomplete. Historical availability records are not treated as current bytes, schema, coverage, or license confirmation.</p></div></section>
<section class="section" id="submission-guide"><h2>Safe submission guide — currently STOP</h2>
<p><strong>Current action: none. There is no file to download or submit.</strong> A future run may proceed only after the blocked gates are resolved and the same protocol is pinned.</p>
<ol class="submission-steps"><li>Obtain the explicit single-method lane assignment; restore the complete parallel-run raster registry, frozen same-protocol best, hash-pinned shared feature cache, evaluator, writer and validator. Do not infer a lane or reset the expired clock.</li>
<li>Run the automated preflight and stop unless every gate passes. Before implementation, preregister 3–5 hypotheses with official data availability confirmed. Budget no more than 3 experiments or 2 hours.</li>
<li>Run feature-alone leakage canaries; AUC above 0.90 is leakage until disproven. Use only the shared evaluator, visible-fault-derived catalogue features and pixel-exact mask. Hold out whole buffered fault segments and report full HOLDOUT-DTI provenance and 95% CI.</li>
<li>Apply the duplicate gate before placement and on final dots: stop if any rank-correlation exceeds 0.90 or more than 70% of dots fall within 3 px of a registry raster. A byte-different file is not enough.</li>
<li>Only the shared writer and automated validator may emit a candidate. Check the exact raster hash, format, bounds, outside encoding, registry result and submission note. A format pass alone never authorizes upload.</li>
<li>Run the separate promotion selector. Upload only the exact filename and note for which the selector records <code>ok_to_submit: true</code>; do not select or spend a weekly slot before that step.</li>
<li>After a manual portal upload, retain its receipt and bind it to the exact raster hash. Only then may a score be labeled ORGANIZER-CONFIRMED. A holdout value or public leaderboard observation is not a receipt.</li></ol>
<p>Historical note: the official outside-footprint encoding and some portal-format irregularities remain unresolved in repository evidence. Do not guess or treat zeros and NaN as interchangeable.</p></section>
<section class="section" id="verification"><h2>Three verification passes</h2>
<ol><li><strong>Pass 1 — inventory and gates:</strong> read the README and operating protocol, inspect the active branch and evidence, run the baseline lint/test/site build, refresh GitHub-only source metadata and run the strict S30 preflight. Result: BLOCKED; no experiment or artifact authorized.</li>
<li><strong>Pass 2 — evidence and implementation review:</strong> pin the nine owner repositories, inspect their current summary pages and the GEMSDOE32 forensic record, register the 3-candidate slate before code changes, and implement this report/guard without changing the experiment lane or creating a TIFF.</li>
<li><strong>Pass 3 — independent recheck:</strong> automated tests validate all nine rows, 72/72 historical directed duplicate comparisons, negative approval flags, absent raster/hash, note length, source scope, hypothesis count and generated page links; final Ruff, pytest and offline build results are recorded in the run card/closeout.</li></ol>
<p>These are repository verification passes, not three geological experiments. No human visual check can override the automated gates.</p></section>
<section class="section" id="irregularities"><h2>Irregularities and unresolved evidence</h2>
<ul><li>The nine-site score table is an October 27 historical, owner-supplied snapshot. Current owner reports contain research-only changes; no current organizer receipt was found.</li>
<li>GEMSDOE24's current GEO1 report describes its HOLDOUT-DTI as compromised by full-label eligibility leakage and reports 99.25% final-dot overlap with a calibration lattice. Do not rank that value as a valid holdout or leaderboard score.</li>
<li>The current public leaderboard and authenticated weekly-submission allowance were not accessible under this run's host policy. Prior 0.4413 / 0.3195 anchors and the saved 0.4544 / 0.3328 observation must not be represented as today's verified standings.</li>
<li>The nine-site 72/72 check is a selected-subset historical geometry audit, not a complete current registry. It nevertheless means none of those nine artifacts meets the requested literal threshold in that audit.</li>
<li>External source availability is dated: the historical inventory records prior fetches, but this run did not re-obtain the source bytes. The HFR2M and DNT candidates remain not viable until their exact official data are fetched and pinned.</li></ul>
<p>Machine-readable source snapshot: <a href="data/s30_source_refresh.json">S30 source refresh record</a> · <a href="data/feed.json">full metadata feed</a>.</p></section>
</main><footer><div class="footer-inner"><p><strong>Maximize P(Win) · Own the Outcome.</strong> S30 ended negative: zero experiments, zero holdouts, zero TIFFs, zero slots selected.</p></div></footer></body></html>'''


def main() -> int:
    card = load(CARD_PATH)
    preflight = load(PREFLIGHT_PATH)
    source = load(SOURCE_REFRESH_PATH)
    hypotheses = load(HYPOTHESES_PATH)
    scorecard = load(SCORECARD_PATH)
    overlap = load(OVERLAP_PATH)
    forensic = load(FORENSIC_PATH)
    validate_records(card, preflight, source, hypotheses, scorecard, overlap, forensic)

    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    (DOCS / "data/s30_run_card.json").write_bytes(CARD_PATH.read_bytes())
    for source_path, target_path in PUBLISHED_EVIDENCE.items():
        target_path.write_bytes(source_path.read_bytes())
    for path, (card_href, review_href, slate_href) in PAGES.items():
        inject(path, panel(card_href, review_href, slate_href))
    (DOCS / "s30-review.html").write_text(
        standalone(card, preflight, source, hypotheses, scorecard, overlap, forensic),
        encoding="utf-8")
    for page in DOCS.glob("*.html"):
        retarget_current_nav(page)
    for page in (ROOT / "index.html", ROOT / "executive-summary.html", ROOT / "current-review.html"):
        retarget_current_nav(page)
    print(json.dumps({
        "status": "built",
        "panel": PANEL_ID,
        "pages": [path.relative_to(ROOT).as_posix() for path in PAGES],
        "review": "docs/s30-review.html",
        "hypotheses": len(hypotheses["hypotheses"]),
        "historical_duplicate_pairs": overlap["pairs_over_0_70"],
        "network_requests": 0,
        "new_tiff": False,
        "experiment_allowed": False,
        "ok_to_download": False,
        "ok_to_submit": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
