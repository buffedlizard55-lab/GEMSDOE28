"""Dependency-free current decision panels; historical cards never grant approval."""
from __future__ import annotations

import csv
import html
import io

HISTORICAL_TIF = "gems28-s22-ctxhgb-20261026-e23dabcec6e2-allfinite.tif"


def esc(value):
    return html.escape(str(value), quote=True)


def score_csv(scorecard):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["site", "historical_reference_file", "highest_supplied_result", "result_evidence_class",
                     "estimated_leaderboard_score", "unique_under_requested_rule", "ok_to_submit", "sha256", "source"])
    for row in scorecard["sites"]:
        writer.writerow([row["site"], row["file"], f"{row['highest_supplied_score']:.4f}",
                         row["score_evidence_class"], "UNAVAILABLE", "NO", "NO", row["sha256"], row["source"]])
    return stream.getvalue()


def notice(card):
    # This renderer cannot select a slot, even if JSON is changed to claim one.
    bounds = card.get("registry", {}).get("bounds", {})
    covered = bounds.get("covered_fraction")
    text = f"{covered * 100:.4f}%" if isinstance(covered, (float, int)) else "not recorded"
    return f'''<section class="readiness-banner callout-danger" id="current-submission" aria-label="Current submission readiness" data-submission-ready="false">
<p class="eyebrow">S23 audit: no new TIFF · 27 OCT 2026 · AUTOMATED DECISION · NO HUMAN INSPECTOR</p>
<h2>Current run: NOT READY TO SUBMIT — NO FILE APPROVED</h2>
<p><strong>OK to download a new submission: NO. OK to submit: NO.</strong> S23 stopped before a new model or TIFF. The shared calibration lattice covers <strong>{esc(text)}</strong> of the footprint within 3 pixels (GEOMETRY-AUDIT, not a score); it blocks the champion-sized budget under your literal any-raster rule.</p>
<p>The inherited S22C file is a <strong>measured duplicate under that rule — DO NOT SUBMIT</strong>. Its format pass does not override novelty or missing buffered validation. No weekly slot has been selected or spent; do not upload it or any prior file as a new submission.</p>
<div class="download-actions"><button class="button" type="button" disabled aria-disabled="true">Submission download locked</button><a class="button quiet" href="data/current_run_card.json" download>Download current JSON run card</a><a class="button quiet" href="executive-summary.html">Executive summary &amp; submission guide</a><a class="button quiet" href="session24-review.html">Latest repository review</a></div>
</section>'''


