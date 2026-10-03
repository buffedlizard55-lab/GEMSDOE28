#!/usr/bin/env python3
"""H38-1 frozen gate: radiometric alteration information recovery (GeoDAWN K, Th, U + Th/K, U/K, U/Th).

Protocol frozen in ``knowledge/38_preregistration_H38-1.md`` **before** this file was executed. Fresh
hypothesis-gate decade 260-269. Every other component - the HistGradientBoosting detector, the
quadrant folds, the 600 m buffer, ``PRE_THIN_FRAC``, ``ridge_nms``, the rung-3.0 budget, the
``H27-4`` blind 1-px catalogue-flank prune and the coverage packing rule - is byte-identical to
``scripts/run_h37_1_holdout.py``; the only difference is the feature matrix of the second detector.

Variants (per cell, all masked to ``active = fold_mask & ~known``):
  base_d280                D0 reference: dot_thin(top-k pool, 2.8)
  cover_r1                 D0: coverage packing at n_pre0 + blind_r1  (the H37-1 emission, fresh decade)
  rad_base_d280            D1: dot_thin(top-k pool, 2.8)               (secondary / do-no-harm rule)
  rad_cover_r1             D1: coverage packing at n_pre0 + blind_r1   (PRIMARY)
  control_random_matched_n content-blind uniform draw at n_pre0 + blind_r1

Writes ``evidence/h38_1_holdout.json``. Reads no hidden truth; never contacts drivendata.org.
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
import rasterio
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, metric, oof_detector, packing, paths, thinning  # noqa: E402

VARIANT_NAMES = [
    "base_d280",
    "cover_r1",
    "rad_base_d280",
    "rad_cover_r1",
    "control_random_matched_n",
]
PRIMARY = "rad_cover_r1"
INCUMBENT = "cover_r1"
CONTROL = "control_random_matched_n"
PROMOTION_MARGIN = 0.0005
CONTROL_SEED_BASE = 991_000
THIN_D_REF = 2.8
RUNG30 = 3.0
#: (raster, 1-based band index, name) - exactly the six channels frozen in knowledge/38 section 2.
RAD_EXTRA_BANDS = [
    ("rad", 1, "rad_K"), ("rad", 2, "rad_Th"), ("rad", 3, "rad_U"),
    ("ext", 1, "ext_ThK"), ("ext", 2, "ext_UK"), ("ext", 3, "ext_UTh"),
]


def load_extras(foot: np.ndarray) -> tuple[np.ndarray, dict]:
    """Six radiometric channels in row-major footprint order; NaN outside the footprint / at u8 zero."""
    planes = []
    for key, band, name in RAD_EXTRA_BANDS:
        path = paths.RAD if key == "rad" else paths.EXTENSIONS
        with rasterio.open(path) as src:
            a = src.read(band).astype(np.float32)
        if a.shape != foot.shape:
            raise SystemExit(f"{name}: shape {a.shape} != footprint {foot.shape}")
        a[(a <= 0) | (~foot)] = np.nan
        planes.append(a)
    stack = np.stack(planes, axis=-1)          # (H, W, 6)
    extras = stack[foot]                       # (n_foot, 6) row-major
    inside = foot.sum()
    finite_frac = float(np.isfinite(extras).mean())
    diag = {
        "names": [n for _, _, n in RAD_EXTRA_BANDS],
        "cells": int(inside),
        "finite_fraction_inside_footprint": finite_frac,
        "nan_outside_footprint": bool(np.isnan(stack[~foot]).all()),
    }
    if not diag["nan_outside_footprint"] or finite_frac < 0.999:
        raise SystemExit(f"radiometric extras failed the integrity precondition: {diag}")
    return extras, diag


def eval_set(pred: np.ndarray, g: np.ndarray, active: np.ndarray) -> tuple[float, float, float, int]:
    """(TPw, FPw, DTI, n_emitted) - identical closure to run_h37_1_holdout.py."""
    p = pred & active
    n_g = int(g.sum())
    if not p.any() or n_g == 0:
        k_pt = metric.kernel_from_distance(distance_transform_edt(~g)) if n_g else np.zeros_like(g, float)
        fp = float((1.0 - k_pt[p]).sum()) if p.any() else 0.0
        return 0.0, fp, 0.0, int(p.sum())
    k_pt = metric.kernel_from_distance(distance_transform_edt(~g))
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[g]).sum())
    fp = float((1.0 - k_pt[p]).sum())
    dti = tp / (tp + 0.2 * fp + 0.8 * (n_g - tp) + 1e-7)
    return tp, fp, dti, int(p.sum())


def top_pool(ridge: np.ndarray, prob: np.ndarray, k: int) -> np.ndarray:
    ys, xs = np.nonzero(ridge)
    pool = np.zeros_like(ridge, bool)
    if len(ys) == 0 or k <= 0:
        return pool
    if len(ys) > k:
        top = np.argpartition(-prob[ys, xs], k - 1)[:k]
        ys, xs = ys[top], xs[top]
    pool[ys, xs] = True
    return pool


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="260-269")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h38_1_holdout.json"))
    args = ap.parse_args()
    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]

    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    extras, extra_diag = load_extras(foot)
    print(f"extras {extra_diag['names']} finite {extra_diag['finite_fraction_inside_footprint']:.5f}",
          flush=True)

    print("Training D0 (32-band control) 4-fold spatial-CV detector...", flush=True)
    prob0 = oof_detector.fit_predict_oof_probabilities(foot, labels, fold)
    ridge0 = oof_detector.ridge_nms(prob0, foot, sigma=1.0)
    t0_done = time.time()
    print(f"D0 done in {t0_done - t0:.1f}s (ridges={int(ridge0.sum()):,})", flush=True)

    print("Training D1 (32 + 6 radiometric bands) 4-fold spatial-CV detector...", flush=True)
    prob1 = oof_detector.fit_predict_oof_probabilities(foot, labels, fold, extra=extras)
    ridge1 = oof_detector.ridge_nms(prob1, foot, sigma=1.0)
    print(f"D1 done in {time.time() - t0_done:.1f}s (ridges={int(ridge1.sum()):,})", flush=True)

    ridge_sym_diff = int((ridge0 ^ ridge1).sum())

    cells: list[dict] = []
    integrity: list[str] = []
    determinism_note = None
    for seed in seeds:
        for f in range(4):
            sp = holdout.make_split(labels, fold, f, seed)
            fm = sp.fold_mask
            sl = holdout.crop(None, fm)
            hid, kn, fmc = sp.hidden[sl], (sp.known & fm)[sl], fm[sl]
            g = hid & fmc & ~kn
            active = fmc & ~kn
            blind_r1 = distance_transform_edt(~kn) <= 1.0

            p0 = np.where(active, prob0[sl], 0.0).astype(np.float32)
            p1 = np.where(active, prob1[sl], 0.0).astype(np.float32)
            r0 = ridge0[sl] & active
            r1 = ridge1[sl] & active

            k = int(round(oof_detector.PRE_THIN_FRAC * int(fmc.sum())))
            n_pre0 = int(thinning.dot_thin(top_pool(r0, p0, k), RUNG30).sum())

            ys, xs = np.nonzero(r0)
            rng = np.random.default_rng(CONTROL_SEED_BASE + 10 * seed + f)
            random_sel = np.zeros_like(r0)
            if len(ys) and n_pre0 > 0:
                take = rng.choice(len(ys), size=min(n_pre0, len(ys)), replace=False)
                random_sel[ys[take], xs[take]] = True

            primary_pre = packing.coverage_greedy(r1, p1, n_pre0)
            incumbent_pre = packing.coverage_greedy(r0, p0, n_pre0)
            if determinism_note is None:
                again = packing.coverage_greedy(r1, p1, n_pre0)
                determinism_note = bool(np.array_equal(primary_pre, again))

            variants = {
                "base_d280": oof_detector.build_oof_dotted_base(
                    prob0[sl], ridge0[sl], fmc, kn, budget_frac=oof_detector.PRE_THIN_FRAC,
                    thin_d=THIN_D_REF) & active,
                "cover_r1": incumbent_pre & ~blind_r1,
                "rad_base_d280": oof_detector.build_oof_dotted_base(
                    prob1[sl], ridge1[sl], fmc, kn, budget_frac=oof_detector.PRE_THIN_FRAC,
                    thin_d=THIN_D_REF) & active,
                "rad_cover_r1": primary_pre & ~blind_r1,
                "control_random_matched_n": random_sel & ~blind_r1,
            }
            variants = {k_: v & active for k_, v in variants.items()}

            # ---- G5 integrity, per cell, before any metric is read -------------------------------
            # ERRATUM (2026-10-03, disclosed in knowledge/38 section 7): the pilot run tested the
            # POST-prune mask against n_pre0, which cannot hold because the arm definition applies the
            # H27-4 blind_r1 prune *after* packing. The check below mirrors the H37-1 gate
            # (run_h37_1_holdout.py line 146): the packer's own output must hit the requested count
            # exactly; the prune's effect is recorded separately as a diagnostic.
            if int(primary_pre.sum()) != n_pre0:
                integrity.append(f"seed {seed} fold {sp.name}: packer emitted "
                                 f"{int(primary_pre.sum())} != n_pre0={n_pre0}")
            if int(incumbent_pre.sum()) != n_pre0:
                integrity.append(f"seed {seed} fold {sp.name}: incumbent packer emitted "
                                 f"{int(incumbent_pre.sum())} != n_pre0={n_pre0}")
            if (variants[PRIMARY] & ~active).any():
                integrity.append(f"seed {seed} fold {sp.name}: primary outside active")
            if (variants[PRIMARY] & kn).any():
                integrity.append(f"seed {seed} fold {sp.name}: primary overlaps known catalogue")
            if int(variants[PRIMARY].sum()) == 0:
                integrity.append(f"seed {seed} fold {sp.name}: primary emitted nothing")

            row = {"seed": seed, "fold": sp.name, "n_truth": int(g.sum()), "n_pre0": n_pre0,
                   "n_packer_emitted": int(primary_pre.sum()),
                   "n_ridges_D0": int(r0.sum()), "n_ridges_D1": int(r1.sum()),
                   "prune_removed_primary": int(primary_pre.sum() - variants[PRIMARY].sum()),
                   "n_packer_emitted_incumbent": int(incumbent_pre.sum()),
                   "prune_removed_incumbent": int(
                       incumbent_pre.sum() - variants[INCUMBENT].sum()),
                   "dots_primary_postprune": int(variants[PRIMARY].sum()),
                   "dots_incumbent_postprune": int(variants[INCUMBENT].sum())}
            for vn, mask in variants.items():
                tp, fp, dti, n_px = eval_set(mask, g, active)
                row[vn] = {"tp": tp, "fp": fp, "dti": dti, "dots": n_px}
            cells.append(row)
        print(f"seed {seed} done (t={time.time()-t0:.0f}s): "
              f"cover={np.mean([c['cover_r1']['dti'] for c in cells if c['seed']==seed]):.5f} "
              f"radcover={np.mean([c['rad_cover_r1']['dti'] for c in cells if c['seed']==seed]):.5f}",
              flush=True)

    base_mean = float(np.mean([c["base_d280"]["dti"] for c in cells]))
    ref_mean = float(np.mean([c[INCUMBENT]["dti"] for c in cells]))

    def gains(vn: str, ref: str = "base_d280") -> list[float]:
        return [float(np.mean([c[vn]["dti"] - c[ref]["dti"] for c in cells if c["seed"] == s]))
                for s in seeds]

    def fold_gains(vn: str, ref: str) -> dict:
        return {fn: float(np.mean([c[vn]["dti"] - c[ref]["dti"] for c in cells if c["fold"] == fn]))
                for fn in holdout.FOLD_NAMES}

    summary = {}
    for vn in VARIANT_NAMES:
        g_seed = [float(np.mean([c[vn]["dti"] - c["base_d280"]["dti"] for c in cells if c["seed"] == s]))
                  for s in seeds]
        prim_seed = [float(np.mean([c[vn]["dti"] - c[INCUMBENT]["dti"] for c in cells if c["seed"] == s]))
                     for s in seeds]
        fg = fold_gains(vn, "base_d280")
        fi = fold_gains(vn, INCUMBENT) if vn != INCUMBENT else {fn: 0.0 for fn in holdout.FOLD_NAMES}
        summary[vn] = {
            "mean_dti": float(np.mean([c[vn]["dti"] for c in cells])),
            "mean_gain_vs_base": float(np.mean(g_seed)),
            "mean_gain_vs_incumbent": float(np.mean(prim_seed)),
            "seeds_won_vs_incumbent": int(sum(g > 0 for g in prim_seed)),
            "min_seed_gain_vs_incumbent": float(np.min(prim_seed)),
            "max_seed_gain_vs_incumbent": float(np.max(prim_seed)),
            "n_seeds": len(seeds),
            "fold_gains_vs_base": fg,
            "folds_improved_vs_base": int(sum(v > 0 for v in fg.values())),
            "fold_gains_vs_incumbent": fi,
            "folds_improved_vs_incumbent": int(sum(v > 0 for v in fi.values())),
            "mean_dots": float(np.mean([c[vn]["dots"] for c in cells])),
            "delta_tp_vs_incumbent": float(sum(c[vn]["tp"] - c[INCUMBENT]["tp"] for c in cells)),
            "delta_fp_vs_incumbent": float(sum(c[vn]["fp"] - c[INCUMBENT]["fp"] for c in cells)),
        }

    g1 = summary[PRIMARY]["mean_gain_vs_incumbent"]
    g3 = summary["rad_base_d280"]["mean_gain_vs_base"] - summary["base_d280"]["mean_gain_vs_base"]
    g4 = summary[PRIMARY]["mean_gain_vs_base"] - summary[CONTROL]["mean_gain_vs_base"]
    gate = {
        "G1_direction_vs_incumbent": bool(g1 > 0),
        "G1_observed": float(g1),
        # G2 uses the incumbent-relative fold statistic, as knowledge/38 section 4 specifies. The
        # 270-279 run used the base-relative one (erratum 2, knowledge/38 section 8); both are stored.
        "G2_promotion": bool(g1 >= PROMOTION_MARGIN
                             and summary[PRIMARY]["seeds_won_vs_incumbent"] >= 8
                             and summary[PRIMARY]["folds_improved_vs_incumbent"] == 4),
        "G2_required": f">= {PROMOTION_MARGIN} mean, >= 8/10 seeds, 4/4 folds",
        "G2_seeds_won": summary[PRIMARY]["seeds_won_vs_incumbent"],
        "G2_folds_improved_vs_base": summary[PRIMARY]["folds_improved_vs_base"],
        "G2_folds_improved_vs_incumbent": summary[PRIMARY]["folds_improved_vs_incumbent"],
        "G3_do_no_harm_rad_base_vs_base": float(g3),
        "G3_passed": bool(g3 >= -0.0005),
        "G4_content_control_margin": float(g4),
        "G4_passed": bool(g4 >= PROMOTION_MARGIN),
        "G5_integrity_violations": integrity,
        "G5_passed": bool(not integrity),
        "G5_determinism_replicated": bool(determinism_note),
        "report_only_cover_vs_base": float(summary[INCUMBENT]["mean_gain_vs_base"]),
        "report_only_ridge_symmetric_difference_px": ridge_sym_diff,
        "reproducibility_note": ("H37-1 measured +0.007289 for its coverage arm on the interleaved proxy "
                                 "(seeds 250-259) and knowledge/33 falsified its far-field transfer; this "
                                 "decade is fresh, so the D0 cover_r1 number here is reported, not gated."),
    }
    gate["passed"] = bool(gate["G1_direction_vs_incumbent"] and gate["G2_promotion"]
                          and gate["G3_passed"] and gate["G4_passed"] and gate["G5_passed"])

    out = {
        "hypothesis": ("H38-1: adding the GeoDAWN radiometric channels K, Th, U and the Th/K, U/K, U/Th "
                       "ratio grids to the 32-band detector changes the emission - gate on the "
                       "spatially blocked interleaved holdout at matched dot count"),
        "preregistration": "knowledge/38_preregistration_H38-1.md",
        "seeds": seeds,
        "n_cells": len(cells),
        "base_d280_mean_dti": base_mean,
        "incumbent_cover_r1_mean_dti": ref_mean,
        "extra_bands": extra_diag,
        "variants": summary,
        "gate": gate,
        "runtime_s": round(time.time() - t0, 1),
        "code_sha256": {
            "runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "oof_detector": hashlib.sha256(
                (paths.REPO / "src" / "gems27" / "oof_detector.py").read_bytes()).hexdigest(),
            "packing": hashlib.sha256((paths.REPO / "src" / "gems27" / "packing.py").read_bytes()).hexdigest(),
        },
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cells": cells,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(json.dumps(gate, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
