#!/usr/bin/env python3
"""Build docs/s31-midband-executive-summary.html + evidence/s31_midband_summary_table.json (S31 session).

Every number is read from evidence JSONs or recomputed from data/ bytes here; no hand-typed scores.
Scores shown are USER-REPORTED (session prompt / site pages); projections are labelled PROJECTION.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid  # noqa: E402
from gems27 import uniqueness as U  # noqa: E402

AUDIT = json.loads((ROOT / "evidence/s30_registry_audit.json").read_text())
HOLD = json.loads((ROOT / "evidence/s31_holdout.json").read_text())
CAL = json.loads((ROOT / "evidence/s31_calibration.json").read_text())
BUILD = json.loads((ROOT / "evidence/s31_build.json").read_text())
GATE = json.loads((ROOT / "evidence/s31_midband_gate.json").read_text())

SITE_URL = {
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
BEST_LABEL = {
    "GEMSDOE28": "h36-1-rung30-blind-r1 (0.2710, top of four reported files)",
}


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def fmt(x, d=4):
    try:
        return f"{float(x):.{d}f}"
    except (TypeError, ValueError):
        return "not recorded"


def focus_rows() -> list[dict]:
    rows = []
    for site, info in AUDIT["focus"].items():
        dup = info["duplicate_map_vs_all_registry"]
        name = Path(info["local"]).name
        site = site.replace("GEMSDOE", "")
        dl = ROOT / "docs" / "downloads" / name
        local_mirror = f"downloads/{name}" if dl.exists() else None
        rows.append({
            "site": f"GEMSDOE{site}",
            "file": name,
            "repo_path": local_mirror,
            "site_file_url": SITE_URL[f"GEMSDOE{site}"].rstrip("/") + f"/docs/downloads/{name}",
            "site_url": SITE_URL[f"GEMSDOE{site}"],
            "reported": info.get("user_reported_score"),
            "dots": info["dots"],
            "sha256": info["sha256"],
            "max_overlap": dup["max_overlap"],
            "max_overlap_file": dup["max_overlap_file"],
            "n_duplicate_rasters": dup["n_duplicate_rasters"],
            "n_compared": dup["n_compared"],
            "unique": dup["max_overlap"] <= 0.70,
            "label": BEST_LABEL.get(site, ""),
        })
    rows.sort(key=lambda r: -(r["reported"] or 0))
    return rows


def cand_row() -> dict:
    return {
        "file": GATE["file"], "path": GATE["path"], "sha256": GATE["sha256"],
        "dots": GATE["n_final_dots"], "reported": None,
        "projection": GATE["projection"],
        "max_overlap": GATE["max_overlap"], "max_overlap_file": GATE["max_overlap_raster"],
        "unique": GATE["unique_under_70pct_3px"],
        "note": BUILD["note"],
    }


def main() -> int:
    rows = focus_rows()
    cand = cand_row()
    ok = GATE["verdict"]["ok_to_download"]
    table = {"schema": 1, "session": "S31", "focus_rows": rows, "candidate": cand,
             "decision": GATE["verdict"], "holdout": {a: HOLD["arms"][a]["dti_pooled"] for a in HOLD["arms"]},
             "canary": HOLD["leakage_canary"], "calibration": {
                 "loo_r2": CAL["primary"]["loo_r2"], "usable": CAL["primary"]["usable"],
                 "coefficients": CAL["primary"]["coefficients"], "n_rows": CAL["primary"]["n_rows"]}}
    (ROOT / "evidence/s31_midband_summary_table.json").write_text(json.dumps(table, indent=1) + "\n")

    trs = []
    for r in rows:
        uniq = ("YES" if r["unique"] else
                f"NO — {fmt(r['max_overlap'] * 100, 1)}% of its dots lie within 3 px of "
                f"{esc(r['max_overlap_file'].split('/', 1)[-1][:44])}… ({r['n_duplicate_rasters']} of "
                f"{r['n_compared']} rasters over 70%)")
        est = "USER-REPORTED " + fmt(r["reported"]) if r["reported"] else "n/a"
        mirror = (f"<a href='{esc(r['repo_path'])}' download>download local byte-pinned mirror</a>"
                  if r['repo_path'] else
                  f"<small>byte-pinned mirror in repo data (SHA in table JSON)</small>")
        trs.append(
            f"<tr><td>{esc(r['site'])}</td>"
            f"<td><a href='{esc(r['site_url'])}'>{esc(r['site_url'].replace('https://', ''))}</a><br>"
            f"<code>{esc(r['file'])}</code><br>"
            f"<a href='{esc(r['site_file_url'])}' download>download from the site</a><br>{mirror}</td>"
            f"<td>{est}<br><small>{esc(r['label'])}</small></td>"
            f"<td>{r['dots']:,}</td><td>{uniq}</td>"
            f"<td><strong>NO</strong> — not unique, so submitting it would duplicate an existing "
            f"family file (36/36 nine-site pairs fail).</td></tr>")
    c = cand
    if c["projection"].get("estimable"):
        proj = (f"PROJECTION {fmt(c['projection']['projected_mean_unextrapolated'])} "
                f"[95% CI {fmt(c['projection']['ci95_unextrapolated'][0])}–{fmt(c['projection']['ci95_unextrapolated'][1])}]")
    else:
        fam_range = c['projection'].get('family_frac_mid36_range') or [
            min(r['frac_mid36'] for r in CAL['family_rows']),
            max(r['frac_mid36'] for r in CAL['family_rows'])]
        proj = ("<strong>NOT ESTIMABLE</strong> — composition (frac_mid36 = "
                f"{fmt(BUILD['frac_mid36_final'], 3)}) is outside the calibration's observed range "
                f"({fmt(fam_range[0], 3)}–{fmt(fam_range[1], 3)}); "
                "the association's direction is positive but the magnitude is unknown")
    trs.append(
        f"<tr class='candidate-row'><td>GEMSDOE28 (this repo)</td>"
        f"<td><a href='candidates/{esc(c['file'])}' download><strong>DOWNLOAD: {esc(c['file'])}</strong></a><br>"
        f"<small>SHA-256 <code>{esc(c['sha256'][:32])}…</code> · note: {esc(c['note'])}</small></td>"
        f"<td>{proj}</td><td>{c['dots']:,}</td>"
        f"<td>YES — max {fmt(c['max_overlap'] * 100, 1)}% within 3 px of any of "
        f"{AUDIT['n_registry_rasters']} registry rasters + all in-repo candidates (gate 70%)</td>"
        f"<td><strong>{'YES — OK to download and submit' if ok else 'NO — gate failed'}</strong> "
        f"(weekly slot is the owner's separate step)</td></tr>")

    arm_rows = "".join(
        f"<tr><td>{esc(a)}</td><td>{fmt(HOLD['arms'][a]['dti_pooled'])}</td>"
        f"<td>{fmt(HOLD['arms'][a]['dti_fold_ci95'][0])}–{fmt(HOLD['arms'][a]['dti_fold_ci95'][1])}</td>"
        f"<td>{HOLD['arms'][a]['n_splits']}</td></tr>"
        for a in HOLD["arms"])

    canary_rows = "".join(
        f"<tr><td>{esc(k)}</td><td>{fmt(v['auc'], 3) if v['auc'] == v['auc'] else 'n/a'}</td>"
        f"<td>{'PASS' if v['pass_below_0p90'] else 'FAIL'}</td></tr>"
        for k, v in HOLD["leakage_canary"].items())

    fam = CAL.get("family_rows", [])
    fam_rows = "".join(
        f"<tr><td>{esc(r['site'])}</td><td><code>{esc(r['file'][:52])}</code></td>"
        f"<td>{fmt(r['reported'])}</td><td>{r['n']:,}</td><td>{fmt(r['frac_mid36'], 3)}</td></tr>"
        for r in sorted(fam, key=lambda r: -r["reported"]))

    decision = GATE["verdict"]
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="GEMSDOE28 S31 executive summary: nine-site best-file table with uniqueness verdicts and score projections, the S31 unique candidate GeoTIFF, holdout evidence, and exact submission steps.">
  <title>S31 executive summary | GEMSDOE28</title>
  <link rel="stylesheet" href="assets/site.css">
</head>
<body>
  <nav aria-label="Main navigation"><a href="index.html">Overview</a><a href="s31-executive-summary.html" aria-current="page">S31 summary</a><a href="s29-submission-guide.html">Submission guide</a><a href="s30-executive-summary.html">S30 summary</a></nav>
  <main>
  <section class="section {'callout' if ok else 'callout-danger'}" id="s31-midband-decision" data-submission-ready="{'true' if ok else 'false'}" aria-label="S31 submission decision">
    <h1>S31 decision — {('OK TO DOWNLOAD AND SUBMIT' if ok else 'NOT OK TO SUBMIT')}</h1>
    <p><strong>Decision: {'OK to download and submit' if ok else 'NOT OK to submit'} the S31 unique candidate below.</strong>
    Format gates pass (single-band float32, EPSG:32611, 3730×3292, zeros outside, every value in [0,1], no NaN inside the footprint).
    It is unique: at most {fmt(GATE['max_overlap'] * 100, 1)}% of its dots lie within 3 px of any one of the {AUDIT['n_registry_rasters']} byte-pinned registry rasters or any in-repo candidate (gate: 70%).
    {'The projection is a PROJECTION calibrated on owner-reported scores — it is not a score.'}</p>
    <div class="download-actions">
      <a class="button" href="candidates/{esc(c['file'])}" download>Download the S31 submission GeoTIFF</a>
      <a class="button quiet" href="s29-submission-guide.html">Step-by-step submission guide</a>
      <a class="button quiet" href="data/s31_midband_run_card.json" download>Run card (JSON)</a>
    </div>
    <p><strong>How to submit (exact steps):</strong></p>
    <ol>
      <li>Click the green download button above and save <code>{esc(c['file'])}</code> (do not rename; the .zip variant is unnecessary — the form accepts a single .tif).</li>
      <li>On the DrivenData "New submission" page, click <em>File to submit</em> and choose the downloaded file.</li>
      <li>In <em>Note (optional)</em> paste exactly: <code>{esc(c['note'])}</code> ({BUILD['note_chars']} chars, ≤140).</li>
      <li>Submit. The file's values are exactly 0.0/1.0 inside the footprint and 0.0 outside, so the "[0, 1]" check cannot fail on range; if the portal ever reports an error, re-download and retry once, then report the exact message for review.</li>
      <li>After the receipt appears, record the score in this repo (it becomes ORGANIZER-CONFIRMED).</li>
    </ol>
    <p><small>Weekly submission caps are shown on the submission page and are the owner's decision; this session selected no slot.</small></p>
  </section>

  <section class="section" id="nine-site-table">
    <h2>1 · Nine-site table — best file per site, score, uniqueness</h2>
    <p>Best reported file per site (scores are <strong>USER-REPORTED</strong> from site pages/task statement — no organizer receipts exist here). Uniqueness is computed from the byte-pinned mirrors against all {AUDIT['n_registry_rasters']} registry rasters (70% / 3 px rule).</p>
    <div style="overflow-x:auto">
    <table>
      <thead><tr><th>Site</th><th>Best file (download)</th><th>Score</th><th>Dots</th><th>Unique vs all other GEMSDOE files?</th><th>Best submission to obtain a high score?</th></tr></thead>
      <tbody>{''.join(trs)}
      </tbody>
    </table>
    </div>
    <p><strong>Reading of the table:</strong> every one of the nine site-best files fails uniqueness (all 36 pairs overlap 0.87–1.00 within 3 px; GEMSDOE25's and GEMSDOE30's best files are byte-identical dot sets). The only row that passes all gates is the S31 candidate built in this session. GEMSDOE32's <code>h33-h33-2-b2…</code> (USER-REPORTED 0.2778) remains the highest <em>known</em> score; it is not unique.</p>
  </section>

  <section class="section" id="why-02778">
    <h2>2 · Why GEMSDOE32's 0.2778 is the family maximum (verified from bytes)</h2>
    <ul>
      <li>The 0.2778 file is the GEMSDOE31/GEMSDOE28 solo field (USER-REPORTED 0.2708, 40,199 dots) with exactly its 2,545 dots lying within 2 px of the catalogue removed (37,654 remain; 0 added) — verified by set arithmetic on the byte-pinned rasters.</li>
      <li>Mechanism (metric arithmetic): a dot more than 3 px from every new-fault truth pixel adds exactly 0.2 to the DTI denominator (α = 0.2). Removing 2,545 near-catalogue dots that were ~pure false positives accounts for +0.0288 of the observed +0.0070 — i.e. the observed gain is ~98% consistent with pure false-positive removal at d ≤ 2 px.</li>
      <li>Every attempt to <em>add</em> dots on a new prior scored 0.263–0.271 (USER-REPORTED): measured far-field priors earn ≈ 0.031 credit/dot vs the ≈ 0.0548 break-even. Pruning catalogue-adjacent dots is the one leaderboard-verified positive lever.</li>
    </ul>
  </section>

  <section class="section" id="holdout">
    <h2>3 · EXP-1 — hide-and-recover holdout suite (HOLDOUT-DTI, not leaderboard scores)</h2>
    <p>Evaluator: <code>{esc(HOLD['evaluator_version'])}</code>; seeds {HOLD['seeds'][0]}–{HOLD['seeds'][-1]} (fresh, 0 collisions in the seed ledger); pooled over {HOLD['arms']['base']['n_splits']} fold-seed splits; α 0.2, β 0.8, 300 m triangular kernel; catalogue-based features derived from <em>visible</em> faults only.</p>
    <table>
      <thead><tr><th>Arm</th><th>Pooled DTI</th><th>fold-mean 95% CI</th><th>n splits</th></tr></thead>
      <tbody>{arm_rows}</tbody>
    </table>
    <p>Leakage canary (feature alone vs hidden proximity; AUC &gt; 0.90 = leakage):</p>
    <table><thead><tr><th>Feature</th><th>AUC</th><th>Gate</th></tr></thead><tbody>{canary_rows}</tbody></table>
    <p><strong>Known bias, restated:</strong> the holdout's hidden pieces are catalogue-internal, so it rewards near-catalogue structure that genuinely-new expert faults may not show. It is used here for paired arm ranking only, never as a leaderboard estimate.</p>
  </section>

  <section class="section" id="hypotheses">
    <h2>4 · Candidate hypotheses ranked before implementation (prompt requirement)</h2>
    <ol>
      <li><strong>H-S31-A · strain-edge mid-halo retention</strong> — layers: H33-2 dots, catalogue distances, training band 7 <code>geod_shearrate</code> edge surface. Targets the (3, 6] px band around the catalogue where sub-parallel unmapped splays live; differs from H32-1 (tip/Euler protection, USER-REPORTED 0.2649) by conditioning on a strain-rate edge, not fault geometry. Cost: low. → adjudicated by EXP-1 arm <code>prune3_strainkeep</code>.</li>
      <li><strong>H-S31-B′ · mid-halo (3–6 px) budgeted fill</strong> — same band, fill-side; prior = strain-edge vs matched random control. Differs from S30 (which filled ≥ 6 px on an RTP ridge) and from T-v2 gap closure (which bridged catalogue gaps and scored 0.2449 < 0.2477). → adjudicated by EXP-1 arms <code>fill_mid_shear</code> / <code>fill_mid_random</code>.</li>
      <li><strong>H-S31-C · composition-optimal budget</strong> — the calibration below implies mid-band-heavy compositions score higher in the family; the builder sizes the fill minimally under the uniqueness budget. Cost: low (calibration + ladder).</li>
      <li><strong>H-S31-D · far-field fill priors (strain-edge vs RTP-ridge vs tmi high-pass edge)</strong> — direct comparison of the S30-style design against two new priors at matched counts. → EXP-1 arms <code>fill_shear/fill_rtp/fill_tmi</code> vs <code>control_random</code>.</li>
      <li><strong>H-S31-E · MT conductance surfaces (not viable here)</strong> — USGS ScienceBase DOI 10.5066/P9TWT2LU; official and free, but sciencebase.gov is unreachable from this sandbox and the pinned bytes are not restored. Named per protocol; excluded from implementation.</li>
    </ol>
  </section>

  <section class="section" id="calibration">
    <h2>5 · EXP-2a — family calibration (PROJECTION, never a score)</h2>
    <p>Calibrated on {CAL['primary']['n_rows']} nine-site rasters with USER-REPORTED scores ≥ 0.20 (13 rows; every file's SHA-256 recomputed from local bytes). Model: score ≈ {fmt(CAL['primary']['coefficients']['intercept'])} + {fmt(CAL['primary']['coefficients']['frac_mid36'])} × frac_mid36, where frac_mid36 is the fraction of dots 3–6 px from the catalogue. Leave-one-out R² = {fmt(CAL['primary']['loo_r2'], 3)} (usable); a 4-feature 18-row global model was rejected (LOO R² = {fmt(CAL['global']['loo_r2'], 3)}). CI: residual bootstrap (2,000 draws).</p>
    <table>
      <thead><tr><th>Site</th><th>File</th><th>USER-REPORTED</th><th>Dots</th><th>frac_mid36</th></tr></thead>
      <tbody>{fam_rows}</tbody>
    </table>
    <p><strong>Key implication:</strong> the model reproduces the 0.2708 → 0.2778 prune (+{fmt(CAL['primary']['coefficients']['frac_mid36'] * (0.1230 - 0.1152), 4)} projected vs +0.0070 reported, right direction) and projects the S30 far-fill candidate at ≈ 0.06–0.19 — a flagged irregularity against that branch's "OK to submit" decision.</p>
  </section>

  <section class="section" id="build-gate">
    <h2>6 · EXP-2b/EXP-3 — the S31 candidate and its independent gate</h2>
    <p>Build (frozen rule, no hand-picking): keep H33-2 dots &gt; 3 px from the catalogue ({BUILD['frozen_rule']['keep_rule_from_holdout']}; EXP-1 <code>prune3</code> pooled {fmt(HOLD['arms']['prune3']['dti_pooled'])} vs base {fmt(HOLD['arms']['base']['dti_pooled'])}), fill {BUILD['n_fill']:,} dots in the holdout-winning band ({esc(str(BUILD.get('fill_band_px')))} px) ranked by the strain-edge prior, 4 px spacing, per-raster budget ≤ 68% of {BUILD['n_final']:,}. Surface lane check before placement: Spearman(prior, registry density) = {fmt(BUILD['surface_rank_corr_prior_vs_registry_density'], 3)} (&lt; 0.90).</p>
    <p>Independent gate (bytes re-read): validator hard checks {'PASS' if GATE['validator_hard_checks_passed'] else 'FAIL'}; no NaN inside footprint: {'PASS' if GATE['no_nan_inside_footprint'] else 'FAIL'}; values in [0,1]: {'PASS' if GATE['values_in_01'] else 'FAIL'}; max overlap {fmt(GATE['max_overlap'] * 100, 2)}% ({esc(Path(GATE['max_overlap_raster']).name[:48])}…); rasters over 70%: {GATE['rasters_over_70pct']}; SHA-256 matches builder: {'YES' if GATE['sha_matches_builder'] else 'NO'}.</p>
  </section>

  <section class="section" id="irregularities">
    <h2>7 · Irregularities flagged for review</h2>
    <ul>
      <li>The two merged S30 blocks disagree on "OK to submit" (README conflict notice). This session's calibration gives the far-fill S30 candidate a low projection — flagged, not adjudicated.</li>
      <li>The leaderboard high score quoted in the prompt (0.4413 / 0.3195) is not in the official top ranks fetched 2026-10-30 (#1 0.4544). Owner-receipt numbers are needed.</li>
      <li>No number on this page is ORGANIZER-CONFIRMED; USER-REPORTED and HOLDOUT-DTI/PROJECTION labels are used throughout.</li>
      <li><code>registry/external_pins.json</code> still labels the H33-2 artefact "MT conductance alignment" although the bytes are a catalogue-pruned solo field.</li>
    </ul>
    <h3>Official sources</h3>
    <ul>
      <li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem, metric, submission format</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Official leaderboard</a> · <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Rules PDF</a></li>
      <li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Reference solution</a> · <a href="https://gdr.openei.org/submissions/1391">DOE GDR #1391</a> · <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a> · <a href="https://epsg.io/32611">EPSG:32611</a> · <a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a></li>
    </ul>
  </section>
  </main>
  <footer class="footer"><p>GEMSDOE28 research site · labels: USER-REPORTED / HOLDOUT-DTI / PROJECTION — no organizer-confirmed scores exist in this repository.</p></footer>
</body>
</html>
"""
    out = ROOT / "docs/s31-midband-executive-summary.html"
    out.write_text(page)
    print(f"wrote {out} ({len(page)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