def session24_review(card):
    """Render the current read-only repo review without turning it into a score or approval."""
    preflight = card["preflight"]
    feed = card["source_feed_observation"]
    registry = card["registry"]
    bounds = registry["calibration_lattice_geometry_bound"]
    verification = card["verification"]
    blockers = "".join(f"<li>{esc(item)}</li>" for item in preflight["blockers"])
    failures = "".join(f"<code>{esc(item)}</code>" for item in feed["failed_ids"])
    return f'''<div class="breadcrumb"><a href="index.html">Overview</a> / Latest review</div>
<section class="hero"><div class="hero-content"><p class="eyebrow">S24 · READ-ONLY REPOSITORY REVIEW · 27 OCT 2026</p><h1>No new TIFF.<br>No submission approval.</h1><p class="lead">This review verified the current repo state, source-feed chronology and automated gates. It did not fit a geological model, generate a prediction surface, run HOLDOUT-DTI, estimate a leaderboard score or select a weekly slot.</p><div class="value-line"><span class="status danger">NEGATIVE · DO NOT SUBMIT</span><span class="value-pill">0 experiments</span><span class="value-pill">0 slots spent</span></div></div></section>
<section class="section"><div class="callout callout-danger"><strong>Automated decision: no file is approved.</strong> There is no new TIFF to download. Do not reuse a historical raster under a different name. The S23 finding that inherited S22C is a duplicate remains in force.</div><h2>Current preflight: {esc(preflight['status'])}</h2><p>Checked {esc(preflight['checked_at_utc'])}; expected fail-closed exit code {esc(preflight['exit_code'])}. The current checkout is missing the preregistered lane/assignment, complete registry, comparable frozen best, feature cache and pinned shared tools.</p><ul>{blockers}</ul><p>The 37,654-dot lattice calculations below are <strong>GEOMETRY-AUDIT, not scores</strong>; they do not prove that every smaller budget is impossible. No search to exploit lattice holes was performed.</p><div class="table-wrap"><table><thead><tr><th>GEOMETRY-AUDIT quantity</th><th>Observed bound</th></tr></thead><tbody><tr><td>Footprint pixels</td><td>{int(bounds['footprint_pixels']):,}</td></tr><tr><td>Pixels within 3 px of calibration lattice</td><td>{int(bounds['covered_within_3px_pixels']):,} ({bounds['coverage_fraction']:.4%})</td></tr><tr><td>Uncovered pixels</td><td>{int(bounds['uncovered_pixels']):,}</td></tr><tr><td>Unspaced minimum overlap at 37,654 dots</td><td>{bounds['unspaced_minimum_overlap_fraction']:.4%}</td></tr><tr><td>Minimum overlap at 2.8 px spacing</td><td>{bounds['minimum_overlap_fraction_with_spacing_2_8px']:.4%}</td></tr><tr><td>Inherited S22C final-dot overlap</td><td>{registry['final_dot_comparison']['candidate_dots_within_3px_fraction']:.4%} · DUPLICATE_STOP</td></tr></tbody></table></div><p>Inherited S22C raw Spearman {registry['final_dot_comparison']['raw_spearman']:.6f} and sampled kernel Spearman {registry['final_dot_comparison']['sampled_kernel_spearman']:.6f} are both below the correlation threshold; its 3-pixel overlap still independently fails. No S24 pre-placement surface exists.</p></section>
<section class="section"><h2>Latest committed source metadata</h2><p>Snapshot time <time datetime="{esc(feed['checked_at_utc'])}">{esc(feed['checked_at_utc'])}</time>: {int(feed['freshly_observed_count'])}/{int(feed['source_count'])} observed; status <strong>{esc(feed['status'])}</strong>. Failed entries: {failures}. Both exceeded the 2,000,000-byte response limit. The snapshot is metadata-only and was about 57 minutes old at the S24 preflight; it is not a live check or a score feed.</p><p>No DrivenData page, leaderboard, account allowance, or submission receipt was fetched in this checkout. A separate concurrent S24 geometry-audit record is linked below; its public leaderboard observation is not a receipt and was not refreshed here. <a href="data/feed.json">View the current committed feed file</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/snapshots/s24_source_feed.json">View the immutable S24 snapshot</a>.</p><p><a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/68_s24_result.md">Separate concurrent S24 geometry audit</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/s24_run_card.json">its independent run card</a>. Its exploratory A/B/C comparator options were not adopted; the literal all-registry duplicate-stop remains active.</p></section>
<section class="section"><h2>Nine-site decision</h2><p>GEMSDOE32's supplied 0.2778 is USER-REPORTED / UNVERIFIED. Pixel forensics support a plausible explanation: its raster removes 2,545 catalogue-adjacent dots from the GEMSDOE31 solo pattern. That may reduce false-positive cost without adding a detector, but does not prove why the organizer assigned a score. All nine sites have a supplied historical best in the <a href="executive-summary.html#nine-site-scorecard">executive summary table</a>; none is a unique new file, and no calibrated hidden-score estimate is available.</p><p>This checkout did not refresh the leaderboard. A separate parallel S24 audit records an approximately 18:50 UTC ORGANIZER-PUBLIC observation (#1 0.4544, #25 0.3195, #50 0.2857); it is not a file-bound receipt or current refresh. See its separate report and run card; do not pool it with this review. The repository's 0.4437 observation is older and not a receipt.</p></section>
<section class="section"><h2>Four ranked mechanisms remain untested proposals</h2><p>PCSE phase-congruent scarp energy remains the top qualitative hypothesis; TCB texture-covariance boundary, MCR matched conductive residual and CSD compound-scarp diffusion spectrum follow. Improvements are unknown; CSD is not viable here without the original official USGS 1 m DEM bytes. Full layer details, physical rationale, mimics and source gates are in the <a href="session23-result.html">S23 research record</a>.</p></section>
<section class="section"><h2>Software verification (not scientific validation)</h2><ul><li>{esc(verification['pytest_status'])}</li><li>Ruff: {esc(verification['ruff_status'])}</li><li>Static site build: {esc(verification['site_build_status'])}</li><li>Current preflight: BLOCKED; no model/holdout/TIFF emitted.</li></ul><p>Full review: <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/68_s24_repository_review.md">repository review report</a> · <a href="data/s24_repository_review_run_card.json" download>Repository-review JSON run card</a> · <a href="https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/s24_preflight.json">preflight evidence</a> · <a href="executive-summary.html">executive summary and exact future submission steps</a>.</p></section>'''


