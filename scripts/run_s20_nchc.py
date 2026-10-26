#!/usr/bin/env python3
"""Execute the preregistered Session 20 lane S20-NCHC (H43-1) within the 3-experiment / 2-hour cap.

Frozen preregistration: ``knowledge/56_s20_preregistration.md``.
Reuses:
  * Cached 32-band stack ``prepared/features.npy`` (``scripts/prepare_data.py``),
  * Shared ``gems.holdout.SegmentHoldout`` (``gems-segment-pooled-v1``),
  * Shared ``gems.novelty.{compare_registry, compare_prospective_registry}``,
  * Shared ``gems.submission.{write_submission, check_variants, scored_content_id, zip_single}``,
  * Shared ``gems27.packing.coverage_greedy`` and ``gems27.promotion.promotion_gate``.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "data" / "shared_template" / "src"))

from gems import holdout as shared_holdout  # noqa: E402
from gems import novelty as shared_novelty  # noqa: E402
from gems import submission as shared_submission  # noqa: E402

from gems27 import grid, heatflow_euler, oof_detector, paths, promotion, registry_compare, s20_nchc  # noqa: E402

SESSION_ID = "S20-NCHC"
HYPOTHESIS_ID = "H43-1"
SEEDS_ENSEMBLE = (340, 341, 342, 343, 344)
OOF_PRIMARY_SEED = 340
BOOTSTRAP_SEED = 20261034
BOOTSTRAP_DRAWS = 1000
BASELINE_H38_SEED = 42

PREREG_PATH = ROOT / "knowledge" / "56_s20_preregistration.md"
STARTED_PATH = ROOT / "evidence" / "s20_nchc.started.json"
REGISTRY_MANIFEST_PATH = ROOT / "evidence" / "s20_registry_manifest.json"
EXP1_PATH = ROOT / "evidence" / "s20_nchc_exp1_surface.json"
EXP2_PATH = ROOT / "evidence" / "s20_nchc_exp2_holdout.json"
EXP3_PATH = ROOT / "evidence" / "s20_nchc_exp3_emission.json"
RUN_CARD_PATH = ROOT / "evidence" / "s20_nchc_run_card.json"
BASELINE_FROZEN_TIF = (
    ROOT / "docs" / "downloads" / "gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-allfinite.tif"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class LazyFootprintFeatureMapping(Mapping[str, np.ndarray]):
    """Memory-safe lazy mapping unpacking one 2D feature at a time for SegmentHoldout.canary."""

    def __init__(self, X_mmap: np.ndarray, foot: np.ndarray, names: tuple[str, ...]) -> None:
        self._X = X_mmap
        self._foot = foot
        self._ys, self._xs = np.nonzero(foot)
        self._names = names
        self._idx = {n: i for i, n in enumerate(names)}

    def __getitem__(self, key: str) -> np.ndarray:
        col = self._idx[key]
        arr = np.zeros(self._foot.shape, dtype=np.float32)
        arr[self._ys, self._xs] = self._X[:, col]
        return arr

    def __iter__(self) -> Iterator[str]:
        return iter(self._names)

    def __len__(self) -> int:
        return len(self._names)


def build_registry_manifest(data_dir: Path) -> tuple[list[Path], list[Path], dict]:
    method_dir = data_dir / "registry_rasters"
    full_dir = data_dir / "registry_rasters_with_controls"
    method_paths = sorted(method_dir.glob("*.tif"))
    full_paths = sorted(full_dir.glob("*.tif"))
    if len(method_paths) < 100:
        raise RuntimeError(f"Registry incomplete: found only {len(method_paths)} rasters in {method_dir}")

    seen_sha: dict[str, Path] = {}
    unique_method_paths: list[Path] = []
    members_meta: list[dict] = []
    for p in method_paths:
        real = p.resolve()
        sha = sha256_file(real)
        if sha in seen_sha:
            continue
        seen_sha[sha] = real
        unique_method_paths.append(p)
        repo_tag, _, fname = p.name.partition("__")
        members_meta.append({
            "repo": repo_tag,
            "filename": fname or p.name,
            "raster_sha256": sha,
        })

    manifest = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": "Synchronized 9-focus-site published rasters (GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36) + GEMSDOE28 PR #48",
        "member_count": len(unique_method_paths),
        "prospective_with_historic_controls_count": len(full_paths),
        "members": members_meta,
    }
    REGISTRY_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_sha256"] = sha256_file(REGISTRY_MANIFEST_PATH)
    return unique_method_paths, full_paths, manifest


def check_surface_spearman(
    surface_2d: np.ndarray,
    foot: np.ndarray,
    registry_paths: list[Path],
) -> tuple[list[dict], dict]:
    vals = np.asarray(surface_2d[foot], dtype=np.float64)
    ranks = rankdata(vals, method="average")
    ra = ranks - ranks.mean()
    denom_a = float(np.sqrt(np.dot(ra, ra)))

    # Also inspect pre-placement top-37654 corridor peaks 3px overlap as a diagnostic
    ys, xs = np.nonzero(foot)
    top_idx = np.argpartition(-vals, 37_654 - 1)[:37_654]
    top_mask = np.zeros(foot.shape, dtype=bool)
    top_mask[ys[top_idx], xs[top_idx]] = True

    card_rows: list[dict] = []
    diag_rows: list[dict] = []
    for p in registry_paths:
        sha = sha256_file(p.resolve())
        with rasterio.open(p) as ds:
            arr = ds.read(1)
        ref_vec = np.where(np.isfinite(arr[foot]), arr[foot], 0.0).astype(np.float64)
        if np.ptp(ref_vec) == 0 or denom_a == 0.0:
            corr = 0.0
        else:
            if np.isin(ref_vec, [0.0, 1.0]).all():
                rb = ref_vec - ref_vec.mean()
            else:
                r_ref = rankdata(ref_vec, method="average")
                rb = r_ref - r_ref.mean()
            corr = float(np.dot(ra, rb) / (denom_a * float(np.sqrt(np.dot(rb, rb)))))

        ref_dots = np.isfinite(arr) & (arr > 0) & foot
        ov = shared_novelty.dot_overlap(top_mask, ref_dots, radius_px=3.0)
        ov_frac = float(ov["candidate_within_3px_of_reference"] or 0.0)
        card_rows.append({
            "raster_sha256": sha,
            "spearman": corr,
            "within_3px_fraction": None,
        })
        diag_rows.append({
            "name": p.name,
            "raster_sha256": sha,
            "spearman": corr,
            "top37654_within_3px_diagnostic": ov_frac,
            "reference_dots": int(ref_dots.sum()),
        })

    worst_corr = max(diag_rows, key=lambda r: abs(r["spearman"]))
    worst_ov = max(diag_rows, key=lambda r: r["top37654_within_3px_diagnostic"])
    summary = {
        "member_count": len(diag_rows),
        "passed_spearman_gate": abs(worst_corr["spearman"]) <= 0.90,
        "max_abs_spearman": abs(worst_corr["spearman"]),
        "max_abs_spearman_member": worst_corr,
        "max_top37654_within_3px_diagnostic": worst_ov["top37654_within_3px_diagnostic"],
        "max_top37654_member": worst_ov,
    }
    return card_rows, summary


def baseline_b0_and_b1_32band_fold(
    fold: dict,
    foot: np.ndarray,
    hf_euler_fields: dict,
    *,
    seed: int = BASELINE_H38_SEED,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute both leak-free retrained comparators on SegmentHoldout fold:
      * B0: GEMSDOE28 retrained visible-only 32-band + H38 heat-flow/Euler corroboration
      * B1: Leak-free retrained visible-only 32-band + d=2.8 thinning + B=2 (d_visible > 2.0)
    """
    X = np.load(paths.PREPARED_FEATURES, mmap_mode="r")
    rc = np.argwhere(foot)
    y = fold["visible"][foot]
    train = fold["train"][foot]
    pos = np.flatnonzero(train & y)
    neg = np.flatnonzero(train & ~y)
    rng = np.random.default_rng(seed)
    chosen = np.sort(np.r_[pos, rng.choice(neg, min(len(neg), 10 * len(pos)), replace=False)])
    clf = HistGradientBoostingClassifier(
        max_iter=100,
        max_leaf_nodes=31,
        learning_rate=0.08,
        l2_regularization=5.0,
        random_state=seed,
    )
    clf.fit(np.asarray(X[chosen], np.float32), y[chosen].astype(int))
    target = np.flatnonzero(fold["valid"][foot])
    scores = np.zeros(foot.shape, dtype=np.float32)
    out = np.empty(len(target), np.float32)
    for start in range(0, len(target), 400_000):
        stop = min(start + 400_000, len(target))
        out[start:stop] = clf.predict_proba(np.asarray(X[target[start:stop]], np.float32))[:, 1]
    target_rc = rc[target]
    scores[target_rc[:, 0], target_rc[:, 1]] = out

    ridge = oof_detector.ridge_nms(scores, fold["valid"], sigma=1.0)
    d_vis = distance_transform_edt(~fold["visible"])
    active = fold["valid"] & ~fold["visible"]

    # B0: GEMSDOE28 H38-1 retrained baseline
    base_b0 = oof_detector.build_oof_dotted_base(
        scores, ridge, fold["valid"], fold["visible"], budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=3.0
    )
    base_b0 &= active & (d_vis > 1.0)
    added_b0 = heatflow_euler.select_corroborated_ridge_dots(
        scores,
        ridge,
        active,
        base_b0,
        fold["visible"],
        hf_euler_fields["joint_mask"],
        score_mult=hf_euler_fields["score_mult"],
        k_cap=heatflow_euler.K_CAP_PER_CELL,
        min_dist_base=heatflow_euler.MIN_DIST_BASE_PX,
        min_dist_known=heatflow_euler.MIN_DIST_KNOWN_PX,
        thin_d=heatflow_euler.THIN_D_PX,
        rng_seed=seed + 50_000,
    )["added"]
    pred_b0 = (base_b0 | added_b0).astype(np.float32)

    # B1: Leak-free retrained H33-2-B2 analog (d=2.8 thinning + d_visible > 2.0)
    base_b1 = oof_detector.build_oof_dotted_base(
        scores, ridge, fold["valid"], fold["visible"], budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8
    )
    pred_b1 = (base_b1 & active & (d_vis > 2.0)).astype(np.float32)
    return pred_b0, pred_b1


