#!/usr/bin/env python3
"""H36-1: the packing-rung re-pack at rung 3.0, with and without the catalogue-flank prunes.

Protocol frozen in ``knowledge/26_preregistration_H36-1.md`` before this file was executed.
Seeds 240-249 (fresh decade). The detector, the budget fraction and the fold definition are
**unmodified** from ``scripts/run_h32_1_holdout.py``; only the emission rules differ, so every
variant is compared through the same instrument.

Variants (see the preregistration for the rationale of each):
  base_oof_d280                    shipped rung (thin_d=2.8) - the reference
  rung30_unpruned                  thin_d=3.0 - the H34 claim in isolation
  rung30_blind_r1                  rung 3.0 then the H27-4 blind 1-px catalogue-flank prune
  rung30_flank_mid                 rung 3.0 then the H32-1 mid-segment flank-shadow prune
  h27_4_blind_r1_d280              shipped rung then the blind prune (incumbent one-click primary)
  control_random_drop_matched_n    base randomly reduced, per fold, to rung30's exact N (anti-budget)
  control_rung30_protected_only    rung 3.0 with only the protected tip/Euler pixels removed

Writes ``evidence/h36_1_holdout.json``. Reads no hidden truth and never contacts drivendata.org.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import convolve, distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, metric, oof_detector, paths  # noqa: E402

VARIANT_NAMES = [
    "base_oof_d280",
    "rung30_unpruned",
    "rung30_blind_r1",
    "rung30_flank_mid",
    "h27_4_blind_r1_d280",
    "control_random_drop_matched_n",
    "control_rung30_protected_only",
]
CANDIDATE_SET = ["rung30_unpruned", "rung30_blind_r1", "rung30_flank_mid", "h27_4_blind_r1_d280"]
INCUMBENT = "h27_4_blind_r1_d280"
TAU_LIVE_0260 = float(metric.inclusion_threshold(0.2600))
PROMOTION_MARGIN = 0.0005
#: RNG namespace for the anti-budget control. Disjoint from holdout seeds (4242 + fold + 1000*seed)
#: and from the LOSFO / thermal namespaces; disclosed in the preregistration.
MATCHED_N_SEED_BASE = 910_000


def eval_set(pred: np.ndarray, g: np.ndarray, active: np.ndarray, k_pt: np.ndarray) -> tuple[float, float, float, int]:
    """(TPw, FPw, DTI, n_emitted) for one variant on one cell - identical to run_h32_1_holdout.py."""
    p = pred & active
    n_g = int(g.sum())
    if not p.any() or n_g == 0:
        fp = float((1.0 - k_pt[p]).sum()) if p.any() else 0.0
        return 0.0, fp, 0.0, int(p.sum())
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[g]).sum())
    fp = float((1.0 - k_pt[p]).sum())
    dti = tp / (tp + 0.2 * fp + 0.8 * (n_g - tp) + 1e-7)
    return tp, fp, dti, int(p.sum())


def load_euler_halo(shape: tuple[int, int], radius_px: float = 3.0) -> np.ndarray:
    """Protected class: shallow Euler depth-coherent clusters (H31-1), 3 px halo."""
    import csv

    df_path = paths.EVIDENCE / "h31_1_euler_clusters.csv"
    eu_mask = np.zeros(shape, bool)
    with df_path.open("r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            r = int(round(float(row["row"])))
            c = int(round(float(row["col"])))
            if 0 <= r < shape[0] and 0 <= c < shape[1]:
                eu_mask[r, c] = True
    return distance_transform_edt(~eu_mask) <= radius_px


def build_flank_mid_mask(known: np.ndarray, eu_halo: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(flank_mid, tip_or_euler) partition of the d_known <= 1.0 (100 m) ring.

    Copied verbatim from ``scripts/run_h32_1_holdout.py`` / ``scripts/build_h32_1_submissions.py``
    so the definition cannot drift between the gate and the builder.
    """
    if not known.any():
        z = np.zeros_like(known, bool)
        return z, z
    d_kn = distance_transform_edt(~known)
    kn_deg = convolve(known.astype(int), np.ones((3, 3), int), mode="constant") - 1
    end_mask = known & (kn_deg <= 1)
    d_end = distance_transform_edt(~end_mask) if end_mask.any() else np.full(known.shape, np.inf)
    kn_nbrs = convolve(known.astype(int), np.ones((3, 3), int), mode="constant")
    r1 = (d_kn > 0.0) & (d_kn <= 1.0)
    flank_mid = r1 & (d_end > 3.0) & (kn_nbrs >= 2) & ~eu_halo
    tip_or_euler = r1 & ~flank_mid
    return flank_mid, tip_or_euler


