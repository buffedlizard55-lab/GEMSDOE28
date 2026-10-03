#!/usr/bin/env python3
"""Build the static, source-linked manual-only Pages site from repository JSON records.

The build is deterministic apart from the data's checked-in observation dates. It reads no rasters,
performs no external requests, and never contacts DrivenData. Review the original standing brief in
README.md before changing the submission path or the claims rendered here.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REPOSITORY_SOURCE_BASE = "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/"
SOURCE_PATH_ROOTS = {"evidence", "knowledge", "registry", "scripts", "src", "tests", ".github"}
SOURCE_PATH_FILES = {"README.md", "AI_DISCLOSURE.md", "pyproject.toml", "requirements.txt"}


def read_json(path: str, default: Any = None) -> Any:
    target = ROOT / path
    if not target.exists():
        if default is not None:
            return default
        raise FileNotFoundError(target)
    return json.loads(target.read_text(encoding="utf-8"))


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def fmt_number(value: Any, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "not recorded"


def comma(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return esc(value)


def range_summary(record: dict) -> str:
    return str(record.get("conclusion", {}).get(
        "most_plausible_explanation", record.get("summary", "Historical validator cause remains unconfirmed.")))


def h31_report_integrity(report: dict, stage: str) -> bool:
    seeds = {"screen": list(range(160, 170)), "confirmation": list(range(170, 180))}.get(stage)
    if not isinstance(report, dict) or seeds is None:
        return False
    check = dict(report)
    recorded = check.get("sha256")
    check["sha256"] = None
    expected_hash = hashlib.sha256(json.dumps(check, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    expected_path = f"evidence/h31_1_euler_{'screen' if stage == 'screen' else 'confirm'}.started.json"
    claim = report.get("single_use_seed_claim", {})
    if not isinstance(claim, dict):
        return False
    claim_path = ROOT / expected_path
    try:
        claim_record = json.loads(claim_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(claim_record, dict):
        return False
    try:
        claim_sha256 = hashlib.sha256(claim_path.read_bytes()).hexdigest()
    except OSError:
        return False
    return bool(
        recorded == expected_hash
        and report.get("schema") == 1
        and report.get("stage") == stage
        and report.get("seeds") == seeds
        and claim.get("path") == expected_path
        and claim.get("sha256") == claim_sha256
        and claim_record.get("stage") == stage
        and claim_record.get("seeds") == seeds
        and claim_record.get("protocol_commit") == report.get("protocol_commit")
        and claim_record.get("protocol_sha256") == report.get("protocol_sha256")
        and claim_record.get("input_hashes") == report.get("input_hashes")
        and claim_record.get("feature_hashes") == report.get("feature_hashes")
        and claim_record.get("code_hashes") == report.get("code_hashes")
        and claim_record.get("runtime_versions") == report.get("runtime_versions")
        and isinstance(report.get("gate"), dict)
        and report.get("submission_raster_written") is False
        and report.get("drivendata_access") is False
    )


def h31_stage_passed(report: dict, stage: str) -> bool:
    return h31_report_integrity(report, stage) and report.get("gate", {}).get("passed") is True


def h31_stage_failed(report: dict, stage: str) -> bool:
    return h31_report_integrity(report, stage) and report.get("gate", {}).get("passed") is False


def h31_integrity_summary(report: dict) -> str:
    checks = report.get("data_integrity_checks", {})
    if not isinstance(checks, dict):
        return ""
    failures = [name for name, passed in checks.items() if passed is False]
    if not failures:
        return ""
    details = []
    if "minimum_spacing_at_least_1_5_px" in failures:
        cells = report.get("cells", [])
        summary = report.get("summary", {})
        total = len(cells) if isinstance(cells, list) else 0
        if not total and isinstance(summary, dict):
            try:
                total = int(summary.get("cells", 0))
            except (TypeError, ValueError):
                total = 0
        count = report.get("minimum_spacing_failures", total)
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = total
        counts = {}
        for group in ("control", "candidate"):
            misses = 0
            observed = 0
            for cell in cells if isinstance(cells, list) else []:
                spacing = cell.get("minimum_spacing_px", {}) if isinstance(cell, dict) else {}
                try:
                    misses += float(spacing[group]) < 1.5
                    observed += 1
                except (KeyError, TypeError, ValueError):
                    continue
            if observed:
                counts[group] = f"{misses}/{observed}"
        detail = f"minimum spacing below 1.5 px in {count}/{total or 'unknown'} cells"
        if len(counts) == 2:
            detail += f" (control {counts['control']}; candidate {counts['candidate']})"
        details.append(detail)
    other_failures = [name for name in failures if name != "minimum_spacing_at_least_1_5_px"]
    if other_failures:
        details.append("other failed checks: " + ", ".join(other_failures))
    elif details:
        details.append("all other listed integrity checks passed")
    return "Integrity gate: " + "; ".join(details) + "."


def h31_stage_line(name: str, report: dict) -> str:
    stage = "screen" if name.lower() == "screen" else "confirmation"
    verified = h31_report_integrity(report, stage)
    outcome = report.get("gate", {}).get("passed") if verified else None
    label = "PASS" if outcome is True else "FAIL" if outcome is False else "UNVERIFIED"
    summary = report.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    try:
        gain = f"{float(summary['mean_paired_gain']):+.6f}"
    except (KeyError, TypeError, ValueError):
        gain = "not recorded"
    folds = summary.get("positive_fold_count", "not recorded")
    seeds = summary.get("positive_seed_count", "not recorded")
    line = (f"{name} frozen gate {label}; mean paired catalogue-proxy ΔDTI {gain}; "
            f"positive folds {folds}/4; positive seed means {seeds}/10.")
    if verified:
        line += " " + h31_integrity_summary(report)
    return line


def h31_result_summary(screen: dict, confirmation: dict, seed_audit: dict) -> str:
    screen_state = seed_audit.get("range_status", {}).get("screen", "UNKNOWN")
    confirmation_state = seed_audit.get("range_status", {}).get("confirmation", "UNKNOWN")
    if not screen and screen_state == "INCOMPLETE":
        return "Screen seeds 160–169 were claimed but no final report exists; treat the run as interrupted and do not rerun."
    if not screen and screen_state in {"CONSUMED", "INVALID"}:
        return f"Seed audit reports screen status {screen_state} but no final screen report exists; investigate before any next stage."
    if not screen and not confirmation:
        if confirmation_state != "UNUSED":
            return f"Confirmation seed status is {confirmation_state} without a final screen/confirmation report; investigate the evidence chain."
        if seed_audit.get("status") != "PASS":
            return f"No final H31 stage report is recorded; the local seed audit is {seed_audit.get('status', 'missing')}, so unused status is not established."
        if screen_state == "UNUSED":
            return "No H31 classifier fit or holdout has been run."
        return f"No final H31 stage report is recorded; screen seed status is {screen_state}. Do not infer that the range is unused."
    parts = []
    if screen:
        parts.append(h31_stage_line("Screen", screen))
    if confirmation:
        parts.append(h31_stage_line("Confirmation", confirmation))
    screen_pass = h31_stage_passed(screen, "screen") if screen else False
    screen_fail = h31_stage_failed(screen, "screen") if screen else False
    confirm_pass = h31_stage_passed(confirmation, "confirmation") if confirmation else False
    if screen_fail:
        parts.append("The frozen failure ends this arm; no confirmation or retuning is allowed.")
    elif screen and confirmation:
        if screen_pass and confirm_pass:
            parts.append("Both results remain catalogue proxies, not organizer-label or competition performance; no weekly slot is authorized.")
        else:
            parts.append("A failed or unverified stage rejects the arm for submission; no weekly slot is authorized.")
    elif screen_pass:
        parts.append("Confirmation on seeds 170–179 remains required; this screen is proxy evidence only and does not authorize a weekly slot.")
    else:
        parts.append("The screen result is not verified as a pass; no confirmation or weekly slot is authorized.")
    return " ".join(parts)


def h31_next_step(screen: dict, confirmation: dict, seed_audit: dict) -> str:
    screen_state = seed_audit.get("range_status", {}).get("screen", "UNKNOWN")
    if not screen:
        if screen_state != "UNUSED":
            return f"Screen range status is {screen_state}; inspect its single-use claim/evidence and do not rerun an uncertain range."
        confirmation_state = seed_audit.get("range_status", {}).get("confirmation", "UNKNOWN")
        if confirmation_state != "UNUSED":
            return f"Confirmation range status is {confirmation_state} without a screen report; investigate and do not fit."
        if seed_audit.get("status") != "PASS":
            return "The local seed audit is not PASS; do not fit until the ledger is reconciled and refreshed."
        if not confirmation:
            return ("The label-free build and local seed audit pass, but the classifier holdout is still unrun. "
                    "Refresh the seed ledger immediately before the single-use screen; no weekly slot is authorized.")
        return "A confirmation report exists without a screen report; stop and investigate the evidence chain."
    if h31_stage_failed(screen, "screen"):
        return "The frozen screen failed; stop this arm without confirmation, retuning or a weekly slot."
    if screen and confirmation:
        if h31_stage_passed(screen, "screen") and h31_stage_passed(confirmation, "confirmation"):
            return ("Both frozen stages passed as catalogue-proxy evidence. Assess transfer limitations and audit any "
                    "exact research file separately; this does not authorize a weekly slot or an upload.")
        return "Confirmation did not pass its frozen gate; reject this arm for submission and do not use a weekly slot."
    if h31_stage_passed(screen, "screen"):
        return ("The screen passed its frozen proxy gate. Refresh the seed ledger and, without changing the recipe, "
                "run the one preregistered confirmation on seeds 170–179; no weekly slot is authorized yet.")
    return "The saved result is incomplete or unverified; stop and review the evidence before any next stage."


def h31_evidence_links(screen: dict, confirmation: dict) -> str:
    links = []
    if screen:
        links.append('<a href="../evidence/h31_1_euler_screen.json">screen evidence</a>')
        links.append('<a href="../evidence/h31_1_euler_screen.started.json">single-use screen claim</a>')
    if confirmation:
        links.append('<a href="../evidence/h31_1_euler_confirm.json">confirmation evidence</a>')
        links.append('<a href="../evidence/h31_1_euler_confirm.started.json">single-use confirmation claim</a>')
    return " · ".join(links)


def h32_result_summary(h32: dict) -> str:
    if not h32:
        return "No H32-1 report is recorded."
    gate = h32.get("gate", {})
    try:
        gain = f"{float(h32['candidate_minus_control_mean_gain']):+.6f}"
    except (KeyError, TypeError, ValueError):
        gain = "not recorded"
    label = "PASS" if gate.get("pass") is True else "FAIL" if gate.get("pass") is False else "UNVERIFIED"
    return (f"H32-1 structural-step frozen screen {label} on seeds 170–179: mean paired catalogue-proxy "
            f"ΔDTI {gain}, positive folds {h32.get('improved_fold_count', 'not recorded')}/4 and positive "
            f"seed means {h32.get('positive_seed_count', 'not recorded')}/10; the arm is closed with no "
            f"confirmation and no weekly slot.")


def seed_range_label(seed_audit: dict, stage: str) -> str:
    state = seed_audit.get("range_status", {}).get(stage)
    if state == "UNUSED":
        return "unused locally"
    if state == "CONSUMED":
        return "consumed locally"
    return "status unknown; do not infer unused"


def nav() -> str:
    links = [
        ("Overview", "index.html"),
        ("Executive summary", "executive-summary.html"),
        ("Research", "research.html"),
        ("Topology", "topology.html"),
        ("Sources", "sources.html"),
    ]
    return "<nav aria-label=\"Main navigation\">" + "".join(
        f'<a href="{href}">{label}</a>' for label, href in links
    ) + "</nav>"


def layout(title: str, body: str, active: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="GEMSDOE28 auditable geoscience research, manual-only submission path, and source-linked evidence.">
  <title>{esc(title)} | GEMSDOE28</title>
  <link rel="stylesheet" href="assets/site.css">
  <script defer src="assets/site.js"></script>
</head>
<body>
<header class="site-header"><div class="header-inner">
  <a class="brand" href="index.html">GEMSDOE28 <small>DOE GEMS · Auditable research</small></a>
  {nav()}
</div></header>
<main>{body}</main>
<footer><div class="footer-inner"><p><strong>Maximize P(Win) · Own the Outcome.</strong> Static pages are source-linked and generated locally from repository JSON. No upload, login, scraping, polling, or automated DrivenData access occurs here. Research proxy results are not competition scores.</p></div></footer>
</body>
</html>
"""


