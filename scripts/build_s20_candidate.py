#!/usr/bin/env python3
"""Session 20 Experiment 3 — build H43-1 candidate, uniqueness audit, exact-file validation.

Preregistration §4 reading rule applies: the Experiment 2 gate FAILED, so this TIFF is a
research artifact marked DO NOT SUBMIT regardless of format validity. Writes
evidence/s20_build.json + docs/downloads/gems28-h43-1-tpb2gkc-20261026-<digest>-allfinite.tif
(primary, all-finite zeros-outside), the -nan companion, a single-member ZIP of the primary, checks JSON
and the <=140-character note file.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src")]
from gems27 import grid, paths, submission  # noqa: E402
from gems27.greedy_cover import cover_surface, eligibility, greedy_kernel_cover  # noqa: E402

TARGET_BUDGET = 37_654


def load_pos(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def dot_digest(dots: np.ndarray) -> str:
    return hashlib.sha256(np.packbits(dots.ravel()).tobytes()).hexdigest()


def main() -> int:
    t0 = time.monotonic()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    pool = load_pos(paths.DATA / "h19_5_nan.tif") & foot
    elig, _d_vis, _d_end = eligibility(pool, labels)
    print(f"pool {int(pool.sum())} eligible {int(elig.sum())} target budget {TARGET_BUDGET}", flush=True)

    surface = cover_surface(pool, elig)
    dots = greedy_kernel_cover(pool, elig, TARGET_BUDGET, min_dist=2.8)
    n_dots = int(dots.sum())
    print(f"greedy placed {n_dots} dots in {time.monotonic()-t0:.1f}s "
          f"({'budget reached' if n_dots == TARGET_BUDGET else 'PACKING EXHAUSTED below budget'})",
          flush=True)
    assert int((dots & labels).sum()) == 0, "dots on catalogue"
    assert int((dots & ~foot).sum()) == 0, "dots outside footprint"
    assert int((dots & ~elig).sum()) == 0, "dots outside eligibles"

    digest12 = dot_digest(dots)[:12]
    stem = f"gems28-h43-1-tpb2gkc-20261026-{digest12}"
    ddir = ROOT / "docs/downloads"
    pred = dots.astype(np.float32)
    primary = submission.write_geotiff(pred, paths.TEMPLATE, ddir / f"{stem}-allfinite.tif", outside="zero")
    nan_tif = submission.write_geotiff(pred, paths.TEMPLATE, ddir / f"{stem}-nan.tif", outside="nan")
    zip_path = submission.zip_single(primary, ddir / f"{stem}-allfinite.zip")
    ver_primary = submission.verify_geotiff(primary, paths.TEMPLATE)
    ver_nan = submission.verify_geotiff(nan_tif, paths.TEMPLATE)
    print("primary hard pass:", ver_primary["hard_checks_passed"], "sha256:", ver_primary["sha256"])

    # Registry: every *.tif under docs/downloads (before this build) + restored family +
    # GEMSDOE32 champion education copy, deduplicated by exact dot-set digest.
    registry_paths = sorted(p for p in ddir.glob("*.tif") if stem not in p.name)
    registry_paths += [paths.DATA / "h19_5_nan.tif", paths.DATA / "dotted_h19_5_d1_5_nan.tif",
                       paths.DATA / "dotted_h19_5_d2_8_nan.tif",
                       paths.DATA / "registry_edu/champion_g32_h33_2_b2_zeros.tif"]
    seen: dict[str, str] = {}
    rows = []
    rng = np.random.default_rng(20261026)
    foot_idx = np.flatnonzero(foot.ravel())
    sample = rng.choice(foot_idx, size=300_000, replace=False)
    surf_sample = surface.ravel()[sample]
    d_cat = distance_transform_edt(~dots)
    for p in registry_paths:
        ref = load_pos(p) & foot
        dg = dot_digest(ref)
        if dg in seen:
            continue
        seen[dg] = p.name
        d_to_ref = distance_transform_edt(~ref) if ref.any() else np.full(foot.shape, np.inf)
        frac = float((d_to_ref[dots] <= 3.0).mean()) if n_dots else 0.0
        rho = float(spearmanr(surf_sample, ref.ravel()[sample].astype(float)).statistic)
        jacc = float((dots & ref).sum() / max((dots | ref).sum(), 1))
        rows.append({"file": p.name, "dots": int(ref.sum()), "dot_digest12": dg[:12],
                     "frac_candidate_dots_within_3px": frac,
                     "spearman_surface_vs_registry_sample300k": rho,
                     "exact_dot_jaccard": jacc})
        rows.sort(key=lambda r: -r["frac_candidate_dots_within_3px"])
    _ = d_cat  # (kept for symmetry/debug; per-registry EDT above is the reported quantity)
    max_frac = max(r["frac_candidate_dots_within_3px"] for r in rows)
    max_abs_rho = max(abs(r["spearman_surface_vs_registry_sample300k"]) for r in rows)
    champ_row = next(r for r in rows if "champion_g32" in r["file"])
    uniq = {"registry_distinct_dot_sets": len(rows),
            "surface_max_abs_spearman": float(max_abs_rho),
            "final_dots_max_fraction_within_3px": float(max_frac),
            "vs_champion": champ_row,
            "thresholds": {"abs_spearman_stop_if_above": 0.90, "dot_overlap_stop_if_above": 0.70},
            "duplicate_by_protocol": bool(max_abs_rho > 0.90 or max_frac > 0.70),
            "exact_duplicate_of_any_registry": bool(dot_digest(dots) in seen),
            "rows_top10_by_overlap": rows[:10], "rows_all": rows}
    print("uniqueness:", {k: uniq[k] for k in ("registry_distinct_dot_sets", "surface_max_abs_spearman",
                                               "final_dots_max_fraction_within_3px",
                                               "duplicate_by_protocol",
                                               "exact_duplicate_of_any_registry")}, flush=True)
    print("vs champion:", champ_row, flush=True)

    holdout = json.loads((ROOT / "evidence/s20_holdout.json").read_text())
    note = (f"S20 H43-1 TPB2-GKC greedy kernel-cover, tip-protected B2, {n_dots} dots; "
            f"holdout gate FAILED; DO NOT SUBMIT")
    assert len(note) <= 140, len(note)
    (ddir / f"note-{stem}.txt").write_text(note + "\n")
    checks = {
        "stem": stem, "primary_file": primary.name, "primary_sha256": ver_primary["sha256"],
        "primary_bytes": primary.stat().st_size, "nan_file": nan_tif.name,
        "nan_sha256": ver_nan["sha256"], "zip_file": zip_path.name,
        "zip_sha256": submission.sha256_file(zip_path),
        "dots": n_dots, "target_budget": TARGET_BUDGET,
        "budget_reached": bool(n_dots == TARGET_BUDGET),
        "verify_primary": ver_primary, "verify_nan": ver_nan,
        "note": note, "note_chars": len(note),
        "gate_pass_exp2": bool(holdout["gate_pass"]),
        "holdout_pooled_gain": holdout["pooled_gain"],
        "verdict": "negative",
        "submission_ready": False,
    }
    (ddir / f"checks-{stem}.json").write_text(json.dumps(checks, indent=1))

    out = {
        "experiment": "S20-EXP3 build + uniqueness + validator",
        "preregistration": "knowledge/56_s20_preregistration_H43-1.md",
        "stem": stem, "dot_digest12": digest12,
        "pool_px": int(pool.sum()), "eligible_px": int(elig.sum()),
        "dots": n_dots, "target_budget": TARGET_BUDGET,
        "budget_reached": bool(n_dots == TARGET_BUDGET),
        "packing_note": "Greedy stopped when no unblocked eligible candidate remained with "
                        "positive uncovered pool mass; see knowledge/57 report analysis.",
        "files": {k: checks[k] for k in ("primary_file", "primary_sha256", "primary_bytes",
                                          "nan_file", "nan_sha256", "zip_file", "zip_sha256")},
        "validator_primary_hard_pass": bool(ver_primary["hard_checks_passed"]),
        "validator_nan_hard_pass": bool(ver_nan["hard_checks_passed"]),
        "verify_primary_checks": ver_primary["checks"],
        "uniqueness": uniq,
        "gate_pass_exp2": bool(holdout["gate_pass"]),
        "verdict": "negative", "submission_ready": False,
        "note": note,
        "runtime_s": round(time.monotonic() - t0, 1),
    }
    (ROOT / "evidence/s20_build.json").write_text(json.dumps(out, indent=1))
    print("wrote evidence/s20_build.json; stem", stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
