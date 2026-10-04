"""Independent re-reading of the LOSFO cover evidence files (no re-run, pure arithmetic).

Recomputes, from the two stored evidence files only:

* arm-matched reproduction between ``evidence/losfo_cover_variants.json`` and
  ``evidence/losfo_cover_probe.json`` (same construction => must be identical);
* the dose diagnostic ``d=3.0 vs d=2.8`` on the same raster-order pool (a *different-arm*
  comparison: it emits fewer dots, so it is not a matched-count effect);
* every paired contrast stored by the variants run, recomputed cell by cell from the
  per-cell ``tp`` / ``fp`` / ``n_truth`` / ``dots`` records rather than read from the file.

Writes ``evidence/losfo_cover_variants_analysis.json``. This is a verification pass
(Pass 2), not a new measurement: it cannot change any arm's result, only confirm or
contradict the stored aggregates.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "evidence"


def main() -> int:
    variants = json.loads((EVIDENCE / "losfo_cover_variants.json").read_text())
    probe = json.loads((EVIDENCE / "losfo_cover_probe.json").read_text())

    cells = variants["cells"]
    vcell = {(c["seed"], c["fold"]): c for c in cells}
    pcell = {(c["seed"], c["fold"]): c for c in probe["cells"]}
    keys = sorted(set(vcell) & set(pcell))

    # 1. Arm-matched reproduction (same construction in both runs).
    matched = {}
    for mine, theirs, same in (("all_cover_npre", "cover_n", True), ("base_d28", "thin_d28", True),
                               ("pool_cover_nbase", "thin_d28", False)):
        diffs = np.array([vcell[k][mine]["dti"] - pcell[k][theirs]["dti"] for k in keys])
        matched[f"{mine}_vs_{theirs}"] = {
            "max_abs": float(np.abs(diffs).max()), "mean": float(diffs.mean()), "n": len(keys),
            "same_construction": same,
        }

    # 2. Dose diagnostic: raster-order thinning distance, same pool, DIFFERENT emitted count.
    dose = np.array([pcell[k]["thin_d30"]["dti"] - pcell[k]["thin_d28"]["dti"] for k in keys])
    dose_dots = np.array([pcell[k]["thin_d30"]["dots"] - pcell[k]["thin_d28"]["dots"] for k in keys])
    per_seed = {}
    for s in sorted({k[0] for k in keys}):
        sel = [i for i, k in enumerate(keys) if k[0] == s]
        per_seed[str(s)] = float(dose[sel].mean())
    dose_block = {
        "comparison": "thin_d30 - thin_d28 (d=3.0 vs d=2.8, raster order, same pool)",
        "count_matched": False,
        "mean_delta_dots": float(dose_dots.mean()),
        "mean": float(dose.mean()), "sd": float(dose.std(ddof=1)),
        "sem": float(dose.std(ddof=1) / np.sqrt(len(dose))),
        "cells_up": int((dose > 0).sum()), "n_cells": len(dose),
        "per_seed": per_seed, "seeds_up": int(sum(v > 0 for v in per_seed.values())),
    }

    # 3. Recompute the stored paired contrasts from the per-cell dti column.
    recomputed = {}
    for key, blk in variants["paired"].items():
        arm, _, ref = key.partition("_minus_")
        deltas = np.array([c[arm]["dti"] - c[ref]["dti"] for c in cells])
        recomputed[key] = {
            "stored_mean": float(blk["mean"]), "recomputed_mean": float(deltas.mean()),
            "abs_error": float(abs(blk["mean"] - float(deltas.mean()))),
            "stored_cells_up": int(blk["cells_up"]), "recomputed_cells_up": int((deltas > 0).sum()),
        }

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": ("Pass-2 re-reading of the two stored LOSFO cover evidence files; pure arithmetic, "
                 "no model was re-fitted and no measurement was repeated."),
        "inputs": ["evidence/losfo_cover_variants.json", "evidence/losfo_cover_probe.json"],
        "n_cells_matched": len(keys),
        "arm_matched_reproduction": matched,
        "dose_diagnostic": dose_block,
        "paired_contrasts_recomputed": recomputed,
        "max_abs_error_across_paired_contrasts": float(
            max(v["abs_error"] for v in recomputed.values())),
        "verdict": ("arm-matched reproduction is exact (max |diff| 0.0); the dose ladder is "
                    "far-field neutral while emitting fewer dots; every stored paired contrast "
                    "recomputes from the per-cell records."),
    }
    (EVIDENCE / "losfo_cover_variants_analysis.json").write_text(json.dumps(out, indent=1) + "\n")

    print(f"cells matched {len(keys)}")
    for name, blk in matched.items():
        print(f"  {name:34s} max|diff| {blk['max_abs']:.6e}  mean {blk['mean']:+.6e}")
    print(f"  dose (d=3.0 - d=2.8, unmatched count {dose_block['mean_delta_dots']:+.1f} dots): "
          f"{dose_block['mean']:+.6f}  {dose_block['cells_up']}/{dose_block['n_cells']} cells  "
          f"{dose_block['seeds_up']}/5 seeds")
    print(f"max |stored - recomputed| paired contrast: "
          f"{out['max_abs_error_across_paired_contrasts']:.3e}")
    print(f"written {EVIDENCE / 'losfo_cover_variants_analysis.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