def score_and_blocks(
    holdout_obj: shared_holdout.SegmentHoldout,
    preds_by_fold: list[np.ndarray],
    active_blocks: np.ndarray,
) -> tuple[dict, np.ndarray]:
    summary = holdout_obj.summarize(preds_by_fold, ci_draws=BOOTSTRAP_DRAWS)
    block_list = []
    for pred, fold in zip(preds_by_fold, holdout_obj.folds):
        _, blocks = holdout_obj.score_fold(pred, fold)
        block_list.append(blocks)
    pooled_blocks = np.sum(block_list, axis=0)[active_blocks]
    summary["ci95"] = shared_holdout.spatial_bootstrap_ci(
        pooled_blocks, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED
    )
    return summary, pooled_blocks


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--resume-exp3",
        action="store_true",
        help="Resume Experiment 3 only when Exp 1 & Exp 2 already completed cleanly.",
    )
    args = ap.parse_args(argv)

    t0 = time.monotonic()
    data_dir = paths.DATA
    prereg_sha = sha256_file(PREREG_PATH)
    baseline_sha = sha256_file(BASELINE_FROZEN_TIF)
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot

    if args.resume_exp3:
        if not (STARTED_PATH.exists() and EXP1_PATH.exists() and EXP2_PATH.exists()):
            raise SystemExit("--resume-exp3 requires existing s20_nchc.started/exp1/exp2 JSONs.")
        if EXP3_PATH.exists() or RUN_CARD_PATH.exists():
            raise SystemExit("Experiment 3 already completed; refusing to overwrite.")
        method_reg_paths = sorted((data_dir / "registry_rasters").glob("*.tif"))
        full_reg_paths = sorted((data_dir / "registry_rasters_with_controls").glob("*.tif"))
        reg_manifest = json.loads(REGISTRY_MANIFEST_PATH.read_text(encoding="utf-8"))
        reg_manifest["manifest_sha256"] = sha256_file(REGISTRY_MANIFEST_PATH)
        exp1_saved = json.loads(EXP1_PATH.read_text(encoding="utf-8"))
        exp2_saved = json.loads(EXP2_PATH.read_text(encoding="utf-8"))
        feat_meta = exp1_saved["feature_stack"]
        canary_res = exp1_saved["canary"]
        X_s20 = np.load(feat_meta["path"], mmap_mode="r")
        s20_summary = exp2_saved["candidate_s20_nchc"]
        b0_summary = exp2_saved["baseline_b0_32band_h38_vis"]
        b1_summary = exp2_saved["baseline_b1_32band_b2_d28_vis"]
        gain_vs_b0 = float(exp2_saved["paired_vs_b0"]["delta_dti"])
        gain_vs_b0_ci95 = list(exp2_saved["paired_vs_b0"]["ci95"])
        folds_won_vs_b0 = int(str(exp2_saved["paired_vs_b0"]["folds_improved"]).split("/")[0])
        gain_vs_b1 = float(exp2_saved["paired_vs_b1_b2_d28_analog"]["delta_dti"])
        gain_vs_b1_ci95 = list(exp2_saved["paired_vs_b1_b2_d28_analog"]["ci95"])
        folds_won_vs_b1 = int(
            str(exp2_saved["paired_vs_b1_b2_d28_analog"]["folds_improved"]).split("/")[0]
        )
    else:
        if STARTED_PATH.exists():
            raise SystemExit(
                f"{STARTED_PATH} already exists; refusing to rerun spent session seeds."
            )
        method_reg_paths, full_reg_paths, reg_manifest = build_registry_manifest(data_dir)
        STARTED_PATH.write_text(
            json.dumps(
                {
                    "session": SESSION_ID,
                    "hypothesis_id": HYPOTHESIS_ID,
                    "started_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "preregistration_path": "knowledge/56_s20_preregistration.md",
                    "preregistration_sha256": prereg_sha,
                    "oof_primary_seed": OOF_PRIMARY_SEED,
                    "full_fit_seeds": list(SEEDS_ENSEMBLE),
                    "bootstrap_seed": BOOTSTRAP_SEED,
                    "max_experiments": 3,
                    "registry_manifest_sha256": reg_manifest["manifest_sha256"],
                    "registry_member_count": reg_manifest["member_count"],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        holdout_obj = shared_holdout.SegmentHoldout(foot, labels, buffer_px=15)

        # =====================================================================
        # EXPERIMENT 1: Feature Stack + Single-Feature Canary + OOF Surface
        # =====================================================================
        print("[Exp 1/3] Building 28-feature label-free S20-NCHC stack...", flush=True)
        feat_meta = s20_nchc.build_s20_feature_stack()
        X_s20 = np.load(feat_meta["path"], mmap_mode="r")

        print(
            "[Exp 1/3] Running SegmentHoldout single-feature leakage canary on all 28 features...",
            flush=True,
        )
        lazy_feats = LazyFootprintFeatureMapping(X_s20, foot, s20_nchc.S20_FEATURE_NAMES)
        canary_res = holdout_obj.canary(lazy_feats, seed=BOOTSTRAP_SEED)
        gc.collect()
        if not canary_res["passed"]:
            raise RuntimeError("STOP: Leakage canary failed on one or more S20-NCHC features!")

        print(
            "[Exp 1/3] Fitting 4-fold spatially purged prior-calibrated HistGBM for OOF surface...",
            flush=True,
        )
        oof_prob_2d = np.zeros(foot.shape, dtype=np.float32)
        fold_fit_infos: list[dict] = []
        fold_prob_surfaces: list[np.ndarray] = []
        for fold in holdout_obj.folds:
            f_seed = OOF_PRIMARY_SEED + int(fold["id"])
            prob_f, f_info = s20_nchc.fit_predict_prior_calibrated_hgb(
                X_s20, foot, fold["train"], fold["visible"], seed=f_seed
            )
            f_info["fold_name"] = fold["name"]
            fold_fit_infos.append(f_info)
            val_prob = np.where(fold["valid"], prob_f, 0.0).astype(np.float32)
            oof_prob_2d[fold["valid"]] = val_prob[fold["valid"]]
            fold_prob_surfaces.append(val_prob)
            del prob_f
            gc.collect()

        print(
            f"[Exp 1/3] Checking pre-placement OOF surface against {len(method_reg_paths)} registry rasters...",
            flush=True,
        )
        _, surface_novelty_summary = check_surface_spearman(oof_prob_2d, foot, method_reg_paths)
        EXP1_PATH.write_text(
            json.dumps(
                {
                    "experiment": 1,
                    "session": SESSION_ID,
                    "elapsed_seconds": round(time.monotonic() - t0, 2),
                    "feature_stack": feat_meta,
                    "canary": canary_res,
                    "fold_fits": fold_fit_infos,
                    "pre_placement_registry_summary": surface_novelty_summary,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            f"[Exp 1/3] Canary passed={canary_res['passed']}; max |Spearman|={surface_novelty_summary['max_abs_spearman']:.4f}; "
            f"top-37654 3px diag={surface_novelty_summary['max_top37654_within_3px_diagnostic']:.4f}",
            flush=True,
        )
        if not surface_novelty_summary["passed_spearman_gate"]:
            raise RuntimeError("STOP: Pre-placement OOF surface exceeded Spearman 0.90 duplicate gate!")

        # =====================================================================
        # EXPERIMENT 2: SegmentHoldout Hide-and-Recover Evaluation vs Baselines
        # =====================================================================
        print("[Exp 2/3] Allocating fold-isolated 300 m submodular corridor dots...", flush=True)
        s20_fold_preds: list[np.ndarray] = []
        s20_alloc_infos: list[dict] = []
        for fold, val_prob in zip(holdout_obj.folds, fold_prob_surfaces):
            pred_f, alloc_info = s20_nchc.allocate_corridor_submodular(
                val_prob, fold["valid"], fold["visible"]
            )
            alloc_info["fold_name"] = fold["name"]
            s20_fold_preds.append(pred_f)
            s20_alloc_infos.append(alloc_info)
        del fold_prob_surfaces, oof_prob_2d
        gc.collect()

        print(
            "[Exp 2/3] Computing paired baselines B0 (retrained 32-band H38) and B1 (32-band d=2.8 B=2 vis)...",
            flush=True,
        )
        hf_res = heatflow_euler.load_heatflow_residual_cells(paths.SB_HEAT_FLOW_JSON, foot)
        eu_res = heatflow_euler.load_euler_contact_clusters(
            ROOT / "evidence" / "h31_1_euler_clusters.csv", foot.shape
        )
        hf_halo = distance_transform_edt(~hf_res["mask"]) <= heatflow_euler.HF_RADIUS_PX
        eu_halo = distance_transform_edt(~eu_res["mask"]) <= heatflow_euler.EULER_RADIUS_PX
        hf_euler_fields = {
            "joint_mask": (hf_halo | eu_halo) & foot,
            "score_mult": (
                1.0
                + heatflow_euler.BONUS_HF * hf_halo.astype(np.float32)
                + heatflow_euler.BONUS_EULER * eu_halo.astype(np.float32)
            ).astype(np.float32),
        }
        del hf_halo, eu_halo

        b0_fold_preds: list[np.ndarray] = []
        b1_fold_preds: list[np.ndarray] = []
        for fold in holdout_obj.folds:
            pb0, pb1 = baseline_b0_and_b1_32band_fold(fold, foot, hf_euler_fields)
            b0_fold_preds.append(pb0)
            b1_fold_preds.append(pb1)
            gc.collect()
        del hf_euler_fields
        gc.collect()

        yy, xx = np.nonzero(foot)
        nx = (foot.shape[1] + 99) // 100
        active_blocks = np.unique((yy // 100) * nx + xx // 100)

        s20_summary, s20_blocks = score_and_blocks(holdout_obj, s20_fold_preds, active_blocks)
        b0_summary, b0_blocks = score_and_blocks(holdout_obj, b0_fold_preds, active_blocks)
        b1_summary, b1_blocks = score_and_blocks(holdout_obj, b1_fold_preds, active_blocks)

        gain_vs_b0 = float(s20_summary["dti"] - b0_summary["dti"])
        gain_vs_b0_ci95 = shared_holdout.pooled_bootstrap(
            s20_blocks, paired=b0_blocks, resamples=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED
        )
        gain_vs_b1 = float(s20_summary["dti"] - b1_summary["dti"])
        gain_vs_b1_ci95 = shared_holdout.pooled_bootstrap(
            s20_blocks, paired=b1_blocks, resamples=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED
        )
        folds_won_vs_b0 = sum(
            1 for a, b in zip(s20_summary["folds"], b0_summary["folds"]) if a["dti"] > b["dti"]
        )
        folds_won_vs_b1 = sum(
            1 for a, b in zip(s20_summary["folds"], b1_summary["folds"]) if a["dti"] > b["dti"]
        )

        exp2_payload = {
            "experiment": 2,
            "session": SESSION_ID,
            "elapsed_seconds": round(time.monotonic() - t0, 2),
            "evaluator_version": shared_holdout.MTR_EVALUATOR_VERSION,
            "candidate_s20_nchc": s20_summary,
            "candidate_allocations": s20_alloc_infos,
            "baseline_b0_32band_h38_vis": b0_summary,
            "baseline_b1_32band_b2_d28_vis": b1_summary,
            "paired_vs_b0": {
                "delta_dti": gain_vs_b0,
                "ci95": gain_vs_b0_ci95,
                "folds_improved": f"{folds_won_vs_b0}/4",
                "passed_positive_ci95": bool(gain_vs_b0_ci95[0] > 0.0),
            },
            "paired_vs_b1_b2_d28_analog": {
                "delta_dti": gain_vs_b1,
                "ci95": gain_vs_b1_ci95,
                "folds_improved": f"{folds_won_vs_b1}/4",
                "passed_positive_ci95": bool(gain_vs_b1_ci95[0] > 0.0),
                "note": "Leak-free fold-retrained 32-band d=2.8 B=2 (d_visible > 2.0 px) champion-analog comparator.",
            },
        }
        EXP2_PATH.write_text(json.dumps(exp2_payload, indent=2) + "\n", encoding="utf-8")
        print(
            f"[Exp 2/3] HOLDOUT-DTI S20-NCHC={s20_summary['dti']:.6f} {s20_summary['ci95']['interval']} "
            f"| vs B0={b0_summary['dti']:.6f} (delta={gain_vs_b0:+.6f}, CI={gain_vs_b0_ci95}, {folds_won_vs_b0}/4 folds) "
            f"| vs B1={b1_summary['dti']:.6f} (delta={gain_vs_b1:+.6f}, CI={gain_vs_b1_ci95}, {folds_won_vs_b1}/4 folds)",
            flush=True,
        )
        del s20_fold_preds, b0_fold_preds, b1_fold_preds
        gc.collect()

    # =========================================================================
    # EXPERIMENT 3: 5-Seed Full-Fit Emission + 112/120 Registry Gate + Run Card
    # =========================================================================
    print("[Exp 3/3] Fitting 5-seed full-footprint ensemble (seeds 340..344)...", flush=True)
    full_prob_acc = np.zeros(foot.shape, dtype=np.float64)
    full_seed_infos: list[dict] = []
    for s in SEEDS_ENSEMBLE:
        p_s, s_info = s20_nchc.fit_predict_prior_calibrated_hgb(
            X_s20, foot, foot, labels, seed=int(s)
        )
        full_prob_acc += p_s.astype(np.float64)
        full_seed_infos.append(s_info)
        del p_s
        gc.collect()
    full_prob_mean = (full_prob_acc / float(len(SEEDS_ENSEMBLE))).astype(np.float32)
    del full_prob_acc

    print("[Exp 3/3] Auditing full-fit continuous surface Spearman against 112 registry rasters...", flush=True)
    surface_card_rows, surface_novelty_summary = check_surface_spearman(
        full_prob_mean, foot, method_reg_paths
    )

    print("[Exp 3/3] Running full-footprint B=2 submodular 300 m allocation...", flush=True)
    full_pred, full_alloc_info = s20_nchc.allocate_corridor_submodular(
        full_prob_mean, foot, labels
    )

    cid12 = shared_submission.scored_content_id(full_pred, foot, labels)
    date_tag = "20261026"
    downloads_dir = ROOT / "docs" / "downloads"
    allfinite_name = f"gems28-s20-nchc-{date_tag}-{cid12}-allfinite.tif"
    nan_name = f"gems28-s20-nchc-{date_tag}-{cid12}-nan.tif"
    zip_name = f"gems28-s20-nchc-{date_tag}-{cid12}-nan.zip"
    note_file_name = f"gems28-s20-nchc-{date_tag}-{cid12}.note.txt"

    allfinite_path = downloads_dir / allfinite_name
    nan_path = downloads_dir / nan_name
    zip_path = downloads_dir / zip_name
    note_file_path = downloads_dir / note_file_name

    # Write via shared submission writer (both all-finite [0,1] and template-nan twin + zip)
    shared_submission.write_submission(full_pred, paths.TEMPLATE, allfinite_path, outside="zero")
    shared_submission.write_submission(full_pred, paths.TEMPLATE, nan_path, outside="nan")
    shared_submission.zip_single(nan_path, zip_path)

    variant_checks_allfinite = shared_submission.check_variants(allfinite_path, paths.TEMPLATE)
    variant_checks_nan = shared_submission.check_variants(nan_path, paths.TEMPLATE)

    print(
        f"[Exp 3/3] Checking post-placement uniqueness against {len(method_reg_paths)} method rasters + {len(full_reg_paths)} prospective rasters...",
        flush=True,
    )
    # Build prospective entries list for shared gems.novelty.compare_prospective_registry
    prospective_entries: list[dict] = []
    full_root = data_dir / "registry_rasters_with_controls"
    for p in full_reg_paths:
        repo_tag, _, fname = p.name.partition("__")
        with rasterio.open(p) as ds_r:
            a_r = ds_r.read(1)
        fp_sha = hashlib.sha256(np.asarray(a_r[foot], dtype="<f4").tobytes()).hexdigest()
        logical_file = (
            f"inputs/calibration/{fname}"
            if repo_tag == "GEMSDOE24-inputs"
            and ("lattice-s5" in fname or "PLACEHOLDER" in fname)
            else f"{repo_tag}/{fname}"
        )
        prospective_entries.append(
            {
                "id": p.stem,
                "file": logical_file,
                "cache_path": p.name,
                "footprint_sha256": fp_sha,
                "raster_sha256": sha256_file(p.resolve()),
                "is_method_dir": repo_tag != "GEMSDOE24-inputs",
            }
        )

    prospective_reg = shared_novelty.compare_prospective_registry(
        full_prob_mean, foot, prospective_entries, full_root, dots=(full_pred > 0)
    )
    del full_prob_mean
    gc.collect()

    # Exact full-footprint dot Spearman & <=3px overlap on the 112 method-lane rasters
    dot_ranks, dot_norm = registry_compare.ranked_centered(full_pred[foot].astype(np.float64))
    cand_bool = (full_pred > 0) & foot
    dots_card_rows: list[dict] = []
    dots_diag_rows: list[dict] = []
    for p in method_reg_paths:
        r_sha = sha256_file(p.resolve())
        with rasterio.open(p) as ds_m:
            arr_m = ds_m.read(1)
        ref_vec = np.where(np.isfinite(arr_m[foot]), arr_m[foot], 0.0).astype(np.float64)
        sp_val = registry_compare.spearman_against(dot_ranks, dot_norm, ref_vec)
        sp = float(0.0 if sp_val is None else sp_val)
        ref_bool = np.isfinite(arr_m) & (arr_m > 0) & foot
        ov = float(registry_compare.within_fraction(cand_bool, ref_bool, radius=3.0) or 0.0)
        dots_card_rows.append(
            {
                "raster_sha256": r_sha,
                "spearman": sp,
                "within_3px_fraction": ov,
            }
        )
        dots_diag_rows.append(
            {
                "name": p.name,
                "raster_sha256": r_sha,
                "spearman": sp,
                "within_3px_fraction": ov,
                "reference_dots": int(ref_bool.sum()),
            }
        )

    worst_dot_corr = max(dots_diag_rows, key=lambda r: abs(r["spearman"]))
    worst_dot_ov = max(dots_diag_rows, key=lambda r: r["within_3px_fraction"])
    dots_duplicate = (
        abs(worst_dot_corr["spearman"]) > 0.90 or worst_dot_ov["within_3px_fraction"] > 0.70
    )
    print(
        f"[Exp 3/3] Post-placement duplicate={dots_duplicate}; "
        f"max |Spearman|={abs(worst_dot_corr['spearman']):.4f} ({worst_dot_corr['name']}); "
        f"max 3px overlap={worst_dot_ov['within_3px_fraction']:.4f} ({worst_dot_ov['name']})",
        flush=True,
    )

    raster_sha = sha256_file(allfinite_path)
    emitted_px = int((full_pred[foot] == 1.0).sum())
    submission_name = f"GEMSDOE28-S20-NCHC-{date_tag}-{cid12}"

    chk_af = variant_checks_allfinite["checks"]
    strict_01_ok = bool(chk_af["variant_strict_whole_array_no_nan_allowed"]["pass"])
    prelim_pass = (
        canary_res["passed"]
        and surface_novelty_summary["passed_spearman_gate"]
        and (not dots_duplicate)
        and (gain_vs_b0_ci95[0] > 0.0)
        and strict_01_ok
    )
    verdict_word = "PROMOTE" if prelim_pass else "DO NOT SUBMIT"
    note_text = (
        f"S20-NCHC nematic+claycap 300m submod B2 {emitted_px}d | "
        f"HOLDOUT-DTI {s20_summary['dti']:.4f} vs {b0_summary['dti']:.4f} | {verdict_word}"
    )
    assert len(note_text) <= 140, f"Note too long: {len(note_text)}"
    note_file_path.write_text(note_text + "\n", encoding="utf-8")

    feature_canaries_dict = {
        fname: float(finfo["pooled_auc"]) for fname, finfo in canary_res["features"].items()
    }
    validator_block = {
        "raster_sha256": raster_sha,
        "no_nan_inside": bool(chk_af["footprint_all_finite"]["pass"]),
        "no_nan_whole_array": strict_01_ok,
        "range_0_1": bool(chk_af["footprint_range_0_1"]["pass"] and strict_01_ok),
        "crs_match": bool(chk_af["crs_epsg_32611"]["pass"]),
        "shape_match": bool(chk_af["shape_matches_template"]["pass"]),
        "transform_match": bool(chk_af["geotransform_matches_template"]["pass"]),
        "single_band": bool(chk_af["single_band"]["pass"] and chk_af["dtype_float32"]["pass"]),
        "emitted_positive_pixels": emitted_px,
        "catalogue_overlap_pixels": int(((full_pred > 0) & labels).sum()),
    }

    run_card = {
        "session": SESSION_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lane": "S20-NCHC: Multi-scale nematic 4-modality lineament concordance + hydrothermal clay-cap/silica-disequilibrium corridor + 300 m submodular kernel allocation",
        "hypothesis": "Concealed Great Basin and Walker Lane faults lacking mapped Quaternary scarps exhibit multi-scale Frangi-Hessian tubular edges co-aligned in nematic strike across magnetics, gravity, conductive base, and piedmont topography, flanked by smectite clay-cap gradients, K-metasomatic Th/K lows, and silica geothermometry disequilibrium.",
        "mechanism": "28 level-invariant derivative/Hessian/nematic/hydrothermal features -> spatially purged prior-calibrated HistGBM -> B=2 clearance -> 300 m Minoux submodular kernel coverage.",
        "non_fault_mimic": "GeoDAWN E-W flight-line micro-leveling stripes and steep-terrain helicopter drape anomalies, Lake Lahontan wave-cut shorelines, curved pluton aureoles, and uncorroborated lateral thermal outflow plumes.",
        "raster_sha256": raster_sha,
        "submission_file": f"docs/downloads/{allfinite_name}",
        "submission_nan_twin_file": f"docs/downloads/{nan_name}",
        "submission_zip_file": f"docs/downloads/{zip_name}",
        "submission_note_file": f"docs/downloads/{note_file_name}",
        "submission_name": submission_name,
        "content_id": cid12,
        "note": note_text,
        "experiments_run": 3,
        "elapsed_seconds": round(time.monotonic() - t0, 2),
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": shared_holdout.MTR_EVALUATOR_VERSION,
            "raster_sha256": raster_sha,
            "baseline_sha256": baseline_sha,
            "baseline_name": "B0_32band_h38_vis (retrained visible-only 32-band + H38 heatflow/Euler)",
            "withheld_positives": int(s20_summary["n_withheld_positive_pixels"]),
            "dti": float(s20_summary["dti"]),
            "ci95": list(s20_summary["ci95"]["interval"]),
            "baseline_dti": float(b0_summary["dti"]),
            "baseline_ci95": list(b0_summary["ci95"]["interval"]),
            "paired_gain": gain_vs_b0,
            "paired_gain_ci95": list(gain_vs_b0_ci95),
            "folds_improved_vs_b0": f"{folds_won_vs_b0}/4",
            "b1_b2_d28_retrained_dti": float(b1_summary["dti"]),
            "b1_b2_d28_retrained_ci95": list(b1_summary["ci95"]["interval"]),
            "paired_gain_vs_b1": gain_vs_b1,
            "paired_gain_vs_b1_ci95": list(gain_vs_b1_ci95),
            "folds_improved_vs_b1": f"{folds_won_vs_b1}/4",
            "whole_segments": True,
            "buffered": True,
            "buffer_m": 1500,
            "visible_only_features": True,
            "pixel_exact_visible_mask": True,
            "pooled": True,
            "alpha": 0.2,
            "beta": 0.8,
            "kernel_m": 300,
            "kernel": "triangular",
        },
        "feature_canaries": feature_canaries_dict,
        "registry": {
            "complete": True,
            "manifest_path": "evidence/s20_registry_manifest.json",
            "manifest_sha256": reg_manifest["manifest_sha256"],
            "member_count": len(method_reg_paths),
            "max_abs_surface_spearman": surface_novelty_summary["max_abs_spearman"],
            "max_abs_dots_spearman": abs(float(worst_dot_corr["spearman"])),
            "max_dots_within_3px_fraction": float(worst_dot_ov["within_3px_fraction"]),
            "max_dots_within_3px_member": worst_dot_ov["name"],
            "prospective_method_lane_passed": bool(prospective_reg["method_lane_passed"]),
            "prospective_literal_all_entries_passed": bool(
                prospective_reg["literal_all_entries_passed"]
            ),
            "prospective_calibration_controls_count": int(
                prospective_reg["calibration_control_rasters_count"]
            ),
            "members": [r["raster_sha256"] for r in surface_card_rows],
            "surface": surface_card_rows,
            "dots": dots_card_rows,
        },
        "validator": validator_block,
    }
    gate_decision = promotion.promotion_gate(run_card)
    run_card["promotion_gate"] = gate_decision
    run_card["verdict"] = gate_decision["verdict"]
    run_card["submission_ready"] = False
    run_card["slot_selected"] = False

    EXP3_PATH.write_text(
        json.dumps(
            {
                "experiment": 3,
                "session": SESSION_ID,
                "elapsed_seconds": round(time.monotonic() - t0, 2),
                "full_seed_fits": full_seed_infos,
                "full_allocation": full_alloc_info,
                "variant_checks_allfinite": variant_checks_allfinite,
                "variant_checks_nan": variant_checks_nan,
                "full_surface_registry_summary": surface_novelty_summary,
                "dots_registry_summary": {
                    "duplicate": dots_duplicate,
                    "member_count": len(dots_diag_rows),
                    "worst_spearman": worst_dot_corr,
                    "worst_3px_overlap": worst_dot_ov,
                },
                "prospective_with_controls_summary": {
                    "method_lane_passed": prospective_reg["method_lane_passed"],
                    "literal_all_entries_passed": prospective_reg["literal_all_entries_passed"],
                    "competing_method_rasters_count": prospective_reg[
                        "competing_method_rasters_count"
                    ],
                    "calibration_control_rasters_count": prospective_reg[
                        "calibration_control_rasters_count"
                    ],
                    "method_lane_max_abs_rank_correlation": prospective_reg[
                        "method_lane_max_abs_rank_correlation"
                    ],
                    "method_lane_max_dot_overlap": prospective_reg["method_lane_max_dot_overlap"],
                    "calibration_control_rows": prospective_reg["calibration_control_rows"],
                },
                "promotion_gate": gate_decision,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    RUN_CARD_PATH.write_text(json.dumps(run_card, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    chk = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_promotion.py"), str(RUN_CARD_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    print("[Exp 3/3] check_promotion.py exit=", chk.returncode, chk.stdout.strip(), flush=True)
    return 0


if __name__ == "__main__":
    os.environ.setdefault("GEMS_DATA_DIR", "/home/user/GEMSDOE28/.cache/gems-data")
    raise SystemExit(main())