def history_links():
    return f'''<section class="section"><h2>Research archive — not approved submissions</h2>
<p>Historical results are preserved rather than rewritten. The S22C “promote” claim and ratio projection are superseded by S23's literal-rule reassessment. A different file hash is not a new geological method.</p>
<p><a href="session19-result.html">S19 archive</a> · <a href="session20-result.html">S20 result</a> · <a href="session21-result.html">S21 result</a> · <a href="session22-result.html">S22-SIGN</a> · <a href="session22-mofr-result.html">S22-MOFR</a> · <a href="session22c-result.html">S22C historical result</a> · <a href="submission-review.html">Parallel review</a> · <a href="topology.html">Topology</a></p>
<details><summary>S22C reference TIFF (duplicate; educational use only)</summary><p><a href="downloads/{HISTORICAL_TIF}" download>Download historical S22C TIFF — DO NOT SUBMIT</a>. This is <strong>not a newly generated file</strong>. Content ID <code>e23dabcec6e2</code>; exact bytes remain registered in <a href="data/run_card_s22c.json">the historical run card</a>.</p></details>
<p><a class="button quiet" href="archive.html">Open all historical research artifacts</a></p></section>'''


def score_table(scorecard):
    rows = []
    for r in scorecard["sites"]:
        rows.append(f'''<tr><th scope="row">{esc(r['site'])}</th>
<td><a href="{esc(r['source'])}"><code>{esc(r['file'])}</code></a><br><small>Historical reference only · SHA-256 {esc(r['sha256'][:12])}…</small><br><a href="{esc(r['source'])}?raw=1" download>Download historical TIFF — DO NOT SUBMIT</a></td>
<td><strong>{r['highest_supplied_score']:.4f}</strong><br><small>USER-REPORTED / UNVERIFIED</small></td>
<td>Unavailable<br><small>No validated hidden-score estimate</small></td>
<td><strong>NO</strong><br>{r['max_overlap_vs_other_eight'] * 100:.2f}% within 3 px of {esc(r['max_overlap_reference'])}</td>
<td>{'PASS' if r['format_checks_passed'] else 'FAIL'} local format<br><strong>DO NOT SUBMIT</strong></td></tr>''')
    return '''<section class="section" id="nine-site-scorecard"><p class="eyebrow">NINE PRIORITY SITES · PINNED FILE BYTES, NOT SCORE RECEIPTS</p>
<h2>Nine-site executive scorecard</h2>
<p><strong>Best reported result is not an approved submission.</strong> GEMSDOE32 H33-2-B2 leads the supplied historical claims, not necessarily the current leaderboard. No table row is a new or recommended upload. “Unavailable” is deliberate: a catalogue holdout cannot reliably estimate an expert-hidden score without transfer calibration.</p>
<p>These are <strong>USER-REPORTED / UNVERIFIED</strong> results, not HOLDOUT-DTI or ORGANIZER-CONFIRMED. All <strong>72 directional comparisons</strong> among the nine historical files exceed the requested 70% proximity threshold. This is <strong>not the complete current registry</strong>.</p>
<div class="table-wrap"><table><caption>File to inspect, supplied result, estimate availability, uniqueness and upload decision for every requested site.</caption><thead><tr><th>Site</th><th>Historical file / source</th><th>Highest supplied result</th><th>Estimated leaderboard score</th><th>Unique vs the other eight?</th><th>Format / upload</th></tr></thead><tbody>''' + "".join(rows) + '''</tbody></table></div>
<p class="small">Overlap is directional and measured across every candidate dot, not a sample. A local format PASS is neither novelty nor organizer acceptance. Source files are owner-repository bytes; source-link availability is not proof of a competition receipt.</p>
<p><a href="data/s23_scorecard.csv" download>Download the table (CSV)</a> · <a href="data/s23_scorecard.json" download>Download the source-pinned scorecard (JSON)</a> · <a href="../evidence/s23_priority_audit.json">Fresh nine-repository audit</a> · <a href="../evidence/s23_focus_novelty.json">All 72 exact comparisons</a></p></section>'''


