import hashlib
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGES = ["index.html", "executive-summary.html", "topology.html", "research.html", "sources.html", "cross-site-review.html", "session23-result.html", "session24-review.html"]


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
    # The current audit ranks four unimplemented physical operators; none is a result.
    assert json.loads(r.stdout)["hypotheses"] == 4
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
        "site_templates/**",
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
    front_page = (DOCS / "archive.html").read_text()
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


def test_branch_local_h38_attempt_discloses_failure_and_seed_reuse_without_promoting_main_result():
    from scripts import build_site

    claim = json.loads((ROOT / "evidence" / "h38_1_holdout.started.json").read_text())
    html = build_site.local_h38_branch_attempt_html(claim)
    assert "FAILED / not evaluable" in html
    assert "seeds 265, 266, 267, 268, 269" in html
    assert "not an independent fresh holdout" in html
    assert "This run wrote no summary and has no C1–C5 decision" in html
    assert "separate mainline heat-flow/Euler and GeoDAWN-radiometric work" in html
    assert "../evidence/losfo_h38_1_raw.json" in html
    assert "../knowledge/39_session14_closeout_2026-10-03.md" in html
    assert "../evidence/h38_1_holdout.json" not in html
    assert "seeds not recorded" in build_site.local_h38_branch_attempt_html({"status": "FAILED", "seeds": None, "seed_independence_review": None})
    assert build_site.local_h38_branch_attempt_html({"status": "RUNNING"}) == ""


def test_local_failure_claim_and_registry_disambiguate_summary_path_collision():
    claim_path = ROOT / "evidence" / "h38_1_holdout.started.json"
    claim = json.loads(claim_path.read_text())
    registry = json.loads((ROOT / "registry" / "next_hypotheses.json").read_text())
    attempt = registry["session14_local_branch_attempt"]
    collision = attempt["summary_path_collision"]
    mainline_report = ROOT / collision["frozen_branch_expected_summary_path"]
    assert claim["summary_result_written"] is False
    assert claim["summary_result_artifact"] is None
    assert "seeds 280–289" in claim["summary_result_disambiguation"]
    claim_sha = hashlib.sha256(claim_path.read_bytes()).hexdigest()
    assert claim_sha == attempt["artifacts"]["claim"]["sha256"]
    irregularities = json.loads((ROOT / "registry" / "irregularities.json").read_text())
    irregularity = next(item for item in irregularities["items"] if item["id"] == "session14-local-h38-euler-gravity-seed-reuse")
    assert claim_sha in irregularity["issue"]
    assert hashlib.sha256(mainline_report.read_bytes()).hexdigest() == collision["current_mainline_path_sha256"]
    assert "GeoDAWN-radiometric" in collision["current_mainline_path_belongs_to"]


def test_all_internal_links_and_assets_resolve():
    for page in list(DOCS.glob("*.html")) + [ROOT / "index.html", ROOT / "executive-summary.html"]:
        parser = Links()
        parser.feed(page.read_text())
        for ref in parser.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            target = page.parent / unquote(url.path) if url.path else page
            assert target.exists(), f"{page.name}: broken internal reference {ref}"
            if url.fragment and target.suffix == ".html":
                destination = Links()
                destination.feed(target.read_text())
                assert unquote(url.fragment) in destination.ids, f"{page.name}: broken anchor {ref}"


def test_pages_source_links_resolve_to_public_repository_files():
    for page in PAGES:
        text = (DOCS / page).read_text()
        assert 'href="../evidence/' not in text
        assert 'href="../knowledge/' not in text
        assert 'href="../registry/' not in text
    research = (DOCS / "research.html").read_text()
    assert "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/evidence/h31_1_prereg_history_audit.json" in research
    assert "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/knowledge/12_preregistration_H31-1_euler.md" in research


def test_repository_root_front_page_locks_new_submission_download():
    root_idx = (ROOT / "index.html").read_text()
    assert 'href="docs/archive.html"' in root_idx
    assert "S23 audit: no new TIFF" in root_idx
    assert "Submission download locked" in root_idx
    assert (ROOT / ".nojekyll").exists()


def test_front_page_links_current_card_and_no_candidate_download():
    idx = (DOCS / "index.html").read_text()
    card = json.loads((DOCS / "data/current_run_card.json").read_text())
    assert 'href="data/current_run_card.json"' in idx
    assert "Submission download locked" in idx
    assert card["submission_name"] is None and card["raster_sha256"] is None
    assert len(card["submission_note"]) <= 140
    assert card["new_tiff_generated"] is False


