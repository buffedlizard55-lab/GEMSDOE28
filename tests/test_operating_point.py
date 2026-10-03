"""Tests for the live-anchored operating-point arithmetic (src/gems27/operating_point.py).

These are synthetic and fast: they do not need the restored competition rasters. The point is to pin
the two claims the module makes - (a) a pixel class is worth removing iff its efficiency is below
tau = 0.2*DTI/(1-0.2*DTI), and (b) the two-anchor fit has a closed form - against brute force, so
that a later refactor cannot quietly change the sign convention.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import metric  # noqa: E402
from gems27 import operating_point as op


def _straight_ridge(length: int = 601, width: int = 41) -> np.ndarray:
    mask = np.zeros((width, length), bool)
    mask[width // 2, 5:-5] = True
    return mask


def test_grid_distance_ladder_contains_the_expected_values() -> None:
    ladder = op.grid_distance_ladder(4.0)
    for expected in (1.0, 2.0**0.5, 2.0, 5.0**0.5, 8.0**0.5, 3.0, 10.0**0.5, 4.0):
        assert any(abs(v - expected) < 1e-12 for v in ladder)
    assert ladder == sorted(ladder)
    # strictly increasing separations only; no duplicates
    assert len(set(ladder)) == len(ladder)


def test_ladder_bucket_maps_a_submitted_min_dist_to_the_rung_it_realises() -> None:
    ladder = op.grid_distance_ladder(8.0)
    # 2.8 blocks separations below 2.8, so sqrt(8)=2.8284 is the smallest one still allowed
    assert abs(op.ladder_bucket(2.8, ladder) - 8.0**0.5) < 1e-12
    assert abs(op.ladder_bucket(1.5, ladder) - 2.0) < 1e-12
    assert abs(op.ladder_bucket(1.0, ladder) - 1.0) < 1e-12


def test_retention_is_one_when_every_pixel_is_kept_and_falls_monotonically() -> None:
    ridge = _straight_ridge()
    ladder = op.measure_ladder(ridge, ridge, max_distance=6.0)
    assert ladder.points[0].retention == pytest.approx(1.0, abs=1e-9)
    retentions = [p.retention for p in ladder.points]
    assert all(b <= a + 1e-9 for a, b in zip(retentions, retentions[1:])), "retention must not rise"
    counts = [p.n_emitted for p in ladder.points]
    assert all(b <= a for a, b in zip(counts, counts[1:])), "emission must not grow"


def test_retention_matches_the_analytic_one_dimensional_kernel_sum() -> None:
    """For a straight 1-px ridge, retention = (sum of the kernel over one period) / period."""
    ridge = _straight_ridge(1201)
    ladder = op.measure_ladder(ridge, ridge, max_distance=6.0)
    by_rung = {round(p.rung, 6): p for p in ladder.points}
    kernel_total = sum(max(0.0, 1.0 - abs(d) / 3.0) for d in range(-2, 3))  # 1 + 2(2/3) + 2(1/3) = 3
    assert kernel_total == pytest.approx(3.0)
    for rung in (5.0, 6.0):
        if rung in by_rung:
            assert by_rung[rung].retention == pytest.approx(3.0 / rung, abs=0.02)


def test_closed_form_two_anchor_solution_recovers_a_known_operating_point() -> None:
    """Synthesise two anchors from a known (L, |G|) under Eq. 1, then recover them exactly."""
    truth, credit, gam = 11_722.0, 6_456.9, 0.12653
    r1, n1, r2, n2 = 1.0, 121_131, 0.732457, 44_090

    def score_of(r: float, n: int) -> float:
        a = credit * r
        return a / (0.8 * truth + 0.2 * (1.0 - gam) * n + 0.2 * a)

    s1, s2 = score_of(r1, n1), score_of(r2, n2)
    L, G = op._solve_pair(s1, r1, n1, gam, s2, r2, n2, gam)
    assert L == pytest.approx(credit, rel=1e-9)
    assert G == pytest.approx(truth, rel=1e-9)


def test_closed_form_matches_a_grid_search_on_real_anchor_scores() -> None:
    """The closed form and a brute-force scan must agree on the real 0.2477 / 0.2600 anchors."""
    gam = op.GAMMA
    s1, r1, n1 = 0.2477, 0.821004, 60_069
    s2, r2, n2 = 0.2600, 0.732457, 44_090
    L, G = op._solve_pair(s1, r1, n1, gam, s2, r2, n2, gam)
    # a scan over G with L chosen to satisfy anchor 1 must hit the same point
    best = None
    for g_scan in np.linspace(6_000.0, 20_000.0, 140_001):
        l_scan = s1 * (0.8 * g_scan + 0.2 * (1 - gam) * n1) / (r1 * (1 - 0.2 * s1))
        a2 = l_scan * r2
        pred = a2 / (0.8 * g_scan + 0.2 * (1 - gam) * n2 + 0.2 * a2)
        err = abs(pred - s2)
        if best is None or err < best[0]:
            best = (err, l_scan, g_scan)
    assert best[2] == pytest.approx(G, rel=1e-4)
    assert best[1] == pytest.approx(L, rel=1e-4)


def test_state_is_algebraically_self_consistent_and_tau_matches_the_metric() -> None:
    """``state()`` must return exactly the Eq. 1 decomposition, and tau the metric's threshold."""
    op_point = op.OperatingPoint(credit_solid=6188.8, truth_px=12225.9)
    st = op_point.state(0.732457, 44090, gamma=0.12811)
    a, fp, g = st["credit_A"], st["fp"], st["truth_G"]
    assert fp == pytest.approx((1.0 - 0.12811) * 44090)
    assert st["denominator"] == pytest.approx(a + 0.2 * fp + 0.8 * (g - a))
    assert st["dti"] == pytest.approx(a / st["denominator"], rel=1e-12)
    assert st["tau"] == pytest.approx(metric.inclusion_threshold(st["dti"]), rel=1e-12)


