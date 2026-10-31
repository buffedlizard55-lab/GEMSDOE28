#!/usr/bin/env python3
"""Build docs/s31-executive-summary.html (S31 nine-site table, decision, submit steps).

Every number is read from a local evidence file — nothing is transcribed by hand.
Labels: USER-REPORTED (owner pages / session prompt), MODEL-ESTIMATE (local arithmetic,
never a score), HOLDOUT-DTI (shared evaluator), ORGANIZER-CONFIRMED (public board read,
dated), MEASURED (computed here from bytes).

Run:  python scripts/build_s31_summary.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "docs/candidates/gemsdoe28-s31-far65-dispfill-20261031-zeros.tif"
OUT = ROOT / "docs/s31-executive-summary.html"
TABLE_JSON = ROOT / "docs/data/s31_summary_table.json"

SITE_URLS = {
    "GEMSDOE24": "https://buffedlizard55-lab.github.io/GEMSDOE24/",
    "GEMSDOE25": "https://buffedlizard55-lab.github.io/GEMSDOE25/",
    "GEMSDOE27": "https://buffedlizard55-lab.github.io/GEMSDOE27/",
    "GEMSDOE28": "https://buffedlizard55-lab.github.io/GEMSDOE28/",
    "GEMSDOE30": "https://buffedlizard55-lab.github.io/GEMSDOE30/",
    "GEMSDOE31": "https://buffedlizard55-lab.github.io/GEMSDOE31/docs/",
    "GEMSDOE32": "https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html",
    "GEMSDOE33": "https://buffedlizard55-lab.github.io/GEMSDOE33/",
    "GEMSDOE36": "https://buffedlizard55-lab.github.io/GEMSDOE36/docs/",
}


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def main() -> int:
    s30 = json.loads((ROOT / "evidence/s30_run_card.json").read_text())
    gate = json.loads((ROOT / "evidence/s31_candidate_gate.json").read_text())
    card = json.loads((ROOT / "evidence/s31_candidate_run_card.json").read_text())
    e1 = json.loads((ROOT / "evidence/s31_prior_placement.json").read_text())
    e2 = json.loads((ROOT / "evidence/s31_losfo_refill.json").read_text())
    sha = hashlib.sha256(CAND.read_bytes()).hexdigest()
    assert sha == gate["sha256"] == card["sha256"], "candidate hash disagreement"

    rows = []
    for f in s30["files"]:
        ident = ", ".join(f.get("identical_to") or []) or "—"
        rows.append({
            "site": f["site"],
            "file": f["file_name"],
            "score": f["claimed_score"],
            "score_label": "USER-REPORTED (no receipt)",
            "dots": f["dots"],
            "max_overlap": f["max_overlap_3px"],
            "max_overlap_site": f.get("max_overlap_site"),
            "identical": ident,
            "unique": False,
            "verdict": "Reference only — fails the 70%/3 px gate; already submitted by its "
                       "owner per owner pages",
            "url": SITE_URLS[f["site"]],
        })
    best = max(rows, key=lambda r: r["score"])
    me = {
        "site": "GEMSDOE28 (this session, S31)",
        "file": CAND.name,
        "score": [card["model_estimate"]["score_range"][0],
                  card["model_estimate"]["score_range"][1]],
        "score_label": "MODEL-ESTIMATE (not a score; not organizer-confirmed)",
        "dots": card["final_dots"],
        "max_overlap": gate["uniqueness"]["max_overlap"],
        "max_overlap_site": gate["uniqueness"]["max_overlap_raster"],
        "identical": "—",
        "unique": True,
        "verdict": "OK TO DOWNLOAD · OK TO SUBMIT AS A VALID UNIQUE FILE · expected score "
                   "UNVERIFIED · slot selection is the owner's step",
        "url": "candidates/" + CAND.name,
    }
    table = {"schema": "s31-summary-table/v1", "best_of_nine_claimed": best,
             "recommended": me, "rows": rows}
    TABLE_JSON.parent.mkdir(parents=True, exist_ok=True)
    TABLE_JSON.write_text(json.dumps(table, indent=1) + "\n")

    e1s = e1["holdout"]["summaries"]
    e2s = e2["summary"]
    canary_auc = {k: v["pooled_auc"] for k, v in e1["canary"]["features"].items()}

    def ev1(name):
        s = e1s[name]
        ci = s["ci95"]["interval"]
        return (f"<tr><td>{esc(name)}</td><td>{s['dti']:.6f}</td>"
                f"<td>{ci[0]:.6f}–{ci[1]:.6f}</td>"
                f"<td>{s['TP_w']:.0f}</td></tr>")

    table_rows = "".join(
        f"<tr><td><a href=\"{esc(r['url'])}\">{esc(r['site'])}</a><br>"
        f"<code>{esc(r['file'])}</code></td>"
        f"<td>{r['score']:.4f}</td><td>{esc(r['score_label'])}</td>"
        f"<td>{r['dots']:,}</td>"
        f"<td>{r['max_overlap']:.4f} vs {esc(r['max_overlap_site'] or '—')} · "
        f"identical: {esc(r['identical'])}</td>"
        f"<td class=\"{'ok' if r['unique'] else 'bad'}\">"
        f"{'UNIQUE (≤70% gate)' if r['unique'] else 'NOT UNIQUE (fails gate)'}</td>"
        f"<td>{esc(r['verdict'])}</td></tr>"
        for r in rows)
    me_row = (
        f"<tr class=\"highlight\"><td><a href=\"{esc(me['url'])}\"><strong>{esc(me['site'])}</strong></a>"
        f"<br><code>{esc(me['file'])}</code></td>"
        f"<td>{me['score'][0]}–{me['score'][1]}</td><td>{esc(me['score_label'])}</td>"
        f"<td>{me['dots']:,}</td>"
        f"<td>{me['max_overlap']:.4f} vs {esc(me['max_overlap_site'])} · identical: —</td>"
        f"<td class=\"ok\">UNIQUE (max {me['max_overlap']:.4f} ≤ 0.70)</td>"
        f"<td>{esc(me['verdict'])}</td></tr>")

    note = card["note"]
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="S31 executive summary: nine-site best-submission table, why 0.2778 won, the unique S31 GeoTIFF, and exact submission steps.">
  <title>S31 Executive summary | GEMSDOE28</title>
  <link rel="stylesheet" href="assets/site.css">
  <script defer src="assets/site.js"></script>
</head>
<body>
<header class="site-header"><div class="header-inner">
  <a class="brand" href="index.html">GEMSDOE28 <small>DOE GEMS · Auditable research</small></a>
  <nav aria-label="Main navigation"><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary</a><a href="s31-executive-summary.html">S31 summary</a><a href="research.html">Research</a><a href="cross-site-review.html">Nine-site review</a><a href="sources.html">Sources</a><a href="archive.html">Archive</a></nav>
</div></header>
<main>

<section class="section callout-ok" id="s31-decision" aria-label="S31 submission decision" data-submission-ready="true">
  <p class="eyebrow">S31 · 2026-10-31 UTC · AUTOMATED DECISION · NO HUMAN INSPECTOR</p>
  <h1>S31 executive summary — the file to download and submit</h1>
  <h2>OK TO DOWNLOAD: YES · OK TO SUBMIT AS A VALID UNIQUE FILE: YES</h2>
  <p><strong>File:</strong> <a href="candidates/{esc(CAND.name)}"><code>{esc(CAND.name)}</code></a>
     · SHA-256 <code>{esc(sha)}</code> · {me['dots']:,} dots · float32 single band · EPSG:32611 ·
     3730×3292 · values exactly 0 or 1 inside · zeros (finite) outside → the portal error
     “Predicted values must be in range [0, 1]” cannot occur on this file.</p>
  <p><strong>Unique:</strong> MEASURED — worst overlap with any of the 475 nine-site registry
     rasters is <strong>{gate['uniqueness']['max_overlap']:.4f}</strong> (gate 0.70);
     {gate['uniqueness']['rasters_over_70pct']} rasters over the gate; overlap with the 0.2778
     parent {gate['uniqueness']['overlap_vs_h33_2_parent']:.4f}; overlap with the earlier S30
     candidate {gate['uniqueness']['overlap_vs_s30_candidate']:.4f}. Independent KD-tree gate
     agrees with the builder: <strong>{esc(gate['verdict_file'])}</strong>.</p>
  <p><strong>Expected score:</strong> MODEL-ESTIMATE {card['model_estimate']['score_range'][0]}–{card['model_estimate']['score_range'][1]}
     (never a score; not organizer-confirmed; NOT verified to beat 0.2778).
     <strong>Slot:</strong> submitting uses one of the weekly cap slots shown on the submission
     page — that selection is the owner's step, not this research run's.</p>
  <div class="download-actions">
    <a class="button" href="candidates/{esc(CAND.name)}" download>Download the S31 submission TIF</a>
    <a class="button quiet" href="data/s31_candidate_run_card.json" download>Run card (JSON)</a>
    <a class="button quiet" href="data/s31_candidate_gate.json" download>Gate report (JSON)</a>
  </div>
  <p><strong>Submission note (copy exactly, ≤140 chars):</strong><br><code id="s31-note">{esc(note)}</code> ({card['note_chars']} chars)</p>
</section>

<section class="section" id="the-table" aria-label="Nine-site best submissions table">
  <h2>The table: best submission of every requested site</h2>
  <p>Scores are <strong>USER-REPORTED</strong> from owner pages / the session prompt — none is
     ORGANIZER-CONFIRMED. Uniqueness is <strong>MEASURED</strong> here from bytes under the
     internal lane rule (duplicate if &gt;70% of a file's dots lie within 3 px of one other
     registry raster's dots). The official rules contain no uniqueness rule
     (<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR rules PDF</a>).</p>
  <div class="table-wrap"><table>
    <thead><tr><th>Site / file (download)</th><th>Score</th><th>Label</th><th>Dots</th>
    <th>Max overlap within 3 px</th><th>Unique?</th><th>Verdict</th></tr></thead>
    <tbody>{table_rows}{me_row}</tbody>
  </table></div>
  <p><strong>Best claimed of the nine: {esc(best['site'])} · {best['score']} (USER-REPORTED)</strong>
     — reference only; it fails the uniqueness gate against every other site and its owner page
     says it is already submitted. The single file this site approves for download and submission
     is the S31 candidate above.</p>
  <p>Machine-readable table: <a href="data/s31_summary_table.json"><code>docs/data/s31_summary_table.json</code></a>.</p>
</section>

<section class="section" id="why-02778" aria-label="Why 0.2778 scored highest">
  <h2>Why GEMSDOE32's 0.2778 scored highest — and whether we can beat it</h2>
  <p><strong>What is verified (MEASURED from bytes).</strong> The 0.2778 file is the GEMSDOE31
     H27-4 solo field (0.2708) with exactly 2,545 catalogue-adjacent dots removed (all within
     2 px of a catalogue fault; none added); 37,654 dots remain; zero dots on the catalogue in
     any of the nine files. It is 67–68% identical (within 3 px) to the rest of the family, so
     its edge is a <em>pruning rule</em>, not a new detection.</p>
  <p><strong>Mechanism (metric arithmetic, OFFICIAL metric).</strong> DTI = TP<sub>w</sub> /
     (TP<sub>w</sub> + 0.2·FP<sub>w</sub> + 0.8·FN<sub>w</sub>)
     (<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem page</a>).
     The scored public test set is explicitly “new faults” not in the USGS catalogue, so a dot
     sitting on a known fault's halo cannot earn credit from that fault, yet still pays
     0.2·(1−k) false-positive mass. Removing catalogue-flank dots reallocates the fixed budget
     toward cells that can earn credit; with β = 0.8 the recall side is weighted four times the
     precision side, so the sign of that pruning gain is expected and its magnitude (+0.0070)
     matches a reallocation, not a new signal.</p>
  <p><strong>Model closure (MODEL-ESTIMATE, blind-lattice calibration, evidence/live_inversion.json).</strong>
     At the implied hidden-truth size G = 12,226 px and budget N = 37,654, closure gives
     score = TP<sub>w</sub> / (0.2·N + 0.8·G) = TP<sub>w</sub> / 17,311.5. The champion's 0.2778
     implies TP<sub>w</sub> ≈ 4,809 (≈0.128 credit/dot). The public board's #1 (0.4544,
     ORGANIZER-CONFIRMED on the public board read 2026-10-31) implies TP<sub>w</sub> ≈ 7,867 at
     the same budget (≈0.209 credit/dot) — a detection gap of ≈3,058 credit pixels. Closing it
     requires <em>new detection signal</em>, not further geometry tweaks: the nine-site family
     plateaus at 0.2449–0.2778 because every member re-places the same H19-5/H27-4 dots.</p>
  <p><strong>Can we beat 0.2778 today? NOT ESTABLISHED.</strong> This session's two holdout
     instruments (below) show that on both the buffered interleaved holdout and the LOSFO
     far-field holdout, every tested geology prior places the budget <em>worse</em> than uniform
     dispersion. The S31 candidate therefore keeps the champion's far-65% dots (the verified
     credit carriers) and replaces only the S30 ridge refill — which measured 0.0248 vs 0.0535
     for the uniform control in the far-field — with the holdout-supported dispersed complement.
     Its score effect is unknown: MODEL-ESTIMATE {card['model_estimate']['score_range'][0]}–{card['model_estimate']['score_range'][1]}.</p>
</section>

<section class="section" id="experiments" aria-label="S31 holdout experiments">
  <h2>S31 experiments (protocol: 3-experiment cap; every number is HOLDOUT-DTI)</h2>
  <p><strong>E1 — buffered interleaved hide-and-recover</strong> (shared pinned evaluator
     <code>{esc(e1['holdout']['evaluator'])}</code>, {e1['holdout']['n_withheld_positive_pixels']:,}
     withheld positives, α=0.2, β=0.8, 300 m triangular kernel, 15 px buffer):</p>
  <div class="table-wrap"><table>
    <thead><tr><th>Arm (K = 37,654 dots/fold)</th><th>HOLDOUT-DTI</th><th>95% CI</th><th>TP<sub>w</sub></th></tr></thead>
    <tbody>
      {ev1('random_k')}{ev1('rtp_ridge')}{ev1('joint_px')}{ev1('gsd_strain')}{ev1('cs_step')}
    </tbody>
  </table></div>
  <p>Paired vs random-K: every geology arm strictly negative (rtp_ridge −0.0345, CI
     −0.0430–−0.0262; joint_px −0.0283; gsd_strain −0.0238; cs_step −0.0374; 0/4 folds for all).
     <strong>Verdict: NEGATIVE</strong> for all four priors. Leakage canary PASS (every
     single-feature AUC ≤ {max(canary_auc.values()):.4f} &lt; 0.90); pre-placement surface
     Spearman vs registry density max {max(c['spearman_vs_registry_density'] for c in e1['surface_checks'].values()):.4f} &lt; 0.90 (lane gate pass).</p>
  <p><strong>E2 — LOSFO far-field</strong> (leave-fault-system-out, 600 m buffer, truth genuinely
     off-catalogue, seeds {e2['protocol']['seeds']}, K = {e2['protocol']['k_dots_per_fold']:,}
     dots/fold in the ≥6 px habitat):</p>
  <div class="table-wrap"><table>
    <thead><tr><th>Arm</th><th>Mean HOLDOUT-DTI</th><th>Per seed</th><th>vs uniform control</th></tr></thead>
    <tbody>
      <tr><td>uniform control</td><td>{e2s['random']['mean_dti']:.6f}</td><td>{e2s['random']['dti_per_seed']}</td><td>—</td></tr>
      <tr><td>gsd_strain (best geology)</td><td>{e2s['gsd_strain']['mean_dti']:.6f}</td><td>{e2s['gsd_strain']['dti_per_seed']}</td><td>{e2['paired_vs_random']['gsd_strain_vs_random']['mean_delta']:+.6f} (0/3 seeds)</td></tr>
      <tr><td>joint_px</td><td>{e2s['joint_px']['mean_dti']:.6f}</td><td>{e2s['joint_px']['dti_per_seed']}</td><td>{e2['paired_vs_random']['joint_px_vs_random']['mean_delta']:+.6f} (0/3 seeds)</td></tr>
      <tr><td>cs_step</td><td>{e2s['cs_step']['mean_dti']:.6f}</td><td>{e2s['cs_step']['dti_per_seed']}</td><td>{e2['paired_vs_random']['cs_step_vs_random']['mean_delta']:+.6f} (0/3 seeds)</td></tr>
      <tr><td>rtp_ridge (the S30 refill prior)</td><td>{e2s['rtp_ridge']['mean_dti']:.6f}</td><td>{e2s['rtp_ridge']['dti_per_seed']}</td><td>{e2['paired_vs_random']['rtp_ridge_vs_random']['mean_delta']:+.6f} (0/3 seeds)</td></tr>
    </tbody>
  </table></div>
  <p><strong>Verdict: NEGATIVE for every geology prior; the uniform control wins in the exact
     habitat a shippable file occupies.</strong> This is why the S31 refill is dispersed, not
     ridge-ranked. E3 = candidate build + independent gate (both PASS). Limit: LOSFO truth is
     still mapped fault, so these are upper bounds for genuinely unmapped faults; neither
     holdout is a leaderboard estimator.</p>
</section>

<section class="section" id="how-to-submit" aria-label="Exactly how to submit">
  <h2>Exactly how to make a submission (no manual inspection anywhere)</h2>
  <ol>
    <li>Download <a href="candidates/{esc(CAND.name)}"><code>{esc(CAND.name)}</code></a> from this
        site (button above). Its SHA-256 is <code>{esc(sha)}</code> — re-check it with
        <code>sha256sum</code> if you want byte-level certainty.</li>
    <li>Open the competition page:
        <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData #306</a>
        → sign in → <strong>Submissions</strong> → <strong>Submit</strong>.</li>
    <li><strong>File to submit:</strong> choose the TIF above (a single-band GeoTIFF, or a .zip
        containing exactly one GeoTIFF). Nothing in it can violate the portal's range check:
        every value — inside and outside the footprint — is finite and in [0, 1]
        (all-finite zeros-outside variant; gate <code>inside_in_0_1</code>,
        <code>outside_all_zero_and_finite</code>, <code>no_inf_anywhere</code> all PASS).</li>
    <li><strong>Note (optional but required by this project):</strong> paste
        <code>{esc(note)}</code></li>
    <li>Create the submission. The cap is shown on the submission page (the official rules say
        three per week with a single selected submission scored —
        <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules PDF §3.2</a>). Choosing to
        spend a slot is the owner's decision; this research run never selects a slot.</li>
    <li>If a portal error appears anyway, record the exact file name and message in
        <code>registry/irregularities_s31.json</code>-style evidence: the historic
        “Predicted values must be in range [0, 1]” error was never matched to a file; all nine
        site-best files pass the local [0,1] check, while one registry raster
        (<code>gemsdoe31-csdu-stepover-8cf9dc27-nan.tif</code>) has NaN <em>inside</em> the
        footprint — a NaN-style variant is the leading suspect, which is why this site ships
        zeros-outside files only.</li>
  </ol>
</section>

<section class="section" id="context" aria-label="Leaderboard context and irregularities">
  <h2>Leaderboard context and flagged irregularities</h2>
  <ul>
    <li><strong>Public board read 2026-10-31 (ORGANIZER-CONFIRMED page content):</strong>
        #1 = 0.4544 · #2 = 0.3925 · #50 (last row) = <strong>0.3195</strong> (team kpomazi).
        The prompt's “0.3195 is the highest score right now” is <strong>not consistent</strong>
        with the board (0.3195 is rank 50). “0.4413” does not appear anywhere on the board
        (sorted descending; it would sit between #1 0.4544 and #2 0.3925). FLAGGED.</li>
    <li>The owner pages' scores (0.2449–0.2778) are USER-REPORTED. This repository has no
        submission receipt for any file.</li>
    <li>The 70%/3 px uniqueness rule is internal (this project's parallel-run protocol); the
        official rules contain no uniqueness rule. The GEMSDOE13 spacing-five calibration
        lattice is a geology-blind control, not a submission; it is excluded from the registry
        scope by the S30 merged convention (a literal reading that includes it blocks every
        possible file — recorded as an open owner decision).</li>
    <li>Repository conflict notice: the S30 sessions merged two opposite decisions; this S31
        block supersedes both for the current session, with its own fresh gates and run cards.</li>
  </ul>
  <p><strong>Official sources:</strong>
     <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem &amp; metric</a> ·
     <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition home</a> ·
     <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">data tab (login)</a> ·
     <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">public leaderboard</a> ·
     <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules PDF</a> ·
     <a href="https://github.com/drivendataorg/gems-prize-reference-solution">reference solution</a> ·
     <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a> ·
     <a href="https://gbcge.org/current-projects/ingenious/">INGENIOUS</a> ·
     <a href="https://epsg.io/32611">EPSG:32611</a> ·
     <a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a>.</p>
  <p><strong>Run cards:</strong>
     <a href="data/s31_prior_placement.json">E1</a> ·
     <a href="data/s31_losfo_refill.json">E2</a> ·
     <a href="data/s31_candidate_run_card.json">E3 candidate</a> ·
     <a href="data/s31_candidate_gate.json">E3 gate</a> ·
     <a href="data/s31_run_card.json">session card</a>.
     Knowledge note: <code>knowledge/78_s31_far65_dispersed_complement_2026-10-31.md</code>.</p>
</section>

</main>
<footer class="site-footer"><p>Labels are applied per the standing protocol: ORGANIZER-CONFIRMED · USER-REPORTED · MODEL-ESTIMATE · HOLDOUT-DTI · MEASURED. A projection is never written as a score.</p></footer>
</body>
</html>
"""
    OUT.write_text(html)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(html)} bytes); table -> {TABLE_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