def site_details(scorecard):
    sections = []
    for row in scorecard["sites"]:
        claims = ", ".join(f"{x:.4f}" for x in row["all_supplied_score_claims"])
        sections.append(f'''<article class="card span-6"><p class="eyebrow">{esc(row['site'])}</p><h3>{row['highest_supplied_score']:.4f} · highest supplied claim</h3>
<p>{esc(row['interpretation'])}</p><p class="small">All supplied claims for this site: {claims} — USER-REPORTED / UNVERIFIED. Verified {row['selected_historical_variants_verified']} historical variants; the repository tree lists {row['published_raster_paths_in_repo']} TIFF paths, including non-submission inputs. No complete-content or organizer-score audit of every path is claimed.</p><p><a href="{esc(row['source'])}">Pinned historical file →</a></p></article>''')
    return '<section class="section"><h2>Executive assessment for every site</h2><div class="grid">' + "".join(sections) + '</div></section>'


def scientific_answer():
    return '''<section class="section" id="why-02778"><h2>Why does the supplied GEMSDOE32 result lead?</h2>
<p><strong>Verified construction, not verified score causation:</strong> the freshly fetched GEMSDOE32 raster is exactly the GEMSDOE31 solo dot set with <strong>2,545</strong> catalogue-adjacent dots (distance ≤2 px) removed. It has <strong>37,654</strong> dots. GEMSDOE25 and GEMSDOE30 have exactly the same historical dot geography; GEMSDOE36 contains every champion dot plus <strong>1,200</strong> extras. These are pixel-forensic counts, not new model results.</p>
<p>The shared evaluator uses a 300 m triangular distance kernel and DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw). Closely packed predictions can be redundant for credit but still add false-positive mass. Pruning low-marginal-credit dots can therefore improve a result <em>without detecting a single new fault</em>. That mechanism is consistent with the supplied ladder; hidden truth and file-bound organizer receipts are absent, so the actual cause of the reported ranking is not established.</p>
<p><strong>Can we honestly claim a file above the reported 0.2778?</strong> No. A distinct detector might improve coverage, but this session did not validate one. S22C's historical ratio projection is withdrawn from current recommendations: its unbuffered catalogue proxy does not establish transfer to expert-mapped missing faults. No credible leaderboard point estimate or interval is available for a new TIFF.</p>
<p><strong>Faults are not geothermal vents.</strong> The <a href="https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb">official reference notebook</a> is a geological-fault detector. A fault prediction does not establish active fluid flow, reservoir temperature or a vent discovery. None is claimed here.</p>
<p><a href="../evidence/s23_focus_novelty.json">Exact reconstruction evidence</a> · <a href="../evidence/s23_official_source_review.json">Verified claims and unavailable sources</a></p></section>'''


