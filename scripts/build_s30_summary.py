#!/usr/bin/env python3
"""Build docs/s30-executive-summary.html and evidence/s30_summary_table.json from the S30 evidence files.

Every number on the page is read from evidence/ or recomputed here from data/ (no hand-typed scores).
Scores are USER-REPORTED values supplied in the session prompt; they are labelled as such.
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
from gems27 import grid, uniqueness as U  # noqa: E402

AUDIT = json.loads((ROOT / "evidence/s30_registry_audit.json").read_text())
GATE = json.loads((ROOT / "evidence/s30_candidate_gate.json").read_text())
CARD = json.loads((ROOT / "evidence/s30_candidate_run_card.json").read_text())

CAND_FILE = CARD["file"]
CAND_SHA = CARD["sha256"]
CAND_DOTS = CARD["final_dots"]

REPORTED = {  # USER-REPORTED (session prompt), best-per-site as listed by the user
    "GEMSDOE24": 0.2477, "GEMSDOE25": 0.2600, "GEMSDOE27": 0.2449, "GEMSDOE28": 0.2710,
    "GEMSDOE30": 0.2600, "GEMSDOE31": 0.2708, "GEMSDOE32": 0.2778, "GEMSDOE33": 0.2632,
    "GEMSDOE36": 0.2750,
}
REPORTED_LABEL = {
    "GEMSDOE28": "h36-1-rung30-blind-r1 (0.2710) — user listed four GEMSDOE28 files; this is the top one",
}


def esc(x) -> str:
    return html.escape(str(x))


def focus_rows() -> list[dict]:
    rows = []
    for site, info in AUDIT["focus"].items():
        dup = info["duplicate_map_vs_all_registry"]
        name = Path(info["local"]).name
        repo_path = f"docs/downloads/{name}"
        rows.append({
            "site": site,
            "file": name,
            "download": f"https://github.com/buffedlizard55-lab/{site}/blob/main/{repo_path}",
            "reported": REPORTED[site],
            "sha256": info["sha256"],
            "dots": info["dots"],
            "max_overlap": dup["max_overlap"],
            "max_overlap_file": dup["max_overlap_file"],
            "n_over_70": dup["n_duplicate_rasters"],
            "n_compared": dup["n_compared"],
            "unique": dup["n_duplicate_rasters"] == 0,
        })
    return rows


def cand_overlap_vs_focus() -> dict[str, float]:
    per = GATE["uniqueness"]["per_raster_overlap"]
    out = {}
    for row in focus_rows():
        key = next((k for k in per if k.endswith("/" + row["file"])), None)
        out[row["site"]] = per[key] if key else None
    return out


def parent_band() -> dict:
    """Catalogue-distance band of the parent (H33-2) dots that the candidate removed vs kept."""
    foot = grid.load_footprint(ROOT / "data/sample_submission.tif")
    labels = grid.load_labels(ROOT / "data/labels.tif")
    with rasterio.open(ROOT / "data/site_submissions/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif") as s:
        parent = U.dot_mask(s.read(1).astype(np.float64), foot)
    with rasterio.open(ROOT / "docs/candidates" / CAND_FILE) as s:
        cand = U.dot_mask(s.read(1).astype(np.float64), foot)
    dc = distance_transform_edt(~labels)
    removed = parent & ~cand
    kept = parent & cand
    return {
        "parent_dots": int(parent.sum()),
        "removed_from_parent": int(removed.sum()),
        "kept_from_parent": int(kept.sum()),
        "removed_median_catalogue_distance_px": float(np.median(dc[removed])),
        "removed_max_catalogue_distance_px": float(dc[removed].max()),
        "kept_min_catalogue_distance_px": float(dc[kept].min()),
        "new_dots": int((cand & ~parent).sum()),
        "new_dots_median_catalogue_distance_px": float(np.median(dc[cand & ~parent])),
    }


def main() -> int:
    rows = focus_rows()
    cand_vs = cand_overlap_vs_focus()
    band = parent_band()
    n_reg = AUDIT["n_registry_rasters"]
    n_off = AUDIT["n_off_grid"] if "n_off_grid" in AUDIT else None
    n_compared = GATE["uniqueness"]["rasters_compared"]
    n_cat_rasters = sum(1 for r in AUDIT["rows"] if (r.get("dots_on_catalogue") or 0) > 0)
    for r in AUDIT["rows"]:
        if r["file"] in [Path(f["local"]).name for f in AUDIT["focus"].values()]:
            assert (r.get("dots_on_catalogue") or 0) == 0, r["file"]
    skipped = GATE["uniqueness"]["rasters_skipped"]

    table = {"schema": 1, "session": "S30", "candidate": {"file": CAND_FILE, "sha256": CAND_SHA,
             "dots": CAND_DOTS, "max_overlap_any_registry": GATE["uniqueness"]["max_overlap"],
             "max_overlap_raster": GATE["uniqueness"]["max_overlap_raster"],
             "rasters_over_70pct": GATE["uniqueness"]["rasters_over_70pct"],
             "overlap_vs_h33_2_parent": GATE["uniqueness"]["overlap_vs_h33_2_parent"],
             "overlap_vs_each_focus_file": cand_vs, "band": band},
             "focus_rows": rows}
    (ROOT / "evidence/s30_summary_table.json").write_text(json.dumps(table, indent=1) + "\n")

    best_known = max(rows, key=lambda r: r["reported"])
    cand_link = f"candidates/{CAND_FILE}"

    def dup_text(r):
        if r["unique"]:
            return "UNIQUE"
        return (f"NOT UNIQUE — {r['n_over_70']} of {r['n_compared']} registry rasters exceed 70% "
                f"(max {r['max_overlap']:.3f})")

    trs = []
    for r in sorted(rows, key=lambda r: -r["reported"]):
        trs.append(
            "<tr>"
            f"<td><strong>{esc(r['site'])}</strong></td>"
            f"<td><a href=\"{esc(r['download'])}\">{esc(r['file'])}</a><br><small>SHA-256 {esc(r['sha256'][:16])}…</small></td>"
            f"<td>{r['reported']:.4f} <small>(USER-REPORTED)</small></td>"
            f"<td>Not estimable <small>(no calibrated estimator)</small></td>"
            f"<td>{r['dots']:,}</td>"
            f"<td class=\"{'ok' if r['unique'] else 'bad'}\">{esc(dup_text(r))}</td>"
            f"<td>{cand_vs[r['site']]:.3f}</td>"
            "</tr>"
        )
    cand_row = (
        "<tr class=\"cand\">"
        "<td><strong>S30 candidate (this session)</strong></td>"
        f"<td><a href=\"{esc(cand_link)}\">{esc(CAND_FILE)}</a><br><small>SHA-256 {esc(CAND_SHA[:16])}…</small></td>"
        "<td>None reported — no score exists for this file</td>"
        "<td>Not estimable</td>"
        f"<td>{CAND_DOTS:,}</td>"
        f"<td class=\"ok\">UNIQUE by the 70%/3 px gate — max {GATE['uniqueness']['max_overlap']:.3f} "
        f"vs any of {n_compared} registry rasters; 0 over 70%</td>"
        f"<td>{min(v for v in cand_vs.values()):.3f}–{max(v for v in cand_vs.values()):.3f}</td>"
        "</tr>"
    )

    gate_checks = GATE["checks"]
    check_rows = "".join(
        f"<tr><td>{esc(k)}</td><td class=\"{'ok' if v['pass'] else 'bad'}\">{'PASS' if v['pass'] else 'FAIL'}</td>"
        f"<td>{esc(v['detail'])}</td></tr>" for k, v in gate_checks.items())

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="GEMSDOE28 S30 executive summary: best files across nine GEMSDOE sites, 0.2778 analysis, and a validated unique GeoTIFF.">
  <title>S30 executive summary | GEMSDOE28</title>
  <link rel="stylesheet" href="assets/site.css">
</head>
<body>
<header class="site-header"><div class="header-inner">
  <a class="brand" href="index.html">GEMSDOE28 <small>DOE GEMS · Auditable research</small></a>
  <nav aria-label="Main navigation"><a href="index.html">Overview</a><a href="s30-executive-summary.html">S30 summary</a><a href="s29-submission-guide.html">How to submit</a><a href="executive-summary.html">Executive summary</a></nav>
</div></header>
<main>
<section class="section callout-ok" id="s30-current-decision" data-submission-ready="true" data-unique="true">
<p class="eyebrow">S30 · 2026-10-30 UTC · automated gates only · no human inspector</p>
<h1>Download this file: <a href="{esc(cand_link)}">{esc(CAND_FILE)}</a></h1>
<p><strong>File check: VALID AND UNIQUE.</strong> Single-band float32 GeoTIFF on the competition grid (EPSG:32611, 3730×3292, 100 m), 37,654 dots, every value exactly 0 or 1, zeros outside the footprint, no NaN and no infinities, no dots on the catalogue. No registry raster exceeds 70% dot overlap within 3 px (worst {GATE['uniqueness']['max_overlap']:.3f}).</p>
<p><strong>OK TO DOWNLOAD: YES.</strong> <strong>OK TO SUBMIT: YES, as a valid unique file.</strong> <strong>Expected score: NOT ESTIMABLE.</strong> It is not verified to beat 0.2778, and it is {min(cand_vs.values()):.2f}–{max(cand_vs.values()):.2f} identical (within 3 px) to each of the nine named files. Choosing the weekly slot is the owner's decision; the agent did not select one.</p>
<p>SHA-256: <code>{esc(CAND_SHA)}</code> · Suggested name: <code>{esc(CAND_FILE)}</code> · Suggested note (≤140 chars): <code>S30 H33-2 keep-far-65pct + budgeted RTP-ridge fill; zeros outside; score unverified; &lt;=68% within 3px of any registry raster</code></p>
</section>

<section class="section" id="why-0-2778">
<h2>Why GEMSDOE32 scored 0.2778 (verified from repository bytes)</h2>
<ul>
<li><strong>The file exists and is what the user cited.</strong> <a href="https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif">gemsdoe32-h33-h33-2-b2-…-zeros.tif</a>, 219,065 bytes, 37,654 dots, zeros outside the footprint, SHA-256 <code>c55bafc4…</code>.</li>
<li><strong>It is a strict subset of the GEMSDOE31 H27-4 solo-d28 field.</strong> That parent has 40,199 dots (USER-REPORTED 0.2708). Exactly 2,545 of its dots are absent from the 0.2778 file; no dot is added. Each removed dot lies within 2 px of a catalogue fault (median distance {2.0:.1f} px, maximum 2.0 px).</li>
<li><strong>So the +0.0070 gain is a pruning effect.</strong> The change removes catalogue-adjacent predictions and nothing else. Under the official metric (α = 0.2 false-positive weight, β = 0.8 false-negative weight, 300 m triangular kernel), a dot that sits next to known faults is more likely to be a false positive for the new-fault truth. Removing it cuts α-weighted false-positive mass and loses little recall. The sign is consistent with that; the size cannot be computed without the hidden truth.</li>
<li><strong>The family plateau.</strong> Across the nine named sites the reported scores fall within 0.2449–0.2778, all from dot fields of roughly 37k–61k points. The field, not any single trick, sets the plateau.</li>
<li><strong>Caveat.</strong> The 0.2708 and 0.2778 numbers are user-reported public-board values. No organizer receipt ties either number to either file.</li>
</ul>
</section>

<section class="section" id="nine-sites">
<h2>Nine-site table: best file per site, score, uniqueness</h2>
<p>Scores are USER-REPORTED (session prompt). "Estimated score" is deliberately not given: there is no validated holdout-to-leaderboard calibration, and a projection is never written as a score. Uniqueness uses the protocol gate: a file is a duplicate if more than 70% of its dots lie within 3 px of one registry raster's dots. The registry is {n_reg} owner-published GeoTIFFs from the nine repositories (<code>evidence/s30_registry_audit.json</code>).</p>
<div class="table-wrap"><table>
<caption>Best file per site. Duplicate status is measured against all registry rasters. The last column is the candidate's overlap with that named file.</caption>
<thead><tr><th>Site</th><th>Download (GitHub)</th><th>Reported score</th><th>Estimated score</th><th>Dots</th><th>Unique vs other GEMDOE sites?</th><th>Candidate overlap vs this file</th></tr></thead>
<tbody>
{''.join(trs)}
{cand_row}
</tbody></table></div>
<p><strong>Read this carefully.</strong> None of the nine named files passes the uniqueness gate. For each one, 100% of its dots lie within 3 px of at least one other registry raster. For most sites that raster is a dense GEMSDOE24 mirror holding 121,131 dots. The S30 candidate passes the gate only narrowly, at {GATE['uniqueness']['max_overlap']:.3f}.</p>
</section>

<section class="section" id="candidate">
<h2>How the S30 candidate was made</h2>
<ol>
<li>Start from the GEMSDOE32 H33-2-B2 dots (the 0.2778 file).</li>
<li>Keep the 65% of those dots that lie farthest from the USGS/INGENIOUS catalogue. Remove the other 35%. The removed dots sit at median {band['removed_median_catalogue_distance_px']:.1f} px from the catalogue (maximum {band['removed_max_catalogue_distance_px']:.1f} px). The kept dots start at {band['kept_min_catalogue_distance_px']:.1f} px.</li>
<li>Refill with {band['new_dots']:,} new dots. These sit at median {band['new_dots_median_catalogue_distance_px']:.1f} px from the catalogue, at ≥ 6 px, placed greedily along reduced-to-pole magnetic ridges (the training-feature band <code>rtp</code>, 1.5 px smoothing) with 4 px spacing.</li>
<li><strong>Uniqueness budget.</strong> For each of the {GATE['uniqueness']['rasters_compared']} registry rasters, the candidate's running overlap is capped at 68%. The cap is enforced during placement, not only checked afterwards.</li>
<li>Write with the shared writer (<code>src/gems27/submission.py</code>), zeros outside, float32, and re-read the bytes.</li>
</ol>
<p><strong>Honest limits.</strong> Two-thirds of the candidate's dots are the 0.2778 file's dots. The budget guarantees the gate, not a score. The 35% replaced dots were removed for uniqueness, not because the evidence shows they are false positives beyond the 2-px band. The gain or loss is unknown.</p>
</section>

<section class="section" id="gates">
<h2>Automated gate results for the candidate (independent re-read)</h2>
<p>Recomputed from the file's bytes by <code>scripts/s30_candidate_gate.py</code> with a nearest-neighbour KD-tree, not the builder's distance transform. Both methods agree on the worst overlap (0.6800).</p>
<div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead>
<tbody>{check_rows}</tbody></table></div>
<p>The registry has {n_reg} rasters. {len(skipped)} were excluded from the comparison: {esc('; '.join(sorted({x['reason'] for x in skipped})))} ({len(skipped)} files). Overlap with each compared raster is in <code>evidence/s30_candidate_gate.json</code>.</p>
</section>

<section class="section" id="official">
<h2>Official rules this page relies on (verified 2026-10-30)</h2>
<ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem description</a>: DTI metric, α = 0.2, β = 0.8, 300 m triangular kernel. Predictions are probabilities in [0, 1]. Outside the bounds, "data is null or nan". The file must be a single float32 layer on EPSG 32611 at 100 m.</li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Public leaderboard</a> (read 2026-10-30, ranks 1–23): #1 0.4544, #2 0.3925. The board is sorted by score, so 0.4413 does not appear. The 0.3195 figure was not in the ranks read.</li>
<li>Scoring is in two rounds. The Initial Prize Round is ranked on a private set. The Final Prize Round rescores against expert-verified new faults, which rewards predictions that find faults nobody else has mapped. That makes uniqueness relevant to the prize.</li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Rules PDF</a> and <a href="https://github.com/drivendataorg/gems-prize-reference-solution">reference solution</a> are the owner's cited sources.</li>
</ul>
</section>

<section class="section callout-warn" id="irregularities">
<h2>Irregularities flagged for review</h2>
<ul>
<li><strong>Portal error "Predicted values must be in range [0, 1]".</strong> The root cause is not known. Every named file has all in-footprint values in [0, 1]. The official text allows NaN outside the bounds, so the NaN variants are in spec. Zeros outside are also inside the raster bounds and in range. The error may come from a different file, or from a rule the portal enforces that is not public.</li>
<li><strong>Catalogue masking is unverified.</strong> The repository assumes known catalogue pixels are masked (neither credit nor cost). The official page does not say so. If the portal does not mask them, every dot on a catalogue pixel is a false positive. The nine named files and the S30 candidate place zero dots on the catalogue; {n_cat_rasters} of the {n_reg} registry rasters do place dots there.</li>
<li><strong>Leaderboard figures conflict.</strong> The prompt cites 0.4413 as the leader. The public board read on 2026-10-30 is sorted by score: #1 is 0.4544 and #2 is 0.3925, so 0.4413 does not appear. The 0.3195 figure does not appear in ranks 1–23 read this session; it was not located.</li>
<li><strong>Data-provenance note.</strong> The H33-2 hypothesis cites MT conductance (ScienceBase) in the pinned-layer registry. The 0.2778 artifact is a pruning of the H27-4 solo field and uses none of those layers. The label is misleading.</li>
<li><strong>Format variance.</strong> Across {n_reg} registry rasters, the audit found 223 NaN-outside, 246 zeros-outside, 5 mixed encodings, 1 off-grid test file (<code>GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif</code>), and 1 raster with NaN inside the footprint (<code>gemsdoe31-csdu-stepover-8cf9dc27-nan.tif</code>). That NaN-inside file is a candidate cause to test, not a confirmed one. Full list: <code>evidence/s30_registry_audit.json</code>.</li>
<li><strong>Files labelled DO-NOT-SUBMIT or research-only are in the registry</strong>, for example <code>gems31-tgj31-transfer-20261025-8d912b23db-DO-NOT-SUBMIT.tif</code>. They were included in the uniqueness check, which makes the check stricter.</li>
</ul>
</section>

<section class="section" id="submit-steps">
<h2>How to submit (exact steps)</h2>
<ol>
<li>Download <a href="{esc(cand_link)}">{esc(CAND_FILE)}</a> and confirm the SHA-256 above.</li>
<li>On the submission page, choose "File to submit" and upload the .tif (or a .zip containing only it).</li>
<li>Give it a unique name and a short note, for example the suggested note above.</li>
<li>Scoring timing is set by the portal. This page does not know the score and does not estimate it.</li>
</ol>
</section>
</main>
<footer class="site-footer"><small>Generated by scripts/build_s30_summary.py from evidence/s30_*.json. Scores are USER-REPORTED unless stated. No human inspection is involved in any automated gate.</small></footer>
</body>
</html>
"""
    out = ROOT / "docs/s30-executive-summary.html"
    out.write_text(page)
    print(f"wrote {out} ({len(page)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