def publish_source_links(page: str) -> str:
    """Turn docs-relative links to repository files into durable public GitHub source links."""
    def replace(match: re.Match[str]) -> str:
        attr, url = match.group(1), match.group(2)
        if not url.startswith("../"):
            return match.group(0)
        path = url[3:]
        root = path.split("/", 1)[0]
        if root in SOURCE_PATH_ROOTS or path in SOURCE_PATH_FILES:
            return attr + REPOSITORY_SOURCE_BASE + path
        return match.group(0)
    return re.sub(r'((?:href|src)=\")([^\"]+)', replace, page)


def note_box(note: str) -> str:
    return (f'<div class="note-box"><code>{esc(note)}</code>'
            f'<button class="copy-note" type="button" data-copy-note="{esc(note)}" aria-label="Copy the exact submission note">Copy note</button></div>')


def file_links(item: dict, prefix: str = "downloads/") -> str:
    links = [f'<a class="button" href="{prefix}{esc(item["nan"])}" download>Download single-band GeoTIFF</a>']
    if item.get("zip"):
        links.append(f'<a class="button quiet" href="{prefix}{esc(item["zip"])}" download>Download ZIP</a>')
    if item.get("allfinite"):
        links.append(f'<a class="button secondary" href="{prefix}{esc(item["allfinite"])}" download>All-finite fallback</a>')
    return '<div class="download-actions">' + "".join(links) + "</div>"


def candidate_card(slot: str, item: dict, *, featured: bool = False) -> str:
    title = item.get("hypothesis", item.get("slug", slot))
    status = item.get("status", "UNSCORED research artifact")
    css = "card span-12" if featured else "card span-6"
    return f"""<article class="{css}">
  <div class="rank">{esc(slot)} · {esc(item.get('content_id', 'no id'))}</div>
  <h3>{esc(title)}</h3><p><span class="status unscored">UNSCORED</span></p>
  <p>{esc(status)}</p>
  {file_links(item)}
  <p><strong>NaN GeoTIFF:</strong> <code class="file-name">{esc(item['nan'])}</code></p>
  <p class="meta">SHA-256 <code>{esc(item.get('sha256_nan', 'not recorded'))}</code> · {esc(item.get('bytes_nan', 'n/a'))} bytes · {esc(item.get('emitted_px', 'n/a'))} positive cells</p>
  <p><strong>Manual note ({len(str(item.get('note', '')))} / 200 characters):</strong></p>{note_box(str(item.get('note', '')))}
</article>"""


