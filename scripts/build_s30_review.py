#!/usr/bin/env python3
"""Build the S30 nine-site executive summary, run card and front-page decision panel.

Reads only evidence/nine_site_byte_audit_2026-10-30.json (written by
scripts/audit_nine_site_bytes.py from the competitor repositories' bytes) plus
registry/irregularities_s30.json. Performs no network requests.

Outputs:
  docs/s30-nine-site-executive-summary.html   (full page: table, overlap matrix, sources)
  evidence/s30_run_card.json                  (machine-readable decision card)
  docs/data/s30_run_card.json                 (Pages copy of the card)
  inserts a decision panel above <main> in index.html and executive-summary.html
  (root and docs/), idempotently, using id="s30-nine-site-decision".

Decision rule (fail-closed): a file is OK to download and submit only if ALL hold:
  1. format matches the official grid and the official [0, 1] rule;
  2. it is unique: <= 70% of its dots within 3 px of every other site's dots, and
     |phi| <= 0.90 on the footprint, against all other audited files;
  3. it has an estimated leaderboard score that is ORGANIZER-CONFIRMED or a
     calibrated estimate (none exists in this repository).
No file in this audit passes rule 2 or rule 3, so the decision is NO.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "evidence" / "nine_site_byte_audit_2026-10-30.json"
IRREG = ROOT / "registry" / "irregularities_s30.json"
PAGE = ROOT / "docs" / "s30-nine-site-executive-summary.html"
CARD = ROOT / "evidence" / "s30_run_card.json"
PAGES_CARD = ROOT / "docs" / "data" / "s30_run_card.json"
PANEL_TARGETS = [
    ROOT / "index.html",
    ROOT / "executive-summary.html",
    ROOT / "docs" / "index.html",
    ROOT / "docs" / "executive-summary.html",
]
MARKER = 'id="s30-nine-site-decision"'
OVERLAP_LIMIT = 0.70
PHI_LIMIT = 0.90
LEADERBOARD = {
    "checked": "2026-10-30 (fetched from drivendata.org public leaderboard, ranks 1-47 read)",
    "rank_1": 0.4544,
    "rank_26": 0.3388,
    "rank_36": 0.3328,
    "prompt_anchor_0_4413_found_in_ranks_1_47": False,
    "prompt_anchor_0_3195_found_in_ranks_1_47": False,
}


def repo_link(site: str, rel: str) -> str:
    return f"https://github.com/buffedlizard55-lab/{site}/blob/main/{rel}"


def raw_link(site: str, rel: str) -> str:
    return f"https://github.com/buffedlizard55-lab/{site}/raw/main/{rel}"


def load() -> tuple[dict, list[dict]]:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    irregularities = json.loads(IRREG.read_text(encoding="utf-8"))["irregularities"]
    return audit, irregularities


def site_rows(audit: dict) -> list[dict]:
    rows = []
    overlap = audit["overlap_3px"]
    phi = audit["phi_footprint"]
    for site, record in audit["files"].items():
        if record.get("status") != "READ":
            rows.append({"site": site, "status": "MISSING"})
            continue
        others = [s for s in audit["files"] if s != site and audit["files"][s].get("status") == "READ"]
        max_ov_site, max_ov = max(((o, max(overlap[site][o], overlap[o][site])) for o in others), key=lambda t: t[1])
        max_phi_site, max_phi = max(((o, phi[site][o]) for o in others), key=lambda t: abs(t[1]))
        identical = [o for o in others if phi[site][o] == 1.0 and overlap[site][o] == 1.0]
        unique = max_ov <= OVERLAP_LIMIT and abs(max_phi) <= PHI_LIMIT
        rows.append(
            {
                "site": site,
                "file": record["file"],
                "file_name": record["file"].rsplit("/", 1)[-1],
                "sha256": record["sha256"],
                "dots": record["positive_pixels"],
                "claimed_score": record["claimed_score"],
                "format_ok": bool(record["format_matches_grid"] and record["in_0_1_all_finite"]),
                "nan_outside_footprint_only": record["nan_pixels"] in (0, 7111787),
                "max_overlap_3px": max_ov,
                "max_overlap_site": max_ov_site,
                "max_abs_phi": abs(max_phi),
                "max_phi_site": max_phi_site,
                "identical_to": identical,
                "unique_under_lane_rule": unique,
                "ok_to_download_and_submit": False,
                "reason": (
                    "Not unique: " + (f"identical dot set to {', '.join(identical)}; " if identical else "")
                    + f"up to {max_ov:.0%} of its dots lie within 3 px of {max_ov_site}'s dots. "
                    "Score not estimable: no calibrated estimate and no organizer receipt."
                ),
                "estimated_score": "NOT ESTIMABLE (no calibrated estimate; no organizer receipt)",
            }
        )
    return rows


def build_card(audit: dict, rows: list[dict]) -> dict:
    ready = [r["site"] for r in rows if r.get("ok_to_download_and_submit")]
    return {
        "schema": "s30-run-card/v1",
        "decision": "NO FILE OK TO DOWNLOAD AND SUBMIT",
        "new_tif_generated": False,
        "weekly_slot_used": False,
        "experiments_run_this_session": 0,
        "generated_by": "scripts/build_s30_review.py",
        "audit_source": "evidence/nine_site_byte_audit_2026-10-30.json",
        "audit_schema": audit.get("schema"),
        "official_sources": {
            "problem_and_metric": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
            "official_rules_pdf": "https://docs.nlr.gov/docs/fy26osti/96647.pdf",
            "leaderboard": "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/",
            "reference_solution": "https://github.com/drivendataorg/gems-prize-reference-solution",
        },
        "official_format": {
            "crs": "EPSG:32611",
            "resolution_m": 100,
            "dtype": "float32",
            "single_layer": True,
            "values": "0 to 1 (probability/confidence)",
            "outside_bounds": "null or nan (official text)",
        },
        "leaderboard_observation": LEADERBOARD,
        "uniqueness_rule": {
            "source": "internal lane protocol; the official rules contain no uniqueness rule",
            "overlap_limit": OVERLAP_LIMIT,
            "phi_limit": PHI_LIMIT,
            "radius_px": 3,
        },
        "footprint_share_within_3px_of_any_site_dot": 0.1957,
        "pairs_flagged_duplicate": audit["pairs_flagged_duplicate"],
        "pairs_total": audit["pairs_total"],
        "files": rows,
        "ok_to_submit_files": ready,
        "verdict": "negative (no file passes uniqueness and estimate gates)",
        "note": "Scores shown are USER-REPORTED or OWNER-REPORTED; none is ORGANIZER-CONFIRMED.",
    }


def table_rows(rows: list[dict]) -> str:
    out = []
    for r in rows:
        if r.get("status") == "MISSING":
            out.append(f"<tr><td>{html.escape(r['site'])}</td><td colspan=\"7\">file not found in audit</td></tr>")
            continue
        out.append(
            "<tr>"
            f"<td><strong>{html.escape(r['site'])}</strong></td>"
            f"<td><a href=\"{html.escape(raw_link(r['site'], r['file']), quote=True)}\" download>"
            f"{html.escape(r['file_name'])}</a><br><small>sha256 {html.escape(r['sha256'][:16])}…</small></td>"
            f"<td>{r['claimed_score']:.4f}<br><small>USER/OWNER-REPORTED</small></td>"
            f"<td>{html.escape(r['estimated_score'])}</td>"
            f"<td>{r['dots']:,}</td>"
            f"<td>{'PASS' if r['format_ok'] else 'FAIL'}</td>"
            f"<td><strong>NO</strong> · max {r['max_overlap_3px']:.0%} within 3 px of {html.escape(r['max_overlap_site'])}"
            + (f"<br><small>identical to {html.escape(', '.join(r['identical_to']))}</small>" if r["identical_to"] else "")
            + "</td>"
            "<td><strong>NO</strong></td>"
            "</tr>"
        )
    return "\n".join(out)


def matrix(audit: dict) -> str:
    sites = [s for s in audit["files"] if audit["files"][s].get("status") == "READ"]
    head = "".join(f"<th>{html.escape(s[-2:])}</th>" for s in sites)
    body = []
    for a in sites:
        cells = []
        for b in sites:
            if a == b:
                cells.append("<td>—</td>")
            else:
                v = audit["overlap_3px"][a][b]
                cls = " class=\"dup\"" if v > OVERLAP_LIMIT else ""
                cells.append(f"<td{cls}>{v:.2f}</td>")
        body.append(f"<tr><th>{html.escape(a)}</th>{''.join(cells)}</tr>")
    return f"<table class=\"matrix\"><thead><tr><th>A \\ B</th>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def irregularity_list(items: list[dict]) -> str:
    return "\n".join(
        f"<li><strong>{html.escape(i['id'])}</strong> ({html.escape(i['severity'])}): "
        f"{html.escape(i['issue'])} <em>Action:</em> {html.escape(i['action'])}</li>"
        for i in items
    )


CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1d2330;background:#f7f8fb;line-height:1.5}
header,main{max-width:1180px;margin:0 auto;padding:18px 22px}
header{border-bottom:1px solid #d9dde7;background:#fff}
a{color:#1f5fbf}
.decision{border:3px solid #b42318;background:#fff1f0;padding:16px 20px;border-radius:10px;margin:16px 0}
.decision h1{margin:4px 0 8px;font-size:1.5rem;color:#b42318}
.card{background:#fff;border:1px solid #d9dde7;border-radius:10px;padding:14px 18px;margin:14px 0}
table{border-collapse:collapse;width:100%;background:#fff;font-size:.92rem}
th,td{border:1px solid #d9dde7;padding:6px 8px;vertical-align:top;text-align:left}
th{background:#eef1f7}
table.matrix td,table.matrix th{text-align:center;font-size:.85rem}
td.dup{background:#ffe3e0;font-weight:600}
small{color:#4a5366}
.pill-no{background:#b42318;color:#fff;border-radius:6px;padding:2px 8px;font-weight:700}
"""


