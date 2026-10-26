"""Tests for the Session-3 live-score inversion, budget model and coverage thinning.

The forward model must reproduce the two live anchors exactly; the retention rule must be a ratio of
blind coverages; the crowding factor of a sparse blind pattern must be ~1. Synthetic small grids are
used so the suite stays fast - no 12 M-pixel distance transforms here.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems27 import coverage_thin, metric, thinning  # noqa: E402

ALPHA, BETA = metric.ALPHA, metric.BETA
KAREA = 9.3803


def forward(tp, n, rho, g):
    return tp / (ALPHA * tp * (1.0 - rho) + ALPHA * n + BETA * g)


def test_kernel_area_constant_matches_direct_sum():
    r = int(np.ceil(metric.RADIUS_PX))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    assert float(np.maximum(1.0 - np.hypot(yy, xx) / metric.RADIUS_PX, 0.0).sum()) == pytest.approx(KAREA, rel=1e-3)


def test_naive_closure_is_the_rho_1_case_of_the_forward_model():
    """FPw = N - TPw (the closure used in knowledge/01) must equal the forward model at rho = 1."""
    for tp, n, g in [(5399, 60069, 12226), (4700, 44090, 12226), (1000, 20000, 12226)]:
        assert forward(tp, n, 1.0, g) == pytest.approx(tp / (ALPHA * n + BETA * g), rel=1e-12)


def test_forward_model_reproduces_both_live_anchors():
    """The two owner-reported anchors, from evidence/live_inversion.json (hash-authenticated rasters)."""
    p = ROOT / "evidence" / "live_inversion.json"
    if not p.exists():
        pytest.skip("run scripts/invert_live_scores.py first")
    inv = json.loads(p.read_text())
    by = {r["label"]: r for r in inv["submissions"]}
    for lbl, live in [("19GEMSDOE h19-5", 0.1922),
                      ("24GEMSDOE h25-1 dotted-h19-5-d1-5 (989f59505db1)", 0.2477)]:
        r = by[lbl]
        got = forward(r["credit_TPw"], r["n_scored"], r["rho_matched_over_TP"], inv["G_used"])
        assert got == pytest.approx(live, abs=2e-4), f"{lbl}: model {got:.4f} vs live {live}"


def test_blind_lattice_crowding_is_near_one():
    """A spacing-5 lattice has ~1 dot per matched truth pixel, so rho must be ~1 (the closure is exact)."""
    p = ROOT / "evidence" / "live_inversion.json"
    if not p.exists():
        pytest.skip("run scripts/invert_live_scores.py first")
    inv = json.loads(p.read_text())
    lat = [r for r in inv["submissions"] if "lattice" in r["label"]][0]
    assert lat["rho_matched_over_TP"] == pytest.approx(1.0, abs=0.05)
    assert lat["crowding_dots_in_kernel"] == pytest.approx(0.0, abs=0.05)


def test_g_estimate_is_inside_the_sibling_range():
    """|G| from the blind lattice must agree with the sibling's independent estimate to a few percent."""
    p = ROOT / "evidence" / "live_inversion.json"
    if not p.exists():
        pytest.skip("run scripts/invert_live_scores.py first")
    g = json.loads(p.read_text())["G_used"]
    assert 11_500 < g < 13_500, f"|G| = {g} outside the 11.5k-13.5k band agreed by three instruments"


def test_retention_rule_is_a_ratio_of_blind_coverages_and_matches_live():
    p = ROOT / "evidence" / "budget_optimum.json"
    if not p.exists():
        pytest.skip("run scripts/optimize_budget.py first")
    bo = json.loads(p.read_text())
    for v in bo["retention_validation"]:
        # the geometric prediction must be within 5% of the live-measured retention
        assert abs(v["relative_error"]) < 0.05, v
    assert len(bo["retention_validation"]) >= 2, "need two independent live pairs"


def test_coverage_thin_hits_budget_exactly_and_is_a_subset():
    rng = np.random.default_rng(0)
    mask = np.zeros((120, 120), bool)
    for _ in range(14):                      # synthetic 1-px ridge network
        y, x = rng.integers(10, 110, 2)
        yy = np.clip(y + np.arange(-18, 19), 0, 119)
        mask[yy, x] = True
    foot = np.ones(mask.shape, bool)
    for budget in (30, 80, 150):
        out = coverage_thin.coverage_thin(mask, budget, foot=foot)
        assert int(out.sum()) == budget
        assert bool((out & ~mask).sum() == 0), "selected pixels must come from the emission"


