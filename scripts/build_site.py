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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def h38_claim_fingerprint(claim: dict) -> str:
    immutable_keys = (
        "schema", "arm_name", "seeds", "reserved_utc", "protocol_commit", "protocol_branch",
        "preregistration", "preregistration_sha256", "candidate_csv", "candidate_csv_sha256",
        "candidate_count", "sufficiency_audit", "sufficiency_audit_sha256", "pre_run_seed_audit",
        "input_sha256", "code_sha256", "runtime_versions", "baseline", "result_paths",
    )
    stable = {key: claim.get(key) for key in immutable_keys}
    return hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def h38_result_integrity(report: dict, claim: dict) -> bool:
    if not isinstance(report, dict) or not isinstance(claim, dict):
        return False
    required_maps = (
        report.get("raw_result"), report.get("candidate"), report.get("benchmark"),
        report.get("gates"), report.get("code_sha256"), report.get("source_records"),
        report.get("preregistration"), report.get("summary"), claim.get("result_paths"),
        claim.get("baseline"), claim.get("code_sha256"),
    )
    if not all(isinstance(value, dict) for value in required_maps):
        return False
    check = dict(report)
    recorded = check.get("sha256")
    check["sha256"] = None
    expected = hashlib.sha256(json.dumps(check, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    raw_info = report.get("raw_result", {})
    candidate = report.get("candidate", {})
    benchmark = report.get("benchmark", {})
    expected_gates = {
        "C1_positive_and_spatially_repeatable", "C2_live_economic_bar",
        "C3_candidate_beats_matched_random", "C4_support_and_integrity",
        "C5_beats_previous_farfield_add_arm_best",
    }
    gates = report.get("gates", {})
    all_gates_pass = (
        set(gates) == expected_gates
        and all(isinstance(value, dict) and type(value.get("passed")) is bool for value in gates.values())
        and all(value.get("passed") is True for value in gates.values())
    )
    raw_rel = raw_info.get("path")
    summary_rel = "evidence/h38_1_holdout.json"
    if (not isinstance(raw_rel, str) or Path(raw_rel).is_absolute()
            or ".." in Path(raw_rel).parts):
        return False
    raw_path = (ROOT / raw_rel).resolve()
    summary_path = (ROOT / summary_rel).resolve()
    if not raw_path.is_relative_to(ROOT.resolve()) or not summary_path.is_relative_to(ROOT.resolve()):
        return False
    try:
        raw_hash = sha256_file(raw_path)
        summary_hash = sha256_file(summary_path)
    except (OSError, ValueError):
        return False
    raw_code = report.get("code_sha256", {}).get("runner_recorded", {})
    expected_code = claim.get("code_sha256", {})
    if not isinstance(raw_code, dict) or not isinstance(expected_code, dict):
        return False
    runner_code_paths = {
        "runner": "scripts/run_losfo_harness.py",
        "losfo": "src/gems27/losfo.py",
        "oof_detector": "src/gems27/oof_detector.py",
        "metric": "src/gems27/metric.py",
        "thinning": "src/gems27/thinning.py",
        "holdout": "src/gems27/holdout.py",
        "grid": "src/gems27/grid.py",
        "paths": "src/gems27/paths.py",
        "packing": "src/gems27/packing.py",
    }
    runner_code_matches = all(raw_code.get(key) == expected_code.get(path) for key, path in runner_code_paths.items())
    recorded_code_matches_claim = all(report.get("code_sha256", {}).get(path) == digest for path, digest in expected_code.items())
    return bool(
        recorded == expected
        and report.get("schema") == 1
        and report.get("seeds") == list(range(265, 270))
        and report.get("folds") == ["NW", "NE_LidarGapHeavy", "SW", "SE"]
        and report.get("protocol_freeze_commit") == claim.get("protocol_commit")
        and report.get("reservation_commit") == claim.get("run_commit")
        and claim.get("protocol_branch") == "arena/01a10412-gemsdoe28"
        and claim.get("run_branch") == "arena/01a10412-gemsdoe28"
        and report.get("claim_fingerprint") == h38_claim_fingerprint(claim)
        and raw_info.get("path") == claim.get("result_paths", {}).get("raw")
        and raw_info.get("sha256") == raw_hash == claim.get("raw_result_sha256")
        and report.get("source_records", {}).get("candidate_sufficiency") == claim.get("sufficiency_audit")
        and report.get("source_records", {}).get("baseline") == claim.get("baseline", {}).get("path")
        and candidate.get("csv") == claim.get("candidate_csv")
        and candidate.get("csv_sha256") == claim.get("candidate_csv_sha256")
        and candidate.get("count") == claim.get("candidate_count") == 140
        and candidate.get("sufficiency_audit_sha256") == claim.get("sufficiency_audit_sha256")
        and benchmark.get("sha256") == claim.get("baseline", {}).get("sha256")
        and report.get("runtime_versions") == claim.get("runtime_versions")
        and runner_code_matches
        and recorded_code_matches_claim
        and report.get("preregistration", {}).get("path") == claim.get("preregistration")
        and report.get("preregistration", {}).get("sha256") == claim.get("preregistration_sha256")
        and claim.get("status") == "CONSUMED"
        and claim.get("seed_range_burned") is True
        and claim.get("holdout_started") is True
        and claim.get("submission_slot_used") is False
        and claim.get("summary_result_path") == summary_rel
        and claim.get("result_paths", {}).get("summary") == summary_rel
        and claim.get("summary_result_sha256") == summary_hash
        and claim.get("promotable") is report.get("promotable")
        and report.get("promotable") is all_gates_pass
        and report.get("status") == ("PASS" if report.get("promotable") else "FAIL")
    )


def h38_status_html(report: dict, claim: dict) -> str:
    if h38_result_integrity(report, claim):
        summary = report.get("summary", {})
        gate_names = {
            "C1_positive_and_spatially_repeatable": "C1 repeatability",
            "C2_live_economic_bar": "C2 live-value bar",
            "C3_candidate_beats_matched_random": "C3 matched random",
            "C4_support_and_integrity": "C4 support/integrity",
            "C5_beats_previous_farfield_add_arm_best": "C5 prior far-field best",
        }
        gate_items = " · ".join(
            f"{gate_names[key]}: {'PASS' if report['gates'][key]['passed'] else 'FAIL'}"
            for key in gate_names
        )
        next_step = (
            "Only a separate fresh-seed confirmation and exact-file review may follow; no weekly slot is authorized."
            if report.get("promotable") else
            "The frozen arm is closed; no confirmation, retuning, candidate TIFF, upload, or weekly slot is authorized."
        )
        return (
            f"<strong>H38-1 frozen LOSFO gate {esc(report.get('status'))}</strong> "
            f"(mean ΔDTI {fmt_number(summary.get('mean_delta_dti_licence_vs_base'), 6)}, "
            f"credit/dot {fmt_number(summary.get('credit_per_added_dot'), 5)}, "
            f"{comma(summary.get('positive_cells'))}/20 positive cells; "
            f"{comma(summary.get('positive_seed_means'))}/5 seed means and "
            f"{comma(summary.get('positive_fold_means'))}/4 fold means positive). "
            f"{esc(gate_items)}. This is an internal mapped-system proxy, not an organizer score. {esc(next_step)} "
            "See <a href=\"../evidence/h38_1_holdout.json\">frozen-gate evidence</a>, "
            "<a href=\"../evidence/losfo_h38_1_raw.json\">raw run</a>, and "
            "<a href=\"../evidence/h38_1_holdout.started.json\">single-use claim</a>."
        )
    status = claim.get("status") if isinstance(claim, dict) else None
    if status in {"RESERVED", "RUNNING", "FAILED", "CONSUMED"}:
        explanations = {
            "RESERVED": "The local claim is reserved, but the holdout has not started.",
            "RUNNING": "The holdout is in progress; seeds 265–269 are burned even if execution fails.",
            "FAILED": "Execution or analysis failed after the holdout started; no frozen-gate decision is available, and seeds 265–269 are burned and must not be rerun.",
            "CONSUMED": "A consumed claim exists, but the summary/result integrity checks do not pass; treat the outcome as unverified.",
        }
        claim_link = (
            'Inspect the <a href="../evidence/h38_1_holdout.started.json">single-use claim</a>'
            if (ROOT / "evidence" / "h38_1_holdout.started.json").is_file() else
            "The claim file is missing"
        )
        audit_link = (
            ' and <a href="../evidence/h38_1_seed_audit_pre_run.json">local seed audit</a>'
            if (ROOT / "evidence" / "h38_1_seed_audit_pre_run.json").is_file() else
            "; the local seed audit file is missing"
        )
        raw_link = (
            ' · <a href="../evidence/losfo_h38_1_raw.json">raw run (unverified; no gate summary)</a>'
            if status == "FAILED" and (ROOT / "evidence" / "losfo_h38_1_raw.json").is_file() else ""
        )
        failure_detail = claim.get("failure_detail") if status == "FAILED" else None
        failure_note = f" Failure detail: {esc(failure_detail)}" if failure_detail else ""
        return (
            f"<strong>H38-1 claim state: {esc(status)}.</strong> {esc(explanations[status])} "
            "The 140 candidate centroids come from a label-free support screen only, not validation. "
            f"{failure_note} {claim_link}{audit_link}{raw_link}; this is not an organizer score."
        )
    if report:
        return (
            "<strong>An H38-1 holdout report artifact exists but its consumed-claim/hash chain is missing or invalid.</strong> "
            "Treat it as unverified; it is not a promotion result or organizer score. "
            "See the <a href=\"../evidence/h38_1_holdout.json\">report artifact</a>."
        )
    return (
        "<strong>H38-1 is a label-free support screen only (140 candidate centroids): no seed claim, "
        "holdout, or promotion result is recorded.</strong>"
    )


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
        links.append(f'<a class="button secondary" href="{prefix}{esc(item["allfinite"])}" download>All-finite, zero-outside variant</a>')
    return '<div class="download-actions">' + "".join(links) + "</div>"


def mirror_line(item: dict) -> str:
    """A download route that does not depend on GitHub Pages being healthy."""
    raw = f"https://github.com/buffedlizard55-lab/GEMSDOE28/raw/main/docs/downloads/{item['nan']}"
    return (
        '<p class="meta"><strong>GitHub Pages fallback:</strong> if the button above returns a stale '
        'page or an error, this direct file route from the repository downloads the identical '
        f'bytes &mdash; <a href="{esc(raw)}" download>raw mirror of {esc(item["nan"])}</a> '
        "(the SHA-256 printed below is the check).</p>"
    )


def candidate_card(slot: str, item: dict, *, featured: bool = False) -> str:
    title = item.get("hypothesis", item.get("slug", slot))
    status = item.get("status", "UNSCORED research artifact")
    far = item.get("note_far_field")
    far_html = f'<p class="callout"><strong>Far-field test:</strong> {esc(far)}</p>' if far else ""
    css = "card span-12" if featured else "card span-6"
    return f"""<article class="{css}">
  <div class="rank">{esc(slot)} · {esc(item.get('content_id', 'no id'))}</div>
  <h3>{esc(title)}</h3><p><span class="status unscored">UNSCORED</span></p>
  <p>{esc(status)}</p>
  <p><strong>Suggested unique portal name (only if later approved):</strong><br><code class="file-name">{esc(item.get('submission_name', 'not recorded'))}</code></p>
  {far_html}
  {file_links(item)}
  <p><strong>NaN GeoTIFF:</strong> <code class="file-name">{esc(item['nan'])}</code></p>
  <p class="meta">SHA-256 <code>{esc(item.get('sha256_nan', 'not recorded'))}</code> · {esc(item.get('bytes_nan', 'n/a'))} bytes · {esc(item.get('emitted_px', 'n/a'))} positive cells</p>
  <p><strong>Manual note ({len(str(item.get('note', '')))} / 200 characters):</strong></p>{note_box(str(item.get('note', '')))}
</article>"""


def render_index(manifest: dict, board: dict, euler: dict, range_audit: dict, restore: dict,
                 screen: dict, confirmation: dict, seed_audit: dict, h32: dict,
                 h35: dict = None, h35_6: dict = None,
                 h38_result: dict = None, h38_claim: dict = None) -> str:
    primary = manifest["primary"]
    q = manifest.get("quaternary", {})
    h35 = h35 or {}
    h35_6 = h35_6 or {}
    # Everything the page says about the advertised file is read from the manifest, so the slot can be
    # re-pointed without leaving another file's numbers attached to it (that bug was found twice).
    _pe = str(primary.get("holdout_evidence", "evidence/h32_1_holdout.json"))
    primary_holdout_clause = (
        f"validated on a 4-fold spatially blocked holdout "
        f"(<a href=\"../{esc(_pe)}\">{esc(_pe)}</a>): <strong>{fmt_number(primary.get('holdout_mean_gain', 0), 6)}</strong> "
        f"mean &Delta;DTI, <strong>{esc(primary.get('holdout_seeds_improved', 'n/a'))}</strong> seeds and "
        f"<strong>{esc(primary.get('holdout_folds_improved', 'n/a'))}</strong> spatial folds improving over the "
        f"same-run <code>d=2.8</code> control"
    )
    primary_evidence_note = primary_holdout_clause + "."
    if primary.get("adjudication_evidence"):
        _ae = str(primary["adjudication_evidence"])
        primary_evidence_note += (
            f" It then won the frozen fresh-seed adjudication on seeds "
            f"{esc(str(primary.get('adjudication_seeds', '')))} "
            f"(<a href=\"../{esc(_ae)}\">{esc(_ae)}</a>), run with the frozen harness unmodified so the "
            f"decade is directly comparable, which is why it is the one-click file rather than the "
            f"preregistered H32-1 arm."
        )
    h35_g1 = h35.get("criteria", {}).get("G1_profitability", {}).get("observed", 0.0)
    # G1's `required` is a human-readable string; the numeric threshold is recorded separately.
    h35_tau = h35.get("auroc_context", {}).get("tau_live", 0.0)
    h35_ctrl = h35.get("summary", {}).get("control", {}).get("credit_per_added_dot", 0.0)
    _adj_v = h35_6.get("variants", {})
    _order = ["h32_1_post_d28", "h32_1_pre_d28", "h27_4_blind_r1_d28",
              "control_prune_protected_only_d28"]
    if _adj_v:
        _best = max(_order, key=lambda k: _adj_v.get(k, {}).get("mean_dti_gain", -9))
        _bv = _adj_v.get(_best, {})
        _ok = _bv.get("seeds_won", 0) >= 4 and _bv.get("folds_improved", 0) >= 3
        h35_6_index = (
            f"The adjudication ran on seeds {h35_6.get('seeds', [0])[0]}–{h35_6.get('seeds', [0])[-1]} "
            f"with the frozen runner unmodified: the best variant is {esc(_best)} at "
            f"{fmt_number(_bv.get('mean_dti_gain', 0), 6)} ({_bv.get('seeds_won', 0)}/"
            f"{_bv.get('n_seeds', 5)} seeds, {_bv.get('folds_improved', 0)}/4 folds), so the frozen promotion "
            f"rule {'IS met and the primary below is the promoted file' if _ok else 'is NOT met and the primary is unchanged'}."
        )
    else:
        h35_6_index = "The fresh-seed adjudication of the candidate ladder had not reported when this page was built."
    observations = board.get("observations", [])
    board_lines = "".join(
        f"<li>Public row: rank {esc(row.get('rank'))}, {esc(row.get('participant_label'))}, {fmt_number(row.get('public_score'))}.</li>"
        for row in observations
    )
    euler_ready = euler.get("status", "label-free transform only")
    range_claim = range_summary(range_audit)
    return f"""<section class="hero"><div class="hero-content">
  <div class="eyebrow">GEMS DOE · Great Basin · 2026</div>
  <h1>Evidence before<br>emission.</h1>
  <p class="lead">An auditable fault-mapping research workflow—not a submission bot. Only spatially validated ideas may approach a weekly slot.</p>
  <div class="value-line"><span class="value-pill">Maximize P(Win)</span><span class="value-pill">Own the Outcome</span><span class="status unscored">NO GEMSDOE28 SCORE</span></div>
  <p><strong>Current status (2026-10-03):</strong> the one-click H36-1 GeoTIFF below passed its recorded spatial holdout but remains <strong>unscored and not slot-approved</strong>. Its suggested unique name and ≤200-character note are shown with the file.</p>
</div></section>

<section class="download-panel" id="download" aria-labelledby="download-heading">
  <div class="eyebrow">Manual research download · no upload made</div>
  <h2 id="download-heading">One-click GeoTIFF — {esc(primary.get('hypothesis', 'H32-1 reference'))}</h2>
  <p><span class="status unscored">UNSCORED · RESEARCH ONLY · NOT SLOT-APPROVED</span></p>
  {file_links(primary)}
  {mirror_line(primary)}
  <p><strong>Suggested unique portal submission name (only if later approved):</strong><br><code class="file-name">{esc(primary.get('submission_name', 'not recorded'))}</code></p>
  <p><strong>Exact filename</strong></p><code class="file-name">{esc(primary['nan'])}</code>
  <p class="meta">SHA-256 <code>{esc(primary.get('sha256_nan', ''))}</code> · {esc(primary.get('bytes_nan'))} bytes · single-band float32 · {esc(primary.get('emitted_px'))} cells equal to 1 · CRS EPSG:32611 · 100 m grid · template footprint {comma(restore.get('grid', {}).get('footprint_pixels', 5167373))} cells.</p>
  <p><strong>Range and mask check:</strong> finite 0/1 predictions inside the footprint; NaN with a NaN nodata tag outside it. The all-finite alternative sets outside cells to zero and has no nodata tag, so its mask semantics differ; neither variant has portal-acceptance confirmation.</p>
  <p><strong>Exact short note ({len(str(primary.get('note', '')))} / 200 characters):</strong></p>
  {note_box(str(primary.get('note', '')))}
  <p class="small">{primary_evidence_note} Built on the owner-reported <strong>{fmt_number(primary.get('base_reference_live_score', 0.26), 4)}</strong> <code>d=2.8</code> base (<code>{esc(str(primary.get('base_reference_id', '')))}</code>) without T-v2 gap closure. This file is a research/reference artifact, not one of the four weekly slots inherited from the predecessor campaign.</p>
</section>

<section class="section" id="decision-context"><div class="eyebrow">Latest research decision</div><h2>Why the download is not slot-approved</h2>
  <p>H37-1 passed the interleaved gate (+0.007289) but tied the raster cascade in the LOSFO far-field test (−0.000037 ± 0.000832); its live projection was withdrawn. H37-3 Euler-only emission was better than same-count random but earned 0.031157 credit per dot, below the fixed 0.0548 live bar, and improved only 13/20 cells. H35-1 also fell below its live bar and its own random control ({fmt_number(h35_g1, 5)} vs {fmt_number(h35_ctrl, 5)} credit/dot; threshold {fmt_number(h35_tau, 5)}). {esc(h35_6_index)}</p>
  <p>{h38_status_html(h38_result or {}, h38_claim or {})} The H38-1 candidate conjunction is a shallow SI-0 Euler cluster near a strong gravity-gradient cell and in low valid LiDAR relief—not proof of faulting. See <a href="../knowledge/37_ranked_hypotheses_session14_2026-10-03.md">the ranked hypothesis record</a>, <a href="../knowledge/38_preregistration_H38-1.md">the frozen protocol</a>, and <a href="../knowledge/39_session14_closeout_2026-10-03.md">the single-use run close-out</a>.</p>
  <p>{esc(h31_result_summary(screen, confirmation, seed_audit))} {esc(h32_result_summary(h32))}</p>
</section>

<section class="section" id="score-context"><div class="eyebrow">Score context · repository analysis, not organizer verification</div><h2>Why the reported 0.2600 was strong—and what beating 0.3195 would require</h2>
  <p>Repository analysis attributes the owner-reported <strong>0.2600</strong> to an H19-5 scarp/geophysics ridge surface thinned to 44,090 dots at <code>d=2.8</code> (versus 60,069 at <code>d=1.5</code>). Under the official 300 m distance-weighted kernel, the approximately one-dimensional fault-trace layout retains more credit than uniform 2-D thinning predicts while removing redundant dots. The inversion estimates about 4,791 weighted true-positive pixels and 90.63% of the denser file's credit; those are calculations conditioned on the owner-reported score/raster association, not an independently authenticated organizer receipt.</p>
  <p>A one-off manual snapshot of the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">official public leaderboard</a> recorded <strong>0.3195</strong> at rank 1 (DARD); the public row does not establish owner identity or bind the score to a local GeoTIFF. Reaching that value at today's 44,090-dot budget would require roughly 1,151 more weighted-credit pixels (about 24%). It is mathematically plausible only through substantially better, high-specificity off-catalogue discoveries—not further pruning of the same ridge family. Current repository evidence does <strong>not</strong> show that any candidate can beat 0.3195, and no GEMSDOE28 artifact has an organizer score.</p>
  <p><a href="../knowledge/37_ranked_hypotheses_session14_2026-10-03.md">Read the ranked hypotheses and calculations →</a> · <a href="../knowledge/39_session14_closeout_2026-10-03.md">read the H38-1 close-out →</a></p>
</section>

<div class="callout"><strong>Manual-only boundary:</strong> no login, download, upload, scrape, poll, or monitoring of DrivenData occurs in this repository. Review the official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a> and <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules</a> yourself before deciding whether to submit. The current file is not slot-approved; a local audit does not guarantee portal acceptance.</div>

<section class="section"><div class="grid">
  <article class="card span-4"><div class="metric">+0.00729</div><div class="metric-caption">H37-1 paired mean OOF ΔDTI · seeds 250–259</div><p>Metric-aware packing (greedy maximum expected coverage of the detector field under the official 300 m kernel) at a matched dot count: 10/10 seeds, 4/4 folds, +0.004614 over the H36-1 incumbent; the content-blind matched-N control scored &minus;0.044684 (0/10 seeds, 0/4 folds), so the gain is placement, not budget.</p><p><strong>Far-field test: F1 FAILED.</strong> Under LOSFO (seeds 210&ndash;214) the rule ties the raster cascade (&minus;0.000037, 95% interval &plusmn;0.000832, 9/20 cells): the interleaved gain is catalogue-adjacency, and the projection is withdrawn. Demoted by the preregistered rule; H36-1 is the primary again.</p><a href="../evidence/h37_1_holdout.json">Open H37-1 gate evidence →</a> · <a href="../knowledge/29_preregistration_H37-1.md">preregistration →</a></article>
  <article class="card span-4"><div class="metric">+0.00127</div><div class="metric-caption">H32-1 paired mean OOF ΔDTI · seeds 180–189</div><p>10/10 seeds and 4/4 spatial folds improved on the <code>d=2.8</code> operating point (+0.00140 pre-thinning). Protected tip &amp; SI-0 Euler depth-cluster pixels have 2.29× higher credit density than mid-segment flank shadow.</p><a href="../evidence/h32_1_holdout.json">Open H32-1 holdout evidence →</a></article>
  <article class="card span-4"><div class="metric">+{fmt_number(0.002948838794400959, 5)}</div><div class="metric-caption">H28-1 paired mean proxy ΔDTI · seeds 140–149</div><p>3/4 spatial folds and 9/10 seeds improved. A proxy result—not a competition result.</p><a href="../evidence/h28_1_edge_holdout.json">Open paired holdout evidence →</a></article>
  <article class="card span-4"><div class="metric">{comma(euler.get('structural_indices', {}).get('0', {}).get('lineament_cluster_stats', {}).get('retained_cluster_count', 6309))}</div><div class="metric-caption">SI-0 Euler depth-labeled clusters in label-free build</div><p>{esc(euler_ready)}. The feature build is label-free; H31 screen outcome is shown above. No H31 submission TIFF exists; SI-0 clusters are used in H32-1 as a structural protection gate.</p><a href="../evidence/h31_1_euler_feature_audit.json">Open Euler audit →</a> {h31_evidence_links(screen, confirmation)}</article>
</div></section>

<section class="section">
  <div class="eyebrow">PhD analysis · 24-submission live-score inversion</div><h2>Why <code>dotted-h19-5-d2-8</code> scored 0.2600, why <code>T-v2</code> scored 0.2449, and how to beat 0.2600.</h2>
  <div class="grid">
    <article class="card span-6"><h3>Why <code>e56ea318af89</code> (<code>d=2.8</code>) achieved 0.2600</h3><p>Priority-ordered Poisson-disk thinning of the 6-expert scarp/geophysics ridge surface <code>H19-5</code> (121,131 px, live 0.1922) at <code>min_dist=2.8 px</code> emits 44,090 off-catalogue dots (0.8532% footprint). Under the 300 m (3 px) linear tolerance kernel, dots spaced at 2.83–3.0 px along a 1D fault crest overlap at 1.41–1.50 px midpoints with <em>k</em> ≥ 0.50, retaining <strong>90.63%</strong> of <code>d=1.5</code> live credit (4,791.0 vs 5,286.1 px at |G| = 12,226 px) while cutting 15,979 redundant dots (−26.60% FP mass) and reducing kernel crowding ρ from 1.429 to 1.179. Because true faults are 1D curves along ridge crests rather than 2D isotropic sheets, live retention beat the 2D uniform-truth prediction (0.2550) by +0.0050. <a href="../evidence/live_inversion.json">Open 24-submission inversion →</a></p></article>
    <article class="card span-6"><h3>Why <code>5512495c6bd1</code> (<code>T-v2</code>) scored 0.2449 &amp; how we beat 0.2600</h3><p>Adding 1,259 straight-line <code>T-v2</code> gap-closure dots onto <code>d=1.5</code> (60,069 → 61,328 px) earned only +2.65 px of live credit (0.00210 credit/dot vs 0.0495 break-even), lowering live DTI by <strong>−0.0028</strong>; <code>26GEMSDOE dilcond-oof-v1</code> (<code>47629f496133</code>) scored <strong>0.1223</strong>. Conversely, 3,891 dots (8.83%) of the 0.2600 <code>d=2.8</code> file sit at <em>d</em><sub>cat</sub> = 100 m beside masked known faults due to 100–400 m USGS-vs-LiDAR scarp offsets (Hermant et al., 2025). Pruning the 2,434 mid-segment flank-shadow dots while protecting fault tips and shallow SI-0 Euler depth clusters (<strong>H32-1</strong>, <code>c3aeda1d31a3</code>, 41,656 px) projects to <strong>0.2665</strong>; solo H27-4 <code>8acb75e1f2cc</code> (40,199 px) to <strong>0.2701</strong>. <strong>H36-1</strong> supersedes both: the H34 live-anchored ladder says the optimal packing rung is <code>3.0</code>, not the shipped <code>2.828</code>, and the rung ladder is <em>not nested</em> — raising the rung re-seeds the greedy Poisson-disk packing and changes 24,091 px of the 44,090-px emission, it does not merely delete 2,757 dots. Re-packing to rung <code>3.0</code> and then applying the H27-4 blind flank prune (37,660 px) projects to <strong>0.2717–0.2727</strong> live, and it passed a fresh 10-seed gate at <strong>+0.002599</strong> &Delta;DTI while a coin-flip deletion to the <em>same</em> dot count scored <strong>−0.001657</strong> — so the gain is the layout, not the smaller budget. <strong>H37-1</strong> then replaced the content-blind packing rule itself: lazy-greedy maximum expected coverage of the detector probability field under the official 300 m kernel, at the same 41,333-px budget, kept the H27-4 blind flank prune, and passed a fresh 10-seed gate at <strong>+0.007289</strong> over the d=2.8 reference (<strong>+0.004614</strong> over H36-1, 10/10 seeds, 4/4 folds; content-blind matched-N control −0.044684), whose modelled live DTI of 0.278–0.286 <strong>did not survive its far-field falsification test</strong>: under LOSFO the rule ties the raster cascade (&minus;0.000037 &plusmn;0.000832), so the projection is withdrawn and the one-click slot returned to H36-1 (0.2717–0.2727). It was a model, and the model was tested. <a href="../knowledge/01_why_0.2477_won_and_the_ceiling.md">Read full PhD analysis →</a> · <a href="../knowledge/30_h37_1_result.md">H37-1 result →</a> · <a href="../knowledge/26_preregistration_H36-1.md">H36-1 preregistration →</a></p></article>
  </div>
</section>

<section class="section">
  <div class="eyebrow">Comparator library · T-v2-free d=2.8 &amp; historical references</div><h2>Every file stays explicitly unscored.</h2>
  <p>These research artifacts preserve comparable model families for review. None is an authorized weekly submission; the one-click file in the download panel above won the frozen fresh-seed adjudication and is the prominent research reference, while these remain the conservative and historical comparators.</p>
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
    if p.get("adjudication_evidence"):
        adj_sentence = (
            " That promotion came from the frozen fresh-seed adjudication "
            "<a href=\"../knowledge/25_preregistration_H35-6_candidate_adjudication.md\">"
            "knowledge/25_preregistration_H35-6_candidate_adjudication.md</a>, run on seeds "
            f"{esc(str(p.get('adjudication_seeds', '')))} with the frozen runner unmodified, because "
            "review found the file previously advertised in this slot dominated on every published "
            "statistic. The defect is registered against this project itself in "
            "<a href=\"../registry/irregularities.json\">registry/irregularities.json</a>."
        )
    else:
        adj_sentence = ""
    check_count = file_audit.get("check_count", "not recorded")
    return f"""<div class="breadcrumb"><a href="index.html">Overview</a> / Executive summary</div>
<section class="hero"><div class="hero-content">
  <div class="eyebrow">Submission executive summary · manual operator checklist</div>
  <h1>Research file,<br>not a score claim.</h1>
  <p class="lead">A concise decision brief for a human owner reviewing whether any local raster is appropriate for a future GEMS submission. The current first-screen download is intentionally labeled UNSCORED and NOT SLOT-APPROVED.</p>
  <div class="value-line"><span class="value-pill">Maximize P(Win)</span><span class="value-pill">Own the Outcome</span><span class="status unscored">NO UPLOAD / NO RECEIPT</span></div>
</div></section>

<section class="section"><div class="grid">
  <article class="card span-8"><h2>Candidate in one paragraph</h2><p><strong>{esc(p.get('hypothesis'))}.</strong> Suggested unique portal name <code class="file-name">{esc(p.get('submission_name', 'not recorded'))}</code>; filename <code class="file-name">{esc(p['nan'])}</code>. {esc(str(p.get('status', '')))} Built on the owner-reported <strong>{fmt_number(p.get('base_reference_live_score', 0.26), 4)}</strong> live base (<code>{esc(str(p.get('base_reference_id', '')))}</code>) with T-v2 gap closure omitted after <code>5512495c6bd1</code> scored <strong>0.2449</strong> (&minus;0.0028 vs 0.2477). Its holdout evidence (<a href="../{esc(str(p.get('holdout_evidence', 'evidence/h32_1_holdout.json')))}">{esc(str(p.get('holdout_evidence', 'evidence/h32_1_holdout.json')))}</a>) records a mean &Delta;DTI of <strong>{fmt_number(p.get('holdout_mean_gain', 0), 6)}</strong> with <strong>{esc(p.get('holdout_folds_improved', 'n/a'))}</strong> spatial folds and <strong>{esc(p.get('holdout_seeds_improved', 'n/a'))}</strong> seeds improving over the same-run control.{adj_sentence} The inherited H28-1 full-map reference <code class="file-name">{esc(candidate.get('nan', ''))}</code> (+0.00294884 on seeds 140–149) is retained for comparison and is not one of the four weekly slots inherited from the predecessor campaign.</p><p><strong>Disposition:</strong> all local rasters pass {check_count} format, grid, <code>[0,1]</code> range, footprint, and SHA-256 checks (<a href="../evidence/submission_file_audit.json">evidence/submission_file_audit.json</a>), and remain unscored until manually submitted by the human operator.</p></article>
  <article class="card span-4"><div class="metric">{comma(p.get('emitted_px'))}</div><div class="metric-caption">binary positive cells emitted</div><hr><div class="metric">+{fmt_number(p.get('holdout_mean_gain', 0), 5)}</div><div class="metric-caption">4-fold spatial OOF &Delta;DTI ({esc(p.get('holdout_seeds_improved', 'n/a'))} seeds)</div></article>
</div></section>

<section class="download-panel"><div class="eyebrow">Prominent single-band GeoTIFF · manual download</div><h2>{esc(p.get('hypothesis'))}</h2><p><span class="status unscored">UNSCORED · NOT SLOT-APPROVED</span></p>
{file_links(p)}{mirror_line(p)}<p><strong>Suggested unique submission name (only if later approved):</strong><br><code class="file-name">{esc(p.get('submission_name', 'not recorded'))}</code></p><p><strong>Primary exact filename:</strong></p><code class="file-name">{esc(p['nan'])}</code><p class="meta">SHA-256 <code>{esc(p.get('sha256_nan'))}</code> · {esc(p.get('bytes_nan'))} bytes · {comma(p.get('emitted_px'))} emitted cells · EPSG:32611 · 3730 × 3292 · 100 m grid.</p><p><strong>Copy this exact short note ({len(str(p.get('note','')))} / 200 characters):</strong></p>{note_box(str(p.get('note','')))}
<p><strong>Range/mask:</strong> the primary has finite 0/1 predictions inside the template footprint and NaN with a NaN nodata tag outside. The all-finite alternative uses 0 outside and no nodata tag, so the mask semantics differ; portal acceptance of either variant has not been confirmed.</p><p>ZIP of the primary TIFF: <a href="downloads/{esc(p['zip'])}" download>{esc(p['zip'])}</a>. The historical range error remains unconfirmed; the current local audit checks the exact range, finiteness, grid, footprint and hashes.</p></section>

<section class="section"><h2>Human submission checklist</h2><ol>
<li><strong>Re-evaluate the evidence.</strong> Read the exact spatially blocked holdout for this file (<a href="../{esc(str(p.get('holdout_evidence', 'evidence/h32_1_holdout.json')))}">{esc(str(p.get('holdout_evidence', 'evidence/h32_1_holdout.json')))}</a>) and the <a href="research.html">current research limits</a>. H37-1's interleaved gain failed to transfer to LOSFO; H37-3's Euler-only additions beat random but earned 0.031157 credit/dot, below the fixed 0.0548 live bar. The current H36-1 file is still labeled UNSCORED and NOT SLOT-APPROVED.</li>
<li><strong>Review the official terms manually.</strong> Open the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a> and <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official rules</a>; confirm the current deadline, account eligibility, file requirements and weekly cap. This site does not log in, upload, or automate portal actions.</li>
<li><strong>Do not upload this research file unless the owner separately authorizes it and a slot is available.</strong> If authorized, sign in to DrivenData, open the GEMS competition's submission interface, start a new submission and select the downloaded single-band GeoTIFF. The visible portal wording can change; the owner must check it directly.</li>
<li><strong>Enter the unique submission name.</strong> Use <code>{esc(p.get('submission_name', 'not recorded'))}</code> as the submission label, if the portal provides a name field. Preserve the filename/content ID and compare the downloaded SHA-256 above with the local audit before selecting the file.</li>
<li><strong>Paste the exact registered note.</strong> Copy the note above (≤200 characters) into the portal's note field if provided. Do not add an unsupported score claim.</li>
<li><strong>Submit and preserve the receipt.</strong> After the owner clicks the portal's submit control, save the exact filename, submission name, note, timestamp, receipt/confirmation, and returned score. If the portal rejects the file, save the full error text and response; the root cause of the historical range error remains unconfirmed.</li>
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


H33_RESULT_SECTION = """
<section class="section"><h2>Session 10 — the first preregistered arm with its data in hand: H33-1, refuted</h2>
<div class="callout"><strong>H33-1 (kinematic reactivation favourability gate) ran on its reserved seeds 200–209 and failed all {n_crit} frozen promotion criteria.</strong> It was executed before any new arm was designed because it was the only preregistered hypothesis whose external data had actually landed. The data precondition was verified from the bytes first — <a href="data/sb_slip_tendency_in_footprint.json">{n_seg} fault segments</a> clipped to the footprint from Siler (2022), DOI 10.5066/P9YL58W6, carrying <code>TS</code>, <code>TD</code>, <code>TS_norm</code>, <code>TD_TS</code>, <code>ShearStres</code>, <code>NormalStre</code> and stress-orientation fields, reprojected from NAD83 Albers to EPSG:32611. Mean paired ΔDTI <strong>{gain:+.6f}</strong>, {won}/{nseeds} seeds, {folds}/4 folds. <code>gate_passed: {gate}</code>.</div>
<table class="table"><thead><tr><th>variant</th><th>mean DTI</th><th>ΔDTI</th><th>seeds won</th><th>folds</th><th>Δdots/seed</th><th>credit per removed FP</th></tr></thead><tbody>{rows}</tbody></table>
<table class="table"><thead><tr><th>promotion criterion</th><th>value</th><th>threshold</th><th></th></tr></thead><tbody>{crits}</tbody></table>
<div class="grid"><article class="card span-4"><h3>1. A hard coverage ceiling of ~12%</h3><p>Only <strong>{cov:.2f}%</strong> of emitted dots (worst fold {covmin:.2f}%) had a catalogued segment within 1 km whose strike agreed within 20°. The other 88% are neutral by construction and can never be pruned. The 60% coverage precondition existed to catch exactly this. The cause is structural, not tunable: <strong>candidate dots are emitted off-catalogue by design</strong>, so most have no similarly oriented mapped segment nearby. Any arm that transfers an attribute <em>from</em> mapped faults <em>to</em> off-catalogue candidates inherits that ceiling.</p></article>
<article class="card span-4"><h3>2. The sign of the physics is inverted</h3><p>The direction control was <em>better</em> than the primary arm, not worse: removing the bottom decile by favourability discarded <strong>{effp:.5f}</strong> credit per removed FP while removing the <em>top</em> decile discarded only <strong>{effc:.5f}</strong>. The dots this score called unfavourably oriented were carrying <em>more</em> DTI credit than the ones it called favourable.</p></article>
<article class="card span-4"><h3>3. Pruning is exhausted as a family</h3><p>All three arms removed pixels at <strong>0.101–0.140 credit per FP</strong> against a break-even inclusion threshold of <strong>{thr:.5f}</strong> — the discarded pixels were worth <strong>5–7× break-even</strong>. With H31-1 and H32-2 that is three independent pruning arms failing the same way, reaching the same conclusion as the frontier from a completely different direction: at this density, pruning destroys credit whatever physical rationale selects the pixels.</p></article></div>
<p><strong>Standing effect.</strong> Per the preregistration the result was recorded and nothing else: no retuning, no re-run on a fresh decade, no candidate TIFF, no submission slot. Seeds 200–209 are spent; the next arm takes 220–229. Attribute transfer from mapped to off-catalogue structure is closed as a pruning signal. <a href="../knowledge/21_result_H33-1_refuted_2026-10-03.md">Full result record</a> · <a href="../knowledge/19_preregistration_H33-1.md">frozen preregistration</a> · <a href="../evidence/h33_1_holdout.json">evidence JSON</a> · <a href="../src/gems27/kinematics.py">score source</a>.</p></section>
"""


def session11_section(h35: dict, h35_6: dict) -> str:
    """Session 11: the H35 hypothesis ledger, the H35-1 refutation, and the slot adjudication.

    Everything rendered here is read from a committed evidence JSON. Nothing is recomputed and no
    claim is made that is not present in `evidence/h35_1_thermal_farfield.json` or
    `evidence/h35_6_candidate_headtohead.json`.
    """
    crit = h35.get("criteria", {})
    g1, g2, g3, g4 = (crit.get(k, {}) for k in
                      ("G1_profitability", "G2_differential", "G3_support", "G4_end_to_end"))
    summ = h35.get("summary", {})
    layer = h35.get("layer", {})
    dose = summ

    def dose_row(key: str, label: str) -> str:
        row = dose.get(key, {})
        if not row:
            return ""
        return (f"<tr><td>{label}</td><td>{comma(int(row.get('adds', 0)))}</td>"
                f"<td>{fmt_number(row.get('credit_per_added_dot', 0), 6)}</td>"
                f"<td>{fmt_number(row.get('mean_delta_dti', 0), 6)}</td></tr>")

    dose_rows = "".join([
        dose_row("thermal", "temp &ge; 20 &deg;C, radius 6 px (primary)"),
        dose_row("dose_temp_ge50c", "temp &ge; 50 &deg;C"),
        dose_row("dose_geotherm_ge100c", "geothermometry &ge; 100 &deg;C"),
        dose_row("dose_radius_1px", "radius 1 px"),
        dose_row("dose_radius_6px", "radius 6 px"),
        dose_row("control", "<strong>matched-count random control</strong>"),
    ])

    status = str(h35.get("status", "NOT RUN"))
    gate_passed = h35.get("gate_passed")

    # --- H35-6 adjudication -------------------------------------------------
    adj = ""
    if h35_6:
        seeds = h35_6.get("seeds", [])
        variants = h35_6.get("variants", {})
        order = ["h32_1_post_d28", "h32_1_pre_d28", "h27_4_blind_r1_d28",
                 "control_prune_protected_only_d28"]
        # Labels name the hypothesis and its PRE-adjudication slot, so the table stays readable after
        # the promotion below moves the winning file to the one-click slot.
        slot_of = {
            "h32_1_post_d28": "H32-1 post-thinning <code>c3aeda1d31a3</code> <span class=\"meta\">(was primary)</span>",
            "h32_1_pre_d28": "H32-1 pre-thinning <code>31e35eee884e</code> <span class=\"meta\">(was secondary)</span>",
            "h27_4_blind_r1_d28": "H27-4 solo r=1 <code>8acb75e1f2cc</code> <span class=\"meta\">(was tertiary &rarr; promoted)</span>",
            "control_prune_protected_only_d28": "anti-selective control",
        }
        rows = "".join(
            f"<tr><td>{slot_of.get(k, esc(k))}</td>"
            f"<td>{fmt_number(variants.get(k, {}).get('mean_dti_gain', 0), 6)}</td>"
            f"<td>{variants.get(k, {}).get('seeds_won', 0)}/{variants.get(k, {}).get('n_seeds', 5)}</td>"
            f"<td>{variants.get(k, {}).get('folds_improved', 0)}/4</td></tr>"
            for k in order)
        best = max(order, key=lambda k: variants.get(k, {}).get("mean_dti_gain", -9))
        bv = variants.get(best, {})
        passed = (bv.get("seeds_won", 0) >= 4 and bv.get("folds_improved", 0) >= 3)
        ctrl = variants.get("control_prune_protected_only_d28", {}).get("mean_dti_gain", 0)
        demo = bv.get("mean_dti_gain", 0) <= ctrl
        adj = f"""
<section class="section"><h2>Session 11b — adjudicating the candidate ladder on fresh seeds {esc(seeds[0] if seeds else '')}–{esc(seeds[-1] if seeds else '')}</h2>
<div class="callout"><strong>Why a fresh decade was spent on a choice rather than a hypothesis.</strong> Review found the one-click primary strictly dominated by the file in its own tertiary slot on every published statistic. The primary is the output of a <em>preregistered</em> gate; the tertiary is the maximum of four correlated variants scored on <em>one</em> holdout run, so re-ranking on that same run would be a multiple-comparison error. The tie was therefore broken on unused seeds with the frozen runner, unmodified, so the new numbers are directly comparable with seeds 180–189. <a href="../knowledge/25_preregistration_H35-6_candidate_adjudication.md">Frozen adjudication protocol</a></div>
<div class="table-wrap"><table><thead><tr><th>Slot</th><th>Mean &Delta;DTI</th><th>Seeds won</th><th>Folds</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="callout"><strong>Outcome:</strong> the best variant is {slot_of.get(best, esc(best))} at {fmt_number(bv.get('mean_dti_gain', 0), 6)} ({bv.get('seeds_won', 0)}/{bv.get('n_seeds', 5)} seeds, {bv.get('folds_improved', 0)}/4 folds). The frozen rule promotes it only with &ge;4/5 seeds and &ge;3/4 folds, which <strong>{'is met' if passed else 'is NOT met — the primary is unchanged'}</strong>. {'The control which removes the <em>most protective</em> pixels also gains (' + fmt_number(ctrl, 6) + '), so the family gain is largely generic prune-harder mass removal and the site does not claim selectivity.' if demo else 'The anti-selective control (' + fmt_number(ctrl, 6) + ') stays below the best variant, so a selective prune is supported rather than a generic prune-harder effect.'} Five seeds cannot resolve a +0.0005 gap; this is a decision under uncertainty, not a measurement. <a href="../evidence/h35_6_candidate_headtohead.json">Adjudication evidence JSON</a></div></section>
"""
    else:
        adj = ""

    return f"""
<section class="section"><h2>Session 11 — five addition hypotheses, and the first one measured to a verdict</h2>
<div class="callout"><strong>The standing problem, restated in one line.</strong> The reachability frontier says beating 0.3195 from the 0.2600 emission needs <strong>+1,151 px of credit (+24.0 %)</strong>, which is more credit than the whole submission captures; thinning efficiency (0.03098) is below break-even (0.05485), so <strong>no reallocation of the existing dots reaches it</strong>. That is a detection gap, and the only class of move that can close a detection gap is new dots that land on structure the detector does not yet cover. Every arm in the H35 series is therefore an <em>addition</em> arm.</div>
<div class="table-wrap"><table><thead><tr><th>Rank</th><th>Hypothesis</th><th>Class</th><th>Physical signature</th><th>Cost</th><th>Data obtainable in-sandbox?</th></tr></thead><tbody>
<tr><td>1</td><td><code>H35-1</code> hydrothermal-discharge conjunction</td><td>ADD</td><td>point process of thermal discharge; not a derivative field</td><td>low</td><td><strong>yes</strong> — hash-verified, in hand</td></tr>
<tr><td>2</td><td><code>H35-4</code> bounded Phase-2 discovery budget</td><td>ADD (bounded)</td><td>budget rule, not a transform</td><td>low</td><td>yes — nothing to fetch</td></tr>
<tr><td>3</td><td><code>H35-2</code> heat-flow residual &times; 2 m probe</td><td>ADD</td><td>conductive residual, a genuinely different field</td><td>high</td><td>no — Actions bridge only (ScienceBase)</td></tr>
<tr><td>4</td><td><code>H35-3</code> drainage-network neotectonics</td><td>ADD</td><td>channel offsets / knickpoints from 716 1 m DEM tiles</td><td>very high</td><td>no — Actions only (3DEP S3)</td></tr>
<tr><td>5</td><td><code>H35-5</code> vent-corridor control</td><td>CONFIRM</td><td>vent alignment — only 21 points, re-ranking only</td><td>low</td><td>yes — in hand</td></tr>
</tbody></table></div>
<p><strong>Why these and not more re-weighting of the catalogue.</strong> The official material settles it: the label set is the USGS Quaternary Fault and Fold Database <em>plus</em> faults newly labelled by experts, and the prize is rescored in a second round against that expanded set. The catalogue is therefore the thing the test set is <em>not</em>. The thermal layer was chosen first because it was the only unused layer whose bytes were already in hand, hash-pinned, and independently re-registered onto the competition grid. <a href="../knowledge/23_h35_hypotheses.md">Full ledger with sources and obtainability checks</a></p>
</section>

<section class="section"><h2>H35-1 — hydrothermal-discharge conjunction: <span class="status blocked">{esc(status)}</span></h2>
<div class="callout"><strong>Verdict: {esc('FAILED' if gate_passed is False else str(gate_passed))} — 3 of 4 frozen criteria failed, arm closed with no candidate TIFF and no weekly slot.</strong> Instrument: leave-fault-system-out, 600 m label buffer, 4 quadrant folds, seeds 230–234. Dataset: GDR submission 1391 (INGENIOUS) — {comma(int(layer.get('audit', {}).get('n_records_raw', 0)))} raw rows, <strong>{comma(int(layer.get('audit', {}).get('n_unique_locations', 0)))} unique sites</strong>, re-registered from <code>utm_x</code>/<code>utm_y</code> through the template geotransform to a max residual of {fmt_number(layer.get('audit', {}).get('max_abs_row_residual_px', 0), 1)} px. The catalogue-derived <code>dist_known_fault_px</code> column was excluded by an explicit allow-list and never read. <a href="../knowledge/24_h35_1_result.md">Result record</a> · <a href="../evidence/h35_1_thermal_farfield.json">Evidence JSON</a></p></div>
<div class="grid"><article class="card span-6"><h3>Every dose variant is at or below the control</h3>
<div class="table-wrap"><table><thead><tr><th>Variant</th><th>Added dots</th><th>Credit / dot</th><th>Mean &Delta;DTI</th></tr></thead><tbody>{dose_rows}</tbody></table></div>
<p>All dose variants were reported and none was allowed to gate. Tightening from every warm site to only the &ge;50 &deg;C sites moves credit/dot the wrong way — and the <em>quartz geothermometer</em>, which samples deeper and hotter fluid, is worse still. If the physics were merely noisy, a harder filter would sharpen it.</p></article>
<article class="card span-6"><h3>Why it fails, mechanistically</h3>
<p>Great Basin hydrothermal discharge is overwhelmingly <strong>basin-margin and fault-controlled</strong> — which is exactly why those faults are already in the catalogue and why the blended detector already fires along those margins. The base emission has therefore already spent its budget on the structure the springs mark, and the candidate pool (<code>ridge AND active AND NOT base</code>) is left with redundant neighbouring slop that earns almost nothing ({fmt_number(g1.get('observed', 0), 5)} credit/dot against a {fmt_number(g1.get('required', 0), 5)} threshold). The matched-count random control draws candidates <strong>&gt; 6 px from any thermal site</strong> and beats the arm ({fmt_number(g2.get('observed_pooled_control', 0), 5)} vs {fmt_number(g2.get('observed_pooled_thermal', 0), 5)}), winning {g2.get('seeds_won', 0)} of {g2.get('seeds_total', 0)} seeds.</p>
<p><strong>Radius confirms the reading.</strong> At 1 px the arm reaches its best value ({fmt_number(summ.get('dose_radius_1px', {}).get('credit_per_added_dot', 0), 5)}) and at 6 px it degrades to {fmt_number(summ.get('dose_radius_6px', {}).get('credit_per_added_dot', 0), 5)}: the association is a sub-pixel coincidence that dissolves as the aperture widens, which is the opposite of a geological control. Mean &Delta;DTI was {fmt_number(g4.get('observed', 0), 6)} (control {fmt_number(summ.get('control', {}).get('mean_delta_dti', 0), 6)}).</p></article></div>
<div class="callout"><strong>Scope, stated so the record is not over-read.</strong> LOSFO truth is <em>mapped</em> fault geometry held out by system, so the stronger claim — a concealed unmapped permeable structure is marked by a spring — is <strong>untested, not refuted</strong>. But because LOSFO is an upper bound, failing it is decisive for the arm as constructed: a dot that cannot earn credit against geometry we can see will not earn credit against geometry we cannot. The layer itself is not impugned; only this conjunction as an addition licence.</div>
</section>
{adj}"""


def render_session14_section(record: dict, h38_result: dict, h38_claim: dict) -> str:
    ranked = sorted(record.get("ranked_hypotheses", []), key=lambda item: item.get("rank", 999))
    rows = []
    for item in ranked:
        lo_hi = item.get("expected_delta_dti", [])
        if isinstance(lo_hi, list) and len(lo_hi) == 2:
            range_text = f"{fmt_number(lo_hi[0], 4)} to +{fmt_number(lo_hi[1], 4)}"
        else:
            range_text = "not stated"
        status = item.get("status", "not recorded")
        if item.get("id") == "H38-1":
            if h38_result_integrity(h38_result, h38_claim):
                status = f"Frozen test {h38_result.get('status')}; no weekly-slot approval"
            elif h38_claim.get("status") in {"RESERVED", "RUNNING", "FAILED", "CONSUMED"}:
                status = f"Claim {h38_claim.get('status')}; see integrity state above"
        layers = "".join(f"<li>{esc(layer)}</li>" for layer in item.get("layers", []))
        detail_fields = (
            ("Physical signature", item.get("physical_signature")),
            ("Why it may find faults absent from the public catalogue", item.get("why_missing_catalogue")),
            ("Difference from prior repository work", item.get("differs_from_repo")),
            ("Data gate / official-source status", item.get("data_gate")),
            ("Principal confounder", item.get("main_confounder")),
        )
        detail_html = "".join(
            f"<p><strong>{esc(label)}:</strong> {esc(value)}</p>"
            for label, value in detail_fields if value
        )
        details = (
            f"<details><summary>Layers, physical signature, novelty &amp; data limits</summary>"
            f"<ul>{layers}</ul>{detail_html}</details>"
        )
        rows.append(
            f"<tr><td>{esc(item.get('rank'))}</td><td><strong>{esc(item.get('id'))}</strong><br>{esc(item.get('title'))}{details}</td>"
            f"<td>{esc(range_text)}</td><td>{esc(item.get('cost'))}</td><td>{esc(status)}</td></tr>"
        )
    ranking_rows = "".join(rows)
    result_line = h38_status_html(h38_result, h38_claim)
    availability = record.get("official_source_checks_2026_10_03", {})
    return f"""<section class="section" id="session14-ranking"><div class="eyebrow">Current hypothesis ranking · Session 14</div>
<h2>Five ranked geological hypotheses and their current status</h2>
<div class="callout">{result_line} H38-1's protocol is <a href="../knowledge/38_preregistration_H38-1.md">frozen here</a>; the full layers, mechanisms, novelty boundaries, risks and source checks are in <a href="../knowledge/37_ranked_hypotheses_session14_2026-10-03.md">the dated ranking record</a>, and the single-use run/analyzer failure is documented in the <a href="../knowledge/39_session14_closeout_2026-10-03.md">close-out</a>. Every ΔDTI interval is a planning prior that includes zero—not an observed holdout gain or competition-score prediction.</div>
<div class="table-wrap"><table class="table"><thead><tr><th>Rank</th><th>Hypothesis</th><th>Planning-only ΔDTI</th><th>Cost / data gate</th><th>Current state</th></tr></thead><tbody>{ranking_rows}</tbody></table></div>
<p><strong>Official-source availability check (page listings, not new local clips):</strong> {esc(availability.get('heat_flow', 'Heat-flow release not recorded'))} {esc(availability.get('ingenious_gdr', 'GDR resource listing not recorded'))} {esc(availability.get('conductance', 'Conductance listing not recorded'))} {esc(availability.get('three_dep', '3DEP listing not recorded'))}</p>
<p><a href="sources.html">Open official-source register →</a> · <a href="../registry/next_hypotheses.json">Registry JSON →</a></p></section>"""


def render_research(registry: dict, h28: dict, euler: dict, board: dict,
                    screen: dict, confirmation: dict, seed_audit: dict, h32: dict,
                    frontier: dict, losfo: dict, h33: dict, h34: dict, h34_hold: dict,
                    h35: dict = None, h35_6: dict = None,
                    h38_result: dict = None, h38_claim: dict = None) -> str:
    hypotheses = sorted(registry.get("hypotheses", []), key=lambda item: item.get("rank", 999))
    hypothesis_html = "".join(render_hypothesis_card(h, screen, confirmation, seed_audit) for h in hypotheses)
    session14 = registry.get("session14_addendum", {})
    session14_section = render_session14_section(session14, h38_result or {}, h38_claim or {})
    si0 = euler.get("structural_indices", {}).get("0", {})
    summary = si0.get("solution_summary", {})
    clusters = si0.get("lineament_cluster_stats", {})
    stability = euler.get("si_cluster_centroid_stability", {})
    h1 = stability.get("si1_vs_si0", {})
    h2 = stability.get("si2_vs_si0", {})
    candidate = h28.get("candidate", {})
    top_val = registry.get("validated_top_candidate", {})
    fr_conc = frontier.get("conclusions", {})
    fr_cur = frontier.get("current_state", {})
    fr_ident = frontier.get("identity_check", {})
    fr_ceil = frontier.get("budget_family_ceiling", {})
    fr_lead = frontier.get("add_arm_frontier", {}).get("0.3195", {})
    fr_dots = fr_lead.get("dots_needed_by_marginal_efficiency", {})
    lo_arms = losfo.get("arms", {})
    lo_ratio = losfo.get("ratios", {})
    lo_ff = losfo.get("far_field_check", {})
    lo_meta = losfo.get("meta", {})
    lo_fold = losfo.get("per_fold", {})
    h34_fit = h34.get("density_scale_fit", {})
    h34_lad = h34.get("ladder_prediction", {})
    h34_thr = h34.get("threshold_arithmetic", {})
    h34_steps = {round(r["rung_from"], 4): r for r in h34.get("rung_efficiencies", [])}
    h34_gate = h34_hold.get("gate", {})
    # steps are emitted in order [2.828->3.000, 3.000->3.162, 2.828->3.162]; index them by position,
    # not by "from", because the first and third share a "from" key.
    _st = h34_hold.get("steps", [])
    h34_s1 = _st[0] if len(_st) > 0 else {}
    h34_s2 = _st[1] if len(_st) > 1 else {}
    h33_v = h33.get("variants", {})
    h33_p = h33_v.get("h33_1_prune_p10", {})
    h33_c = h33_v.get("control_top_p10", {})
    h33_d = h33.get("data_precondition", {})
    h33_crit = h33.get("promotion_criteria", {})
    h33_rows = "".join(
        f"<tr><td><code>{esc(k)}</code></td><td>{fmt_number(v.get('mean_dti', 0), 6)}</td>"
        f"<td>{v.get('mean_dti_gain', 0):+.6f}</td><td>{v.get('seeds_won', 0)}/{v.get('n_seeds', 10)}</td>"
        f"<td>{v.get('folds_improved', 0)}/4</td><td>{fmt_number(v.get('delta_dots_per_seed', 0), 1)}</td>"
        f"<td>{fmt_number(v.get('removed_credit_per_removed_fp', 0), 5)}</td></tr>"
        for k, v in h33_v.items())
    h33_crit_rows = "".join(
        f"<tr><td>{esc(k)}</td><td>{fmt_number(v.get('value', 0), 6)}</td>"
        f"<td>{fmt_number(v.get('threshold', 0), 6)}</td>"
        f"<td>{'PASS' if v.get('passed') else '<strong>FAIL</strong>'}</td></tr>"
        for k, v in h33_crit.items())
    untried = [h["id"] for h in hypotheses if h["id"].startswith("H33")]
    n_untried = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}.get(len(untried), str(len(untried)))
    h33_section = H33_RESULT_SECTION.format(
        n_crit=len(h33_crit), n_seg=comma(int(h33_d.get("n_segments", 0))),
        gain=h33_p.get("mean_dti_gain", 0.0), won=h33_p.get("seeds_won", 0),
        nseeds=h33_p.get("n_seeds", 10), folds=h33_p.get("folds_improved", 0),
        gate=str(h33.get("gate_passed")).lower(), rows=h33_rows, crits=h33_crit_rows,
        cov=(h33.get("fav_coverage_mean") or 0.0) * 100, covmin=(h33.get("fav_coverage_min") or 0.0) * 100,
        effp=h33_p.get("removed_credit_per_removed_fp", 0.0),
        effc=h33_c.get("removed_credit_per_removed_fp", 0.0),
        thr=h33.get("inclusion_threshold_oof", 0.0))
    fold_spread = ", ".join(
        f"{k} {(v['losfo_tp'] / v['leaky_tp']):.3f}" for k, v in lo_fold.items() if v.get("leaky_tp")
    )
    return f"""<div class="breadcrumb"><a href="index.html">Overview</a> / Research</div>
<section class="hero"><div class="hero-content"><div class="eyebrow">Hypotheses, evidence and preregistration</div><h1>Test the geology.<br>Respect the proxy.</h1>
<p class="lead">The current Session 14 record ranks {len(session14.get('ranked_hypotheses', []))} candidate fault-discovery rules; H38-1 is shown with its current frozen-holdout status below. Older H33/H37 work remains in the archive. Planning ranges are uncertain catalogue-holdout priors—not observed gains or competition-score predictions.</p>
<div class="value-line"><span class="value-pill">Maximize P(Win)</span><span class="value-pill">Own the Outcome</span><span class="status proxy">PROXY ≠ COMPETITION</span></div></div></section>

{session14_section}

<section class="section"><h2>Historical validated candidate — H32-1 de-jittering (PASS on 4-fold spatially blocked holdout, seeds 180–189)</h2>
<div class="callout"><strong>Why tip- &amp; Euler-protected mid-segment de-jittering was designed and validated before touching a weekly slot:</strong> Live score inversion of all 24 SHA-256-authenticated submissions (<a href="../evidence/live_inversion.json">evidence/live_inversion.json</a>) proved that <code>25GEMSDOE dotted-h19-5-d2-8</code> (<code>e56ea318af89</code>, 44,090 px) scored <strong>0.2600</strong> (+0.0123 over 0.2477 <code>d=1.5</code>), whereas <code>27GEMSDOE topo-gap-closure-t-v2-on-d1-5</code> (<code>5512495c6bd1</code>, 61,328 px) scored <strong>0.2449</strong> (−0.0028 vs 0.2477, 0.00210 credit/dot vs 0.0495 break-even) and <code>26GEMSDOE dilcond-oof-v1</code> (<code>47629f496133</code>) scored <strong>0.1223</strong>. In the 0.2600 <code>d=2.8</code> emission, 3,891 pixels (8.83%) lie at <em>d</em><sub>cat</sub> = 100 m beside masked known catalogue faults. <strong>{esc(top_val.get('title', 'H32-1'))}</strong> prunes the 2,434 mid-segment lateral flank-shadow pixels (<em>d</em><sub>cat</sub> ≤ 100 m AND <em>d</em><sub>end</sub> &gt; 300 m AND cat_nbrs ≥ 2 AND <em>d</em><sub>Euler</sub> &gt; 300 m) while protecting the 1,457 pixels within 300 m of a catalogue fault tip or a retained Reid et al. (1990) SI=0 Euler depth-coherent contact cluster (<a href="../evidence/h31_1_euler_clusters.csv">evidence/h31_1_euler_clusters.csv</a>). On fresh seeds 180–189 (<a href="../evidence/h32_1_holdout.json">evidence/h32_1_holdout.json</a>), <code>h32_1_post_d28</code> gained <strong>+0.001272</strong> mean ΔDTI (10/10 seeds, 4/4 spatial folds) and <code>h32_1_pre_d28</code> gained <strong>+0.001399</strong> (10/10 seeds, 4/4 folds), with protected tip/Euler pixels carrying <strong>2.29× higher credit density</strong> than mid-segment flank shadow (0.00919 vs 0.00402 credit/FP).</div></section>

<section class="section"><h2>Session 10 — what beating 0.3195 costs, in pixels of credit</h2>
<div class="callout"><strong>The gap is a detection gap, not a budget gap.</strong> <code>scripts/reachability_frontier.py</code> (<a href="../evidence/reachability_frontier.json">evidence/reachability_frontier.json</a>) inverts the official metric. The closed form <code>DTI = TPw / (0.2·TPw·(1−ρ) + 0.2·N + 0.8·|G|)</code> is <strong>checked numerically against <code>metric.dti_binary</code> on {esc(fr_ident.get('n_cases', 0))} synthetic grids</strong> before use — max absolute residual <code>{fr_ident.get('max_abs_residual', float('nan')):.2e}</code>, and the substitution <code>FPw = N − MPw</code> holds in every case. At the calibrated |G| = {comma(int(frontier.get('inputs', {}).get('G_used_px', 0)))} px, the best owner-anchored submission earns <strong>{comma(int(fr_cur.get('credit_TPw', 0)))} px of credit ({fmt_number(fr_cur.get('credit_fraction_of_G', 0) * 100, 1)}% of |G|)</strong> at N = {comma(int(fr_cur.get('emitted_px', 0)))}. Reaching <strong>0.3195</strong> at that same budget needs <strong>{comma(int(fr_lead.get('credit_required_at_current_budget', 0)))} px</strong> — a gap of <strong>+{comma(int(fr_conc.get('credit_gap_to_leader_at_current_budget_px', 0)))} px, {fmt_number(fr_conc.get('relative_credit_increase_needed', 0) * 100, 1)}% more credit than the entire 0.2600 submission captures</strong>.</div>
<div class="grid">
<article class="card span-6"><h3>Why thinning cannot buy it</h3><p>The programme has one exactly-controlled live measurement of <em>marginal</em> efficiency: thinning the same ridge from <code>d=1.5</code> (60,069 px, 0.2477) to <code>d=2.8</code> (44,090 px, 0.2600) removed <strong>{comma(int(frontier.get('live_measured_marginal_efficiency', {}).get('thinning_pair', {}).get('pixels_removed', 0)))} dots</strong> and lost <strong>{fmt_number(frontier.get('live_measured_marginal_efficiency', {}).get('thinning_pair', {}).get('credit_lost', 0), 1)} px of credit</strong> — <strong>{fmt_number(frontier.get('live_measured_marginal_efficiency', {}).get('thinning_pair', {}).get('marginal_credit_per_removed_pixel', 0), 5)} credit/px</strong>, below the break-even {fmt_number(fr_ceil.get('asymptote_at_live_marginal_efficiency', 0) * 0 + 0.05485, 5)} at 0.2600. A dot earning that little does not clear the <code>0.2·target</code> charge, so <strong>no quantity of dots at the current marginal efficiency reaches 0.3195</strong>.</p><p>Pruning arms are still worth taking — they are free and compose — but each is worth ~0.001–0.010, one to two orders of magnitude short.</p></article>
<article class="card span-6"><h3>What would reach it</h3><p>New dots that land on genuinely unmapped fault traces, by the credit each earns:</p><ul>
<li><code>e = 0.20</code> → <strong>{comma(int(fr_dots.get('0.20', {}).get('dots_needed', 0)))}</strong> dots</li>
<li><code>e = 0.30</code> → <strong>{comma(int(fr_dots.get('0.30', {}).get('dots_needed', 0)))}</strong> dots</li>
<li><code>e = 0.40</code> → <strong>{comma(int(fr_dots.get('0.40', {}).get('dots_needed', 0)))}</strong> dots</li>
<li><code>e = 0.50</code> → <strong>{comma(int(fr_dots.get('0.50', {}).get('dots_needed', 0)))}</strong> dots</li></ul>
<p>≈<strong>2,600–3,400 well-placed dots</strong> at 0.4–0.5 credit each. That is an <em>addition</em> arm. Full frontier and |G| sensitivity: <a href="../evidence/reachability_frontier.json">evidence/reachability_frontier.json</a> · <a href="../knowledge/20_strategy_after_reachability_frontier.md">knowledge/20</a>.</p></article></div></section>

<section class="section"><h2>Session 10 — a far-field holdout that can finally gate addition arms</h2>
<div class="callout"><strong>Why it was needed:</strong> the standing holdout hides catalogue components <em>interleaved</em> with the known catalogue, so <strong>100% of its hidden truth lies at distance 0 from the published catalogue</strong> (<a href="../evidence/arm_habitat_decomposition.json">evidence/arm_habitat_decomposition.json</a>: habitat-A truth = 0 of 120,983 px). A shippable file may place <em>no</em> pixel on a catalogue cell, so that protocol contains no truth in the only habitat a submission can occupy — it <strong>cannot validate any arm that proposes dots where nothing is catalogued</strong>, which §above says is the only class that can reach 0.3195.</div>
<div class="callout"><strong>What was built:</strong> <code>src/gems27/losfo.py</code> + <code>scripts/run_losfo_harness.py</code> (<a href="../evidence/losfo_farfield_diagnostic.json">evidence/losfo_farfield_diagnostic.json</a>). {comma(int(lo_meta.get('n_systems', 0)))} catalogue pixels are grouped into <strong>{comma(int(lo_meta.get('n_systems', 0)))}</strong> fault systems; <strong>{comma(int(lo_meta.get('n_systems_held_out', 0)))} systems / {comma(int(lo_meta.get('held_out_px', 0)))} px</strong> are held out per seed with a <strong>600 m label buffer erased</strong>, so truth is <strong>≥ {fmt_number(lo_ff.get('min_dist_truth_to_known_px_over_cells', 0) * 100, 0)} m</strong> from every pixel the detector saw as positive (median {fmt_number(lo_ff.get('median_dist_truth_to_known_px_over_cells', 0) * 100, 0)} m). {fmt_number((lo_ff.get('frac_dots_ge_300m_from_known') or 0) * 100, 1)}% of emitted dots are ≥ 300 m from any known pixel.</div>
<div class="table-wrap"><table><thead><tr><th>Arm</th><th>Mean DTI</th><th>Credit TPw</th><th>recall_w</th><th>Credit/dot</th></tr></thead><tbody>
<tr><td><code>losfo</code> — 600 m buffer erased from training labels</td><td>{fmt_number(lo_arms.get('losfo', {}).get('mean_dti', 0), 5)}</td><td>{fmt_number(lo_arms.get('losfo', {}).get('sum_tp', 0), 1)}</td><td>{fmt_number(lo_arms.get('losfo', {}).get('recall_w', 0), 4)}</td><td>{fmt_number(lo_arms.get('losfo', {}).get('credit_per_dot', 0), 4)}</td></tr>
<tr><td><code>leaky</code> — unmasked control, same truth</td><td>{fmt_number(lo_arms.get('leaky', {}).get('mean_dti', 0), 5)}</td><td>{fmt_number(lo_arms.get('leaky', {}).get('sum_tp', 0), 1)}</td><td>{fmt_number(lo_arms.get('leaky', {}).get('recall_w', 0), 4)}</td><td>{fmt_number(lo_arms.get('leaky', {}).get('credit_per_dot', 0), 4)}</td></tr></tbody></table></div>
<p><strong>Result, stated with its uncertainty.</strong> Pooled ratio <code>losfo/leaky</code> = <strong>{fmt_number(lo_ratio.get('credit_losfo_over_leaky', 0), 4)}</strong> on credit and {fmt_number(lo_ratio.get('mean_dti_losfo_over_leaky', 0), 4)} on DTI: the base arm keeps ~99% of its far-field credit when 600 m of surrounding catalogue is hidden, so <strong>no large catalogue-interpolation inflation was detected</strong>. But the per-fold credit ratios are <strong>{esc(fold_spread)}</strong> — a spread of roughly −12% to +20% — so with 5 seeds this harness <strong>cannot resolve effects smaller than about ±12% per fold</strong>. The aggregate is a bound, not a measurement of a small effect. Two confounds are recorded, not smoothed over: the masked arm also has fewer positive training pixels ({comma(int(lo_meta.get('masked_label_px', 0)))} vs {comma(int(lo_meta.get('full_label_px', 0)))}), and held-out systems are still <em>mapped</em> faults, so this measures an <strong>upper bound</strong> on performance against genuinely unmapped faults. What is solidly gained: <strong>a far-field truth set on which addition arms can be gated</strong>, with a measured base operating point (recall_w {fmt_number(lo_arms.get('losfo', {}).get('recall_w', 0), 4)}, credit/dot {fmt_number(lo_arms.get('losfo', {}).get('credit_per_dot', 0), 4)}) to beat.</p></section>

<section class="section"><h2>H34: the packing ladder, and the threshold every arm was judged against</h2>
<div class="callout"><strong>State (session 10b, 2026-10-03): gate {esc(str(h34_gate.get('overall', 'FAIL')).upper())}, arm CLOSED.</strong> The preregistered holdout ran once on fresh seeds 220–229 (40 cells, 4 spatially blocked folds × 10 seeds). Criterion 1 passed — the measured removal efficiency of the <code>2.828 → 3.000</code> rung step is <strong>{fmt_number(h34_s1.get('mean_efficiency', 0), 5)}</strong>, below the live break-even {fmt_number(h34_thr.get('live_submission', {}).get('tau', 0), 5)}, with {esc(h34_s1.get('seeds_below_tau_live', 0))}/10 seeds and {esc(h34_s1.get('folds_below_tau_live', 0))}/4 folds agreeing. Criterion 2, the direction control, <strong>failed</strong>: the next rung measures {fmt_number(h34_s2.get('mean_efficiency', 0), 5)}, also below the threshold, so the proxy rates every step profitable and cannot locate a stopping rung. Per the frozen protocol: no confirmation, no retuning on 220–229, <strong>no candidate TIFF, no weekly slot</strong>. The primary download is unchanged.</div>
<div class="grid"><article class="card span-6"><h3>Why the proxy cannot see the stopping rung</h3><p>Removal efficiency scales with credit per dot, because <code>e</code> is credit lost divided by mass shed and both scale with how densely an emission covers truth. The proxy detector earns <strong>{fmt_number(h34_hold.get('variant_summary', {}).get('rung_2_828', {}).get('mean_tpw', 0) / max(h34_hold.get('variant_summary', {}).get('rung_2_828', {}).get('mean_n', 1), 1), 5)}</strong> credit per dot; the H19-5 surface earns <strong>{fmt_number(4791.0488856019765 / 44090, 5)}</strong> — {fmt_number((4791.0488856019765 / 44090) / max(h34_hold.get('variant_summary', {}).get('rung_2_828', {}).get('mean_tpw', 1) / max(h34_hold.get('variant_summary', {}).get('rung_2_828', {}).get('mean_n', 1), 1), 1e-9), 2)}× more. That flattens the proxy's efficiency ladder by {fmt_number(h34_steps.get(3.0, {}).get('efficiency', 0) / max(h34_s2.get('mean_efficiency', 1e-9), 1e-9), 1)}× on the decisive step, so it would keep thinning indefinitely — which is false, since DTI goes to zero at infinite spacing.</p></article>
<article class="card span-6"><h3>The threshold result that outlives the arm</h3><p>A pixel class with removal efficiency <code>e</code> is worth dropping iff <code>e &lt; τ = 0.2·DTI/(1−0.2·DTI)</code>, which <strong>rises with DTI</strong>. The catalogue-holdout proxy scores {fmt_number(h34_thr.get('proxy', {}).get('dti', 0), 4)} → τ = <strong>{fmt_number(h34_thr.get('proxy', {}).get('tau', 0), 5)}</strong>. The 0.2600 submission those harnesses inform scores {fmt_number(h34_thr.get('live_submission', {}).get('dti', 0), 4)} → τ = <strong>{fmt_number(h34_thr.get('live_submission', {}).get('tau', 0), 5)}</strong>, <strong>{fmt_number(h34_thr.get('ratio_live_over_proxy', 0), 2)}× more permissive</strong>. Any arm whose efficiency lies in (0.019, 0.055) was rejected by a threshold that does not apply to it.</p><p>The rule is confirmed empirically: on 40 independent cells the proxy's ΔDTI crosses zero at measured e = {fmt_number(h34_s1.get('mean_efficiency', 0), 5)} against predicted τ = {fmt_number(h34_thr.get('proxy', {}).get('tau', 0), 5)} (ΔDTI {fmt_number(h34_s1.get('mean_d_dti', 0), 6)}), and the next step at e = {fmt_number(h34_s2.get('mean_efficiency', 0), 5)} &gt; τ gives ΔDTI {fmt_number(h34_s2.get('mean_d_dti', 0), 6)} — right sign, right magnitude.</p></article></div>
<div class="grid"><article class="card span-6"><h3>A modelling error found and fixed</h3><p>The new module closed the metric as <code>FP = N − A</code>, charging every emitted pixel full false-positive mass. That is not the metric: it ignores the crowding excess <code>Ã − A</code>, which the inversion measures as <strong>0.18×, 0.43× and 1.46× of A</strong> on the three anchors — a factor-of-eight range no fit can absorb. Corrected to <code>FP = (1−γ)N</code> with γ = Ã/N <strong>measured</strong> at <code>0.12569 / 0.12576 / 0.12811</code> — constant to 1.9 %, exactly what non-selective thinning predicts. A second error: the retention curve is measured on a network with 1:1 dot-to-truth density while the surface runs ~10:1, so one fitted <strong>density scale</strong> rescales the loss.</p><p>With L, |G| and γ all measured the model has <strong>one</strong> free parameter (s = {fmt_number(h34_fit.get('density_scale', 0), 4)}) and reproduces three hash-authenticated live scores to ≤ {h34_fit.get('max_abs_residual', float('nan')):.2e}. The old two-parameter fit is <strong>rejected</strong>: it fits to 3.2e-04 but recovers |G| = {comma(int(h34.get('two_parameter_fit', {}).get('truth_px', 0)))}, <strong>{fmt_number(abs(h34.get('two_parameter_fit', {}).get('external_check', {}).get('relative_difference', 0)) * 100, 1)} % below</strong> the blind lattice.</p></article>
<article class="card span-6"><h3>What the corrected model says</h3><p>Best rung is <strong>{fmt_number(h34_lad.get('best_rung', 0), 4)} → N = {comma(int(h34_lad.get('best_n_emitted', 0)))}</strong>, DTI {fmt_number(h34_lad.get('best_dti', 0), 5)} against {fmt_number(h34_lad.get('current_dti', 0), 5)} at the shipped rung, i.e. <strong>+{fmt_number(h34_lad.get('delta_dti_best_minus_current', 0), 5)}</strong> — stable across the whole plausible range of s. And it <em>does</em> satisfy the direction control the proxy missed: <code>e(3.000→3.162) = {fmt_number(h34_steps.get(3.0, {}).get('efficiency', 0), 5)}</code> &gt; τ = {fmt_number(h34_steps.get(3.0, {}).get('breakeven_tau', 0), 5)}, so the next rung is correctly judged unprofitable.</p><p><strong>This does not reopen the arm.</strong> A model projection is not a validated result, and the preregistration is binding. The corrected closure is algebraically identical to the one the reachability frontier above already uses — substituting ρ = γN/A makes the denominators equal term for term — so the two sessions' arithmetic agrees; only the new module had the bug. It is now guarded by <code>tests/test_operating_point.py</code>.</p></article></div>
<p><a href="../knowledge/21_preregistration_H34.md">Frozen H34 protocol</a> · <a href="../knowledge/22_h34_result.md">H34 result record</a> · <a href="../evidence/h34_holdout.json">Holdout evidence JSON</a> · <a href="../evidence/h34_operating_point.json">Operating-point evidence JSON</a> · <a href="../scripts/run_h34_holdout.py">Holdout runner source</a> · <a href="../src/gems27/operating_point.py">Operating-point module</a></p></section>
{session11_section(h35 or {}, h35_6 or {})}
{h33_section}
<section class="section"><h2>Historical Session 10 H33 queue — preserved, not the current ranking</h2><p>This earlier four-item register is retained for continuity and is superseded by the Session 14 ranking above. “Untried” in the archived entries describes their state when that queue was written, not a claim of global scientific novelty. H31-1 status: {esc(h31_result_summary(screen, confirmation, seed_audit))} {esc(h32_result_summary(h32))}</p><div class="grid">{hypothesis_html}</div></section>

<section class="section"><h2>H31-1: depth-labeled Euler source solutions, not gradient peaks</h2><div class="callout"><strong>State:</strong> protocol revision 2 is committed at 524bf27 before any classifier fit or holdout; the current label-free feature build is bound to it and passes all three pre-fit data-sufficiency checks. Earlier protocol commit hashes cited by prior working-copy artifacts are absent from this checkout's Git history; the initial build's commit chronology is not proven and is disclosed in the history audit. Magnetic field units remain unauthenticated. H31 current outcome: {esc(h31_result_summary(screen, confirmation, seed_audit))} No H31 submission candidate has been created. Local seed audit status {esc(seed_audit.get('status', 'not recorded'))} covers {comma(len(seed_audit.get('evidence_json_sha256_scanned', {})))} evidence JSON files; screen seeds 160–169 are {esc(seed_range_label(seed_audit, 'screen'))} by the failed H31-1 screen, and seeds 170–179 are {esc(seed_range_label(seed_audit, 'h32_1_screen'))} by the single H32-1 screen, so the H31-1 confirmation decade no longer exists. External/sibling-workspace seed use remains unknowable. {esc(h31_next_step(screen, confirmation, seed_audit))}</div>
<div class="grid"><article class="card span-6"><h3>What was built</h3><ul><li>Source field: owner-mirror band 14 <code>tmi</code>; embedded unit tags are absent.</li><li>Euler system solves for source coordinates, depth and base-level offset in 10 × 10 windows; source windows are screened and solutions clustered.</li><li>SI-0 primary: {comma(summary.get('n', 0))} accepted source solutions; {comma(clusters.get('aligned_solution_count', 0))} aligned to gradient ridges within 200 m; {comma(clusters.get('retained_cluster_count', 0))} retained depth-coherent clusters.</li><li>Median SI-0 depth {fmt_number(summary.get('depth_m_median'), 1)} m (P10 {fmt_number(summary.get('depth_m_p10'), 1)}, P90 {fmt_number(summary.get('depth_m_p90'), 1)}); output estimates are not verified geological depths.</li><li>Vertical-derivative coverage: {fmt_number(euler.get('derivative', {}).get('vertical_coverage_share_of_valid_field', 0) * 100, 1)}% of valid TMI cells.</li></ul></article>
<article class="card span-6"><h3>Structural-index instability</h3><p>SI-1 retains {comma(h1.get('sensitivity_clusters', 5665))} clusters; {fmt_number(h1.get('matched_primary_share_within_600m', 0)*100, 1)}% of SI-0 centroids match within 600 m and median nearest-centroid distance is {fmt_number(h1.get('median_nearest_centroid_distance_m', 0), 0)} m.</p><p>SI-2 retains {comma(h2.get('sensitivity_clusters', 4661))} clusters; {fmt_number(h2.get('matched_primary_share_within_600m', 0)*100, 1)}% match within 600 m and median distance is {fmt_number(h2.get('median_nearest_centroid_distance_m', 0), 0)} m. SI=1/2 are descriptive sensitivity checks, not alternative indices to select after seeing a favorable holdout.</p></article></div>
<p>SI=0 approximates an idealized contact with effectively infinite depth extent. Real faults may be finite, dipping, intersecting or have mixed geometry and may require higher indices. Euler does not estimate dip; the structural index is a geological model choice, not an automatically “correct” value. Candidate gradient ridges are used only to test alignment with Euler-derived source solutions, never as the inferred source locations.</p>
<p>Official USGS GeoDAWN metadata reports nominal magnetic flight-line spacing of 200 m in Area 1 and 400 m in Area 2, with variable terrain clearance. The 100 m output grid is not independent 100 m survey resolution. The exact pinned mirror is not organizer-authenticated, and derivative units/conventions have not been calibrated against survey units.</p>
<p><a href="../knowledge/12_preregistration_H31-1_euler.md">Frozen H31-1 protocol</a> · <a href="../evidence/euler_input_audit.json">Input/convention audit</a> · <a href="../evidence/h31_1_euler_feature_audit.json">Label-free feature/depth audit</a> · <a href="../evidence/h31_1_prereg_history_audit.json">Protocol-history disclosure</a> · <a href="../evidence/h31_1_seed_reuse_audit.json">Local seed-reuse audit</a> · <a href="../evidence/h31_1_euler_clusters.csv">Depth-labeled cluster table</a> · {h31_evidence_links(screen, confirmation)} · <a href="https://doi.org/10.1190/1.1442774">Reid et al. (1990), DOI</a></p></section>

<section class="section"><h2>H32-1: structural-step coherence of depth-to-base, conductivity and strain derivatives</h2><div class="callout"><strong>State:</strong> one preregistered screen ran on seeds 170–179 with the frozen protocol bytes matching the committed blob. {esc(h32_result_summary(h32))} Six deterministic label-free derivative features (robust-scaled |∇| at 300 m/1 km, Laplacian curvature, both-strong concordance and |cos| orientation agreement between conductivity-base and depth gradients, and a strain step) were appended to the unchanged 38-column H28-1/T-v2/r1 control. The candidate cache is SHA-256-pinned in the evidence record; no candidate TIFF exists. Per the preregistration no retuning, rerun or confirmation is permitted on these seeds; the next new hypothesis needs a fresh decade (180–189).</div>
<p><a href="../knowledge/14_preregistration_H32-1.md">Frozen H32-1 protocol</a> · <a href="../knowledge/15_h32_1_result.md">H32-1 result record</a> · <a href="../evidence/h32_1_structural_step_holdout.json">Screen evidence JSON</a> · <a href="../evidence/h31_1_seed_reuse_audit.json">Local seed-reuse audit</a> · <a href="../src/gems27/structural_step.py">Feature transform source</a></p></section>

<section class="section"><h2>H32-2: shallow-over-deep magnetic gradient de-screening — FROZEN GATE FAILED (closed)</h2><div class="callout"><strong>State (session 9, 2026-10-03):</strong> the preregistered screen (<a href="../knowledge/16_preregistration_H32-2.md">frozen protocol</a>, SHA-256 recorded in the evidence JSON) ran once on fresh seeds 190–199 and <strong>failed every gain criterion</strong>: mean paired ΔDTI −0.003767 for the primary p10 prune (0/10 seeds, 0/4 folds; p05 variant −0.001776, also 0/10). The direction control supported the physics — pruning the <em>shallowest</em> dots loses more credit per removed FP (0.038273) than pruning the deepest (0.034350) — but the deep-magnetic dot class still carries ≈1.78× the OOF inclusion threshold (0.019265), so it is not removable false-positive mass on this proxy. Per the frozen protocol the arm is <strong>closed</strong>: no confirmation, no retuning, no candidate TIFF, no weekly slot. Run 1 was invalidated by a runner data-check defect (the float32 nodata sentinel |v| ≥ 1e30 was ingested into the P99 scaling, collapsing the attenuation ratio); the invalid record is preserved and the repaired run used the repository's frozen validity rule with no gate change.</div>
<p><a href="../knowledge/16_preregistration_H32-2.md">Frozen H32-2 protocol + run-1 integrity correction</a> · <a href="../knowledge/17_h32_2_result.md">H32-2 result record</a> · <a href="../evidence/h32_2_holdout.json">Valid screen evidence JSON</a> · <a href="../evidence/h32_2_holdout_run1_invalid_2026-10-03.json">Preserved invalid run 1</a> · <a href="../scripts/run_h32_2_holdout.py">Runner source</a></p></section>

<section class="section"><h2>H28-1 benchmark and candidate file</h2><p>The paired hide-and-recover screen compared H28-1 multiscale magnetic/gravity edge-coherence features against the best comparable same-run control, across spatially blocked folds and seeds 140–149. The mean paired catalogue proxy ΔDTI was {fmt_number(candidate.get('holdout_mean_gain', 0.002948838794400959), 6)}, with 3/4 folds and 9/10 seed means positive; the frozen screen gate passed. This is not a leaderboard score and does not establish transfer to expert-created faults outside the catalogue habitat.</p><p>Candidate filename: <code>{esc(candidate.get('nan', ''))}</code>. Its full-map construction is separate from the holdout-only fit and no current GEMSDOE28 upload exists. It is not one of the four weekly slots inherited from the predecessor project. The file is an auditable research reference, not a submission recommendation.</p><p>Local manual downloads: <a href="downloads/{esc(candidate.get('nan', ''))}" download>{esc(candidate.get('nan', ''))}</a> · <a href="downloads/{esc(candidate.get('allfinite', ''))}" download>{esc(candidate.get('allfinite', ''))}</a> · <a href="downloads/{esc(candidate.get('zip', ''))}" download>{esc(candidate.get('zip', ''))}</a>.</p><p><a href="../evidence/h28_1_edge_holdout.json">Holdout evidence</a> · <a href="../knowledge/08_preregistration_H28-1.md">H28-1 preregistration</a> · <a href="../knowledge/09_preregistration_H28-1_candidate.md">Full-map candidate construction record</a></p>
<p>Current Session 14 ranking and source checks: <a href="../knowledge/37_ranked_hypotheses_session14_2026-10-03.md">knowledge/37</a>. H38-1 frozen protocol: <a href="../knowledge/38_preregistration_H38-1.md">knowledge/38</a>. Single-use run close-out: <a href="../knowledge/39_session14_closeout_2026-10-03.md">knowledge/39</a>. Earlier hypothesis queues: <a href="../knowledge/18_new_hypotheses_H33_series_2026-10-03.md">knowledge/18</a> and <a href="../knowledge/13_current_ranked_hypotheses_2026-10-03.md">knowledge/13</a>.</p></section>

<section class="section"><h2>Promotion gate and what counts</h2><div class="table-wrap"><table><thead><tr><th>Stage</th><th>Required evidence</th><th>What it is not</th></tr></thead><tbody>
<tr><td>Pre-fit</td><td>Freeze transform, data and provenance, folds/draws, response, model, metrics, seeds, analysis and gate; run label-free sufficiency only.</td><td>Not permission to tune thresholds on a held-out seed.</td></tr>
<tr><td>Screen</td><td>Paired spatial hide-and-recover against the best same-run control; frozen gate on all seeds/folds and integrity checks.</td><td>Not a public/private leaderboard result.</td></tr>
<tr><td>Confirmation</td><td>One unchanged independent seed range and exact code/data/evidence hashes.</td><td>Not a second chance to adjust the candidate.</td></tr>
<tr><td>Promotion</td><td>Reproducible superiority, confirmation, separate proxy-transfer assessment and exact-file audit.</td><td>Not automatic approval to consume a weekly slot.</td></tr>
</tbody></table></div><p>A candidate must not spend a weekly slot until every predeclared gate is met. The catalogue hide-and-recover task is necessarily a proxy: labels are mostly faults already represented in a published catalogue and do not provide an independent sample of hidden expert-created, far-field faults.</p></section>

<section class="section"><h2>Live score and leaderboard boundaries</h2><p>A one-off manual public-page observation on {esc(board.get('snapshot_date', 'not recorded'))} records DARD #1 at 0.3195 and wbg1 #15 at 0.2600. A public leaderboard row alone does not link a score to the repository owner or a local TIFF. The owner-reported 0.2477 is likewise unverified without an organizer receipt. No row is treated as a score claim for this project. <a href="{esc(board.get('url', 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'))}">Manual-review link</a>; automated access and monitoring are prohibited by project policy.</p></section>
<section class="section"><h2>Historical screen archive (superseded)</h2><div class="callout"><strong>Archive marker:</strong> the predecessor project used the heading “Current Session 5 untried screen (4 hypotheses).” That was a dated four-item view. The Session 10 H33 queue preserved above contains the {n_untried} H33-series entries ({", ".join(untried)}); H33-1 was run on its reserved seeds 200–209 and refuted. Session 14’s five H38 candidates above are the current ranked list. Nothing in this archive section is the current untried list.</div>
<h3>H27-10 annulus result — REJECTED; no weekly slot.</h3><p>The frozen 100–300 m annulus/reallocation gate on seeds 150–159 failed: mean paired ΔDTI +0.000846, 4/4 fold means but only 7/10 seed means improved, and annulus gross efficiency 0.03357 was below the 0.05212 live break-even estimate. A spacing-check bug in the first diagnostic was corrected for an integrity rerun on the same seeds; values and the frozen FAIL did not change. This is not fresh confirmation.</p><p>Evidence: <a href="../evidence/h27_10_annulus_holdout_initial.json">h27_10_annulus_holdout_initial.json</a> · <a href="../evidence/h27_10_annulus_holdout.json">corrected integrity rerun</a> · <a href="../knowledge/07_untried_hypotheses.md">historical disclosure</a>. The rejected H27-10 arm is not part of the current untried list and is not eligible to justify a weekly slot.</p></section>
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
<p><a href="../registry/sources.json">Download the machine-readable source ledger</a> · <a href="../registry/irregularities.json">Review disclosed irregularities</a> · <a href="../registry/data_manifest.json">Review input hashes and provenance labels</a> · <a href="../AI_DISCLOSURE.md">Generative-AI use disclosure</a>.</p></section>
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
    frontier = read_json("evidence/reachability_frontier.json", {})
    losfo = read_json("evidence/losfo_farfield_diagnostic.json", {})
    h33 = read_json("evidence/h33_1_holdout.json", {})
    h34 = read_json("evidence/h34_operating_point.json", {})
    h34_hold = read_json("evidence/h34_holdout.json", {})
    h35 = read_json("evidence/h35_1_thermal_farfield.json", {})
    h35_6 = read_json("evidence/h35_6_candidate_headtohead.json", {})
    h38_result = read_json("evidence/h38_1_holdout.json", {})
    h38_claim = read_json("evidence/h38_1_holdout.started.json", {})
    pages = {
        "index.html": layout("Overview", render_index(manifest, board, euler, range_audit, restore, screen, confirmation, seed_audit, h32, h35, h35_6, h38_result, h38_claim), "Overview"),
        "executive-summary.html": layout("Executive summary", render_executive(manifest, board, file_audit, range_audit, screen, confirmation, seed_audit, h32), "Executive summary"),
        "research.html": layout("Research and hypotheses", render_research(hypotheses, h28_manifest, euler, board, screen, confirmation, seed_audit, h32, frontier, losfo, h33, h34, h34_hold, h35, h35_6, h38_result, h38_claim), "Research"),
        "topology.html": layout("Topology review", render_topology(manifest, irregularities, sources, topology_review), "Topology"),
        "sources.html": layout("Sources and verification", render_sources(sources, board), "Sources"),
    }
    DOCS.mkdir(parents=True, exist_ok=True)
    for name, content in pages.items():
        (DOCS / name).write_text(publish_source_links(content), encoding="utf-8")
    (ROOT / "index.html").write_text(root_relative_links(pages["index.html"]), encoding="utf-8")
    print(json.dumps({"status": "built", "pages": sorted(pages), "sources": len(sources.get("sources", [])),
                      "hypotheses": len(hypotheses.get("session14_addendum", {}).get("ranked_hypotheses", [])),
                      "generated_from_json_only": True, "external_requests": 0,
                      "primary_download": manifest["primary"]["nan"]}, indent=2))
    return 0


if __name__ == "__main__":
    import json
    raise SystemExit(main())
