#!/usr/bin/env python3
"""H35-1 frozen gate: does a *hydrothermal-discharge conjunction* license added far-field dots?

The arm
-------
The reachability frontier (`evidence/reachability_frontier.json`) says the gap to the public #1 is
`~1,150` px of credit that only an *addition* arm can supply, and `knowledge/22_h34_result.md` §5
requires additions to be gated against `tau_live = 0.2*DTI/(1-0.2*DTI)` on truth that is genuinely
off-catalogue. The standing interleaved holdout has **no** far-field truth
(`evidence/arm_habitat_decomposition.json`), so the only admissible instrument is LOSFO
(`src/gems27/losfo.py`).

H35-1 asks: among ridge pixels the current emission does **not** already occupy, do those within
300 m of a GDR-1391 thermal spring/well earn enough marginal credit to pay the false-positive charge?

* Independent layer: `src/gems27/thermal.py` (GDR 1391 INGENIOUS). Not derived from the fault
  catalogue, so it does not inherit H33-1's `11.95 %` catalogue-coverage ceiling.
* Physics: thermal discharge is a *surface expression of subsurface permeability*. The competition's
  labels are a *surface-rupture* catalogue, so hydraulically active structures with no mapped
  Quaternary scarp are exactly the missing class.

Frozen criteria (all four must pass; written into `knowledge/23_h35_hypotheses.md` before the run)
-------------------------------------------------------------------------------------------------
G1 profitability   pooled marginal credit per thermal-added dot >= tau_live (at the 0.2600 anchor)
G2 differential    thermal credit/dot > matched-count random control, pooled, and per-seed win >= 4/5
G3 support         mean thermal-added dots per seed >= 200
G4 end-to-end      pooled DTI of base+thermal adds > pooled DTI of base (paired cells)

Dose-response columns (T>=50 C, geothermometry >=100 C, radius 1 px and 6 px) are reported for
interpretation only and are **not** part of the gate. Any failure closes the arm: no candidate TIFF,
no submission slot, no retuning within this run.

Nothing here contacts any network host.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, losfo, metric, oof_detector, paths, thermal  # noqa: E402

FOLD_NAMES = holdout.FOLD_NAMES
LIVE_ANCHOR_DTI = 0.2600  # dotted-h19-5-d2-8, GEMSDOE25 (owner-reported live score)


def tau_at(dti: float) -> float:
    """Inclusion threshold implied by the official metric at a given DTI."""
    return 0.2 * dti / (1.0 - 0.2 * dti)


def dti_of(pred: np.ndarray, truth: np.ndarray, active: np.ndarray) -> dict:
    p = np.asarray(pred, bool) & active
    n_g = int(truth.sum())
    if n_g == 0:
        return {"tp": 0.0, "fp": float(p.sum()), "dti": 0.0, "dots": int(p.sum()), "n_truth": 0}
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[truth]).sum())
    fp = float((1.0 - metric.kernel_from_distance(distance_transform_edt(~truth))[p]).sum())
    dti = tp / (tp + metric.ALPHA * fp + metric.BETA * (n_g - tp) + metric.EPS)
    return {"tp": tp, "fp": fp, "dti": dti, "dots": int(p.sum()), "n_truth": n_g}


def zeros_pool() -> dict:
    return {"cells": 0, "adds": 0, "marginal_credit": 0.0, "base_dti_sum": 0.0, "add_dti_sum": 0.0,
            "n_truth": 0, "base_tp": 0.0, "add_tp": 0.0, "base_dots": 0}


def update(pool: dict, *, adds: int, credit: float, base: dict, add: dict) -> None:
    pool["cells"] += 1
    pool["adds"] += int(adds)
    pool["marginal_credit"] += float(credit)
    pool["base_dti_sum"] += base["dti"]
    pool["add_dti_sum"] += add["dti"]
    pool["n_truth"] += base["n_truth"]
    pool["base_tp"] += base["tp"]
    pool["add_tp"] += add["tp"]
    pool["base_dots"] += base["dots"]


def summarise(pool: dict) -> dict:
    if not pool["cells"]:
        return {"cells": 0}
    return {
        "cells": pool["cells"],
        "adds": pool["adds"],
        "marginal_credit": pool["marginal_credit"],
        "credit_per_added_dot": pool["marginal_credit"] / max(1, pool["adds"]),
        "mean_base_dti": pool["base_dti_sum"] / pool["cells"],
        "mean_add_dti": pool["add_dti_sum"] / pool["cells"],
        "mean_delta_dti": (pool["add_dti_sum"] - pool["base_dti_sum"]) / pool["cells"],
        "mean_added_dots_per_cell": pool["adds"] / pool["cells"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="230-234", help="new decade; 210-214 is the Session-10 diagnostic")
    ap.add_argument("--thin-d", type=float, default=2.8, help="rung of the current live best emission")
    ap.add_argument("--control-per-cell", type=int, default=200,
                    help="target size of the random control draw per cell")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h35_1_thermal_farfield.json"))
    args = ap.parse_args()

    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]
    t0 = time.time()

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)

    sites = thermal.load_sites(paths.WELLSPRING)
    audit = sites.attrs["audit"]
    layers = {
        "primary_temp_ge20c": dict(temp_c_min=thermal.TEMP_CUT_PRIMARY_C),
        "dose_temp_ge50c": dict(temp_c_min=thermal.TEMP_CUT_DOSE_C),
        "dose_geotherm_ge100c": dict(geotherm_c_min=thermal.GEOTHERM_CUT_DOSE_C),
    }
    masks = {k: thermal.sites_mask(sites, foot, **v) for k, v in layers.items()}
    layer_counts = {k: int(m.sum()) for k, m in masks.items()}

    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    tau_live = tau_at(LIVE_ANCHOR_DTI)

    print(f"thermal sites: {len(sites):,} unique (raw {audit['n_records_raw']:,}); "
          f"grid cells {layer_counts}", flush=True)
    print(f"tau_live @ DTI {LIVE_ANCHOR_DTI} = {tau_live:.6f}", flush=True)

    pools = {"thermal": zeros_pool(), "control": zeros_pool(),
             "dose_temp_ge50c": zeros_pool(), "dose_geotherm_ge100c": zeros_pool(),
             "dose_radius_1px": zeros_pool(), "dose_radius_6px": zeros_pool()}
    per_seed_win = []
    cells = []
    threshold_stability = {}

    for seed in seeds:
        hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=seed)
        masked = losfo.masked_labels(labels, sys_grid, hold, losfo.DEFAULT_BUFFER_PX)
        prob = oof_detector.fit_predict_oof_probabilities(foot, masked, fold)
        ridge = oof_detector.ridge_nms(prob, foot, sigma=1.0)
        rng = np.random.default_rng(seed)

        seed_thermal_credit = seed_control_credit = 0.0
        seed_thermal_adds = seed_control_adds = 0

        for f in range(4):
            sp = losfo.build_losfo_split(labels, sys_grid, hold, fold, f, seed,
                                         FOLD_NAMES, losfo.DEFAULT_BUFFER_PX)
            if not sp.hidden.any():
                continue
            sl = holdout.crop(None, sp.fold_mask)
            fm = sp.fold_mask[sl]
            hidden = sp.hidden[sl]
            active = fm & ~sp.known[sl]

            base = oof_detector.build_oof_dotted_base(
                prob[sl], ridge[sl], fm, sp.known[sl],
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=args.thin_d) & active
            cand = ridge[sl] & active & ~base
            cys, cxs = np.nonzero(cand)
            if len(cys) == 0:
                continue

            base_res = dti_of(base, hidden, active)
            d_primary = thermal.distance_to_sites(masks["primary_temp_ge20c"])[sl]

            for name, near_px, pool_key in (
                ("thermal", thermal.NEAR_PX_PRIMARY, "thermal"),
                ("dose_radius_1px", 1, "dose_radius_1px"),
                ("dose_radius_6px", 6, "dose_radius_6px"),
            ):
                sel = d_primary[cys, cxs] <= near_px
                adds = np.zeros_like(base)
                if sel.any():
                    adds[cys[sel], cxs[sel]] = True
                cred = thermal.marginal_credit(base, adds, hidden)
                res = dti_of(base | adds, hidden, active)
                update(pools[pool_key], adds=int(sel.sum()), credit=cred, base=base_res, add=res)
                if pool_key == "thermal":
                    seed_thermal_credit += cred
                    seed_thermal_adds += int(sel.sum())

            # dose-response on the temperature / geothermometry cuts, at the primary radius
            for key in ("dose_temp_ge50c", "dose_geotherm_ge100c"):
                dd = thermal.distance_to_sites(masks[key])[sl]
                sel = dd[cys, cxs] <= thermal.NEAR_PX_PRIMARY
                adds = np.zeros_like(base)
                if sel.any():
                    adds[cys[sel], cxs[sel]] = True
                cred = thermal.marginal_credit(base, adds, hidden)
                update(pools[key], adds=int(sel.sum()), credit=cred,
                       base=base_res, add=dti_of(base | adds, hidden, active))

            # matched-count random control drawn from candidates NOT near any primary site
            far = d_primary[cys, cxs] > 6
            fys, fxs = cys[far], cxs[far]
            n_ctrl = min(len(fys), max(args.control_per_cell, int((d_primary[cys, cxs] <= 3).sum())))
            if n_ctrl:
                pick = rng.choice(len(fys), size=n_ctrl, replace=False)
                adds = np.zeros_like(base)
                adds[fys[pick], fxs[pick]] = True
                cred = thermal.marginal_credit(base, adds, hidden)
                update(pools["control"], adds=n_ctrl, credit=cred, base=base_res,
                       add=dti_of(base | adds, hidden, active))
                seed_control_credit += cred
                seed_control_adds += n_ctrl

            cells.append({
                "seed": seed, "fold": sp.name,
                "n_truth": base_res["n_truth"], "n_base_dots": base_res["dots"],
                "n_candidates": int(len(cys)),
                "n_thermal_adds": int((d_primary[cys, cxs] <= 3).sum()),
                "base_dti": base_res["dti"],
            })

        if seed_control_adds and seed_thermal_adds:
            win = (seed_thermal_credit / seed_thermal_adds) > (seed_control_credit / seed_control_adds)
            per_seed_win.append({"seed": seed, "thermal_credit_per_dot":
                                 seed_thermal_credit / max(1, seed_thermal_adds),
                                 "control_credit_per_dot": seed_control_credit / max(1, seed_control_adds),
                                 "thermal_wins": bool(win)})
        print(f"seed {seed} done (t={time.time() - t0:.0f}s)", flush=True)

    summary = {k: summarise(v) for k, v in pools.items()}
    wins = sum(1 for w in per_seed_win if w["thermal_wins"])
    crit = {
        "G1_profitability": {
            "required": f">= tau_live = {tau_live:.6f} credit per added dot",
            "observed": summary["thermal"]["credit_per_added_dot"],
            "pass": bool(summary["thermal"]["credit_per_added_dot"] >= tau_live),
        },
        "G2_differential": {
            "required": "thermal credit/dot > matched-count random control, pooled, and >= 4/5 seeds",
            "observed_pooled_thermal": summary["thermal"]["credit_per_added_dot"],
            "observed_pooled_control": summary["control"]["credit_per_added_dot"],
            "seeds_won": wins, "seeds_total": len(per_seed_win),
            "pass": bool(summary["thermal"]["credit_per_added_dot"]
                         > summary["control"]["credit_per_added_dot"] and wins >= 4),
        },
        "G3_support": {
            "required": ">= 200 thermal-added dots per seed on average",
            "observed": summary["thermal"]["mean_added_dots_per_cell"] if not cells else
                        summary["thermal"]["adds"] / max(1, len(seeds)),
            "pass": bool(summary["thermal"]["adds"] / max(1, len(seeds)) >= 200),
        },
        "G4_end_to_end": {
            "required": "pooled mean delta DTI > 0 when adding the thermal dots to the emission",
            "observed": summary["thermal"]["mean_delta_dti"],
            "pass": bool(summary["thermal"]["mean_delta_dti"] > 0),
        },
    }
    gate_passed = all(c["pass"] for c in crit.values())

    # threshold stability: which DTI anchor would flip G1?
    if summary["thermal"]["credit_per_added_dot"] > 0:
        e = summary["thermal"]["credit_per_added_dot"]
        solve = [d for d in np.arange(0.02, 0.60, 0.005) if tau_at(float(d)) <= e]
        threshold_stability = {
            "measured_efficiency": e,
            "tau_at_losfo_base_dti": tau_at(summary["thermal"]["mean_base_dti"]),
            "dti_at_which_e_becomes_profitable": (float(min(solve)) if solve else None),
            "note": ("the arm is judged at the LIVE anchor 0.2600 (tau=0.0548) because that is the "
                     "shippable file the added dots would go into; the LOSFO scale DTI is a proxy "
                     "and is reported for context only"),
        }

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hypothesis": "H35-1 hydrothermal-discharge conjunction (ADDITION arm)",
        "instrument": "leave-fault-system-out (LOSFO), 600 m label buffer, 4 quadrant folds",
        "status": "PROMOTABLE" if gate_passed else "CLOSED_ON_OWN_EVIDENCE",
        "gate_passed": bool(gate_passed),
        "criteria": crit,
        "auroc_context": {"tau_live_anchor_dti": LIVE_ANCHOR_DTI, "tau_live": tau_live},
        "layer": {
            "file": "data/gdr_wellspring_in_footprint.csv",
            "provenance": "GDR submission 1391 (INGENIOUS), hash-pinned public mirror; "
                          "integrity-pinned, not organizer-authenticated",
            "audit": audit,
            "cells": layer_counts,
            "catalogue_derived_columns_used": [],
            "excluded_columns": list(thermal.CATALOGUE_DERIVED_COLUMNS),
        },
        "summary": summary,
        "per_seed": per_seed_win,
        "threshold_stability": threshold_stability,
        "cells": cells,
        "seeds": seeds,
        "thin_d_px": args.thin_d,
        "code_sha256": {
            "thermal": hashlib.sha256((paths.REPO / "src" / "gems27" / "thermal.py").read_bytes()).hexdigest(),
            "losfo": hashlib.sha256((paths.REPO / "src" / "gems27" / "losfo.py").read_bytes()).hexdigest(),
            "oof_detector": hashlib.sha256(
                (paths.REPO / "src" / "gems27" / "oof_detector.py").read_bytes()).hexdigest(),
            "runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "disclosure": [
            "Held-out systems are still *mapped* faults, so the measured credit/dot is an UPPER BOUND "
            "on performance against genuinely unmapped faults (losfo.py 'Known limits').",
            "The 32-band feature rasters are not re-derived with held-out systems removed; the "
            "thermal layer is not catalogue-derived, so it is admissible, but the magnetic/gravity "
            "bands may carry a catalogue imprint that this protocol cannot remove.",
            "No seed in 210-214 (the Session-10 diagnostic decade) or 180-229 (consumed by H32/H33/H34) "
            "is reused: this run takes the next free decade 230-234.",
        ],
        "seconds": time.time() - t0,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")

    print(json.dumps({k: {"pass": v["pass"]} for k, v in crit.items()}, indent=1))
    print(f"\nthermal credit/dot {summary['thermal']['credit_per_added_dot']:.5f} vs tau_live "
          f"{tau_live:.5f}; control {summary['control']['credit_per_added_dot']:.5f}")
    print(f"gate {'PASSED' if gate_passed else 'FAILED'} -> {out['status']}")
    print(f"written {args.out} ({out['seconds']:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