def render_index(manifest: dict, board: dict, euler: dict, range_audit: dict, restore: dict,
                 screen: dict, confirmation: dict, seed_audit: dict, h32: dict) -> str:
    primary = manifest["primary"]
    q = manifest.get("quaternary", {})
    observations = board.get("observations", [])
    board_lines = "".join(
        f"<li>Public row: rank {esc(row.get('rank'))}, {esc(row.get('participant_label'))}, {fmt_number(row.get('public_score'))}.</li>"
        for row in observations
    )
    euler_ready = euler.get("status", "label-free transform only")
    range_claim = range_summary(range_audit)
    restore_status = restore.get("status", "local restore audit exists; consult its JSON record")
    return f"""<section class="hero"><div class="hero-content">
  <div class="eyebrow">GEMS DOE · Great Basin · 2026</div>
  <h1>Evidence before<br>emission.</h1>
  <p class="lead">An auditable geoscience research workflow aimed at better fault mapping—not a submission bot. Every idea must earn its way through a spatially blocked holdout, independent confirmation, and an exact-file audit before it can approach a weekly slot.</p>
  <div class="value-line"><span class="value-pill">Maximize P(Win)</span><span class="value-pill">Own the Outcome</span><span class="status unscored">NO GEMSDOE28 SCORE</span></div>
  <p><strong>Current status:</strong> the best available file below is an inherited H28-1 full-map research raster with catalogue-proxy holdout evidence. It is locally format-audited, <strong>unscored</strong>, and not slot-approved. H31-1 status: {esc(h31_result_summary(screen, confirmation, seed_audit))} {esc(h32_result_summary(h32))}</p>
</div></section>

<section class="download-panel" id="download" aria-labelledby="download-heading">
  <div class="eyebrow">Manual research download · no upload made</div>
  <h2 id="download-heading">One-click GeoTIFF — {esc(primary.get('hypothesis', 'H28-1 reference'))}</h2>
  <p><span class="status unscored">UNSCORED · RESEARCH ONLY · NOT SLOT-APPROVED</span></p>
  {file_links(primary)}
  <p><strong>Exact filename</strong></p><code class="file-name">{esc(primary['nan'])}</code>
  <p class="meta">SHA-256 <code>{esc(primary.get('sha256_nan', ''))}</code> · {esc(primary.get('bytes_nan'))} bytes · single-band float32 · {esc(primary.get('emitted_px'))} cells equal to 1 · CRS EPSG:32611 · 100 m grid · template footprint {comma(restore.get('grid', {}).get('footprint_pixels', 5167373))} cells.</p>
  <p><strong>Exact short note ({len(str(primary.get('note', '')))} / 200 characters):</strong></p>
  {note_box(str(primary.get('note', '')))}
  <p class="small">The note's +0.00295 is a preregistered catalogue hide-and-recover proxy ΔDTI on seeds 140–149; it is not a leaderboard score and not confirmation on hidden expert labels. This file is a research/reference artifact, not one of the four weekly slots inherited from the predecessor campaign.</p>
</section>

<div class="callout"><strong>Manual-only boundary:</strong> no login, download, upload, scrape, poll, or monitoring of DrivenData occurs in this repository. Review the official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a> and <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules</a> yourself before deciding whether to submit. A local audit does not guarantee portal acceptance.</div>

<section class="section"><div class="grid">
  <article class="card span-4"><div class="metric">{comma(restore.get('grid', {}).get('footprint_pixels', 5167373))}</div><div class="metric-caption">template-footprint cells on the verified local grid</div><p>Restoration status: <strong>{esc(restore_status)}</strong>. The nine pinned files are owner-repository mirrors, not organizer-authenticated bytes.</p><a href="../evidence/restore_audit.json">Open the local restoration audit →</a></article>
  <article class="card span-4"><div class="metric">+{fmt_number(0.002948838794400959, 5)}</div><div class="metric-caption">H28-1 paired mean proxy ΔDTI · seeds 140–149</div><p>3/4 spatial folds and 9/10 seeds improved. A proxy result—not a competition result.</p><a href="../evidence/h28_1_edge_holdout.json">Open paired holdout evidence →</a></article>
  <article class="card span-4"><div class="metric">{comma(euler.get('structural_indices', {}).get('0', {}).get('lineament_cluster_stats', {}).get('retained_cluster_count', 6309))}</div><div class="metric-caption">SI-0 Euler depth-labeled clusters in label-free build</div><p>{esc(euler_ready)}. The feature build is label-free; H31 screen outcome is shown above. No H31 submission TIFF exists.</p><a href="../evidence/h31_1_euler_feature_audit.json">Open Euler audit →</a> {h31_evidence_links(screen, confirmation)}</article>
</div></section>

<section class="section">
  <div class="eyebrow">Historical comparator library</div><h2>Every file stays explicitly unscored.</h2>
  <p>These research artifacts preserve comparable model families for review. None is a recommendation or authorized weekly submission; the primary H28-1 file above is the only prominent one-click research reference.</p>
  <div class="grid">{candidate_card('secondary', manifest.get('secondary', {}))}{candidate_card('tertiary', manifest.get('tertiary', {}))}{candidate_card('quaternary', q)}</div>
</section>

<section class="section"><div class="eyebrow">Claim discipline</div><h2>Public rows are not file receipts.</h2>
  <p>A one-off manual leaderboard observation on {esc(board.get('snapshot_date', 'not recorded'))} showed:</p><ul>{board_lines}</ul>
  <p>That observation does not identify this repository's owner or associate a score with any local GeoTIFF. The reported 0.2477 is owner-reported and unverified. Current GEMSDOE28 files remain unscored.</p>
  <p><strong>Historical range error:</strong> {esc(range_claim)} The predecessor all-finite raster had positives outside the footprint, so it is not a valid shortcut. See the <a href="../evidence/range_validator_forensics_2026-10-03.json">hash-pinned forensic record</a>.</p>
  <p>For exact file/grid/range/mask/hash checks, see <a href="downloads/manifest.json">the download manifest</a> and <a href="../evidence/submission_file_audit.json">the current local file audit</a>.</p>
</section>

<section class="section"><div class="grid">
  <article class="card span-6"><div class="eyebrow">What is next</div><h3>One frozen test at a time</h3><p>{esc(h31_next_step(screen, confirmation, seed_audit))}</p><a href="research.html">See ranked hypotheses and limitations →</a></article>
  <article class="card span-6"><div class="eyebrow">Manual review</div><h3>Read the original sources</h3><p>Open the dated <a href="sources.html">source ledger</a>, <a href="topology.html">topology review</a>, and <a href="executive-summary.html">submission instructions</a>. Every external-data status distinguishes a listing from actual byte/schema/coverage/licence verification.</p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Official public leaderboard — human spot-check only</a></article>
</div></section>
"""