def geometry_explanation(card):
    b = card["registry"]["bounds"]
    spacing = b["spacing"]
    return f'''<section class="section" id="registry-blocker"><h2>The rule that stops this run</h2>
<p>The registered spacing-5 calibration lattice is a comparison control, not a copied geological detector. Nevertheless, your rule says <em>any registry raster</em>; it cannot be silently exempted. The pinned shared novelty code already distinguishes a control diagnostically while retaining the literal stop rule. This audit confirms that behavior.</p>
<div class="grid"><article class="card span-4"><p class="eyebrow">GEOMETRY-AUDIT · NOT A SCORE</p><div class="metric">{b['covered_fraction'] * 100:.4f}%</div><p>of {b['footprint_pixels']:,} footprint pixels are within 3 px of the lattice.</p></article>
<article class="card span-4"><p class="eyebrow">COUNTING BOUND · NOT A SCORE</p><div class="metric">≥{b['unspaced_overlap_lower_bound'] * 100:.2f}%</div><p>overlap for <em>every</em> {b['candidate_budget']:,}-dot raster, even without a spacing constraint. Only {b['uncovered_pixels']:,} cells are uncovered; at least {b['required_uncovered_dots_to_pass']:,} uncovered dots would be needed to pass.</p></article>
<article class="card span-4"><p class="eyebrow">INHERITED S22C · NOT HOLDOUT-DTI</p><div class="metric">{card['registry']['inherited_final_within_3px_fraction'] * 100:.2f}%</div><p>of its final dots are within 3 px of the lattice. Raw final-raster Spearman is approximately {card['registry']['inherited_final_raw_spearman']:.6f}; low correlation does not override an overlap failure.</p></article></div>
<p>Proof: if U cells are uncovered and a candidate contains B distinct dots, at least B−U dots must lie in covered cells. Thus overlap ≥max(0,1−U/B). At the intended {b['candidate_budget']:,}-dot budget the rule is impossible. For 2.8 px-spaced dots, a square-partition capacity bound tightens this to <strong>≥{spacing['overlap_lower_bound'] * 100:.2f}%</strong> (GEOMETRY-AUDIT). This is not a claim that every conceivable smaller budget is impossible.</p>
<p><strong>Independent historical format audit:</strong> 51 registered TIFFs / 868 checks, still FAILING two legacy nodata-tag variants. This is not organizer acceptance. <a href="../evidence/s23_download_audit.json">Read the exact-file failures</a>.</p>
<p><strong>Disposition:</strong> stop the inherited lane. Do not relocate predictions into lattice holes, lower a budget after this test, or drop a comparator to manufacture a pass. The requested new TIFF and top-hypothesis holdout remain <strong>uncompleted</strong>; no false approval replaces them.</p>
<p><a href="../evidence/s23_registry_feasibility.json">Reproducible geometry / shared-novelty report</a> · <a href="../src/gems27/registry_feasibility.py">Counting-bound extension</a> · <a href="../registry/protocol_assets.json">Pinned shared tools</a></p></section>'''


def overview(card, scorecard):
    return '''<section class="hero"><div class="hero-content"><p class="eyebrow">GEMSDOE28 · END-TO-END EVIDENCE</p><h1>A higher score needs<br>new evidence, not a new name.</h1><p class="lead">Nine priority sites reviewed. Historical bytes verified. An inherited “promote” recommendation corrected. The project will not spend a scarce slot on an invalid uniqueness claim.</p><div class="value-line"><span class="value-pill">Maximize P(Win)</span><span class="value-pill">Own the Outcome</span><span class="status danger">NEGATIVE · NO NEW TIFF</span></div><p><a href="executive-summary.html">Exactly what to download and when to submit →</a></p></div></section>''' + score_table(scorecard) + geometry_explanation(card) + scientific_answer() + history_links()


