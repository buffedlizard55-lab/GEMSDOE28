"""Tests for the reachability-frontier analysis (`scripts/reachability_frontier.py`).

These tests do not trust the closed-form algebra: they re-derive the reported requirements by
substituting them back into the official metric identity, and they check the closed form against the
exact `metric.dti_binary` implementation on degenerate and realistic geometries.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import metric  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "reachability_frontier", ROOT / "scripts" / "reachability_frontier.py"
)
rf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rf)  # type: ignore[union-attr]

EVIDENCE = ROOT / "evidence" / "reachability_frontier.json"


# --------------------------------------------------------------------------------------------
# 1. the closed form really is the official metric
# --------------------------------------------------------------------------------------------
def test_identity_check_passes_on_degenerate_and_realistic_geometry():
    res = rf.verify_identity(n_cases=30, seed=7)
    assert res["pass"], res
    assert res["max_abs_residual"] < 1e-8
    # FPw = N - MPw is the substitution the whole inversion rests on; it must hold case by case
    assert res["closure_fpw_equals_n_minus_mpw"]


def test_identity_holds_for_the_exact_shapes_the_inversion_uses():
    """Independent check: closed form == metric.dti_binary on a 1-D-trace geometry."""
    rng = np.random.default_rng(11)
    H = W = 60
    truth = np.zeros((H, W), bool)
    for _ in range(4):
        y, x = 20, int(rng.integers(5, 20))
        for _ in range(30):
            truth[y, x] = True
            y = int(np.clip(y + rng.integers(-1, 2), 0, H - 1))
            x = int(np.clip(x + 1, 0, W - 1))
    pred = np.zeros((H, W), bool)
    ys, xs = np.nonzero(truth)
    pred[ys[::3], xs[::3]] = True
    exact = metric.dti_binary(pred, truth)
    p = pred > 0
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[truth]).sum())
    mp = float(metric.kernel_from_distance(distance_transform_edt(~truth)[p]).sum())
    rho = mp / tp
    closed = tp / (0.2 * tp * (1 - rho) + 0.2 * int(p.sum()) + 0.8 * int(truth.sum()) + metric.EPS)
    assert closed == pytest.approx(exact["dti"], abs=1e-9)


# --------------------------------------------------------------------------------------------
# 2. the frontier functions invert consistently (substitute the answer back in)
# --------------------------------------------------------------------------------------------
def test_credit_required_round_trips_through_the_identity():
    g = 12225.896194356133
    for target in (0.10, 0.2477, 0.2600, 0.3195, 0.45):
        for n in (1000, 44090, 121131):
            for rho in (1.0, 1.179, 2.0):
                tp = rf.credit_required(target, n, g, rho)
                back = tp / (0.2 * tp * (1 - rho) + 0.2 * n + 0.8 * g)
                assert back == pytest.approx(target, rel=1e-9), (target, n, rho)


def test_budget_required_round_trips_through_the_identity():
    g = 12225.896194356133
    for target in (0.2477, 0.2600, 0.3195):
        for tp in (2000.0, 4791.05, 6000.0):
            for rho in (1.0, 1.4):
                n = rf.budget_required(target, tp, g, rho)
                back = tp / (0.2 * tp * (1 - rho) + 0.2 * n + 0.8 * g)
                assert back == pytest.approx(target, rel=1e-9), (target, tp, rho)


def test_add_arm_frontier_dots_needed_is_exact():
    """The reported dot count, applied at its own marginal efficiency, must hit the target.

    At rho = 1 the official denominator collapses: FPw = N - TPw and FNw = |G| - TPw give
    TPw + 0.2 FPw + 0.8 FNw = 0.2 N + 0.8 |G| exactly (the TPw terms cancel), so the round-trip
    check below uses that collapsed form rather than re-expanding it.
    """
    g = 12225.896194356133
    tp0, n0 = 4791.0488856019765, 44090
    for target in (0.2665, 0.2800, 0.3195):
        fr = rf.add_arm_frontier(target, tp0, n0, g)
        for e_str, row in fr["dots_needed_by_marginal_efficiency"].items():
            dn = row["dots_needed"]
            if not np.isfinite(dn):
                # unreachable: the marginal dot does not clear the FP charge
                assert float(e_str) <= 0.2 * target + 1e-12
                continue
            assert float(e_str) > 0.2 * target
            tp = tp0 + float(e_str) * dn
            n = n0 + dn
            back = tp / (0.2 * n + 0.8 * g)          # rho = 1 collapsed denominator
            assert back == pytest.approx(target, rel=1e-8), (target, e_str)
            assert row["reachable_by_adding_dots"] is (dn > 0)


def test_rho_one_denominator_cancels_the_credit_term():
    """Guard the identity the collapsed form above relies on."""
    g, n = 12225.896194356133, 44090
    for tp in (1000.0, 4791.05, 9000.0):
        full = tp / (tp + 0.2 * (n - tp) + 0.8 * (g - tp))
        collapsed = tp / (0.2 * n + 0.8 * g)
        assert full == pytest.approx(collapsed, rel=1e-12)



def test_inclusion_threshold_matches_the_metric_module_derivation():
    for dti in (0.10, 0.2477, 0.2600, 0.3195):
        assert rf.metric.inclusion_threshold(dti) == pytest.approx(0.2 * dti / (1 - 0.2 * dti))


def test_leader_target_requires_strictly_more_credit_than_the_best_anchor():
    g = 12225.896194356133
    tp0, n0 = 4791.0488856019765, 44090
    req = rf.credit_required(0.3195, n0, g)
    assert req > tp0
    assert req / g > tp0 / g


def test_budget_expansion_at_the_live_marginal_efficiency_cannot_reach_the_leader_target():
    """A dot earning less than 0.2*target lowers DTI, so no amount of them reaches it."""
    g = 12225.896194356133
    e_marginal = 0.03098          # live-measured from the d=1.5 -> d=2.8 thinning pair
    fr = rf.add_arm_frontier(0.3195, 4791.0488856019765, 44090, g)
    # every efficiency in the table below the break-even must be reported unreachable
    for e_str, row in fr["dots_needed_by_marginal_efficiency"].items():
        if float(e_str) < 0.2 * 0.3195:
            assert not row["reachable_by_adding_dots"]
    assert e_marginal < metric.inclusion_threshold(0.2600)


# --------------------------------------------------------------------------------------------
# 3. the committed evidence file is internally consistent
# --------------------------------------------------------------------------------------------
@pytest.mark.skipif(not EVIDENCE.exists(), reason="run scripts/reachability_frontier.py first")
def test_committed_evidence_is_consistent_with_the_functions():
    d = json.loads(EVIDENCE.read_text())
    assert d["identity_check"]["pass"] is True
    g = d["inputs"]["G_used_px"]
    cur = d["current_state"]
    req = d["conclusions"]["credit_gap_to_leader_at_current_budget_px"] + cur["credit_TPw"]
    assert req == pytest.approx(
        rf.credit_required(rf.LIVE_TARGET_LEADER, cur["emitted_px"], g), rel=1e-9
    )
    assert d["conclusions"]["gap_is_a_detection_gap"] is True
    assert d["conclusions"]["pruning_family_can_close_gap"] is False
    # the reported gap must be a large multiple of the best pruning arm ever measured (+0.0018 DTI)
    assert d["conclusions"]["credit_gap_to_leader_at_current_budget_px"] > 500.0