def test_coverage_thin_is_deterministic():
    rng = np.random.default_rng(1)
    mask = rng.random((80, 80)) < 0.05
    foot = np.ones(mask.shape, bool)
    a = coverage_thin.coverage_thin(mask, 60, foot=foot)
    b = coverage_thin.coverage_thin(mask, 60, foot=foot)
    assert np.array_equal(a, b)


def test_dot_thin_budget_is_monotone_in_distance():
    rng = np.random.default_rng(2)
    mask = rng.random((90, 90)) < 0.10
    counts = [int(thinning.dot_thin(mask, d).sum()) for d in (1.0, 1.5, 2.0, 3.0)]
    assert counts == sorted(counts, reverse=True), counts


@pytest.mark.requires_rasters
def test_verify_downloads_still_passes_with_four_slots(tmp_path):
    # Never rewrite a tracked historical evidence file as a side effect of testing.
    # Inherits GEMS_DATA_DIR so it verifies the same cache the suite is using.
    # S22 registered every previously unregistered TIFF (S21-AUDIT next-step #1), which exposed
    # exactly two genuine legacy defects: the h40-1/h41-1 thermal *allfinite* files carry a stray
    # nodata=NaN tag over clean zero values (knowledge/63 irregularity 4). Historical bytes are
    # hash-bound evidence and are not rewritten to hide this; the audit must fail with precisely
    # those two checks and nothing else.
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_downloads.py"),
                        "--out", str(tmp_path / "archive-audit.json")],
                       capture_output=True, text=True)
    report = json.loads((tmp_path / "archive-audit.json").read_text())
    known_legacy = {
        "archive_gems28_h40_1_thermal_vent_allfinite_outside_zero",
        "archive_gems28_h41_1_thermal_spring_allfinite_outside_zero",
    }
    assert set(report["failures"]) == known_legacy, r.stdout[-3000:]
    assert r.returncode == 1 and "2 failure(s)" in r.stdout
    for slot in ("primary", "secondary", "tertiary", "quaternary"):
        assert f"{slot}/nan" in r.stdout or slot in r.stdout, f"{slot} not verified"
    s22_checks = [c for c in report["checks"] if c["check"].startswith("s22c_candidate")]
    assert s22_checks and all(c["pass"] for c in s22_checks)


def test_historical_manifest_slots_remain_only_in_archive():
    man = json.loads((ROOT / "docs" / "downloads" / "manifest.json").read_text())
    for k in ("primary", "secondary", "tertiary", "quaternary"):
        assert k in man and man[k]["emitted_px"] > 0
        assert (ROOT / "docs" / "downloads" / man[k]["nan"]).exists()
        assert (ROOT / "docs" / "downloads" / man[k]["zip"]).exists()
        assert len(man[k]["note"]) <= 200
    archive = (ROOT / "docs" / "archive.html").read_text()
    assert "DO NOT SUBMIT" in archive
    assert man["quaternary"]["nan"] in archive
    current = (ROOT / "docs" / "index.html").read_text()
    assert "Submission download locked" in current
    assert man["quaternary"]["nan"] not in current


def test_h32_1_holdout_and_new_live_scores_0_2600_0_2449_0_1223():
    inv = json.loads((ROOT / "evidence" / "live_inversion.json").read_text())
    assert inv["n_corpus"] == 24
    by = {r["label"]: r for r in inv["submissions"]}
    for lbl, live in [
        ("25GEMSDOE dotted-h19-5-d2-8 (e56ea318af89)", 0.2600),
        ("27GEMSDOE topo-gap-closure-t-v2-on-d1-5 (5512495c6bd1)", 0.2449),
        ("26GEMSDOE dilcond-oof-v1 (47629f496133)", 0.1223),
    ]:
        r = by[lbl]
        got = forward(r["credit_TPw"], r["n_scored"], r["rho_matched_over_TP"], inv["G_used"])
        assert got == pytest.approx(live, abs=2e-4)

    h32 = json.loads((ROOT / "evidence" / "h32_1_holdout.json").read_text())
    assert h32["seeds"] == list(range(180, 190))
    assert h32["gate_passed"] is True
    post = h32["variants"]["h32_1_post_d28"]
    pre = h32["variants"]["h32_1_pre_d28"]
    ctrl = h32["variants"]["control_prune_protected_only_d28"]
    assert post["seeds_won"] == 10 and post["folds_improved"] == 4 and post["mean_dti_gain"] > 0.001
    assert pre["seeds_won"] == 10 and pre["folds_improved"] == 4 and pre["mean_dti_gain"] > 0.001
    assert ctrl["removed_credit_per_removed_fp"] > 2.0 * post["removed_credit_per_removed_fp"]