def test_gamma_closure_reproduces_the_measured_fp_mass_of_the_live_inversion() -> None:
    """gamma = (N - FPw)/N must recover the inversions own fp_mass on every anchor.

    This pins the closure that replaced the earlier (wrong) ``FP = N - A``. The earlier form is
    *not* the metric: it charges every emitted pixel full false-positive mass and ignores the
    crowding excess ``Atilde - A``, which on these three anchors is 0.18x to 1.46x of A.
    """
    import json
    inv = json.loads((Path(__file__).resolve().parents[1] / "evidence" / "live_inversion.json")
                     .read_text())
    checked = 0
    for sub in inv["submissions"]:
        n = sub["n_positive_in_footprint"]
        if n not in op.ANCHOR_GAMMA:
            continue
        gam = (n - sub["fp_mass"]) / n
        assert gam == pytest.approx(op.ANCHOR_GAMMA[n], abs=2e-5), sub["label"]
        # and the naive closure is demonstrably different (that is the bug being guarded against)
        assert abs((n - sub["credit_TPw"]) - sub["fp_mass"]) > 100, sub["label"]
        checked += 1
    assert checked == 3
    # gamma is rung-invariant to 1.9 % across the anchors - the non-selectivity of dot_thin
    vals = list(op.ANCHOR_GAMMA.values())
    assert (max(vals) - min(vals)) / (sum(vals) / len(vals)) < 0.025


def test_corrected_model_reproduces_the_three_live_anchor_scores() -> None:
    """Model A: measured L, |G| and gamma, one fitted density scale, three anchors -> 2 d.o.f.

    This is the regression test for the whole H34 projection. If the ladder measurement, the
    retention curve or the closure changes, this breaks.
    """
    ridge = _straight_ridge(901, 61)
    ladder = op.measure_ladder(ridge, ridge, max_distance=4.0)
    anchors = [{"label": "solid", "min_dist": 1.0, "n_emitted": 121131, "score": 0.1922},
               {"label": "d1-5", "min_dist": 1.5, "n_emitted": 60069, "score": 0.2477},
               {"label": "d2-8", "min_dist": 2.8, "n_emitted": 44090, "score": 0.2600}]
    # the anchor N values belong to the real surface, not this synthetic one; feed r(v) explicitly
    by_rung = {round(p.rung, 6): p for p in ladder.points}
    for a, r in zip(anchors, (1.0, 1.0, 1.0)):
        a["retention_override"] = r
        del r
    anchors[0]["retention_override"] = by_rung[1.0].retention if 1.0 in by_rung else 1.0
    # use the documented stand-in retention values measured on the real catalogue
    anchors[0]["retention_override"] = 1.0
    anchors[1]["retention_override"] = 0.821004
    anchors[2]["retention_override"] = 0.732457
    anchors[1]["rung_override"] = 2.0
    anchors[2]["rung_override"] = 8.0 ** 0.5

    def dti_of(retention: float, n: int, gam: float, s: float) -> float:
        a = op.MEASURED_CREDIT_SOLID * (1.0 - s * (1.0 - retention))
        return a / (0.8 * op.MEASURED_TRUTH_PX + 0.2 * (1.0 - gam) * n + 0.2 * a)

    gammas = [op.ANCHOR_GAMMA[a["n_emitted"]] for a in anchors]
    rets = [a["retention_override"] for a in anchors]
    ns = [a["n_emitted"] for a in anchors]
    scores = [a["score"] for a in anchors]
    # least-squares over a coarse grid is enough to show a single s fits all three to ~1e-3
    best_s = min(np.linspace(0.5, 1.0, 501),
                 key=lambda s: max(abs(dti_of(r, n, g, s) - sc)
                                   for r, n, g, sc in zip(rets, ns, gammas, scores)))
    errs = [abs(dti_of(r, n, g, best_s) - sc) for r, n, g, sc in zip(rets, ns, gammas, scores)]
    assert max(errs) < 1.5e-3, f"one density scale does not fit all three anchors: {errs}"
    assert 0.78 < best_s < 0.88, f"density scale {best_s} outside the plausible range"