def render_executive(manifest: dict, board: dict, file_audit: dict, range_audit: dict,
                     screen: dict, confirmation: dict, seed_audit: dict, h32: dict) -> str:
    p = manifest["primary"]
    candidate = read_json("docs/downloads/h28_1_candidate_manifest.json", {"candidate": {}}).get("candidate", {})
    audit_status = file_audit.get("status", "not yet recorded")
    check_count = file_audit.get("check_count", "not recorded")
    return f"""<div class="breadcrumb"><a href="index.html">Overview</a> / Executive summary</div>
<section class="hero"><div class="hero-content">
  <div class="eyebrow">Submission executive summary · manual operator checklist</div>
  <h1>Research file,<br>not a score claim.</h1>
  <p class="lead">A concise decision brief for a human owner reviewing whether any local raster is appropriate for a future GEMS submission. The current first-screen download is intentionally labeled UNSCORED and NOT SLOT-APPROVED.</p>
  <div class="value-line"><span class="value-pill">Maximize P(Win)</span><span class="value-pill">Own the Outcome</span><span class="status unscored">NO UPLOAD / NO RECEIPT</span></div>
</div></section>

<section class="section"><div class="grid">
  <article class="card span-8"><h2>Candidate in one paragraph</h2><p><strong>{esc(p.get('hypothesis'))}.</strong> Filename <code class="file-name">{esc(p['nan'])}</code>. This is an inherited H28-1 full-map research artifact from the predecessor project, with local single-band GeoTIFF/grid/range/mask checks. Its paired catalogue hide-and-recover evidence reports a mean ΔDTI of +0.00294884, three of four spatial folds and nine of ten seeds improving over the same-run control. It is a proxy experiment, not evidence of competition performance on new expert labels. The file has not been uploaded or organizer-scored.</p><p><strong>Disposition:</strong> do not consume a weekly submission slot on the basis of this page. It is a research reference and is not one of the four weekly slots inherited from the predecessor campaign.</p></article>
  <article class="card span-4"><div class="metric">{comma(p.get('emitted_px'))}</div><div class="metric-caption">binary positive cells</div><hr><div class="metric">{fmt_number(candidate.get('holdout_mean_gain', 0.002948838794400959), 5)}</div><div class="metric-caption">catalogue proxy mean gain, not score</div></article>
</div></section>

<section class="download-panel"><div class="eyebrow">Prominent single-band GeoTIFF · manual download</div><h2>{esc(p.get('hypothesis'))}</h2><p><span class="status unscored">UNSCORED · NOT SLOT-APPROVED</span></p>
{file_links(p)}<p><strong>Primary exact filename:</strong></p><code class="file-name">{esc(p['nan'])}</code><p class="meta">SHA-256 <code>{esc(p.get('sha256_nan'))}</code> · {esc(p.get('bytes_nan'))} bytes · {comma(p.get('emitted_px'))} emitted cells · EPSG:32611 · 3730 × 3292 · 100 m grid.</p><p><strong>Copy this exact short note ({len(str(p.get('note','')))} / 200 characters):</strong></p>{note_box(str(p.get('note','')))}
<p>Alternative package: <a href="downloads/{esc(p['zip'])}" download>{esc(p['zip'])}</a>. The separately named all-finite TIFF uses zero outside the template footprint as a manual fallback; it is not claimed to solve the old portal error. Do not use the predecessor all-finite file with out-of-footprint positives.</p></section>

<section class="section"><h2>Human submission checklist</h2><ol>
<li><strong>Re-evaluate evidence, not just the file.</strong> Read <a href="../evidence/h28_1_edge_holdout.json">the exact paired holdout</a> and <a href="research.html">current limits/ranking</a>. {esc(h31_result_summary(screen, confirmation, seed_audit))} {esc(h32_result_summary(h32))} {h31_evidence_links(screen, confirmation)}</li>
<li><strong>Review the official rules and data terms manually.</strong> Check the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a>, <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules</a>, current deadline and submission cap. This site does not log in or automate any interaction.</li>
<li><strong>Choose the exact local file yourself.</strong> The suggested `.tif` above is a single-band float32 GeoTIFF with values 0/1 within the sample-template footprint and nodata outside. Use the exact filename and SHA-256 in the local audit; do not rename it in a way that loses its content ID.</li>
<li><strong>Paste the registered note manually.</strong> Copy the exact short note above. Include no unsupported score claim. Keep a screenshot or receipt that identifies the selected filename and the organizer's returned score.</li>
<li><strong>Preserve the outcome.</strong> If a portal error appears, save its exact text, time, filename and organizer response. Do not infer that the cause is NaN or range until the actual returned message and payload are re-audited.</li>
</ol></section>

<section class="section"><div class="callout"><strong>What has been locally audited:</strong> current submission-file audit status <strong>{esc(audit_status)}</strong> ({esc(check_count)} checks). The local checker reports only file format, grid, `[0,1]`/finiteness, footprint, catalogue overlap, hashes, ZIP membership and note length. It does not authenticate input bytes with the organizer and does not guarantee portal acceptance.</div>
<div class="callout callout-danger"><strong>Historical range-validator error remains unconfirmed.</strong> Exact predecessor files were hash-pinned; the old NaN variant contains internal NaNs, and the old all-finite variant contains 625,805 positive cells outside the mask. Internal NaNs are a plausible local explanation, not proof of the portal validator's root cause. <a href="../evidence/range_validator_forensics_2026-10-03.json">Read exact file forensics</a> (summary: {esc(range_summary(range_audit))}).</div></section>

<section class="section"><h2>Score and ownership claims</h2><p>Reported 0.2477 remains owner-reported without an organizer receipt or authoritative association to a local TIFF. A one-off manual official leaderboard read on {esc(board.get('snapshot_date', 'not recorded'))} recorded rows for DARD (rank 1, 0.3195) and wbg1 (rank 15, 0.2600). Public rows do not identify the repository owner or bind a score to a file. No GEMSDOE28 candidate has an organizer score.</p><p><a href="{esc(board.get('url', 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'))}">Official public leaderboard — manual review only</a> · no automated access or monitoring.</p></section>
"""


def h31_hypothesis_status(screen: dict, confirmation: dict, seed_audit: dict) -> str:
    if not screen:
        status = seed_audit.get("range_status", {}).get("screen", "UNKNOWN")
        confirmation_state = seed_audit.get("range_status", {}).get("confirmation", "UNKNOWN")
        if (status == "UNUSED" and confirmation_state == "UNUSED"
                and seed_audit.get("status") == "PASS" and not confirmation):
            return "SCREEN PENDING — label-free feature build only"
        if status == "INCOMPLETE":
            return "SCREEN INTERRUPTED — single-use seed range consumed; do not rerun"
        return "SCREEN STATUS UNVERIFIED — inspect seed claim and evidence"
    if h31_stage_failed(screen, "screen"):
        return "FROZEN SCREEN FAILED — H31-1 rejected"
    if screen and confirmation:
        if h31_stage_passed(screen, "screen") and h31_stage_passed(confirmation, "confirmation"):
            return "SCREEN AND CONFIRMATION PASSED — catalogue proxy only; not slot-approved"
        return "CONFIRMATION FAILED OR UNVERIFIED — H31-1 rejected for submission"
    if h31_stage_passed(screen, "screen"):
        return "SCREEN PASSED — unchanged confirmation required; not slot-approved"
    return "STAGE STATUS UNVERIFIED — no weekly slot"