def executive(card, scorecard):
    return '''<section class="section"><p class="eyebrow">EXECUTIVE SUMMARY · READ THE DECISION FIRST</p><h1>Which file should I submit?</h1><p class="lead"><strong>None from this run.</strong> There is no newly generated, validated, unique submission TIFF. All file links in the table are historical references, not permission to re-upload. This is an automated rejection, not a request for a human geological inspector.</p><p><strong>New submission name:</strong> not assigned — no new TIFF. <strong>Portal note:</strong> not applicable. The JSON run card has a short audit note, not an upload instruction.</p></section>''' + score_table(scorecard) + site_details(scorecard) + '''<section class="section" id="submission-guide"><h2>Exactly how a future eligible submission works</h2><ol class="submission-steps">
<li><strong>Check the current decision.</strong> If the page says NOT READY, stop. A working download, unique filename or format PASS alone is insufficient. That is the state today: <strong>not OK to submit</strong>.</li>
<li><strong>Pass automated scientific and novelty gates.</strong> Reuse the verified cache/shared evaluator/writer; test every feature alone, withhold whole fault components with a spatial buffer, derive catalogue features from visible faults only, and mask those faults pixel-exactly. Require pooled HOLDOUT-DTI with evaluator version, withheld-positive count and paired spatial 95% CI beating a frozen same-protocol best. Check the surface before placement and final dots against the full registry. Stop on any duplicate.</li>
<li><strong>Write and re-read the exact file.</strong> One float32 GeoTIFF band; CRS, shape and geotransform exactly match the sample; finite values in [0,1] inside the footprint. Verify its SHA-256 and ZIP membership if packaged. Reject invalid values; never silently clamp a scientific prediction to make validation appear green.</li>
<li><strong>Publish one content-bound new file, name and ≤140-character note.</strong> Only then should a one-click submission download appear. Keep technical validation, scientific eligibility and actual slot authorization separate.</li>
<li><strong>The separate selector checks the actual authenticated submission page.</strong> Confirm the current weekly cap and remaining allowance. Neither is available here. No research run may select or upload a real slot.</li>
<li><strong>At the contest form, only after those steps:</strong> choose New submission → File to submit; select the approved .tif (or ZIP containing that single GeoTIFF), paste the registered short note, and submit. This account-side operation has not been performed here.</li>
<li><strong>Preserve the exact organizer receipt.</strong> Bind the returned score to filename and SHA-256 before calling it ORGANIZER-CONFIRMED. A repository claim, public leaderboard row or local holdout is not that receipt.</li></ol>
<h3>The earlier “Predicted values must be in range [0, 1]” error</h3>
<p>The cause remains unknown. The shared writer rejects NaN/Inf or out-of-range values inside the footprint. Its all-finite zero-outside variant avoids a whole-array NaN/range violation and clears the nodata tag; its NaN-outside variant follows the stored sample convention. Neither variant guarantees portal acceptance. Do not infer a portal bug or an accepted footprint policy from this error text alone.</p>
<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official format / metric</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">Official data / sample</a> · <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules PDF</a>. These non-GitHub pages were not freshly retrieved in this runtime.</p></section>''' + geometry_explanation(card) + scientific_answer() + history_links()


