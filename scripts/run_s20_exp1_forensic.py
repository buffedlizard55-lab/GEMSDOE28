#!/usr/bin/env python3
"""Session 20 Experiment 1 — champion lineage byte forensics + leakage canary.

Frozen in knowledge/56_s20_preregistration_H43-1.md §4. No gate seeds are fitted here:
seed 340's split *assignment* is used only to score single-feature AUCs (assignment is a
function of seed + catalogue geometry). Writes evidence/s20_exp1_forensic.json.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src")]
from gems27 import grid, holdout, paths  # noqa: E402
from gems27.greedy_cover import eligibility  # noqa: E402
from gems27.thinning import dot_thin  # noqa: E402


def load_pos(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def frac_within_3px(dots: np.ndarray, ref: np.ndarray) -> float:
    if not dots.any():
        return 0.0
    if not ref.any():
        return 0.0
    d = distance_transform_edt(~ref)
    return float((d[dots] <= 3.0).mean())


def main() -> int:
    t0 = time.monotonic()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    d_cat = distance_transform_edt(~labels)

    files = {
        "h19_5": paths.DATA / "h19_5_nan.tif",
        "dotted_d1_5": paths.DATA / "dotted_h19_5_d1_5_nan.tif",
        "dotted_d2_8": paths.DATA / "dotted_h19_5_d2_8_nan.tif",
        "solo_r1_local": ROOT / "docs/downloads/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
        "champion_g32_b2": paths.DATA / "registry_edu/champion_g32_h33_2_b2_zeros.tif",
    }
    masks, meta = {}, {}
    for name, p in files.items():
        masks[name] = load_pos(p)
        m = masks[name]
        meta[name] = {
            "path": str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),
            "sha256": sha256_file(p),
            "dots": int(m.sum()),
            "dots_on_catalogue": int((m & labels).sum()),
            "dots_ring_le1": int((m & (d_cat > 0) & (d_cat <= 1.0)).sum()),
            "dots_ring_1_2": int((m & (d_cat > 1.0) & (d_cat <= 2.0)).sum()),
            "dots_ring_2_3": int((m & (d_cat > 2.0) & (d_cat <= 3.0)).sum()),
            "dots_d_cat_le2_offcat": int((m & (d_cat > 0) & (d_cat <= 2.0)).sum()),
        }
        print(name, meta[name], flush=True)

    champ, solo, d28, h195 = (masks[k] for k in ("champion_g32_b2", "solo_r1_local", "dotted_d2_8", "h19_5"))
    solo_minus_ring2 = solo & (d_cat > 2.0)
    d28_minus_ring1 = d28 & (d_cat > 1.0)
    rel = {
        "champion_subset_of_solo": bool((champ & ~solo).sum() == 0),
        "champion_added_vs_solo": int((champ & ~solo).sum()),
        "champion_removed_vs_solo": int((solo & ~champ).sum()),
        "solo_minus_ringLe2_equals_champion": bool(np.array_equal(solo_minus_ring2, champ)),
        "solo_minus_ringLe2_symmetric_difference_vs_champion": int((solo_minus_ring2 ^ champ).sum()),
        "solo_equals_d28_minus_ringLe1": bool(np.array_equal(d28_minus_ring1, solo)),
        "d28_minus_ringLe1_symmetric_difference_vs_solo": int((d28_minus_ring1 ^ solo).sum()),
        "d28_subset_of_h19_5": bool((d28 & ~h195).sum() == 0),
        "champion_subset_of_h19_5": bool((champ & ~h195).sum() == 0),
        "champion_fraction_within_3px_of_solo": frac_within_3px(champ, solo),
        "h19_5_on_catalogue_px": int((h195 & labels).sum()),
    }
    print(rel, flush=True)

    # Regeneration check: dot_thin(H19-5 minus catalogue, 2.8) vs pinned d2.8.
    regen = dot_thin(h195 & ~labels & foot, 2.8)
    rel["dot_thin_h19_5_minus_catalogue_2p8_px"] = int(regen.sum())
    rel["dot_thin_regen_equals_pinned_d2_8"] = bool(np.array_equal(regen, d28))
    rel["dot_thin_regen_symmetric_difference"] = int((regen ^ d28).sum())
    print("regen", rel["dot_thin_h19_5_minus_catalogue_2p8_px"], rel["dot_thin_regen_equals_pinned_d2_8"],
          rel["dot_thin_regen_symmetric_difference"], flush=True)

    # Leakage canary on seed-340 assignment (all 4 quadrant splits pooled; features visible-only).
    from sklearn.metrics import roc_auc_score

    fold = holdout.make_quadrant_folds(foot)
    rng = np.random.default_rng(20261026)
    canary = {}
    for fid in range(4):
        sp = holdout.make_split(labels, fold, fid, seed=340)
        visible = sp.known
        elig, d_vis, d_end = eligibility(h195, visible)
        feats = {
            "neg_d_visible": -np.minimum(d_vis, 50.0),
            "ring_le2_indicator": ((d_vis > 0) & (d_vis <= 2.0)).astype(float),
            "tip_indicator": (d_end <= 3.0).astype(float),
            "eligible_indicator": elig.astype(float),
            "pool_indicator": h195.astype(float),
        }
        fm = sp.fold_mask & foot
        idx = np.flatnonzero(fm.ravel())
        sample = rng.choice(idx, size=min(200_000, idx.size), replace=False)
        y = sp.hidden.ravel()[sample].astype(int)
        row = {"fold": holdout.FOLD_NAMES[fid], "hidden_px_in_fold": int(sp.hidden.sum()),
               "sample_px": int(sample.size), "auc": {}}
        for fname, f in feats.items():
            x = f.ravel()[sample]
            row["auc"][fname] = float(roc_auc_score(y, x)) if len(np.unique(y)) > 1 else None
        canary[holdout.FOLD_NAMES[fid]] = row
        print("canary", row, flush=True)
    max_auc = max(v for r in canary.values() for v in r["auc"].values() if v is not None)

    out = {
        "experiment": "S20-EXP1 forensic + leakage canary",
        "preregistration": "knowledge/56_s20_preregistration_H43-1.md",
        "inputs": meta,
        "relations": rel,
        "canary_seed340_assignment_only": canary,
        "canary_max_auc": float(max_auc),
        "canary_pass_le_0_90": bool(max_auc <= 0.90),
        "catalogue_px": int(labels.sum()),
        "footprint_px": int(foot.sum()),
        "runtime_s": round(time.monotonic() - t0, 1),
        "note": "Scores in provenance text are USER-REPORTED / UNVERIFIED. Champion audit JSON at "
                "GEMSDOE32@012e17b labels the file UNSCORED with MODEL projection 0.2747.",
    }
    dst = ROOT / "evidence/s20_exp1_forensic.json"
    dst.write_text(json.dumps(out, indent=1))
    print("wrote", dst, "max_auc", max_auc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
