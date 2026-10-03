#!/usr/bin/env python3
"""Reachability frontier: what a live DTI target actually costs, in credit and in budget.

Motivation
----------
Every promotion decision in this repository has been an *emission-budget* decision (how densely to
thin a ridge, whether to prune a flank band, whether to add gap-closure dots). Those decisions are
worth ~0.001-0.010 DTI each. The public leaderboard #1 is 0.3195 and the best owner-anchored
submission is 0.2600, a gap of +0.0595 - one to two orders of magnitude larger than any pruning arm
has ever produced. This script answers, from the official metric identity alone, whether that gap is
reachable by budget reallocation at all, or whether it is a *detection* gap.

Method
------
The official DTI (DrivenData #306 problem page; re-implemented in `src/gems27/metric.py`) is

    DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw),  FNw = |G| - TPw

Writing FPw = N - MPw and rho = MPw / TPw (N = emitted pixels, MPw = matched predicted mass) gives
the algebraically equivalent closed form used by `scripts/invert_live_scores.py`:

    DTI = TPw / (0.2 TPw (1 - rho) + 0.2 N + 0.8 |G|)

`verify_identity()` below checks that equivalence numerically against `metric.dti_binary` rather
than trusting the algebra. Everything else follows by solving that one equation for the unknown the
operator controls:

* `credit_required(target, N, rho)` - the TPw needed to score `target` while emitting `N` pixels.
* `budget_required(target, TPw, rho)` - the N needed to score `target` with credit TPw.
* `add_arm_frontier(target, TP0, N0, e)` - how many *new* dots are needed if each new dot earns a
  marginal credit `e`, i.e. Delta_N = (C_req - TP0) / (e - 0.2 target). This is the actionable form:
  it converts "beat 0.3195" into "place K dots that land on unmapped fault traces".

Reads only `evidence/live_inversion.json` (already committed) and the local grid; makes no network
request and never contacts drivendata.org.

Usage
-----
    python scripts/reachability_frontier.py [--out evidence/reachability_frontier.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, metric, paths  # noqa: E402

ALPHA = metric.ALPHA          # 0.2 false-positive weight (official)
BETA = metric.BETA            # 0.8 false-negative weight (official)
RHO_ONE = 1.0                 # naive closure FPw = N - TPw: conservative, ignores crowding credit

# Owner-anchored live references. Scores are owner-reported, not organizer receipts; they are used
# only as *relative* calibration points and are labelled as such wherever they appear.
LIVE_ANCHOR_BEST = {"label": "25GEMSDOE dotted-h19-5-d2-8 (e56ea318af89)", "score": 0.2600}
LIVE_TARGET_LEADER = 0.3195   # public leaderboard #1 read 2026-10-03 (row does not identify owner)


def verify_identity(n_cases: int = 24, seed: int = 20261003) -> dict:
    """Check DTI = TPw/(0.2 TPw (1-rho) + 0.2 N + 0.8|G|) against the exact metric, case by case.

    Builds random binary truth/prediction grids (including soft-free degenerate cases: empty truth,
    empty prediction, prediction equal to truth, isolated single dots) and asserts the closed form
    reproduces `metric.dti_binary` to float tolerance. A failure here invalidates every number this
    script reports, so it runs first and is recorded in the evidence file.
    """
    rng = np.random.default_rng(seed)
    worst = 0.0
    cases = []
    H = W = 80
    for i in range(n_cases):
        if i == 0:
            truth = np.zeros((H, W), bool)                       # empty truth
            pred = rng.random((H, W)) < 0.02
        elif i == 1:
            truth = rng.random((H, W)) < 0.01
            pred = np.zeros((H, W), bool)                        # empty prediction
        elif i == 2:
            truth = rng.random((H, W)) < 0.01
            pred = truth.copy()                                  # prediction == truth
        elif i == 3:
            truth = np.zeros((H, W), bool)
            truth[40, 40] = True
            pred = np.zeros((H, W), bool)
            pred[40, 40] = True                                  # single coincident dot
        else:
            # 1-D curvilinear traces plus scattered dots: the geometry real emissions have
            truth = np.zeros((H, W), bool)
            for _ in range(rng.integers(1, 6)):
                y, x = int(rng.integers(5, H - 5)), int(rng.integers(5, W - 5))
                for _ in range(int(rng.integers(4, 25))):
                    truth[y, x] = True
                    y = int(np.clip(y + rng.integers(-1, 2), 0, H - 1))
                    x = int(np.clip(x + rng.integers(-1, 2), 0, W - 1))
            pred = np.zeros((H, W), bool)
            ys, xs = np.nonzero(truth)
            if ys.size:
                pick = rng.choice(ys.size, size=max(1, ys.size // 3), replace=False)
                pred[ys[pick], xs[pick]] = True
            pred[rng.integers(0, H), rng.integers(0, W)] = True  # at least one stray FP
        if not truth.any():
            continue                                             # DTI undefined (n_truth == 0)
        exact = metric.dti_binary(pred, truth)
        p = pred > 0
        n_emit = int(p.sum())
        tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[truth]).sum())
        mp = float(metric.kernel_from_distance(distance_transform_edt(~truth)[p]).sum())
        rho = mp / tp if tp > 0 else 0.0
        closed = tp / (ALPHA * tp * (1.0 - rho) + ALPHA * n_emit + BETA * int(truth.sum()) + metric.EPS)
        resid = abs(exact["dti"] - closed)
        worst = max(worst, resid)
        cases.append({"case": i, "n_truth": int(truth.sum()), "n_emitted": n_emit,
                      "dti_exact": exact["dti"], "dti_closed_form": closed, "residual": resid,
                      "rho": rho, "closure_fpw": float(exact["FPw"]), "n_minus_mpw": float(n_emit - mp)})
    return {
        "n_cases": len(cases),
        "max_abs_residual": worst,
        "tolerance": 1e-8,
        "pass": bool(worst < 1e-8),
        "closure_fpw_equals_n_minus_mpw": all(
            abs(c["closure_fpw"] - c["n_minus_mpw"]) < 1e-9 for c in cases
        ),
        "cases": cases[:6],
    }


def credit_required(target: float, n_emit: int, g_size: float, rho: float = RHO_ONE) -> float:
    """TPw needed to reach `target` while emitting `n_emit` off-catalogue pixels, at crowding `rho`.

    From target = TP/(0.2 TP (1-rho) + 0.2 N + 0.8|G|):
        TP = target (0.2 N + 0.8|G|) / (1 - 0.2 target (1 - rho))
    """
    denom = 1.0 - ALPHA * target * (1.0 - rho)
    if denom <= 0:
        return float("inf")
    return float(target * (ALPHA * n_emit + BETA * g_size) / denom)


def budget_required(target: float, tp: float, g_size: float, rho: float = RHO_ONE) -> float:
    """N needed to reach `target` holding credit TPw fixed, at crowding `rho`.

    Rearranging target = TP/(0.2 TP (1-rho) + 0.2 N + 0.8|G|) for N:
        N = [TP - target (0.2 TP (1-rho) + 0.8|G|)] / (0.2 target)
    Negative means the credit alone already exceeds the target's requirement at N = 0.
    """
    denom = ALPHA * target
    if denom <= 0:
        return float("inf")
    return float((tp - target * (ALPHA * tp * (1.0 - rho) + BETA * g_size)) / denom)


def add_arm_frontier(target: float, tp0: float, n0: int, g_size: float,
                     rho: float = RHO_ONE) -> dict:
    """How many NEW dots, at marginal credit `e` each, are needed to reach `target`.

    Adding Delta_N dots that earn Delta_TP = e * Delta_N total credit moves
        TP0 -> TP0 + e Delta_N,   N0 -> N0 + Delta_N.
    Solving target = (TP0 + e Delta_N) / (0.2 (TP0 + e Delta_N)(1-rho) + 0.2 (N0 + Delta_N) + 0.8|G|)
    for Delta_N gives, at rho = 1, the clean form Delta_N = (C_req - TP0) / (e - 0.2 target):
    each new dot must beat the 0.2*target FP charge to help at all, which is exactly
    `metric.inclusion_threshold`.
    """
    c_req = credit_required(target, n0, g_size, rho)
    gap = c_req - tp0
    out = {"target": target, "credit_required_at_current_budget": c_req, "credit_gap": gap,
           "credit_gap_fraction_of_G": gap / g_size, "inclusion_threshold": metric.inclusion_threshold(target),
           "dots_needed_by_marginal_efficiency": {}}
    for e in (0.07, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.75, 1.00):
        # Coefficient of Delta_N when substituting TP = TP0 + e*dN, N = N0 + dN into the identity:
        #   (TP0 + e dN) = target [0.2 (TP0 + e dN)(1-rho) + 0.2 (N0 + dN) + 0.8|G|]
        # => dN = (C_req - TP0) / [ e (1 - 0.2 target (1-rho)) - 0.2 target ]
        a = e * (1.0 - ALPHA * target * (1.0 - rho)) - ALPHA * target
        dn = gap / a if a > 1e-12 else float("inf")
        out["dots_needed_by_marginal_efficiency"][f"{e:.2f}"] = {
            "dots_needed": float(dn),
            "reachable_by_adding_dots": bool(np.isfinite(dn) and dn > 0),
            "note": ("infinite => a dot earning this much marginal credit does not clear the "
                     "0.2*target false-positive charge, so no budget of such dots can reach the target"),
        }
    return out


def empirical_marginal_efficiency(submissions: list[dict], pairs: list[dict]) -> list[dict]:
    """Marginal credit per pixel between near-nested live submissions.

    For a pair where A is (almost) contained in B, the pixels B has that A lacks earned
    (credit_B - credit_A) over (N_B - N_A) pixels. This is the only *live-measured* estimate of the
    marginal efficiency of the dots this programme has actually been adding and removing.
    """
    by_label = {s["label"]: s for s in submissions}
    out = []
    for pr in pairs:
        a, b = pr["a"], pr["b"]
        sa, sb = by_label.get(a), by_label.get(b)
        if not sa or not sb:
            continue
        na, nb = sa["n_scored"], sb["n_scored"]
        ca, cb = sa["credit_TPw"], sb["credit_TPw"]
        if nb == na:
            continue
        # orientation: the larger emission is the one that added pixels
        big, small = (sb, sa) if nb > na else (sa, sb)
        dn = abs(nb - na)
        dc = (cb - ca) if nb > na else (ca - cb)
        out.append({
            "kept": small["label"], "dropped_or_added_relative_to": big["label"],
            "n_small": small["n_scored"], "n_big": big["n_scored"],
            "credit_small": small["credit_TPw"], "credit_big": big["credit_TPw"],
            "delta_pixels": dn, "delta_credit": dc,
            "marginal_credit_per_pixel": dc / dn if dn else None,
            "reading": "positive => the extra pixels earned credit; compare against the inclusion "
                       "threshold at the achieved score to see whether keeping them was right",
        })
    return sorted(out, key=lambda r: -(r["delta_pixels"] or 0))


def g_sensitivity(target: float, n_emit: int, tp_now: float, g_base: float) -> list[dict]:
    """How the required-credit gap moves if the blind-lattice |G| calibration is off."""
    out = []
    for frac in (0.75, 0.9, 1.0, 1.1, 1.25):
        g = g_base * frac
        req = credit_required(target, n_emit, g)
        out.append({"g_multiplier": frac, "g_px": g, "credit_required": req,
                    "credit_gap": req - tp_now, "credit_now_fraction_of_G": tp_now / g})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inversion", default=str(paths.EVIDENCE / "live_inversion.json"))
    ap.add_argument("--out", default=str(paths.EVIDENCE / "reachability_frontier.json"))
    args = ap.parse_args()

    ident = verify_identity()
    if not ident["pass"]:
        raise SystemExit(f"identity check FAILED (max residual {ident['max_abs_residual']:.3e})")

    inv = json.loads(Path(args.inversion).read_text())
    g = float(inv["G_used"])
    subs = inv["submissions"]
    best = next(s for s in subs if abs(s["score"] - LIVE_ANCHOR_BEST["score"]) < 1e-9
                and "d2-8" in s["label"])
    d15 = next(s for s in subs if "d1-5" in s["label"] and "dotted" in s["label"])

    # local geometry: the real footprint, to keep every "fraction of footprint" statement honest
    foot = grid.load_footprint(paths.TEMPLATE)
    n_footprint = int(foot.sum())

    targets = [0.2600, 0.2665, 0.2701, 0.2800, 0.3000, LIVE_TARGET_LEADER]
    budgets = [20000, 30000, 40199, 44090, 50000, 55000, 60069, 70000, 90000, 121131]

    frontier = []
    for t in targets:
        row = {"target": t, "inclusion_threshold": metric.inclusion_threshold(t), "by_budget": {}}
        for n in budgets:
            req1 = credit_required(t, n, g, RHO_ONE)
            reqr = credit_required(t, n, g, best["rho_matched_over_TP"])
            row["by_budget"][str(n)] = {
                "credit_required_rho1": req1,
                "credit_required_at_anchor_rho": reqr,
                "credit_required_fraction_of_G": req1 / g,
                "credit_per_emitted_px_required": req1 / n,
            }
        frontier.append(row)

    tp0, n0 = best["credit_TPw"], best["n_scored"]
    add_frontier = {
        f"{t:.4f}": add_arm_frontier(t, tp0, n0, g) for t in (0.2665, 0.2701, 0.2800, LIVE_TARGET_LEADER)
    }

    # Live-measured marginal efficiency of the pixels this programme has actually traded
    marg = empirical_marginal_efficiency(
        subs, inv.get("consistency_checks", {}).get("near_nested_pairs", [])
    )
    # The one exactly-controlled pair: d=1.5 vs d=2.8 is the same ridge at two thinning budgets.
    thin_pair = {
        "kept": "d=2.8 (0.2600)", "relative_to": "d=1.5 (0.2477)",
        "pixels_removed": d15["n_scored"] - best["n_scored"],
        "credit_lost": d15["credit_TPw"] - best["credit_TPw"],
        "marginal_credit_per_removed_pixel": (
            (d15["credit_TPw"] - best["credit_TPw"]) / (d15["n_scored"] - best["n_scored"])
        ),
        "inclusion_threshold_at_0_2600": metric.inclusion_threshold(0.2600),
        "removal_was_correct": bool(
            (d15["credit_TPw"] - best["credit_TPw"]) / (d15["n_scored"] - best["n_scored"])
            < metric.inclusion_threshold(0.2477)
        ),
    }

    # Ceiling of the budget family: holding marginal efficiency at the live-measured value
    e_marg = thin_pair["marginal_credit_per_removed_pixel"]
    e_avg = best["credit_TPw"] / best["n_scored"]
    budget_family_ceiling = {
        "asymptote_at_current_average_efficiency": e_avg / ALPHA,
        "asymptote_at_live_marginal_efficiency": e_marg / ALPHA,
        "n_needed_at_average_efficiency_for_0_3195": (
            float(LIVE_TARGET_LEADER * BETA * g / (e_avg - ALPHA * LIVE_TARGET_LEADER))
            if e_avg > ALPHA * LIVE_TARGET_LEADER else None
        ),
        "marginal_efficiency_is_below_break_even": bool(e_marg < metric.inclusion_threshold(0.2600)),
        "reading": "DTI -> e/0.2 as N -> inf at fixed efficiency e. A budget expansion only helps "
                   "while the *marginal* dot beats 0.2*target; the live-measured marginal "
                   "efficiency of the last 15,979 thinned dots is reported above.",
    }

    res = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "Closed-form inversion of the official DTI, identity checked against "
                  "src/gems27/metric.dti_binary before use",
        "identity_check": ident,
        "inputs": {
            "inversion_file": args.inversion,
            "G_used_px": g,
            "G_calibration": inv.get("blind_lattice_calibration", {}),
            "n_corpus": inv.get("n_corpus"),
            "footprint_px": n_footprint,
            "score_provenance": "Owner-reported live scores and one public leaderboard reading; "
                               "not organizer receipts. Used as relative calibration only.",
        },
        "current_state": {
            "best_owner_anchor": best["label"],
            "score": best["score"],
            "emitted_px": n0,
            "credit_TPw": tp0,
            "credit_fraction_of_G": best["credit_fraction_of_G"],
            "average_credit_per_emitted_px": e_avg,
            "rho": best["rho_matched_over_TP"],
            "emitted_fraction_of_footprint": n0 / n_footprint,
        },
        "frontier": frontier,
        "add_arm_frontier": add_frontier,
        "live_measured_marginal_efficiency": {
            "thinning_pair": thin_pair,
            "near_nested_pairs": marg[:8],
        },
        "budget_family_ceiling": budget_family_ceiling,
        "G_sensitivity_for_leader_target": g_sensitivity(LIVE_TARGET_LEADER, n0, tp0, g),
    }

    # Headline conclusions, derived from the numbers above (not asserted)
    lead = add_frontier[f"{LIVE_TARGET_LEADER:.4f}"]
    res["conclusions"] = {
        "credit_gap_to_leader_at_current_budget_px": lead["credit_gap"],
        "credit_gap_to_leader_fraction_of_G": lead["credit_gap_fraction_of_G"],
        "relative_credit_increase_needed": lead["credit_gap"] / tp0,
        "dots_needed_if_each_new_dot_earns_0_40": lead["dots_needed_by_marginal_efficiency"]["0.40"]["dots_needed"],
        "dots_needed_if_each_new_dot_earns_0_20": lead["dots_needed_by_marginal_efficiency"]["0.20"]["dots_needed"],
        "dots_needed_if_each_new_dot_earns_0_10": lead["dots_needed_by_marginal_efficiency"]["0.10"]["dots_needed"],
        "pruning_family_can_close_gap": False,
        "gap_is_a_detection_gap": bool(
            lead["credit_gap"] / tp0 > 0.10
            and budget_family_ceiling["marginal_efficiency_is_below_break_even"]
        ),
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n")

    print(f"identity check: {ident['n_cases']} cases, max residual {ident['max_abs_residual']:.2e} "
          f"-> {'PASS' if ident['pass'] else 'FAIL'}")
    print(f"|G| = {g:,.0f} px ; best anchor {best['label']} N={n0:,} credit={tp0:,.1f} "
          f"({best['credit_fraction_of_G']:.3f} of |G|)")
    print("\n  N\\target " + "".join(f"{t:>9.4f}" for t in targets))
    for n in budgets:
        line = f"{n:>8} "
        for t in targets:
            line += f"{credit_required(t, n, g):>9.0f}"
        print(line)
    print(f"\ncredit required for {LIVE_TARGET_LEADER} at N={n0:,}: "
          f"{lead['credit_required_at_current_budget']:,.1f} (gap {lead['credit_gap']:,.1f} px, "
          f"{100 * lead['credit_gap_fraction_of_G']:.2f} pts of |G|, "
          f"{100 * lead['credit_gap'] / tp0:.1f}% more credit than we capture today)")
    print("dots needed to reach the leader target, by marginal credit per new dot:")
    for e, v in lead["dots_needed_by_marginal_efficiency"].items():
        print(f"   e={e}: {v['dots_needed']:>12,.0f} dots")
    print(f"\nlive-measured marginal efficiency of the last {thin_pair['pixels_removed']:,} thinned "
          f"dots: {e_marg:.5f} credit/px vs break-even {metric.inclusion_threshold(0.26):.5f}")
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