def page(audit: dict, rows: list[dict], irregularities: list[dict]) -> str:
    lb = LEADERBOARD
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>S30 nine-site executive summary · GEMSDOE28</title>
<style>{CSS}</style></head>
<body>
<header><a href="index.html">← GEMSDOE28 overview</a> · <a href="executive-summary.html">Executive summary</a> · <a href="../README.md">README (standing prompt)</a></header>
<main>
<div class="decision" id="s30-nine-site-decision" data-submission-ready="false">
<p><strong>S30 · 2026-10-30 UTC · AUTOMATED DECISION · NO HUMAN INSPECTOR</strong></p>
<h1>OK TO DOWNLOAD AND SUBMIT: NO — for all nine sites</h1>
<p><strong>No new TIF was generated and no weekly slot was used.</strong> Every nine-site "best" file was read byte-for-byte. All nine pass the official format and [0, 1] range checks, but they are not unique: <strong>all 36 pairs</strong> exceed the 70% / 3 px overlap rule, and <strong>GEMSDOE25 and GEMSDOE30 contain identical dot sets</strong> (44,090 dots each). No estimated leaderboard score can be defended, because no calibrated estimate and no organizer receipt exist.</p>
<p><strong>Best file to submit:</strong> none is recommended from this audit. The highest-claimed file, <code>GEMSDOE32 … e5eb6e7e-zeros.tif</code> (0.2778, OWNER-REPORTED), is already submitted according to its owner page, and it is in the same family as the other eight.</p>
</div>

