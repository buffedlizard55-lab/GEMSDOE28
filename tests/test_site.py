import hashlib
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGES = ["index.html", "executive-summary.html", "topology.html", "research.html", "sources.html"]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        for k in ("href", "src"):
            if k in d:
                self.refs.append(d[k])
        if "id" in d:
            self.ids.add(d["id"])


def test_site_builds_from_json_only_and_pages_exist():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["hypotheses"] == 5
    for p in PAGES:
        assert (DOCS / p).is_file() and (DOCS / p).stat().st_size > 2000


def test_build_site_workflow_tracks_generator_inputs_and_outputs():
    workflow = (ROOT / ".github" / "workflows" / "build-site.yml").read_text()
    builder = (ROOT / "scripts" / "build_site.py").read_text()
    inputs = {
        line.split('read_json("', 1)[1].split('"', 1)[0]
        for line in builder.splitlines()
        if 'read_json("' in line
    }
    inputs.add("docs/downloads/h28_1_candidate_manifest.json")
    for path in inputs | {
        "docs/data/topology_review_classes.json",
        "evidence/losfo_h38_1_raw.json",
        "evidence/h38_1_seed_audit_pre_run.json",
        "knowledge/39_session14_closeout_2026-10-03.md",
        "AI_DISCLOSURE.md",
        "scripts/build_site.py",
        ".github/workflows/build-site.yml",
        "docs/assets/**",
        "docs/*.html",
        "index.html",
    }:
        assert workflow.count(f"'{path}'") == 2, f"missing push/pull_request trigger for {path}"


