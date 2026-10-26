#!/usr/bin/env python3
"""S19 Experiment 1 (knowledge/57): label-free RADLIN surface, leakage canary,
pre-placement registry uniqueness. No detector fit, no TIFF written.

Registry scope (declared, not global): local docs/downloads/*-nan.tif at freeze
time plus byte-verified forensic copies of the nine focus sites' highest-reported
artifacts in /tmp/forensic (hashes pinned in evidence/s18_champion_forensic.json).
Forensic copies are education/comparison only and never enter placement.
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
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, holdout, losfo, packing, paths, radlin  # noqa: E402

SEED_CANARY = 320


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while c := f.read(1 << 20):
            h.update(c)
    return h.hexdigest()


def load_dots(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def within_frac(ours: np.ndarray, ref: np.ndarray, r: float = 3.0) -> float:
    y, x = np.nonzero(ours)
    yb, xb = np.nonzero(ref)
    if len(y) == 0 or len(yb) == 0:
        return 0.0
    d, _ = cKDTree(np.c_[yb, xb].astype(float)).query(np.c_[y, x].astype(float), workers=1)
    return float((d <= r).mean())


def registry_files() -> dict[str, Path]:
    reg: dict[str, Path] = {}
    for p in sorted((ROOT / "docs/downloads").glob("*-nan.tif")):
        reg[p.name] = p
    forensic = json.loads((ROOT / "evidence/s18_champion_forensic.json").read_text())
    for site in forensic["sites"]:
        cand = Path("/tmp/forensic") / (site["site"] + "-" + Path(site["artifact"]).name)
        # allfinite/zeros twins share dot sets with some -nan locals; keep forensic copy anyway
        if cand.is_file() and sha256_file(cand) == site["sha256"]:
            reg[f"forensic_{site['site']}"] = cand
        else:
            print(f"WARNING forensic missing/hash-mismatch: {cand}", flush=True)
    return reg


def main() -> int:
    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot
    with rasterio.open(paths.DATA / "geodawn_extensions_u8.tif") as s:
        thk = s.read(1)
        uth = s.read(3)
        ext_desc = list(s.descriptions)
    with rasterio.open(paths.DATA / "geodawn_rad_u8.tif") as s:
        rad_desc = list(s.descriptions)
        rad_valid_frac = float((s.read(1)[foot] > 0).mean())
    assert ext_desc[0].startswith("ThK") and ext_desc[2].startswith("UTh"), ext_desc

    surf = radlin.radiometric_lineament_surface(thk, foot)
    score, bonus, field = surf["score"], surf["bonus"], surf["field"]
    out_npz = paths.DATA / "prepared" / "s19_radlin_surface.npz"
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_npz, score=score, bonus=bonus, field=field)
    print(f"surface: {surf['meta']} ({time.time()-t0:.0f}s)", flush=True)

    # --- leakage canary on LOSFO seed 320 withheld systems ---
    fold = holdout.make_quadrant_folds(foot)
    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=SEED_CANARY)
    held_ids = np.flatnonzero(hold >= 0) + 1
    hidden = np.isin(sys_grid, held_ids) & foot
    d_hidden = distance_transform_edt(~hidden)
    rng = np.random.default_rng(SEED_CANARY)
    neg_pool = np.flatnonzero((foot & (d_hidden > 6)).ravel())
    neg_idx = rng.choice(neg_pool, size=min(250_000, len(neg_pool)), replace=False)
    pos_idx = np.flatnonzero(hidden.ravel())
    canary = {}
    for name, arr in (("score", score), ("bonus", bonus), ("field_inverted_thk", field)):
        y = np.r_[np.ones(len(pos_idx)), np.zeros(len(neg_idx))]
        v = np.r_[arr.ravel()[pos_idx], arr.ravel()[neg_idx]].astype(np.float64)
        auc = float(roc_auc_score(y, v))
        canary[name] = {"auc": auc, "max_auc_inv": max(auc, 1 - auc),
                        "pass_le_0.90": max(auc, 1 - auc) <= 0.90}
    print(f"canary: {canary}", flush=True)

    # --- pre-placement registry check ---
    d_cat = distance_transform_edt(~labels)
    eligible = (score > 0) & foot & (d_cat > 2)
    pool = packing.prob_order_pack(score, eligible, n_target=37_654, min_dist=2.8)
    print(f"eligible {int(eligible.sum()):,}; top pool {int(pool.sum()):,}", flush=True)
    reg = registry_files()
    foot_idx = np.flatnonzero(foot.ravel())
    sample = np.sort(np.random.default_rng(19).choice(foot_idx, size=400_000, replace=False))
    table = {}
    for name, p in reg.items():
        ref = load_dots(p)
        rho = float(spearmanr(score.ravel()[sample].astype(np.float64),
                              ref.ravel()[sample].astype(np.float64)).statistic)
        table[name] = {"spearman_surface_sample400k": rho,
                       "frac_pool_within3px": within_frac(pool, ref),
                       "registry_dots": int(ref.sum()), "sha256": sha256_file(p)}
    worst_rho = max(table.items(), key=lambda kv: abs(kv[1]["spearman_surface_sample400k"]))
    worst_ov = max(table.items(), key=lambda kv: kv[1]["frac_pool_within3px"])
    passed = (all(v["pass_le_0.90"] for v in canary.values())
              and abs(worst_rho[1]["spearman_surface_sample400k"]) <= 0.90
              and worst_ov[1]["frac_pool_within3px"] <= 0.70)
    out = {
        "session": "S19B-RADLIN", "experiment": 1, "preregistration": "knowledge/57_s19b_radlin_preregistration.md",
        "surface_npz": str(out_npz.relative_to(ROOT)), "surface_npz_sha256": sha256_file(out_npz),
        "surface_meta": surf["meta"], "extensions_descriptions": ext_desc,
        "rad_descriptions": rad_desc, "rad_K_valid_frac_in_footprint": rad_valid_frac,
        "uth_valid_px": int(((uth > 0) & foot).sum()),
        "canary": {"seed": SEED_CANARY, "withheld_positives": int(hidden.sum()),
                   "negatives_sampled": int(len(neg_idx)), "features": canary},
        "preplacement": {"pool_dots": int(pool.sum()), "eligible_px": int(eligible.sum()),
                         "worst_by_spearman": {"raster": worst_rho[0], **worst_rho[1]},
                         "worst_by_overlap": {"raster": worst_ov[0], **worst_ov[1]},
                         "table": table},
        "registry_scope": "local docs/downloads/*-nan.tif + byte-verified /tmp/forensic focus-9 copies; declared snapshot, not a global parallel registry",
        "passed": bool(passed), "seconds": round(time.time() - t0, 1),
    }
    (ROOT / "evidence/s19b_radlin_surface.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"passed": passed, "worst_rho": out["preplacement"]["worst_by_spearman"],
                      "worst_overlap": out["preplacement"]["worst_by_overlap"]}, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