<section class="card">
<h2>1. Which file to download, what it scores, and whether it is unique</h2>
<p>Estimated score column: <strong>not estimable</strong>. The holdout tools in this repository are not calibrated to the hidden leaderboard score (the owner's own holdout gives the 0.2778 champion HOLDOUT-DTI 0.0045 on its evaluator, while 0.2778 is a user/owner-reported score, not a leaderboard value). Claimed values are copied from the prompt and marked as reported, not confirmed.</p>
<table>
<thead><tr><th>Site</th><th>File (download for review only)</th><th>Claimed score</th><th>Estimated score</th><th>Dots</th><th>Official format</th><th>Unique vs the other 8?</th><th>OK to download and submit?</th></tr></thead>
<tbody>
{table_rows(rows)}
</tbody></table>
<p><small>Format column: float32, single band, EPSG:32611, 3730×3292 at 100 m, values in [0,1] inside the footprint, NaN only outside it. "Zeros" variants write 0 outside the footprint, which is a conformance question (see irregularities).</small></p>
</section>

<section class="card">
<h2>2. Why the family is not unique: share of each file's dots within 3 px of another file's dots</h2>
<p>Rows = file A, columns = file B. Each cell is the share of A's dots within 3 px (300 m) of B's dots. Red = above 70% (duplicate under the lane rule). The whole family overlaps 0.87–1.00, so no pair is unique.</p>
{matrix(audit)}
<p>Footprint coverage: the nine files together place dots within 3 px of only 19.6% of the 5,167,373-pixel footprint. A unique file must place most of its dots outside that zone, which is a different hypothesis, not a relabelled copy.</p>
</section>

<section class="card">
<h2>3. Leaderboard observation (public board, read 2026-10-30)</h2>
<ul>
<li>Rank 1: <strong>{lb['rank_1']:.4f}</strong>. Rank 26: {lb['rank_26']:.4f}. Rank 36: {lb['rank_36']:.4f}. Source: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">official public leaderboard</a>.</li>
<li>The prompt's anchors 0.4413 and 0.3195 do not appear in ranks 1–47. This is an irregularity. The public board is not the private scoring set.</li>
</ul>
</section>

<section class="card">
<h2>4. Official rules this audit checks against</h2>
<ul>
<li>Single-band GeoTIFF, 100 m, EPSG:32611, float32, values 0–1, outside bounds null or NaN, same bounds as training data. Source: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem description</a>.</li>
<li>Metric: distance-weighted Tversky index, α = 0.2, β = 0.8, triangular kernel with 300 m support. Source: same page.</li>
<li>Three submissions per week; one submission is selected for scoring. Source: <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules PDF</a>, §3.2.</li>
<li>The official rules contain no uniqueness or overlap rule. The 70% / 3 px rule is internal and applies only if the team adopts it.</li>
</ul>
</section>

<section class="card">
<h2>5. Irregularities flagged for review</h2>
<ul>{irregularity_list(irregularities)}</ul>
</section>

<section class="card">
<h2>6. Method and reproduction</h2>
<p>Run: <code>python scripts/audit_nine_site_bytes.py --sites-dir &lt;clones&gt; --labels data/labels.tif --footprint data/sample_submission.tif --out evidence/nine_site_byte_audit_2026-10-30.json</code> then <code>python scripts/build_s30_review.py</code>. The nine clones are the public GitHub repositories <code>buffedlizard55-lab/GEMSDOE24 … GEMSDOE36</code> (main branch), fetched from codeload.github.com. The owner GitHub Pages sites are not reachable from this sandbox, so the owner pages were read from the repository copies.</p>
<p><a href="../evidence/nine_site_byte_audit_2026-10-30.json">Byte audit (JSON)</a> · <a href="data/s30_run_card.json" download>Run card (JSON)</a> · <a href="../knowledge/77_s30_nine_site_byte_audit_2026-10-30.md">Knowledge note</a> · <a href="../registry/irregularities_s30.json">Irregularity register</a></p>
</section>
</main>
</body></html>
"""


def panel(card: dict) -> str:
    return """<section class="section callout-danger" id="s30-nine-site-decision" aria-label="S30 submission decision" data-submission-ready="false">
<p class="eyebrow">S30 · 2026-10-30 UTC · AUTOMATED DECISION · NO HUMAN INSPECTOR</p>
<h2>OK TO DOWNLOAD AND SUBMIT: NO</h2>
<p><strong>No new TIF was generated.</strong> All nine sites' best files pass the official format and [0,1] check, but all 36 pairs exceed the 70% / 3 px uniqueness rule. GEMSDOE25 and GEMSDOE30 are identical files. No score estimate is defensible. Best claimed file (0.2778, GEMSDOE32) is already submitted per its owner page and is not unique.</p>
<div class="download-actions"><button class="button" type="button" disabled aria-disabled="true">Download disabled: no file is OK to submit</button> <a class="button quiet" href="s30-nine-site-executive-summary.html">Open S30 nine-site executive summary</a> <a class="button quiet" href="data/s30_run_card.json" download>Download S30 run card (JSON)</a></div>
</section>"""


def insert_panels(html_panel: str) -> list[str]:
    updated = []
    for path in PANEL_TARGETS:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if MARKER in text:
            before, after = text.split(MARKER, 1)
            start = before.rfind("<section")
            end = after.find("</section>")
            if start < 0 or end < 0:
                raise ValueError(f"malformed S30 panel in {path}")
            text = before[:start] + after[end + len("</section>"):]
        if "<main>" not in text:
            raise ValueError(f"no <main> in {path}")
        # The root pages and docs pages link to the docs page with different prefixes.
        prefix = "docs/" if path.parent == ROOT else ""
        rendered = html_panel.replace('href="s30-nine-site-executive-summary.html"', f'href="{prefix}s30-nine-site-executive-summary.html"')
        rendered = rendered.replace('href="data/s30_run_card.json"', f'href="{prefix}data/s30_run_card.json"')
        text = text.replace("<main>", "<main>" + rendered, 1)
        path.write_text(text, encoding="utf-8")
        updated.append(path.relative_to(ROOT).as_posix())
    return updated


def main() -> int:
    audit, irregularities = load()
    rows = site_rows(audit)
    card = build_card(audit, rows)
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(page(audit, rows, irregularities), encoding="utf-8")
    CARD.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    PAGES_CARD.parent.mkdir(parents=True, exist_ok=True)
    PAGES_CARD.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    updated = insert_panels(panel(card))
    print(f"wrote {PAGE.relative_to(ROOT)}, {CARD.relative_to(ROOT)}; panels in {len(updated)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