def render_hypothesis_card(h: dict, screen: dict, confirmation: dict, seed_audit: dict) -> str:
    lo_hi = h.get("expected_holdout_delta_dti", [None, None])
    if isinstance(lo_hi, list) and len(lo_hi) == 2:
        range_text = f"{fmt_number(lo_hi[0], 3)} to +{fmt_number(lo_hi[1], 3)}"
    else:
        range_text = "not stated"
    layer_tags = "".join(f"<li>{esc(layer)}</li>" for layer in h.get("layers", []))
    status = h.get("status", "UNTRIED")
    validation = h.get("validation", "not recorded")
    stage_links = ""
    if h.get("id") == "H31-1":
        status = h31_hypothesis_status(screen, confirmation, seed_audit)
        validation = f"{validation} Current stage: {h31_result_summary(screen, confirmation, seed_audit)}"
        stage_links = h31_evidence_links(screen, confirmation)
    return f"""<article class="card span-6"><div class="rank">Rank {esc(h.get('rank'))} · {esc(h.get('id'))}</div><h3>{esc(h.get('title'))}</h3><p><span class="status blocked">{esc(status)}</span></p>
<p><strong>Layers:</strong></p><ul class="tag-list">{layer_tags}</ul>
<p><strong>Physical signature:</strong> {esc(h.get('signature', 'not recorded'))}</p>
<p><strong>Why it might find faults missing from the catalogue:</strong> {esc(h.get('why_missing_faults', 'not recorded'))}</p>
<p><strong>Different from prior work:</strong> {esc(h.get('differs_from_repo', 'not recorded'))}</p>
<p><strong>Confounders:</strong> {esc(h.get('confounders', 'not recorded'))}</p>
<p><strong>Planning-only ΔDTI range:</strong> {esc(range_text)}. This is an uncertain prior, not an observed holdout result or leaderboard prediction.</p>
<p><strong>Cost:</strong> {esc(h.get('cost', 'not recorded'))}</p>
<p><strong>Data/access gate:</strong> {esc(h.get('data_gate', 'not recorded'))}</p>
<p><strong>Validation:</strong> {esc(validation)} {stage_links}</p></article>"""