def random_drop_matched_n(base: np.ndarray, n_target: int, rng: np.random.Generator) -> np.ndarray:
    """Uniformly at random delete pixels of ``base`` until exactly ``n_target`` remain.

    Deletion order is drawn independently of any feature, so this is the anti-budget control: it
    matches the *count* of the rung-3.0 emission without reproducing its *layout*.
    """
    ys, xs = np.nonzero(base)
    n = len(ys)
    if n_target >= n:
        return base.copy()
    keep = rng.choice(n, size=n_target, replace=False)
    out = np.zeros_like(base, bool)
    out[ys[keep], xs[keep]] = True
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="240-249")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h36_1_holdout.json"))
    args = ap.parse_args()
    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]

    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    eu_halo = load_euler_halo(labels.shape, radius_px=3.0)

    print("Training 4-fold spatial-CV HistGradientBoostingClassifier (600 m buffer)...", flush=True)
    oof_prob = oof_detector.fit_predict_oof_probabilities(foot, labels, fold)
    ridge_all = oof_detector.ridge_nms(oof_prob, foot, sigma=1.0)
    print(f"OOF probabilities & ridges computed in {time.time()-t0:.1f}s "
          f"(total ridges={int(ridge_all.sum()):,})", flush=True)

    cells = []
    for seed in seeds:
        for f in range(4):
            sp = holdout.make_split(labels, fold, f, seed)
            fm = sp.fold_mask
            sl = holdout.crop(None, fm)
            hid, kn, fmc = sp.hidden[sl], (sp.known & fm)[sl], fm[sl]
            g = hid & fmc & ~kn
            active = fmc & ~kn
            k_pt = (metric.kernel_from_distance(distance_transform_edt(~g))
                    if g.any() else np.zeros_like(g, float))

            flank_mid, tip_or_eu = build_flank_mid_mask(kn, eu_halo[sl])
            blind_r1 = distance_transform_edt(~kn) <= 1.0

            base = oof_detector.build_oof_dotted_base(
                oof_prob[sl], ridge_all[sl], fmc, kn,
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8,
            ) & active
            rung30 = oof_detector.build_oof_dotted_base(
                oof_prob[sl], ridge_all[sl], fmc, kn,
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=3.0,
            ) & active

            rng = np.random.default_rng(MATCHED_N_SEED_BASE + 10 * seed + f)
            variants = {
                "base_oof_d280": base,
                "rung30_unpruned": rung30,
                "rung30_blind_r1": rung30 & ~blind_r1 & active,
                "rung30_flank_mid": rung30 & ~flank_mid & active,
                "h27_4_blind_r1_d280": base & ~blind_r1 & active,
                "control_random_drop_matched_n": random_drop_matched_n(base, int(rung30.sum()), rng),
                "control_rung30_protected_only": rung30 & ~tip_or_eu & active,
            }

            row = {"seed": seed, "fold": sp.name, "n_truth": int(g.sum())}
            for vn, mask in variants.items():
                tp, fp, dti, n_px = eval_set(mask, g, active, k_pt)
                row[vn] = {"tp": tp, "fp": fp, "dti": dti, "dots": n_px}
            cells.append(row)
        print(f"seed {seed} done (t={time.time()-t0:.0f}s): "
              f"base={np.mean([c['base_oof_d280']['dti'] for c in cells if c['seed']==seed]):.5f} "
              f"rung30={np.mean([c['rung30_unpruned']['dti'] for c in cells if c['seed']==seed]):.5f} "
              f"rung30_r1={np.mean([c['rung30_blind_r1']['dti'] for c in cells if c['seed']==seed]):.5f} "
              f"randN={np.mean([c['control_random_drop_matched_n']['dti'] for c in cells if c['seed']==seed]):.5f}",
              flush=True)

    base_mean_dti = float(np.mean([c["base_oof_d280"]["dti"] for c in cells]))
    summary = {}
    for vn in VARIANT_NAMES[1:]:
        gains_by_seed = [
            float(np.mean([c[vn]["dti"] - c["base_oof_d280"]["dti"] for c in cells if c["seed"] == s]))
            for s in seeds
        ]
        gains_by_fold = {
            fn: float(np.mean([c[vn]["dti"] - c["base_oof_d280"]["dti"] for c in cells if c["fold"] == fn]))
            for fn in holdout.FOLD_NAMES
        }
        dtp = sum(c[vn]["tp"] - c["base_oof_d280"]["tp"] for c in cells)
        dfp = sum(c[vn]["fp"] - c["base_oof_d280"]["fp"] for c in cells)
        summary[vn] = {
            "mean_dti": float(base_mean_dti + np.mean(gains_by_seed)),
            "mean_dti_gain": float(np.mean(gains_by_seed)),
            "min_seed_gain": float(np.min(gains_by_seed)),
            "max_seed_gain": float(np.max(gains_by_seed)),
            "seeds_won": int(sum(g > 0 for g in gains_by_seed)),
            "n_seeds": len(seeds),
            "fold_gains": gains_by_fold,
            "folds_improved": int(sum(v > 0 for v in gains_by_fold.values())),
            "delta_dots_per_seed": float(
                sum(c[vn]["dots"] - c["base_oof_d280"]["dots"] for c in cells) / len(seeds)
            ),
            "removed_credit_per_removed_fp": float(
                (dtp / dfp) if dfp > 0 else ((-dtp) / (-dfp) if dfp < 0 else 0.0)
            ),
        }

    # ---- frozen gate (knowledge/26_preregistration_H36-1.md section 5) -------------------------
    def _s(v): return summary[v]["seeds_won"]
    def _f(v): return summary[v]["folds_improved"]
    def _g(v): return summary[v]["mean_dti_gain"]

    g1 = bool(_g("rung30_unpruned") > 0 and _s("rung30_unpruned") >= 8 and _f("rung30_unpruned") == 4)
    g2_delta = float(_g("rung30_unpruned") - _g("control_random_drop_matched_n"))
    g2 = "repack" if g2_delta > 0.0003 else ("budget-only" if g2_delta > -0.0003 else "worse-than-budget")
    prune_ok = {
        v: bool(_g(v) > 0 and _s(v) >= 8 and _f(v) == 4
                and summary[v]["removed_credit_per_removed_fp"] < TAU_LIVE_0260)
        for v in ("rung30_blind_r1", "rung30_flank_mid", INCUMBENT)
    }
    passing = [v for v in CANDIDATE_SET if (_s(v) >= 8 and _f(v) == 4)]
    winner = max(passing, key=_g) if passing else None
    promotion = None
    if winner is not None and winner != INCUMBENT:
        promotion = "PROMOTE" if (_g(winner) - _g(INCUMBENT)) >= PROMOTION_MARGIN else "TIE - incumbent stays"
    elif winner == INCUMBENT:
        promotion = "INCUMBENT WINS - no change"
    g5 = bool(winner is not None and _g("control_rung30_protected_only") >= _g(winner))

    out = {
        "hypothesis": ("H36-1: packing-rung re-pack at rung 3.0 (N=41,333), with and without the "
                       "H27-4 / H32-1 catalogue-flank prunes, on fresh seeds 240-249"),
        "preregistration": "knowledge/26_preregistration_H36-1.md",
        "seeds": seeds,
        "n_cells": len(cells),
        "base_oof_d280_mean_dti": base_mean_dti,
        "base_oof_d280_dots_per_seed": float(
            np.mean([sum(c["base_oof_d280"]["dots"] for c in cells if c["seed"] == s) for s in seeds])
        ),
        "tau_live_0_2600": TAU_LIVE_0260,
        "variants": summary,
        "gate": {
            "G1_rung_effect_passed": g1,
            "G2_repack_vs_budget": g2,
            "G2_delta_vs_matched_n_control": g2_delta,
            "G3_prune_variants_passed": prune_ok,
            "G4_winner": winner,
            "G4_promotion": promotion,
            "G4_promotion_margin": PROMOTION_MARGIN,
            "G5_antiselective_control_unsupported": g5,
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print("\n--- H36-1 ---")
    for vn in VARIANT_NAMES[1:]:
        s = summary[vn]
        print(f"  {vn:<32s} gain={s['mean_dti_gain']:+.6f} seeds={s['seeds_won']}/{s['n_seeds']} "
              f"folds={s['folds_improved']}/4 d_dots={s['delta_dots_per_seed']:+.0f} "
              f"eff={s['removed_credit_per_removed_fp']:.5f}")
    print(f"  G1={g1}  G2={g2} (delta {g2_delta:+.6f})  winner={winner}  {promotion}  G5={g5}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