def hypotheses(slate):
    rows = []
    for h in slate["hypotheses"]:
        rows.append(f'''<tr><th scope="row">{h['rank']} · {esc(h['id'])}<br>{esc(h['name'])}</th><td>{esc(', '.join(h['layers']))}<br><br>{esc(h['physical_signature'])}</td><td>{esc(h['missing_catalogue_mechanism'])}</td><td>{esc(h['repo_difference'])}</td><td>{esc(h['non_fault_mimic'])}</td><td>Improvement: <strong>unknown</strong><br>Cost: {esc(h['implementation_cost'])}<br><br>{esc(h['data_status'])}</td></tr>''')
    return '''<section class="section" id="s23-hypotheses"><p class="eyebrow">FROZEN BEFORE IMPLEMENTATION · NONE RUN</p><h2>Four ranked geological hypotheses</h2><p>Qualitative expected benefit versus cost, not numerical DTI forecasts. Specific operators were not found in this checkout; global novelty and exclusive lane assignment are not established. These mechanisms are hypotheses, not findings verified by the organizer notebook or newly retrieved field literature.</p><div class="table-wrap"><table><caption>Unimplemented geological proposals, ranked qualitatively by benefit and cost.</caption><thead><tr><th>Rank / hypothesis</th><th>Layers / transform</th><th>Why potentially off-catalogue?</th><th>Difference from this repo</th><th>Non-fault mimic</th><th>Benefit / cost / obtainability</th></tr></thead><tbody>''' + "".join(rows) + '''</tbody></table></div><p><a href="../knowledge/66_s23_preregistration.md">Frozen rationale, order and stop rules</a> · <a href="../registry/s23_hypotheses.json">Machine-readable hypothesis ledger</a></p>
<p><strong>Top hypothesis not validated:</strong> registry/preflight gates stopped the run before any new feature or model. Do not spend a slot on PCSE. Original USGS 3DEP DEM tile bytes are unavailable under this runtime's network policy, so CSD is explicitly not viable today.</p></section>'''


def source_review(review):
    verified = "".join(f'<li>{esc(c["claim"])} <small>({esc(c["location"])})</small></li>' for c in review["official_reference"]["verified_claims"])
    inaccessible = "".join(f'<li><a href="{esc(s["source"])}">{esc(s["id"])}</a> — not freshly retrieved here.</li>' for s in review["external_sources_not_freshly_retrieved"])
    return f'''<section class="section" id="s23-source-review"><p class="eyebrow">SOURCE-BY-SOURCE CLAIM BOUNDARIES</p><h2>What was verified, and what was not</h2><p>Fresh official-reference bytes were retrieved through GitHub and SHA-256 pinned at commit <code>{esc(review['official_reference']['commit'])}</code>. Verified from those bytes:</p><ul>{verified}</ul>
<p>The shared evaluator/writer are owner-maintained tools, not organizer code. Current pins bring in the upstream empty-canary guard, strict comparator-grid checks and paired comparison without creating a private fork. Synthetic tests validate their software contracts only.</p>
<p><strong>Current leaderboard and weekly allowance: unknown.</strong> The repository retains a historical <strong>public leaderboard observation</strong> of <strong>0.4437</strong> at 2026-10-26 22:02 UTC. It is not an organizer receipt, a fresh observation today or evidence for any local raster. The prompt's 0.3195 / 0.4413 anchors must not be asserted as today's top. No competition page was requested automatically in S23.</p>
<details><summary>Official links retained for review — availability/content not freshly verified here</summary><ul>{inaccessible}</ul></details>
<p>Input hashes prove equality to disclosed owner mirrors, not original organizer provenance, license permission or competition acceptance. No new field study or original DEM tile was obtained in this session. Freshness of source metadata is not verification of scientific content.</p>
<p><a href="../evidence/s23_official_source_review.json">Line-item source and claim ledger</a> · <a href="../evidence/s23_shared_template_contract.json">Shared-tool software checks</a> · <a href="../evidence/s23_preflight.json">Current automatic preflight</a> · <a href="../AI_DISCLOSURE.md">AI-use disclosure</a> · <a href="../knowledge/67_s23_result.md">Complete S23 report / next work</a> · <a href="../evidence/s23_verification.json">Three-pass verification</a></p></section>'''