def test_current_cross_site_review_is_linked_and_fail_closed():
    page = (DOCS / "cross-site-review.html").read_text()
    index = (DOCS / "index.html").read_text()
    card = json.loads((ROOT / "evidence/s19_ascp_run_card.json").read_text())
    assert "GEMSDOE32 H33-2-B2" in page
    assert "0.2778" in page and "USER-REPORTED / UNVERIFIED" in page
    assert "72 directional comparisons" in page and "not the complete current registry" in page
    assert "0.4437" in page and "public leaderboard observation" in page
    assert "DO NOT SUBMIT" in page
    for name in ("Displaced potential-field piercing markers", "Paired-geothermometer cooling corridors",
                 "Lithology-conditioned U/Th transport dipoles"):
        assert name in page
    assert "cross-site-review.html" in index
    assert card["verdict"] == "negative" and card["submission_ready"] is False
    assert card["holdout"]["label"] == "HOLDOUT-DTI"
    assert card["holdout"]["paired_gain_ci95"][1] < 0


def test_research_page_lists_preregistered_h28_hypotheses_and_evidence_link():
    research = (DOCS / "research.html").read_text()
    registry = json.loads((ROOT / "registry" / "next_hypotheses.json").read_text())
    # The mainline registry preserves the four-item Session 10 H33 queue; the separate five-item
    # branch-local H38 ranking is historical and linked from the failure/reconciliation notice.
    historical_ids = {h["id"] for h in registry["hypotheses"]}
    assert historical_ids == {"H33-2", "H33-3", "H33-4", "H33-5"}
    assert len(registry["hypotheses"]) == 4
    assert "Archived branch-local H38-1 attempt — FAILED / not evaluable" in research
    assert "knowledge/37_ranked_hypotheses_session14_2026-10-03.md" in research
    assert "H38-1" in research and "do not combine their results" in research
    assert "owner-reported, not independently organizer-verified" in research
    assert "SHA-256 verifies local bytes, not a DrivenData receipt" in research
    assert "one-off manual public-page observation" in research
    assert "H33-1 was run on its reserved seeds 200\u2013209 and refuted" in research
    ranking = (ROOT / "knowledge" / "37_ranked_hypotheses_session14_2026-10-03.md").read_text()
    assert all(f"H38-{i}" in ranking for i in range(1, 6))
    assert "**Layers:**" in ranking
    assert "Physical signature" in ranking
    assert "USGS 3DEP" in ranking
    assert "not holdout results, organizer results" in ranking
    assert "FAILED / NOT EVALUABLE" in ranking
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
        assert "not an authorized weekly submission" in research
        summary = (DOCS / "archive.html").read_text()
        assert candidate["nan"] in summary
        assert "not an authorized weekly submission" in summary


def test_ai_use_disclosure_is_present_and_linked_from_source_ledger():
    disclosure = (ROOT / "AI_DISCLOSURE.md").read_text()
    sources = (DOCS / "sources.html").read_text()
    assert "Arena.ai Agent Mode" in disclosure
    assert "not a substitute for the required narrative statement" in disclosure
    assert "AI_DISCLOSURE.md" in sources
    assert "required final-round narrative" in sources


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


def test_current_run_notice_is_above_historical_body():
    for page in PAGES:
        text = (DOCS / page).read_text()
        assert 'Current run: NOT READY TO SUBMIT' in text
        assert 'NO FILE APPROVED' in text and 'do not upload it or any prior file' in text
        assert 'S23 audit: no new TIFF' in text
        assert 'data/current_run_card.json' in text
    overview = (DOCS / 'index.html').read_text()
    executive = (DOCS / 'executive-summary.html').read_text()
    assert '72 directional comparisons' in overview
    assert 'Historical GeoTIFF — NOT APPROVED FOR SUBMISSION' in (DOCS / 'archive.html').read_text()
    assert 'NO FILE APPROVED' in executive and 'not OK to submit' in executive
    assert 'If you submit anything, use the primary' not in overview + executive
    card = json.loads((DOCS / 'data/run_card_2026-10-26.json').read_text())
    assert card['verdict'] == 'negative' and card['submission_ready'] is False
    assert card['session'] == 'S22-AUDIT-20261026'
    assert card['raster_sha256'] is None and card['slot_selected'] is False
    assert card['experiments_run'] == 0