def render_research(registry: dict, h28: dict, euler: dict, board: dict,
                    screen: dict, confirmation: dict, seed_audit: dict, h32: dict) -> str:
    hypotheses = sorted(registry.get("hypotheses", []), key=lambda item: item.get("rank", 999))
    hypothesis_html = "".join(render_hypothesis_card(h, screen, confirmation, seed_audit) for h in hypotheses)
    si0 = euler.get("structural_indices", {}).get("0", {})
    summary = si0.get("solution_summary", {})
    clusters = si0.get("lineament_cluster_stats", {})
    stability = euler.get("si_cluster_centroid_stability", {})
    h1 = stability.get("si1_vs_si0", {})
    h2 = stability.get("si2_vs_si0", {})
    candidate = h28.get("candidate", {})
    return f"""<div class="breadcrumb"><a href="index.html">Overview</a> / Research</div>
<section class="hero"><div class="hero-content"><div class="eyebrow">Hypotheses, evidence and preregistration</div><h1>Test the geology.<br>Respect the proxy.</h1>
<p class="lead">{len(hypotheses)} currently ranked untried geological hypotheses, reviewed against in-repository experiments and evidence. Planning ranges are subjective, uncertain catalogue-holdout priors—not observed gains or competition-score predictions.</p>
<div class="value-line"><span class="value-pill">Maximize P(Win)</span><span class="value-pill">Own the Outcome</span><span class="status proxy">PROXY ≠ COMPETITION</span></div></div></section>

<section class="section"><h2>Current ranking</h2><p>Ranking weighs expected catalogue-proxy gain, testability and cost. “Untried” refers to the proposed transform/holdout arm in this checkout, not a claim of global scientific novelty. H31-1 status: {esc(h31_result_summary(screen, confirmation, seed_audit))} {esc(h32_result_summary(h32))}</p><div class="grid">{hypothesis_html}</div></section>

<section class="section"><h2>H31-1: depth-labeled Euler source solutions, not gradient peaks</h2><div class="callout"><strong>State:</strong> protocol revision 2 is committed at 524bf27 before any classifier fit or holdout; the current label-free feature build is bound to it and passes all three pre-fit data-sufficiency checks. Earlier protocol commit hashes cited by prior working-copy artifacts are absent from this checkout's Git history; the initial build's commit chronology is not proven and is disclosed in the history audit. Magnetic field units remain unauthenticated. H31 current outcome: {esc(h31_result_summary(screen, confirmation, seed_audit))} No H31 submission candidate has been created. Local seed audit status {esc(seed_audit.get('status', 'not recorded'))} covers {comma(len(seed_audit.get('evidence_json_sha256_scanned', {})))} evidence JSON files; screen seeds 160–169 are {esc(seed_range_label(seed_audit, 'screen'))} by the failed H31-1 screen, and seeds 170–179 are {esc(seed_range_label(seed_audit, 'h32_1_screen'))} by the single H32-1 screen, so the H31-1 confirmation decade no longer exists. External/sibling-workspace seed use remains unknowable. {esc(h31_next_step(screen, confirmation, seed_audit))}</div>
<div class="grid"><article class="card span-6"><h3>What was built</h3><ul><li>Source field: owner-mirror band 14 <code>tmi</code>; embedded unit tags are absent.</li><li>Euler system solves for source coordinates, depth and base-level offset in 10 × 10 windows; source windows are screened and solutions clustered.</li><li>SI-0 primary: {comma(summary.get('n', 0))} accepted source solutions; {comma(clusters.get('aligned_solution_count', 0))} aligned to gradient ridges within 200 m; {comma(clusters.get('retained_cluster_count', 0))} retained depth-coherent clusters.</li><li>Median SI-0 depth {fmt_number(summary.get('depth_m_median'), 1)} m (P10 {fmt_number(summary.get('depth_m_p10'), 1)}, P90 {fmt_number(summary.get('depth_m_p90'), 1)}); output estimates are not verified geological depths.</li><li>Vertical-derivative coverage: {fmt_number(euler.get('derivative', {}).get('vertical_coverage_share_of_valid_field', 0) * 100, 1)}% of valid TMI cells.</li></ul></article>
<article class="card span-6"><h3>Structural-index instability</h3><p>SI-1 retains {comma(h1.get('sensitivity_clusters', 5665))} clusters; {fmt_number(h1.get('matched_primary_share_within_600m', 0)*100, 1)}% of SI-0 centroids match within 600 m and median nearest-centroid distance is {fmt_number(h1.get('median_nearest_centroid_distance_m', 0), 0)} m.</p><p>SI-2 retains {comma(h2.get('sensitivity_clusters', 4661))} clusters; {fmt_number(h2.get('matched_primary_share_within_600m', 0)*100, 1)}% match within 600 m and median distance is {fmt_number(h2.get('median_nearest_centroid_distance_m', 0), 0)} m. SI=1/2 are descriptive sensitivity checks, not alternative indices to select after seeing a favorable holdout.</p></article></div>
<p>SI=0 approximates an idealized contact with effectively infinite depth extent. Real faults may be finite, dipping, intersecting or have mixed geometry and may require higher indices. Euler does not estimate dip; the structural index is a geological model choice, not an automatically “correct” value. Candidate gradient ridges are used only to test alignment with Euler-derived source solutions, never as the inferred source locations.</p>
<p>Official USGS GeoDAWN metadata reports nominal magnetic flight-line spacing of 200 m in Area 1 and 400 m in Area 2, with variable terrain clearance. The 100 m output grid is not independent 100 m survey resolution. The exact pinned mirror is not organizer-authenticated, and derivative units/conventions have not been calibrated against survey units.</p>
<p><a href="../knowledge/12_preregistration_H31-1_euler.md">Frozen H31-1 protocol</a> · <a href="../evidence/euler_input_audit.json">Input/convention audit</a> · <a href="../evidence/h31_1_euler_feature_audit.json">Label-free feature/depth audit</a> · <a href="../evidence/h31_1_prereg_history_audit.json">Protocol-history disclosure</a> · <a href="../evidence/h31_1_seed_reuse_audit.json">Local seed-reuse audit</a> · <a href="../evidence/h31_1_euler_clusters.csv">Depth-labeled cluster table</a> · {h31_evidence_links(screen, confirmation)} · <a href="https://doi.org/10.1190/1.1442774">Reid et al. (1990), DOI</a></p></section>

<section class="section"><h2>H32-1: structural-step coherence of depth-to-base, conductivity and strain derivatives</h2><div class="callout"><strong>State:</strong> one preregistered screen ran on seeds 170–179 with the frozen protocol bytes matching the committed blob. {esc(h32_result_summary(h32))} Six deterministic label-free derivative features (robust-scaled |∇| at 300 m/1 km, Laplacian curvature, both-strong concordance and |cos| orientation agreement between conductivity-base and depth gradients, and a strain step) were appended to the unchanged 38-column H28-1/T-v2/r1 control. The candidate cache is SHA-256-pinned in the evidence record; no candidate TIFF exists. Per the preregistration no retuning, rerun or confirmation is permitted on these seeds; the next new hypothesis needs a fresh decade (180–189).</div>
<p><a href="../knowledge/14_preregistration_H32-1.md">Frozen H32-1 protocol</a> · <a href="../knowledge/15_h32_1_result.md">H32-1 result record</a> · <a href="../evidence/h32_1_structural_step_holdout.json">Screen evidence JSON</a> · <a href="../evidence/h31_1_seed_reuse_audit.json">Local seed-reuse audit</a> · <a href="../src/gems27/structural_step.py">Feature transform source</a></p></section>

<section class="section"><h2>H28-1 benchmark and candidate file</h2><p>The paired hide-and-recover screen compared H28-1 multiscale magnetic/gravity edge-coherence features against the best comparable same-run control, across spatially blocked folds and seeds 140–149. The mean paired catalogue proxy ΔDTI was {fmt_number(candidate.get('holdout_mean_gain', 0.002948838794400959), 6)}, with 3/4 folds and 9/10 seed means positive; the frozen screen gate passed. This is not a leaderboard score and does not establish transfer to expert-created faults outside the catalogue habitat.</p><p>Candidate filename: <code>{esc(candidate.get('nan', ''))}</code>. Its full-map construction is separate from the holdout-only fit and no current GEMSDOE28 upload exists. It is not one of the four weekly slots inherited from the predecessor project. The file is an auditable research reference, not a submission recommendation.</p><p>Local manual downloads: <a href="downloads/{esc(candidate.get('nan', ''))}" download>{esc(candidate.get('nan', ''))}</a> · <a href="downloads/{esc(candidate.get('allfinite', ''))}" download>{esc(candidate.get('allfinite', ''))}</a> · <a href="downloads/{esc(candidate.get('zip', ''))}" download>{esc(candidate.get('zip', ''))}</a>.</p><p><a href="../evidence/h28_1_edge_holdout.json">Holdout evidence</a> · <a href="../knowledge/08_preregistration_H28-1.md">H28-1 preregistration</a> · <a href="../knowledge/09_preregistration_H28-1_candidate.md">Full-map candidate construction record</a></p>
<p>Historical hypothesis register: <a href="../knowledge/07_untried_hypotheses.md">knowledge/07_untried_hypotheses.md</a>. Historical H28 preregistration: <a href="../knowledge/08_preregistration_H28-1.md">knowledge/08_preregistration_H28-1.md</a>. Current hypothesis ranking: <a href="../knowledge/13_current_ranked_hypotheses_2026-10-03.md">knowledge/13_current_ranked_hypotheses_2026-10-03.md</a>.</p></section>

<section class="section"><h2>Promotion gate and what counts</h2><div class="table-wrap"><table><thead><tr><th>Stage</th><th>Required evidence</th><th>What it is not</th></tr></thead><tbody>
<tr><td>Pre-fit</td><td>Freeze transform, data and provenance, folds/draws, response, model, metrics, seeds, analysis and gate; run label-free sufficiency only.</td><td>Not permission to tune thresholds on a held-out seed.</td></tr>
<tr><td>Screen</td><td>Paired spatial hide-and-recover against the best same-run control; frozen gate on all seeds/folds and integrity checks.</td><td>Not a public/private leaderboard result.</td></tr>
<tr><td>Confirmation</td><td>One unchanged independent seed range and exact code/data/evidence hashes.</td><td>Not a second chance to adjust the candidate.</td></tr>
<tr><td>Promotion</td><td>Reproducible superiority, confirmation, separate proxy-transfer assessment and exact-file audit.</td><td>Not automatic approval to consume a weekly slot.</td></tr>
</tbody></table></div><p>A candidate must not spend a weekly slot until every predeclared gate is met. The catalogue hide-and-recover task is necessarily a proxy: labels are mostly faults already represented in a published catalogue and do not provide an independent sample of hidden expert-created, far-field faults.</p></section>

<section class="section"><h2>Live score and leaderboard boundaries</h2><p>A one-off manual public-page observation on {esc(board.get('snapshot_date', 'not recorded'))} records DARD #1 at 0.3195 and wbg1 #15 at 0.2600. A public leaderboard row alone does not link a score to the repository owner or a local TIFF. The owner-reported 0.2477 is likewise unverified without an organizer receipt. No row is treated as a score claim for this project. <a href="{esc(board.get('url', 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'))}">Manual-review link</a>; automated access and monitoring are prohibited by project policy.</p></section>
<section class="section"><h2>Historical screen archive (superseded)</h2><div class="callout"><strong>Archive marker:</strong> the predecessor project used the heading “Current Session 5 untried screen (4 hypotheses).” That was a dated four-item view; the current GEMSDOE28 ranking above also contains four untried hypotheses and is maintained separately.</div>
<h3>H27-10 annulus result — REJECTED; no weekly slot.</h3><p>The frozen 100–300 m annulus/reallocation gate on seeds 150–159 failed: mean paired ΔDTI +0.000846, 4/4 fold means but only 7/10 seed means improved, and annulus gross efficiency 0.03357 was below the 0.05212 live break-even estimate. A spacing-check bug in the first diagnostic was corrected for an integrity rerun on the same seeds; values and the frozen FAIL did not change. This is not fresh confirmation.</p><p>Evidence: <a href="../evidence/h27_10_annulus_holdout_initial.json">h27_10_annulus_holdout_initial.json</a> · <a href="../evidence/h27_10_annulus_holdout.json">corrected integrity rerun</a> · <a href="../knowledge/07_untried_hypotheses.md">historical disclosure</a>. The rejected H27-10 arm is not part of the current four-item untried list and is not eligible to justify a weekly slot.</p></section>
"""


