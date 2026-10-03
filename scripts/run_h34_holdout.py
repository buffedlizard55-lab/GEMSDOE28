#!/usr/bin/env python3
"""Spatially-blocked 4-fold out-of-fold holdout for H34: packing-ladder rung selection.

Protocol and gate are frozen in knowledge/21_preregistration_H34.md (registrered 2026-10-03, before
this run). Seeds 220-229, one use. The primary response is the *removal efficiency*

    e(a->b) = |dTPw| / |dFPw|

of each rung step, compared against tau_live = 0.2*DTI/(1-0.2*DTI) = 0.0548, the threshold of the
0.2600 submission this arm is meant to modify. The catalogue-holdout proxy scores ~0.095 and gates at
tau = 0.0193 - 2.85x stricter - so reading the proxy's own dDTI as the decision variable is the error
this arm corrects. The proxy dDTI is still reported, as a diagnostic, and is expected to be negative.

Writes evidence/h34_holdout.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, metric, oof_detector, paths  # noqa: E402

PREREG = Path(__file__).resolve().parents[1] / "knowledge" / "21_preregistration_H34.md"

# Rung values: the smallest separation dot_thin still allows on the integer grid.
RUNGS = {"rung_2_828": 2.8, "rung_3_000": 3.0, "rung_3_162": 3.1622776601683795}
ORDER = ["rung_2_828", "rung_3_000", "rung_3_162"]

# tau at the live operating point of the file this arm modifies (dotted-h19-5-d2-8, 0.2600).
TAU_LIVE = metric.inclusion_threshold(0.2600)
# tau at the proxy's own base control (H32-2 control mean, evidence/h32_2_holdout.json).
TAU_PROXY = metric.inclusion_threshold(0.094506)


def eval_set(pred: np.ndarray, g: np.ndarray, active: np.ndarray, k_pt: np.ndarray) -> dict:
    p = pred & active
    n_g = int(g.sum())
    n = int(p.sum())
    if n and n_g:
        tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[g]).sum())
        fp = float((1.0 - k_pt[p]).sum())
        dti = tp / (tp + metric.ALPHA * fp + metric.BETA * (n_g - tp) + metric.EPS)
    else:
        tp, fp, dti = 0.0, float((1.0 - k_pt[p]).sum()) if n else 0.0, 0.0
    return {"n": n, "tpw": tp, "fpw": fp, "dti": dti, "n_truth": n_g}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="220-229")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h34_holdout.json"))
    args = ap.parse_args()
    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]

    t0 = time.time()
    prereg_sha = hashlib.sha256(PREREG.read_bytes()).hexdigest() if PREREG.exists() else None

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)

    print("Training 4-fold spatial-CV HistGradientBoostingClassifier (600 m buffer) ...", flush=True)
    oof_prob = oof_detector.fit_predict_oof_probabilities(foot, labels, fold)
    ridge_all = oof_detector.ridge_nms(oof_prob, foot, sigma=1.0)
    finite = np.isfinite(oof_prob[foot]).all() and float(oof_prob[foot].min()) >= 0.0 \
        and float(oof_prob[foot].max()) <= 1.0
    print(f"ridges={int(ridge_all.sum()):,}  probabilities in [0,1]: {finite}", flush=True)

    cells = []
    for seed in seeds:
        for f in range(4):
            split = holdout.make_split(labels, fold, f, seed)
            active = split.fold_mask & ~split.known
            d_g = distance_transform_edt(~split.hidden)
            k_pt = metric.kernel_from_distance(d_g)
            base = oof_detector.build_oof_dotted_base(oof_prob, ridge_all, split.fold_mask,
                                                      split.known)
            row = {"seed": seed, "fold": f, "fold_name": split.name}
            for name, d in RUNGS.items():
                from gems27 import thinning
                dots = thinning.dot_thin(base, d)
                row[name] = eval_set(dots, split.hidden, active, k_pt)
            cells.append(row)
            print(f"  seed {seed} fold {split.name}: " +
                  "  ".join(f"{n.split('_',1)[1]}={row[n]['n']}" for n in ORDER), flush=True)

    # ---- step efficiencies -------------------------------------------------------------------
    def step_eff(key_from: str, key_to: str) -> dict:
        per_cell = []
        for c in cells:
            d_tp = c[key_to]["tpw"] - c[key_from]["tpw"]
            d_fp = c[key_to]["fpw"] - c[key_from]["fpw"]
            d_n = c[key_to]["n"] - c[key_from]["n"]
            per_cell.append({"seed": c["seed"], "fold": c["fold"], "fold_name": c["fold_name"],
                             "d_tpw": d_tp, "d_fpw": d_fp, "d_n": d_n,
                             "efficiency": abs(d_tp) / abs(d_fp) if d_fp else float("inf"),
                             "d_dti": c[key_to]["dti"] - c[key_from]["dti"]})
        effs = np.array([p["efficiency"] for p in per_cell], dtype=float)
        by_seed, by_fold = {}, {}
        for p in per_cell:
            by_seed.setdefault(p["seed"], []).append(p["efficiency"])
            by_fold.setdefault(p["fold_name"], []).append(p["efficiency"])
        return {
            "from": key_from, "to": key_to,
            "mean_efficiency": float(effs.mean()), "median_efficiency": float(np.median(effs)),
            "p10_efficiency": float(np.percentile(effs, 10)), "p90_efficiency": float(np.percentile(effs, 90)),
            "mean_d_dti": float(np.mean([p["d_dti"] for p in per_cell])),
            "mean_d_tpw": float(np.mean([p["d_tpw"] for p in per_cell])),
            "mean_d_fpw": float(np.mean([p["d_fpw"] for p in per_cell])),
            "mean_d_n": float(np.mean([p["d_n"] for p in per_cell])),
            "count_below_tau_live": int((effs < TAU_LIVE).sum()),
            "seeds_below_tau_live": int(sum(np.mean(v) < TAU_LIVE for v in by_seed.values())),
            "folds_below_tau_live": int(sum(np.mean(v) < TAU_LIVE for v in by_fold.values())),
            "n_cells": len(per_cell),
            "per_fold_efficiency": {k: float(np.mean(v)) for k, v in sorted(by_fold.items())},
            "per_seed_efficiency": {str(k): float(np.mean(v)) for k, v in sorted(by_seed.items())},
            "per_cell": per_cell,
        }

    steps = [step_eff(ORDER[0], ORDER[1]), step_eff(ORDER[1], ORDER[2]), step_eff(ORDER[0], ORDER[2])]

    # ---- the proxy's own optimum, reported as a diagnostic of the operating-point shift -------
    proxy_ladder = {}
    for name in ORDER:
        proxy_ladder[name] = {"mean_n": float(np.mean([c[name]["n"] for c in cells])),
                              "mean_tpw": float(np.mean([c[name]["tpw"] for c in cells])),
                              "mean_dti": float(np.mean([c[name]["dti"] for c in cells]))}
    proxy_best = max(proxy_ladder, key=lambda k: proxy_ladder[k]["mean_dti"])

    monotone = all(c[ORDER[0]]["n"] > c[ORDER[1]]["n"] > c[ORDER[2]]["n"] for c in cells)
    s1, s2 = steps[0], steps[1]
    gate = {
        "1_profitable_at_live_threshold": bool(s1["mean_efficiency"] < TAU_LIVE),
        "2_direction_control_next_rung_unprofitable": bool(s2["mean_efficiency"] > TAU_LIVE),
        "3_consistency_seeds_ge_8_of_10": bool(s1["seeds_below_tau_live"] >= 8),
        "3_consistency_folds_ge_3_of_4": bool(s1["folds_below_tau_live"] >= 3),
        "4_integrity_monotone_n_all_cells": bool(monotone),
        "4_integrity_probabilities_in_unit_interval": bool(finite),
        "4_integrity_grid_pinned": bool(int(foot.sum()) == 5_167_373 and int(labels.sum()) == 60_988),
    }
    gate["overall"] = "PASS" if all(gate[k] for k in gate if k != "overall") else "FAIL"

    report = {
        "schema": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis": "H34 packing-ladder rung selection (knowledge/21_preregistration_H34.md)",
        "preregistration_sha256": prereg_sha,
        "seeds": [seeds[0], seeds[-1]],
        "n_cells": len(cells),
        "rungs": RUNGS,
        "thresholds": {"tau_live": TAU_LIVE, "tau_proxy": TAU_PROXY,
                       "ratio": TAU_LIVE / TAU_PROXY,
                       "tau_live_basis": "0.2*DTI/(1-0.2*DTI) at the owner-reported 0.2600 submission",
                       "tau_proxy_basis": "same formula at the H32-2 base control mean 0.094506"},
        "variant_summary": proxy_ladder,
        "proxy_optimal_rung": proxy_best,
        "steps": steps,
        "gate": gate,
        "runtime_s": round(time.time() - t0, 1),
        "provenance_warning": ("Holdout truth is catalogue-internal; the proxy scores ~0.10 while the "
                               "modified artifact scores 0.26. Efficiencies are assumed, not proven, to "
                               "transfer across that gap (see preregistration section 5)."),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("\n--- H34 gate ---")
    print(f"tau_live={TAU_LIVE:.5f}  tau_proxy={TAU_PROXY:.5f}  ratio={TAU_LIVE/TAU_PROXY:.2f}")
    for k, v in gate.items():
        print(f"  {k:<48} {v}")
    for s in steps[:2]:
        print(f"  e({s['from']}->{s['to']}) mean={s['mean_efficiency']:.5f} "
              f"median={s['median_efficiency']:.5f}  seeds {s['seeds_below_tau_live']}/10 "
              f"folds {s['folds_below_tau_live']}/4  proxy dDTI={s['mean_d_dti']:+.5f}")
    print(f"  proxy's own optimal rung: {proxy_best}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