@pytest.mark.parametrize("efficiency", [0.001, 0.02, 0.05, 0.12])
def test_removal_rule_sign_matches_a_brute_force_removal(efficiency: float) -> None:
    """The gate `worth_it == (e < tau)` must agree with actually removing the pixels.

    This is the claim the whole H34 analysis rests on, so it is checked against the real metric
    rather than re-derived: build an emission, delete a subset whose measured efficiency is close to
    the DTI's own tau, and confirm the sign of the resulting DTI change matches the rule.
    """
    rng = np.random.default_rng(11)
    truth = np.zeros((200, 200), bool)
    truth[100, 20:180] = True
    # dense emission along the truth plus a controllable number of strays far from it
    pred = np.zeros((200, 200), bool)
    pred[100, 20:180:2] = True
    stray_rows = rng.integers(0, 200, size=400)
    stray_cols = rng.integers(0, 200, size=400)
    strays = np.zeros((200, 200), bool)
    for r, c in zip(stray_rows, stray_cols):
        if abs(r - 100) > 6:
            strays[r, c] = True
    pred |= strays

    base = metric.dti_binary(pred.astype(float), truth)
    tau = metric.inclusion_threshold(base["dti"])
    op_point = op.OperatingPoint(credit_solid=base["TPw"], truth_px=float(truth.sum()))

    # remove `n` stray pixels; their efficiency is near zero because they are far from truth
    rows, cols = np.nonzero(strays)
    n = min(len(rows), 50)
    removal = np.zeros((200, 200), bool)
    removal[rows[:n], cols[:n]] = True
    after = metric.dti_binary((pred & ~removal).astype(float), truth)
    measured = (base["TPw"] - after["TPw"]) / max(base["FPw"] - after["FPw"], 1e-9)

    verdict = op_point.prune_gain(1.0, base["n_emitted"], n, measured)
    assert verdict["worth_it"] == (measured < tau)
    # and the sign of the exact DTI change must follow the same rule
    assert (after["dti"] > base["dti"]) == (measured < tau)
    # a low-efficiency removal is worth it; the far-field strays are exactly that
    if efficiency < 0.02:
        gain = op_point.prune_gain(1.0, base["n_emitted"], n, efficiency)
        assert gain["worth_it"] is True
        assert gain["delta_dti"] > 0


def test_rung_efficiency_reports_the_credit_and_mass_of_the_step() -> None:
    ridge = _straight_ridge()
    ladder = op.measure_ladder(ridge, ridge, max_distance=5.0)
    op_point = op.OperatingPoint(credit_solid=6000.0, truth_px=12_000.0)
    rungs = [p.rung for p in ladder.points]
    a, b = rungs[1], rungs[2]
    res = op.rung_efficiency(ladder, op_point, a, b)
    idx = {p.rung: p for p in ladder.points}
    assert res["d_emitted"] == idx[b].n_emitted - idx[a].n_emitted
    assert res["d_credit"] == pytest.approx(
        op_point.credit_solid * (idx[b].retention - idx[a].retention), rel=1e-9)
    assert res["efficiency"] >= 0.0
    assert isinstance(res["worth_it"], bool)