def render_topology(manifest: dict, irregularities: dict, sources: dict, review: dict) -> str:
    selected = manifest.get("primary", {})
    count = int(review.get("candidate_count", 345))
    priority = int(review.get("priority_candidate_count", 81))
    counts = review.get("counts_by_exclusive_review_class", {})
    same_fid = int(counts.get("same-FID_multipart-continuity", 230))
    same_name = int(counts.get("H27-5b_inter-FID_same-name-kinematic-compatible", 81))
    other_name = int(counts.get("inter-FID_other-name_kinematic-compatible", 22))
    conflict = int(counts.get("inter-FID_kinematic-conflict-or-unknown", 12))
    priority_csv = review.get("files", {}).get("priority_csv", "docs/data/topology_priority_h27_5b.csv")
    priority_geojson = review.get("files", {}).get("priority_geojson", "docs/data/topology_priority_h27_5b.geojson")
    priority_csv_page = priority_csv.removeprefix("docs/")
    priority_geojson_page = priority_geojson.removeprefix("docs/")
    preview = "assets/fig_map_h27_5b_priority.png"
    official = review.get("official_sources", {})
    basis = review.get("priority_basis", {})
    return f"""<div class="breadcrumb"><a href="index.html">Overview</a> / Topology review</div>
<section class="hero"><div class="hero-content"><div class="eyebrow">Prior research · continuity, not automatic interpolation</div><h1>Map structures.<br>Do not bridge blindly.</h1><p class="lead">The topology work is retained as a comparator and a geologist-review queue. Fault-link candidates are local geological hypotheses, not facts about subsurface continuity.</p><div class="value-line"><span class="value-pill">Maximize P(Win)</span><span class="value-pill">Own the Outcome</span><span class="status proxy">REVIEW ONLY</span></div></div></section>
<section class="section"><h2>What the earlier tests found</h2><div class="grid">
<article class="card span-6"><h3>Topology gate</h3><p>Earlier in-repository T-v2 candidate arms proposed 1–4 km connections between named/categorized fault traces with structural and spatial controls. The historical catalogue-component and whole-feature hide-and-recover metrics are proxy results; they do not demonstrate a connection at a particular hidden fault or transfer to the competition's expert labels.</p><p>Every link is an explicit, reviewable geologic claim, with endpoint attributes, spacing, orientation, kinematic compatibility, third-system proximity, alternative interpretations and limitations. A graph must not bridge broad basins merely because an algorithm finds nearby endpoints.</p><p><a href="../knowledge/03_preregistration_topology_gate.md">Frozen historical topology gate</a> · <a href="../knowledge/04_topology_graph_argument.md">Topology/graph rationale</a> · <a href="../evidence/vector_topology_validation.json">Vector topology evidence</a></p></article>
<article class="card span-6"><h3>Current file is not a graph-proof</h3><p>The prominent file is {esc(selected.get('hypothesis', 'an H28-1 research reference'))}. It contains a historical T-v2 component among other transformations, but its holdout evidence is for a paired catalogue proxy. The primary download is <strong>UNSCORED</strong>, and no GEMSDOE28 score or submission receipt is recorded.</p><p><code class="file-name">{esc(selected.get('nan', ''))}</code></p><p><a href="index.html#download">Return to the one-click download and exact note</a></p></article>
</div></section>
<section class="section"><h2>H27-5b geologist-review queue</h2>
<div class="callout"><strong>Geologist-review priority class: H27-5b ({priority} / {count} links)</strong><br>These are the {priority} same-name, cross-FID, permissively kinematic-compatible links drawn from the existing 345 shipped T-v2 links. All 345 have a 1–4 km gap. This is a review-priority class, not a prediction rank, new candidate generation, validated subsurface connection, score, or proof of transfer.</div>
<p>Exclusive review-class counts for the existing population: {same_fid} same-FID · {same_name} H27-5b · {other_name} other-name compatible · {conflict} conflict/unknown. The H27-5b class is defined by different NBMG FID, same non-unnamed NAME, and a permissive kinematic-compatibility screen. Blank/unspecified source attributes may pass; compatibility is not a verified slip history.</p>
<figure class="card"><img src="{preview}" alt="Map-view schematic of 81 H27-5b endpoint connector segments. Fault traces are not plotted; connectors are for geologist review only." style="width:100%;height:auto;border-radius:10px"><figcaption class="small">Connector-only map-view schematic. It does not plot the catalogue fault traces and does not establish geological continuity. Review endpoints in the official NBMG layer.</figcaption></figure>
<p>Download the sorted, source-linked review rows: <a href="{esc(priority_csv_page)}">{esc(priority_csv_page)}</a> · <a href="{esc(priority_geojson_page)}">{esc(priority_geojson_page)}</a> · <a href="{preview}">{preview}</a>.</p>
<div class="table-wrap"><table><thead><tr><th>review class</th><th>Count</th><th>Interpretation / boundary</th></tr></thead><tbody>
<tr><td>same-FID multipart continuity</td><td>{same_fid}</td><td>Records share an NBMG FID; not an independent survey.</td></tr>
<tr><td>H27-5b inter-FID, same-name, compatible</td><td>{same_name}</td><td>Priority for map review only; source attributes and line geometry need geologist review.</td></tr>
<tr><td>inter-FID other-name compatible</td><td>{other_name}</td><td>Not prioritized by same-name rule.</td></tr>
<tr><td>inter-FID conflict or unknown</td><td>{conflict}</td><td>Kinematic conflict or uncertain fields; not removed from catalogue or deemed invalid.</td></tr>
</tbody></table></div>
<p>Whole-FID holdout context (seeds 120–129): H27-5b catalogue-proxy efficiency {fmt_number(basis.get('h27_5b_efficiency'), 6)} versus rotated-control {fmt_number(basis.get('rotated_control_efficiency'), 6)} ({fmt_number(basis.get('enrichment_over_control'), 2)}×). This is internal holdout enrichment only, not a score or proof of transfer; the candidate review class was not selected by graph ΔP.</p>
<p>Manual source links: <a href="{esc(official.get('nbmg_qfaults_layer', 'https://web2.nbmg.unr.edu/arcgis/rest/services/Qfaults/Qfaults_INGENIOUS/MapServer/0'))}" target="_blank" rel="noopener noreferrer">NBMG Qfaults official layer</a> · <a href="{esc(official.get('faulds_hinz_2015_context', 'https://www.osti.gov/servlets/purl/1724082'))}" target="_blank" rel="noopener noreferrer">Faulds &amp; Hinz (2015) setting context</a> · <a href="{esc(official.get('berkowitz_2000_publisher', 'https://agupubs.onlinelibrary.wiley.com/doi/10.1029/1999GL011241'))}" target="_blank" rel="noopener noreferrer">Berkowitz et al. (2000) publisher record</a>.</p>
</section>
<section class="section"><h2>How to review a proposed connection</h2><ol><li>Verify source geometry and official vector attribute definitions rather than relying on raster connectivity alone.</li><li>Record endpoint spacing, orientation/kinematic compatibility, mapped-name relationship, third-system proximity and alternative interpretations.</li><li>Compare against spatially blocked controls that preserve the same density, length scale and data-quality context.</li><li>Freeze candidate generation and scoring before the holdout. Use an independent confirmation seed set unchanged.</li><li>Separate catalogue hide-and-recover performance from live competition performance and local-file audit.</li></ol></section>
<section class="section"><div class="callout"><strong>Do not revive refuted signals:</strong> the graph-ΔP ranking and overlapping en-echelon step-over test were refuted as holdout-improvement signals in Addendum D. An individual “tip-to-tip oblique” cue is not evidence of an overlapping step-over, a favorable relay, or a productive geothermal setting. H27-5b is a geologist-review label, not a way to re-rank by graph value.</div>
<div class="callout"><strong>Geologic caution:</strong> the Qfaults catalogue primarily documents Quaternary surface-deformation evidence. Older bedrock faults, concealed structures, faults without mapped surficial expression and hydrothermal pathways can be absent for different reasons. The prior H27-10 100–300 m annulus screen failed its frozen gate; its spacing-check implementation was repaired only for deterministic integrity rerun, not for confirmatory evidence. See <a href="../evidence/h27_10_annulus_holdout.json">the preserved gate record</a> and <a href="../knowledge/07_untried_hypotheses.md">historical disclosure</a>.</div></section>
<section class="section"><h2>Evidence and provenance</h2><p>The source ledger distinguishes official publication from owner-mirror bytes. A GDR or ScienceBase listing is not evidence that a package was downloaded, parsed, covered the study area, or carried a compatible licence. <a href="sources.html">Review source-by-source access and verification status</a>.</p><p>Known repository irregularities: {sum(1 for x in irregularities.get('items', []))} disclosures in <a href="../registry/irregularities.json">the irregularities ledger</a>. Full existing candidate output: <a href="data/topology_links.csv">docs/data/topology_links.csv</a> · <a href="data/topology_links.geojson">docs/data/topology_links.geojson</a> · priority-class summary <a href="data/topology_review_classes.json">docs/data/topology_review_classes.json</a>.</p></section>
"""