def test_h31_site_status_distinguishes_screen_confirmation_and_proxy_results(tmp_path, monkeypatch):
    from scripts import build_site

    monkeypatch.setattr(build_site, "ROOT", tmp_path)
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()

    def report(stage, passed, gain, positive_folds, positive_seeds):
        seeds = list(range(160, 170)) if stage == "screen" else list(range(170, 180))
        filename = f"h31_1_euler_{'screen' if stage == 'screen' else 'confirm'}.started.json"
        relative = f"evidence/{filename}"
        provenance = {
            "protocol_commit": "pinned-protocol", "protocol_sha256": "protocol-hash",
            "input_hashes": {"input": "input-hash"}, "feature_hashes": {"feature": "feature-hash"},
            "code_hashes": {"runner": "code-hash"}, "runtime_versions": {"python": "3.x"},
        }
        claim = {"stage": stage, "seeds": seeds, **provenance}
        claim_bytes = (json.dumps(claim, indent=2) + "\n").encode()
        (evidence_dir / filename).write_bytes(claim_bytes)
        result = {
            "schema": 1, "stage": stage, "seeds": seeds, **provenance,
            "single_use_seed_claim": {"path": relative, "sha256": hashlib.sha256(claim_bytes).hexdigest()},
            "gate": {"passed": passed},
            "summary": {"mean_paired_gain": gain, "positive_fold_count": positive_folds,
                        "positive_seed_count": positive_seeds},
            "submission_raster_written": False, "drivendata_access": False, "sha256": None,
        }
        result["sha256"] = hashlib.sha256(
            json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return result

    unused = {"status": "PASS", "range_status": {"screen": "UNUSED", "confirmation": "UNUSED"}}
    assert build_site.h31_result_summary({}, {}, unused) == "No H31 classifier fit or holdout has been run."
    assert build_site.h31_hypothesis_status({}, {}, unused) == "SCREEN PENDING — label-free feature build only"
    screen_pass = report("screen", True, 0.0012, 3, 8)
    consumed = {"status": "PASS", "range_status": {"screen": "CONSUMED", "confirmation": "UNUSED"}}
    screen_text = build_site.h31_result_summary(screen_pass, {}, consumed)
    assert "Screen frozen gate PASS" in screen_text
    tampered = json.loads(json.dumps(screen_pass))
    tampered["summary"]["mean_paired_gain"] = 99.0
    assert "Screen frozen gate UNVERIFIED" in build_site.h31_result_summary(tampered, {}, consumed)
    assert "catalogue-proxy" in screen_text and "Confirmation on seeds 170–179 remains required" in screen_text
    assert "weekly slot" in screen_text
    assert build_site.h31_hypothesis_status(screen_pass, {}, consumed) == "SCREEN PASSED — unchanged confirmation required; not slot-approved"
    research = (DOCS / "research.html").read_text()
    front_page = (DOCS / "index.html").read_text()
    assert "No model fit, holdout score, confirmation, or promotion decision." not in front_page
    assert "The feature build is label-free; H31 screen outcome is shown above." in front_page
    assert "screen evidence" in front_page
    assert "single-use screen claim" in front_page
    assert "Screen frozen gate FAIL" in front_page
    assert "Screen frozen gate FAIL" in research
    assert "single-use screen claim" in research
    assert "minimum spacing below 1.5 px in 40/40 cells" in research
    assert "control 40/40; candidate 39/40" in research
    assert "all other listed integrity checks passed" in research
    assert "screen evidence" in research
    assert "screen seeds 160–169 are consumed locally" in research
    assert "seeds 170–179 are consumed locally by the single H32-1 screen" in research
    assert "the H31-1 confirmation decade no longer exists" in research
    assert "SCREEN PENDING — label-free feature build only" not in research
    assert "H32-1 structural-step frozen screen FAIL" in front_page
    assert "H32-1 structural-step frozen screen FAIL" in research
    assert "UNTRIED HOLDOUT: feature build only; no model fit or candidate TIFF." not in research
    confirm_fail = report("confirmation", False, -0.0001, 1, 4)
    both_consumed = {"status": "PASS", "range_status": {"screen": "CONSUMED", "confirmation": "CONSUMED"}}
    failed_text = build_site.h31_result_summary(screen_pass, confirm_fail, both_consumed)
    assert "Confirmation frozen gate FAIL" in failed_text and "rejects the arm for submission" in failed_text
    assert "weekly slot" in build_site.h31_next_step(screen_pass, confirm_fail, both_consumed)
    interrupted = {"status": "PASS", "range_status": {"screen": "INCOMPLETE", "confirmation": "UNUSED"}}
    assert "interrupted" in build_site.h31_result_summary({}, {}, interrupted)
    assert "do not rerun" in build_site.h31_next_step({}, {}, interrupted)
    stray_confirmation = {"status": "PASS", "range_status": {"screen": "UNUSED", "confirmation": "INCOMPLETE"}}
    assert "without a final screen/confirmation" in build_site.h31_result_summary({}, {}, stray_confirmation)
    assert "without a screen report" in build_site.h31_next_step({}, {}, stray_confirmation)


def test_h38_result_requires_consumed_claim_raw_hash_and_frozen_gate_integrity(tmp_path, monkeypatch):
    from scripts import build_site

    monkeypatch.setattr(build_site, "ROOT", tmp_path)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    raw_path = evidence / "losfo_h38_1_raw.json"
    raw_path.write_text('{"fixture": true}\n')
    raw_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    code = {
        "knowledge/38_preregistration_H38-1.md": "a" * 64,
        "scripts/run_losfo_harness.py": "b" * 64,
        "src/gems27/losfo.py": "c" * 64,
        "src/gems27/oof_detector.py": "d" * 64,
        "src/gems27/metric.py": "e" * 64,
        "src/gems27/thinning.py": "f" * 64,
        "src/gems27/holdout.py": "1" * 64,
        "src/gems27/grid.py": "2" * 64,
        "src/gems27/paths.py": "3" * 64,
        "src/gems27/packing.py": "4" * 64,
    }
    runtime = {"python": "3.12.0", "numpy": "2.0.0", "scipy": "1.14.0", "scikit_learn": "1.5.0", "rasterio": "1.4.0"}
    claim = {
        "schema": 1, "status": "CONSUMED", "arm_name": "H38-1 shallow Euler × gravity × low-relief licence",
        "seeds": list(range(265, 270)), "reserved_utc": "2026-10-03T00:00:00Z",
        "protocol_commit": "freeze", "protocol_branch": "arena/01a10412-gemsdoe28",
        "run_commit": "reservation", "run_branch": "arena/01a10412-gemsdoe28",
        "preregistration": "knowledge/38_preregistration_H38-1.md", "preregistration_sha256": code["knowledge/38_preregistration_H38-1.md"],
        "candidate_csv": "evidence/h38_1_candidate_clusters.csv", "candidate_csv_sha256": "5" * 64,
        "candidate_count": 140, "sufficiency_audit": "evidence/h38_1_sufficiency_audit.json",
        "sufficiency_audit_sha256": "6" * 64, "pre_run_seed_audit": "evidence/h38_1_seed_audit_pre_run.json",
        "input_sha256": {"evidence/h38_1_candidate_clusters.csv": "5" * 64}, "code_sha256": code,
        "runtime_versions": runtime, "baseline": {"path": "evidence/losfo_h37_3_licence.json", "sha256": "7" * 64},
        "result_paths": {"raw": "evidence/losfo_h38_1_raw.json", "summary": "evidence/h38_1_holdout.json"},
        "raw_result_sha256": raw_hash, "seed_range_burned": True, "holdout_started": True,
        "submission_slot_used": False, "promotable": True,
        "summary_result_path": "evidence/h38_1_holdout.json",
    }
    code_map = {
        "runner": "scripts/run_losfo_harness.py", "losfo": "src/gems27/losfo.py",
        "oof_detector": "src/gems27/oof_detector.py", "metric": "src/gems27/metric.py",
        "thinning": "src/gems27/thinning.py", "holdout": "src/gems27/holdout.py",
        "grid": "src/gems27/grid.py", "paths": "src/gems27/paths.py", "packing": "src/gems27/packing.py",
    }
    runner_recorded = {key: code[path] for key, path in code_map.items()}
    gate_names = {
        "C1_positive_and_spatially_repeatable", "C2_live_economic_bar",
        "C3_candidate_beats_matched_random", "C4_support_and_integrity",
        "C5_beats_previous_farfield_add_arm_best",
    }
    report = {
        "schema": 1, "seeds": list(range(265, 270)),
        "folds": ["NW", "NE_LidarGapHeavy", "SW", "SE"],
        "protocol_freeze_commit": "freeze", "reservation_commit": "reservation",
        "claim_fingerprint": build_site.h38_claim_fingerprint(claim),
        "raw_result": {"path": "evidence/losfo_h38_1_raw.json", "sha256": raw_hash},
        "source_records": {"candidate_sufficiency": claim["sufficiency_audit"], "baseline": claim["baseline"]["path"]},
        "candidate": {"csv": claim["candidate_csv"], "csv_sha256": claim["candidate_csv_sha256"],
                      "count": 140, "sufficiency_audit_sha256": claim["sufficiency_audit_sha256"]},
        "benchmark": {"sha256": claim["baseline"]["sha256"]}, "runtime_versions": runtime,
        "code_sha256": {**code, "runner_recorded": runner_recorded},
        "preregistration": {"path": claim["preregistration"], "sha256": claim["preregistration_sha256"]},
        "gates": {name: {"passed": True} for name in gate_names},
        "promotable": True, "status": "PASS",
        "summary": {"mean_delta_dti_licence_vs_base": 0.001, "credit_per_added_dot": 0.06,
                    "positive_cells": 18, "positive_seed_means": 5, "positive_fold_means": 4},
        "sha256": None,
    }
    report["sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    result_path = evidence / "h38_1_holdout.json"
    result_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    claim["summary_result_sha256"] = hashlib.sha256(result_path.read_bytes()).hexdigest()

    assert build_site.h38_result_integrity(report, claim)
    assert "frozen LOSFO gate PASS" in build_site.h38_status_html(report, claim)
    tampered = json.loads(json.dumps(report))
    tampered["summary"]["mean_delta_dti_licence_vs_base"] = 0.9
    assert not build_site.h38_result_integrity(tampered, claim)
    assert "H38-1 claim state: RUNNING" in build_site.h38_status_html({}, {"status": "RUNNING"})
    assert "report artifact exists but its consumed-claim/hash chain is missing or invalid" in build_site.h38_status_html({"schema": 1}, {})
    assert not build_site.h38_result_integrity({"gates": None}, {"code_sha256": None})


def test_failed_h38_claim_discloses_missing_gate_and_links_raw_artifact(tmp_path, monkeypatch):
    from scripts import build_site

    evidence = tmp_path / "evidence"
    evidence.mkdir()
    for name in ("h38_1_holdout.started.json", "h38_1_seed_audit_pre_run.json", "losfo_h38_1_raw.json"):
        (evidence / name).write_text("{}")
    monkeypatch.setattr(build_site, "ROOT", tmp_path)
    html = build_site.h38_status_html({}, {
        "status": "FAILED",
        "failure_detail": "TypeError: Object of type int64 is not JSON serializable",
    })
    assert "no frozen-gate decision is available" in html
    assert "not validation" in html
    assert "TypeError: Object of type int64 is not JSON serializable" in html
    assert "../evidence/losfo_h38_1_raw.json" in html
    assert "raw run (unverified; no gate summary)" in html


def test_all_internal_links_and_assets_resolve():
    for base, p in [(DOCS, q) for q in PAGES] + [(ROOT, "index.html")]:
        parser = Links()
        parser.feed((base / p).read_text())
        for ref in parser.refs:
            if re.match(r"^(https?:|mailto:|#|data:)", ref):
                continue
            target = ref.split("#")[0]
            assert (base / target).exists(), f"{base.name}/{p}: broken internal reference {ref}"


def test_pages_source_links_resolve_to_public_repository_files():
    for page in PAGES:
        text = (DOCS / page).read_text()
        assert 'href="../evidence/' not in text
        assert 'href="../knowledge/' not in text
        assert 'href="../registry/' not in text
    research = (DOCS / "research.html").read_text()
    assert "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/h31_1_prereg_history_audit.json" in research
    assert "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/12_preregistration_H31-1_euler.md" in research


def test_repository_root_front_page_serves_the_one_click_download():
    man = json.loads((DOCS / "downloads" / "manifest.json").read_text())
    root_idx = (ROOT / "index.html").read_text()
    P = man["primary"]
    assert f'href="docs/downloads/{P["nan"]}"' in root_idx and "download" in root_idx
    assert (ROOT / ".nojekyll").exists()


def test_front_page_has_download_and_exact_note():
    man = json.loads((DOCS / "downloads" / "manifest.json").read_text())
    idx = (DOCS / "index.html").read_text()
    P = man["primary"]
    assert f'href="downloads/{P["nan"]}"' in idx and "download" in idx
    assert (DOCS / "downloads" / P["nan"]).is_file() and (DOCS / "downloads" / P["zip"]).is_file()
    assert P["note"] in idx.replace("&#x27;", "'") or P["note"].replace("|", "|") in idx
    assert len(P["note"]) <= 200
    assert "UNSCORED" in idx


def test_research_page_lists_preregistered_h28_hypotheses_and_evidence_link():
    research = (DOCS / "research.html").read_text()
    registry = json.loads((ROOT / "registry" / "next_hypotheses.json").read_text())
    # Session 10's H33 queue is historical; Session 14 is the current five-item ranked research set.
    historical_ids = {h["id"] for h in registry["hypotheses"]}
    assert historical_ids == {"H33-2", "H33-3", "H33-4", "H33-5"}
    assert len(registry["hypotheses"]) == 4
    session14 = registry["session14_addendum"]
    assert [h["id"] for h in session14["ranked_hypotheses"]] == ["H38-1", "H38-2", "H38-3", "H38-4", "H38-5"]
    assert "The current Session 14 record ranks 5 candidate fault-discovery rules" in research
    assert "Five ranked geological hypotheses and their current status" in research
    assert "Historical Session 10 H33 queue" in research
    assert "H33-1 was run on its reserved seeds 200\u2013209 and refuted" in research
    assert "Layers, physical signature, novelty &amp; data limits" in research
    assert "Why it may find faults absent from the public catalogue" in research
    assert "USGS 3DEP one-meter bare-earth DEM tiles" in research
    assert "not an observed holdout gain or competition-score prediction" in research
    assert "140 candidate centroids" in research
    assert "not part of the current untried list" in research
    assert "four-item untried list" not in research
    # the site must never still claim H33-1 is untried
    assert "the five untried H33-series hypotheses" not in research
    assert "H31-1" not in historical_ids
    assert "H33-1" not in historical_ids
    h33_1 = next(item for item in registry["tested_hypotheses"] if item["id"] == "H33-1")
    assert h33_1["outcome"] == "REFUTED"
    assert h33_1["seeds"] == "200-209"
    assert h33_1["criteria_failed"] == "6 of 6"
    # the result section must render the measured numbers, not placeholders
    assert "0.12855" in research and "0.10104" in research and "-0.003014" in research
    assert "Pruning is exhausted as a family" in research
    h32_2 = next(item for item in registry["tested_hypotheses"] if item["id"] == "H32-2")
    assert "FROZEN GATE FAILED" in h32_2["status"]
    assert "H32-2" in research and "evidence/h32_2_holdout.json" in research
    assert "knowledge/16_preregistration_H32-2.md" in research and "knowledge/17_h32_2_result.md" in research
    h31 = next(item for item in registry["tested_hypotheses"] if item["id"] == "H31-1")
    assert "FROZEN SCREEN GATE FAILED" in h31["status"]
    for hypothesis in registry["hypotheses"]:
        assert hypothesis["id"] in research
    assert "knowledge/07_untried_hypotheses.md" in research
    assert "knowledge/08_preregistration_H28-1.md" in research
    evidence = ROOT / "evidence" / "h28_1_edge_holdout.json"
    if evidence.exists():
        assert "evidence/h28_1_edge_holdout.json" in research
        assert "leaderboard score" in research
    candidate_manifest = DOCS / "downloads" / "h28_1_candidate_manifest.json"
    if candidate_manifest.exists():
        candidate = json.loads(candidate_manifest.read_text())["candidate"]
        assert candidate["format_verified"] is True
        assert len(candidate["note"]) <= 200
        assert candidate["nan"] in research and candidate["zip"] in research
        assert candidate["allfinite"] in research
        assert "not one of the four weekly slots" in research
        summary = (DOCS / "executive-summary.html").read_text()
        assert candidate["nan"] in summary
        assert "not one of the four weekly slots" in summary


def test_no_score_is_claimed_for_27gemsdoe_and_scripts_never_fetch_drivendata():
    sc = json.loads((ROOT / "registry" / "live_scores.json").read_text())
    assert all(x["score"] is None for x in sc["27GEMSDOE"])
    for py in list((ROOT / "scripts").glob("*.py")) + list((ROOT / "src").rglob("*.py")):
        txt = py.read_text()
        for m in re.finditer(r"requests\.(get|head|post)\(([^)]*)", txt):
            assert "drivendata" not in m.group(2).lower(), f"{py.name} requests drivendata.org"
    feed = (ROOT / "scripts" / "refresh_source_feed.py").read_text()
    assert 'FORBIDDEN = ("drivendata.org",)' in feed and "refusing to request" in feed


def test_downloads_have_unique_names_and_zip_single_member():
    import zipfile
    names = [p.name for p in (DOCS / "downloads").glob("*.tif")]
    assert len(names) == len(set(names)) and all(re.search(r"-[0-9a-f]{12}-(nan|allfinite)\.tif$", n) for n in names)
    for z in (DOCS / "downloads").glob("*.zip"):
        with zipfile.ZipFile(z) as zf:
            assert len(zf.namelist()) == 1 and zf.namelist()[0].endswith(".tif")
