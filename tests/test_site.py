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
        "scripts/build_site.py",
        ".github/workflows/build-site.yml",
        "docs/assets/**",
        "docs/*.html",
        "index.html",
    }:
        assert workflow.count(f"'{path}'") == 2, f"missing push/pull_request trigger for {path}"


def test_h31_site_status_distinguishes_screen_confirmation_and_proxy_results():
    from scripts import build_site

    assert build_site.h31_result_summary({}, {}) == "No H31 classifier fit or holdout has been run."
    screen_pass = {"gate": {"passed": True}, "summary": {
        "mean_paired_gain": 0.0012, "positive_fold_count": 3, "positive_seed_count": 8,
    }}
    screen_text = build_site.h31_result_summary(screen_pass, {})
    assert "Screen frozen gate PASS" in screen_text
    assert "catalogue-proxy" in screen_text and "Confirmation on seeds 170–179 remains required" in screen_text
    assert "weekly slot" in screen_text
    confirm_fail = {"gate": {"passed": False}, "summary": {
        "mean_paired_gain": -0.0001, "positive_fold_count": 1, "positive_seed_count": 4,
    }}
    failed_text = build_site.h31_result_summary(screen_pass, confirm_fail)
    assert "Confirmation frozen gate FAIL" in failed_text and "rejects the arm for submission" in failed_text
    assert "weekly slot" in build_site.h31_next_step(screen_pass, confirm_fail)


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
