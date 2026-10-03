#!/usr/bin/env python3
"""H37-1: directional (anisotropic) Poisson-disk re-pack of the H19-5 ridge.

Protocol frozen in ``knowledge/28_preregistration_H37-1.md`` before this file was executed.
Seeds 250-254 (fresh decade). The detector, the budget fraction and the fold definition are
**unmodified** from ``scripts/run_h36_1_holdout.py`` so every variant is comparable to H36-1
on the same OOF probability surface.

Variants (see the preregistration for the rationale):
  base_oof_d280                     shipped rung (thin_d=2.8) - the reference
  rung30_unpruned                   thin_d=3.0 - the H34 rung
  dir_3p5_2p0_unpruned              anisotropic pack, (a_along=3.5, a_across=2.0)
  dir_3p5_2p0_blind_r1              dir_3p5_2p0 then the H27-4 blind 1-px catalogue-flank prune
  dir_4p0_2p0_unpruned              anisotropic pack, (a_along=4.0, a_across=2.0)
  dir_3p0_2p0_unpruned              anisotropic pack, (a_along=3.0, a_across=2.0) - symmetric
  control_random_drop_matched_n     base randomly reduced, per fold, to dir_3p5_2p0's exact N
  control_iso_rung30_then_blind_r1  rung30 then blind prune (matches dir except anisotropic)

Writes ``evidence/h37_1_holdout.json``. Reads no hidden truth and never contacts drivendata.org.
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
from gems27 import grid, holdout, metric, oof_detector, paths, thinning  # noqa: E402

VARIANT_NAMES = [
    "base_oof_d280",
    "rung30_unpruned",
    "dir_3p5_2p0_unpruned",
    "dir_3p5_2p0_blind_r1",
    "dir_4p0_2p0_unpruned",
    "dir_3p0_2p0_unpruned",
    "control_random_drop_matched_n",
    "control_iso_rung30_then_blind_r1",
]
CANDIDATE_SET = [
    "dir_3p5_2p0_unpruned",
    "dir_3p5_2p0_blind_r1",
    "dir_4p0_2p0_unpruned",
    "dir_3p0_2p0_unpruned",
]
INCUMBENT = "dir_3p5_2p0_blind_r1"  # primary candidate if G1..G4 pass
TAU_LIVE_0260 = float(metric.inclusion_threshold(0.2600))
PROMOTION_MARGIN = 0.0003
#: RNG namespace for the anti-budget control. Disjoint from holdout seeds and from
#: H36-1 (910_000) / LOSFO namespaces; disclosed in the preregistration.
MATCHED_N_SEED_BASE = 937_000


def eval_set(pred: np.ndarray, g: np.ndarray, active: np.ndarray, k_pt: np.ndarray) -> tuple[float, float, float, int]:
    """(TPw, FPw, DTI, n_emitted) for one variant on one cell - identical to run_h36_1_holdout.py."""
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


def compute_ridge_strike(oof_prob: np.ndarray, foot: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-pixel unit strike vector on the OOF ridge surface, NaN outside the mask.

    Uses ``ridge_nms`` (already in ``oof_detector``) and the per-pixel sectorisation that drives it,
    mapping the gradient *normal* to four orthogonal strike bins (0, 45, 90, 135 degrees). Pixels
    outside the OOF ridge receive (0, 0) so ``directional_dot_thin`` falls back to isotropic there.
    """
    from scipy.ndimage import gaussian_filter
    sigma = 1.0
    s = np.where(foot & np.isfinite(oof_prob), oof_prob, 0.0).astype(np.float32)
    sm = gaussian_filter(s, sigma=sigma) if sigma > 0 else s
    gy, gx = np.gradient(sm)
    theta = np.mod(np.arctan2(gy, gx), np.pi)
    sector = np.floor(((theta + np.pi / 8.0) % np.pi) / (np.pi / 4.0)).astype(int)
    # Strike perpendicular to gradient normal: sector 0 (E-W normal) -> N-S ridge -> strike x=0, y=1
    strike_x = np.where(sector == 0, 0.0,
                np.where(sector == 2, 1.0,
                 np.where(sector == 1, -0.7071, 0.7071))).astype(np.float32)
    strike_y = np.where(sector == 0, 1.0,
                np.where(sector == 2, 0.0,
                 np.where(sector == 1, 0.7071, 0.7071))).astype(np.float32)
    return strike_x, strike_y


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="250-254")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h37_1_holdout.json"))
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
    print(f"OOF probabilities computed in {time.time()-t0:.1f}s", flush=True)

    # Pre-thinned base at the four rung sats -- H36-1's exact algorithm
    base_rung28 = oof_detector.build_oof_dotted_base(
        oof_prob, foot, fold >= 0, labels,
        budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8,
    )
    base_rung30 = oof_detector.build_oof_dotted_base(
        oof_prob, foot, fold >= 0, labels,
        budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=3.0,
    )
    # Strike field used by every anisotropic variant
    sx_full, sy_full = compute_ridge_strike(oof_prob, foot)
    print(f"Strike field computed in {time.time()-t0:.1f}s", flush=True)

    def build_dir(a_along: float, a_across: float) -> np.ndarray:
        return thinning.directional_dot_thin(
            base_rung30, sx_full, sy_full, a_along, a_across
        )

    dir_3p5_2p0 = build_dir(3.5, 2.0)
    dir_4p0_2p0 = build_dir(4.0, 2.0)
    dir_3p0_2p0 = build_dir(3.0, 2.0)
    print(f"Directional packs computed in {time.time()-t0:.1f}s "
          f"(3.5x2.0={int(dir_3p5_2p0.sum())}, 4.0x2.0={int(dir_4p0_2p0.sum())}, "
          f"3.0x2.0={int(dir_3p0_2p0.sum())} px)", flush=True)

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

            blind_r1 = distance_transform_edt(~kn) <= 1.0

            base = base_rung28[sl] & active
            rung30 = base_rung30[sl] & active
            dir_3p5 = dir_3p5_2p0[sl] & active
            dir_4p0 = dir_4p0_2p0[sl] & active
            dir_3p0 = dir_3p0_2p0[sl] & active

            rng = np.random.default_rng(MATCHED_N_SEED_BASE + 10 * seed + f)
            variants = {
                "base_oof_d280": base,
                "rung30_unpruned": rung30,
                "dir_3p5_2p0_unpruned": dir_3p5,
                "dir_3p5_2p0_blind_r1": dir_3p5 & ~blind_r1 & active,
                "dir_4p0_2p0_unpruned": dir_4p0,
                "dir_3p0_2p0_unpruned": dir_3p0,
                "control_random_drop_matched_n": _random_drop(base, int(dir_3p5.sum()), rng),
                "control_iso_rung30_then_blind_r1": rung30 & ~blind_r1 & active,
            }

            row = {"seed": seed, "fold": sp.name, "n_truth": int(g.sum())}
            for vn, mask in variants.items():
                tp, fp, dti, n_px = eval_set(mask, g, active, k_pt)
                row[vn] = {"tp": tp, "fp": fp, "dti": dti, "dots": n_px}
            cells.append(row)
        print(f"seed {seed} done (t={time.time()-t0:.0f}s): "
              f"base={np.mean([c['base_oof_d280']['dti'] for c in cells if c['seed']==seed]):.5f} "
              f"dir_3p5={np.mean([c['dir_3p5_2p0_unpruned']['dti'] for c in cells if c['seed']==seed]):.5f} "
              f"dir_3p5_r1={np.mean([c['dir_3p5_2p0_blind_r1']['dti'] for c in cells if c['seed']==seed]):.5f} "
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

    # ---- frozen gate (knowledge/28_preregistration_H37-1.md section 3) -------------------------
    def _s(v): return summary[v]["seeds_won"]
    def _f(v): return summary[v]["folds_improved"]
    def _g(v): return summary[v]["mean_dti_gain"]

    primary = INCUMBENT
    g1 = bool(_g(primary) > 0 and _s(primary) >= 4 and _f(primary) == 4)  # 5 seeds -> 4/5
    g2_delta = float(_g("dir_3p5_2p0_unpruned") - _g("control_random_drop_matched_n"))
    g2 = "anisotropic" if g2_delta > 0.0003 else ("generic" if g2_delta > -0.0003 else "worse-than-budget")
    g3_delta = float(_g("dir_3p5_2p0_unpruned") - _g("control_iso_rung30_then_blind_r1"))
    g3 = "beats-isotropic" if g3_delta > 0 else ("ties-isotropic" if g3_delta > -0.0003 else "worse-than-isotropic")
    eff = summary[primary]["removed_credit_per_removed_fp"]
    g4 = bool(eff > TAU_LIVE_0260)
    gate_passed = bool(g1 and g2 == "anisotropic" and g3 == "beats-isotropic" and g4)

    out = {
        "hypothesis": ("H37-1: directional (anisotropic) Poisson-disk re-pack of the H19-5 ridge, "
                       "(a_along, a_across) = (3.5, 2.0), with and without the H27-4 blind 1-px "
                       "catalogue-flank prune, on fresh seeds 250-254"),
        "preregistration": "knowledge/28_preregistration_H37-1.md",
        "seeds": seeds,
        "n_cells": len(cells),
        "base_oof_d280_mean_dti": base_mean_dti,
        "tau_live_0_2600": TAU_LIVE_0260,
        "variants": summary,
        "gate": {
            "G1_profitability_passed": g1,
            "G2_anisotropy_vs_budget_delta": g2_delta,
            "G2_anisotropy_vs_budget": g2,
            "G3_anisotropy_vs_isotropic_delta": g3_delta,
            "G3_anisotropy_vs_isotropic": g3,
            "G4_live_breakeven_passed": g4,
            "G4_efficiency": eff,
            "gate_passed": gate_passed,
        },
        "disclosures": {
            "matched_n_rng_namespace": MATCHED_N_SEED_BASE,
            "tied_to_h36_1_instrument": True,
            "no_external_data": True,
        },
        "runtime_s": round(time.time() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print("\n--- H37-1 ---")
    for vn in VARIANT_NAMES[1:]:
        s = summary[vn]
        print(f"  {vn:<32s} gain={s['mean_dti_gain']:+.6f} seeds={s['seeds_won']}/{s['n_seeds']} "
              f"folds={s['folds_improved']}/4 d_dots={s['delta_dots_per_seed']:+.0f} "
              f"eff={s['removed_credit_per_removed_fp']:.5f}")
    print(f"  G1={g1}  G2={g2} (delta {g2_delta:+.6f})  "
          f"G3={g3} (delta {g3_delta:+.6f})  G4={g4}  gate_passed={gate_passed}")
    print(f"\nwrote {args.out}")
    return 0


def _random_drop(base: np.ndarray, n_target: int, rng: np.random.Generator) -> np.ndarray:
    """Uniformly at random delete pixels of ``base`` until exactly ``n_target`` remain.

    Disjoint namespace from ``run_h36_1_holdout.random_drop_matched_n`` (910_000 vs 937_000) so
    the two harnesses cannot produce identical control layouts.
    """
    ys, xs = np.nonzero(base)
    n = len(ys)
    if n_target >= n:
        return base.copy()
    keep = rng.choice(n, size=n_target, replace=False)
    out = np.zeros_like(base, bool)
    out[ys[keep], xs[keep]] = True
    return out


if __name__ == "__main__":
    raise SystemExit(main())