def test_download_manifest_marks_current_audit_no_new_raster():
    manifest = json.loads((DOCS / 'downloads/manifest.json').read_text())
    current = manifest['current_run']
    assert current['status'] == 'NEGATIVE — NO FILE APPROVED'
    assert current['new_tiff_generated'] is False
    assert current['submission_ready'] is False and current['slot_selected'] is False
    assert manifest['s19_candidate']['verdict'] == 'negative'


def test_build_metadata_and_canonical_card_do_not_authorize_historical_upload(capsys):
    from scripts import build_site

    assert build_site.main() == 0
    metadata = json.loads(capsys.readouterr().out)
    assert metadata['submission_ready'] is False and metadata['slot_selected'] is False
    assert 'primary_download' not in metadata and metadata['research_download'] is None
    assert metadata['inspection_artifacts']
    current = json.loads((DOCS / 'data/current_run_card_2026-10-26.json').read_text())
    exact = json.loads((ROOT / 'evidence/s22_audit_run_card.json').read_text())
    assert current == exact and current['verdict'] == 'negative'
    assert (DOCS / 'data/current_run_card.json').read_bytes() == (ROOT / 'evidence/s23_run_card.json').read_bytes()
    parallel = json.loads((ROOT / 'evidence/s18_run_card.json').read_text())
    assert parallel['experiments_run'] == 0 and parallel['raster_sha256'] is None


def test_repository_root_front_page_locks_submission_download_and_preserves_archive():
    man = json.loads((DOCS / "downloads" / "manifest.json").read_text())
    root_idx = (ROOT / "index.html").read_text()
    P = man["primary"]
    assert f'href="docs/downloads/{P["nan"]}"' not in root_idx
    assert 'href="docs/archive.html"' in root_idx
    assert "Submission download locked" in root_idx
    assert (ROOT / ".nojekyll").exists()



def test_archive_preserves_exact_download_and_note_without_approval():
    man = json.loads((DOCS / "downloads" / "manifest.json").read_text())
    idx = (DOCS / "archive.html").read_text()
    P = man["primary"]
    assert f'href="downloads/{P["nan"]}"' in idx and "download" in idx
    assert (DOCS / "downloads" / P["nan"]).is_file() and (DOCS / "downloads" / P["zip"]).is_file()
    assert P["note"] in idx.replace("&#x27;", "'") or P["note"].replace("|", "|") in idx
    assert len(P["note"]) <= 200
    assert P["submission_name"] in idx and P["content_id"] in P["submission_name"]
    assert "UNSCORED" in idx



def test_download_manifest_marks_all_current_slots_blocked():
    manifest = json.loads((DOCS / "downloads" / "manifest.json").read_text())
    current = manifest["current_run"]
    assert current["status"] == "NEGATIVE — NO FILE APPROVED"
    assert current["submission_ready"] is False
    assert current["slot_selected"] is False
    assert current["new_tiff_generated"] is False


def test_site_build_metadata_does_not_call_historical_raster_a_submission_download(capsys):
    from scripts import build_site

    assert build_site.main() == 0
    build_result = json.loads(capsys.readouterr().out)
    assert build_result["submission_ready"] is False
    assert build_result["slot_selected"] is False
    assert "primary_download" not in build_result
    assert build_result["inspection_artifacts"]



def test_feed_refresh_rebuilds_and_deploys_without_requiring_a_branch_push_event():
    feed = (ROOT / ".github/workflows/source-feed.yml").read_text()
    pages = (ROOT / ".github/workflows/pages.yml").read_text()
    assert "python scripts/build_site.py" in feed
    assert "docs/*.html index.html" in feed
    assert "branches: [main]" in feed and "branches: ['arena/**']" not in feed
    assert "workflow_run:" in pages
    assert "workflows: ['Source metadata feed (no competition requests)']" in pages
    assert "github.event.workflow_run.conclusion == 'success'" in pages
    assert "cp -a docs/. build/pages/docs/" in pages  # legacy /docs/ bookmarks remain valid
    assert "path: build/pages" in pages