def render_sources(sources_registry: dict, board: dict) -> str:
    sources = sources_registry.get("sources", [])
    items = []
    for source in sources:
        url = source.get("url", "")
        title = source.get("title", source.get("id", "Source"))
        status = source.get("status", "not verified")
        items.append(f"""<article class="source-row" id="{esc(source.get('id', 'source'))}">
<h3><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(title)}</a></h3>
<p class="source-meta">{esc(source.get('publisher', ''))} · {esc(source.get('category', ''))} · accessed {esc(source.get('accessed', 'date not recorded'))}</p>
<p><strong>Verification status:</strong> {esc(status)}</p>
<p><strong>Use:</strong> {esc(source.get('used_for', 'not stated'))}</p>
<p><strong>Evidence/limitation:</strong> {esc(source.get('evidence', 'No evidence note recorded.'))}</p>
</article>""")
    return f"""<div class="breadcrumb"><a href="index.html">Overview</a> / Sources</div>
<section class="hero"><div class="hero-content"><div class="eyebrow">Manual source review ledger</div><h1>Claims tied<br>to their sources.</h1><p class="lead">Each entry says what was reviewed, how it was accessed, and what remains unknown. A repository mirror or catalog listing does not establish official byte identity, schema, coverage, downloadability, or licence.</p><div class="value-line"><span class="value-pill">Primary/official first</span><span class="value-pill">No invented provenance</span><span class="status blocked">NO DD AUTOMATION</span></div></div></section>
<section class="section"><div class="callout"><strong>Competition-page policy:</strong> no automated DrivenData fetch, browser bot, API, scraping, upload, scheduled job or monitoring. The leaderboard snapshot dated {esc(board.get('snapshot_date', 'not recorded'))} was read once manually. <a href="{esc(board.get('url', 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'))}">Manual human-review link</a>. Public scores shown there are not linked to the repository owner or local files.</div>
<p>Registry note: {esc(sources_registry.get('note', 'Verification status varies by source.'))}</p>
<p>The site generator reads the local JSON registry only; it makes no external request. The separately invoked <code>scripts/refresh_source_feed.py</code> has an explicit forbidden-host guard for <code>drivendata.org</code> and is not part of site build or CI.</p>
</section>
<section class="section"><h2>{len(sources)} registered source records</h2>{''.join(items)}
<p><a href="../registry/sources.json">Download the machine-readable source ledger</a> · <a href="../registry/irregularities.json">Review disclosed irregularities</a> · <a href="../registry/data_manifest.json">Review input hashes and provenance labels</a>.</p></section>
"""


def root_relative_links(page: str) -> str:
    """Rebase docs-relative internal URLs for the repository-root convenience page."""
    def replace(match: re.Match[str]) -> str:
        attr, url = match.group(1), match.group(2)
        if url.startswith(("https://", "http://", "mailto:", "#", "data:")):
            return match.group(0)
        if url.startswith("../"):
            return attr + url[3:]
        return attr + "docs/" + url
    return re.sub(r'((?:href|src)=")([^"]+)', replace, page)


def main() -> int:
    manifest = read_json("docs/downloads/manifest.json")
    board = read_json("registry/leaderboard_snapshot_2026-10-03.json")
    hypotheses = read_json("registry/next_hypotheses.json")
    sources = read_json("registry/sources.json")
    irregularities = read_json("registry/irregularities.json")
    euler = read_json("evidence/h31_1_euler_feature_audit.json", {})
    screen = read_json("evidence/h31_1_euler_screen.json", {})
    confirmation = read_json("evidence/h31_1_euler_confirm.json", {})
    seed_audit = read_json("evidence/h31_1_seed_reuse_audit.json", {})
    h32 = read_json("evidence/h32_1_structural_step_holdout.json", {})
    range_audit = read_json("evidence/range_validator_forensics_2026-10-03.json", {})
    restore = read_json("evidence/restore_audit.json", {})
    file_audit = read_json("evidence/submission_file_audit.json", {})
    h28_manifest = read_json("docs/downloads/h28_1_candidate_manifest.json", {"candidate": {}})

    topology_review = read_json("docs/data/topology_review_classes.json", {})
    pages = {
        "index.html": layout("Overview", render_index(manifest, board, euler, range_audit, restore, screen, confirmation, seed_audit, h32), "Overview"),
        "executive-summary.html": layout("Executive summary", render_executive(manifest, board, file_audit, range_audit, screen, confirmation, seed_audit, h32), "Executive summary"),
        "research.html": layout("Research and hypotheses", render_research(hypotheses, h28_manifest, euler, board, screen, confirmation, seed_audit, h32), "Research"),
        "topology.html": layout("Topology review", render_topology(manifest, irregularities, sources, topology_review), "Topology"),
        "sources.html": layout("Sources and verification", render_sources(sources, board), "Sources"),
    }
    DOCS.mkdir(parents=True, exist_ok=True)
    for name, content in pages.items():
        (DOCS / name).write_text(publish_source_links(content), encoding="utf-8")
    (ROOT / "index.html").write_text(root_relative_links(pages["index.html"]), encoding="utf-8")
    print(json.dumps({"status": "built", "pages": sorted(pages), "sources": len(sources.get("sources", [])),
                      "hypotheses": len(hypotheses.get("hypotheses", [])),
                      "generated_from_json_only": True, "external_requests": 0,
                      "primary_download": manifest["primary"]["nan"]}, indent=2))
    return 0


if __name__ == "__main__":
    import json
    raise SystemExit(main())