def test_static_build_still_needs_no_third_party_dependencies():
    result = subprocess.run([sys.executable, "-S", str(ROOT / "scripts/build_site.py")],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr



def test_combined_archive_namespaces_ids_and_accessible_labels():
    from scripts.build_site import namespace_anchors

    html = '<h2 id="title">Old</h2><p id="body" data-id="cache" aria-labelledby="title outside"></p><a href="#title">Jump</a><a href="index.html#download">Current</a>'
    result = namespace_anchors(html, "old-")
    assert 'id="old-title"' in result and 'id="old-body"' in result
    assert 'aria-labelledby="old-title outside"' in result
    assert 'href="#old-title"' in result
    assert 'href="index.html#download"' in result
    assert 'data-id="cache"' in result



def test_historical_dated_aliases_stay_s22_while_current_notice_advances():
    source = json.loads((ROOT / 'evidence/s22_audit_run_card.json').read_text())
    for name in ('run_card_2026-10-26.json', 'current_run_card_2026-10-26.json'):
        assert json.loads((DOCS / 'data' / name).read_text()) == source
    historical = json.loads((ROOT / 'evidence/s18_run_card.json').read_text())
    assert historical['run_id'] != source['session'] and historical['submission_ready'] is False
    workflow = (ROOT / '.github/workflows/pages.yml').read_text()
    assert 'EXPECTED_CARD_SHA256' in workflow and 'hashlib.sha256(body)' in workflow
    assert (ROOT / 'data/current_run_card_2026-10-26.json').read_bytes() == (
        DOCS / 'data/current_run_card_2026-10-26.json').read_bytes()
    root_summary = (ROOT / 'executive-summary.html').read_text()
    assert 'Submission download locked' in root_summary and 'S23 audit: no new TIFF' in root_summary


def test_session18_h39_5_candidate_is_unique_valid_but_do_not_submit():
    # Parallel Session 18 H39-5 experiment (knowledge/52-53): unique + format
    # valid, frozen LOSFO gate FAILED -> DO NOT SUBMIT everywhere it appears.
    archive = (DOCS / 'archive.html').read_text()
    assert '719b83fb659b' in archive
    assert 'RED DO NOT SUBMIT - HOLDOUT GATE FAILED - INSPECTION ONLY' in archive
    card = json.loads((ROOT / 'evidence/s18_h39_5_run_card.json').read_text())
    assert card == json.loads((DOCS / 'data/run_card_s18_2026-10-25.json').read_text())
    assert card['verdict'] == 'negative'
    assert card['submission_ready'] is False
    assert card['slot_selected'] is False
    assert card['selector_promotion'] is False
    assert card['holdout_dti']['gate_passed'] is False
    assert card['correlation_overlap_vs_registry']['uniqueness_pass_strict'] is True
    assert card['validator']['nan_hard_pass'] is True
    assert card['validator']['allfinite_hard_pass'] is True
    assert card['validator']['no_nan_inside_footprint'] is True
    assert card['validator']['values_in_0_1'] is True
    assert len(card['note']) <= 140 and 'DO NOT SUBMIT' in card['note']
    manifest = json.loads((DOCS / 'downloads/manifest.json').read_text())
    slot = manifest['s18_h39_5_candidate']
    assert slot['verdict'] == 'negative' and slot['content_id'] == '719b83fb659b'
    assert slot['run_card'] == 'evidence/s18_h39_5_run_card.json'
    assert (DOCS / 'downloads' / slot['nan']).is_file()
    assert (DOCS / 'downloads' / slot['allfinite']).is_file()
    # The parallel safety review keeps its own card/path (label collision).
    review = json.loads((ROOT / 'evidence/s18_run_card.json').read_text())
    assert review['run_id'] == 's18-safety-review-20261025'
    assert review['experiments_run'] == 0 and card['experiments_run'] == 3

def test_legacy_main_root_routes_match_generated_pages_and_current_card():
    from scripts.build_site import root_relative_links

    for name in ('index.html', 'executive-summary.html'):
        expected = root_relative_links((DOCS / name).read_text())
        assert (ROOT / name).read_text() == expected
        # All root-mirror relative links resolve through /docs/ and remain
        # available when either the legacy or Actions publisher finishes last.
        for url in re.findall(r'(?:href|src)="([^"]+)"', expected):
            if url.startswith(('https://', 'http://', '#', 'mailto:')):
                continue
            path = url.split('#')[0]
            if path:
                assert (ROOT / path).is_file(), (name, url)
    assert (ROOT / 'data/current_run_card_2026-10-25.json').read_bytes() == (
        DOCS / 'data/current_run_card_2026-10-25.json'
    ).read_bytes()


def test_session18b_h42_1_candidate_is_unique_valid_but_do_not_submit():
    # Parallel Session 18B H42-1 experiment (knowledge/52 preregistration,
    # knowledge/54 result): unique + format valid, frozen LOSFO gate FAILED.
    # Renamed from s18 at merge; never combined with H39-5 / safety-review runs.
    archive = (DOCS / 'archive.html').read_text()
    assert '290553965159' in archive
    assert 'DO NOT SUBMIT — FROZEN HOLDOUT GATE FAILED' in archive
    card = json.loads((ROOT / 'evidence/s18b_run_card.json').read_text())
    assert card == json.loads((DOCS / 'data/run_card_s18b.json').read_text())
    assert card['verdict'] == 'negative'
    assert card['submission_ready'] is False
    assert card['slot_selected'] is False
    assert card['experiments_run'] == 3
    assert card['holdout']['label'] == 'HOLDOUT-DTI'
    assert card['registry']['binding_pass'] is True
    assert card['validator']['no_nan_inside'] is True
    assert card['validator']['range_0_1'] is True
    assert card['validator']['nan_variant_hard_pass'] is True
    assert card['preregistration_deviations']  # coherence-vs-support deviation disclosed
    assert len(card['note']) <= 140 and 'DO NOT SUBMIT' in card['note']
    manifest = json.loads((DOCS / 'downloads/manifest.json').read_text())
    slot = manifest['s18b_candidate']
    assert slot['verdict'] == 'negative' and slot['content_id'] == '290553965159'
    assert slot['run_card'] == 'evidence/s18b_run_card.json'
    assert slot['sha256_allfinite'] == card['raster_sha256']
    assert (DOCS / 'downloads' / slot['nan']).is_file()
    assert (DOCS / 'downloads' / slot['allfinite']).is_file()
    # The parallel Session 18 artifacts keep their own names/numbers.
    assert manifest['s18_h39_5_candidate']['content_id'] == '719b83fb659b'


def test_session20_result_is_linked_and_fail_closed():
    page = (DOCS / "session20-result.html").read_text()
    index = (DOCS / "index.html").read_text()
    executive = (DOCS / "executive-summary.html").read_text()
    card = json.loads((ROOT / "evidence/session20_h43_run_card.json").read_text())
    stem = "gems28-h43-1-tpb2gkc-20261026-76737f19814e"
    assert "DO NOT SUBMIT the new Session 20 TIFF" in page
    assert "Submission download locked" in page
    assert f"downloads/{stem}-allfinite.tif" in page
    assert "data/run_card_s20_2026-10-26.json" in page
    assert "session20-result.html" in index and "session20-result.html" in executive
    assert "HOLDOUT-DTI" in page and "USER-REPORTED / UNVERIFIED" in page
    assert "0.2778" in page and "GEMSDOE32" in page
    assert card["verdict"] == "negative" and card["submission_ready"] is False
    assert card["slot_selected"] is False and card["new_tiff_generated"] is True
    assert card["experiments_run"] == 3 and card["holdout"]["gate_pass"] is False
    assert card["holdout"]["pooled_gain"] < 0
    assert card["registry_comparison"]["exact_duplicate_of_any_registry"] is False
    assert card["registry_comparison"]["duplicate_by_protocol"] is True
    assert len(card["submission_note"]) <= 140
    # The generated S20 TIFF is bound to the run card hash and never approved.
    tif = DOCS / "downloads" / f"{stem}-allfinite.tif"
    assert tif.is_file()
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == card["raster_sha256"]
    build = json.loads((ROOT / "evidence/s20_build.json").read_text())
    assert build["validator_primary_hard_pass"] is True
    assert build["dots"] == 33354 and build["budget_reached"] is False


def test_session20_s20_nchc_candidate_remains_historical_and_literal_gate_fails():
    manifest = json.loads((DOCS / "downloads/manifest.json").read_text())
    slot = manifest["s20_nchc_candidate"]
    card = json.loads((ROOT / "evidence/s20_nchc_run_card.json").read_text())
    assert slot["verdict"] == "negative" and slot["sha256_allfinite"] == card["raster_sha256"]
    assert len(card["note"]) <= 140 and "DO NOT SUBMIT" in card["note"]
    assert card["submission_ready"] is False and card["slot_selected"] is False
    assert card["holdout"]["label"] == "HOLDOUT-DTI"
    assert card["registry"]["prospective_method_lane_passed"] is True
    assert card["registry"]["prospective_literal_all_entries_passed"] is False
    assert (DOCS / "downloads" / slot["allfinite"]).is_file()
    assert (DOCS / "downloads" / slot["nan"]).is_file()
    assert (DOCS / "downloads" / slot["zip"]).is_file()
    assert json.loads((DOCS / "data/run_card_s20_nchc.json").read_text()) == card
    page = (DOCS / "cross-site-review.html").read_text()
    assert "literal all-entries surface check is false" in page
    assert "genuinely unique" not in page.lower()
    assert "0.4437" in page and "0.2778" in page
