"""Multi-physics conductive heat-flow residual & shallow SI=0 Euler lineament corroboration (H38).

Pure, deterministic, label-free transforms for the Session 14 H38 addition hypotheses:
  * ``H38-1`` (primary): sub-threshold 1-px ridge lineament corroborated within 1 km (10 px) by a
    positive conductive heat-flow residual (``hf_resid >= 50 mW/m^2`` from DeAngelo et al., 2022,
    USGS ScienceBase item 6297d2fad34ec53d276c5b28, DOI 10.5066/P9BZPVUC, clipped by the Actions
    bridge to ``docs/data/sb_heat_flow_in_footprint.json``) and/or within 300 m (3 px) by a
    shallow, low-dispersion SI=0 Euler deconvolution fault-contact cluster (``depth_mad_m <= 60 m``,
    ``median_depth_m <= 400 m``, ``n_solutions >= 8`` from ``evidence/h31_1_euler_clusters.csv``,
    Reid et al., 1990, DOI 10.1190/1.1442774), ranked by the multiplicative corroboration score
    ``prob * (1 + 0.5*hf_halo + 0.5*euler_halo)``.
  * ``H38-1a`` (component): conductive heat-flow residual ``hf_resid >= 50 mW/m^2`` within 1 km
    corroborating a sub-threshold 1-px ridge lineament.
  * ``H38-1b`` (component): shallow SI=0 Euler contact cluster within 300 m corroborating a
    sub-threshold 1-px ridge lineament.
  * ``H38-2`` (concealed basin-fill conjunction): smooth low-relief basin fill (LiDAR ``valid > 0``
    and ``relief <= P35``) corroborated within 300 m by a shallow SI=0 Euler contact cluster on a
    sub-threshold 1-px ridge lineament.

No function in this module reads labels or hidden truth during feature/mask construction. All
catalogue-proximity exclusions (``d_known >= min_dist_known``) are computed inside each evaluation
cell from that cell's allowed ``known`` mask so held-out systems never leak.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

from . import grid, thinning

# Frozen constants (preregistered in knowledge/37 and knowledge/38 before seeds 265-279 run).
HF_LAYER_NAME = "USGS_gbHeatFlowWells_wEstimates.shp"
HF_RESID_COL = "hf_resid"
HF_RESID_MIN = 50.0        # mW/m^2 departure above de-convected 2D-LOESS regional background
HF_RADIUS_PX = 10.0        # 1 km conductive upflow halo radius (100 m pixels)
EULER_MAD_MAX = 60.0       # m within-cluster depth MAD
EULER_DEPTH_MAX = 400.0    # m median depth (shallow contact)
EULER_N_MIN = 8            # minimum Euler window solutions in cluster
EULER_RADIUS_PX = 3.0      # 300 m corroboration radius (matches 300 m DTI kernel & 1 km window)
LOW_RELIEF_Q = 35.0        # lowest tercile (35th percentile) of LiDAR 300 m relief over valid foot
BONUS_HF = 0.5             # score multiplier bonus for conductive heat-flow residual leg
BONUS_EULER = 0.5          # score multiplier bonus for shallow SI=0 Euler contact leg
K_CAP_PER_CELL = 100       # pre-thinning top-k candidate ridge pixels per quadrant cell
MIN_DIST_BASE_PX = 2.8     # minimum clearance from existing base emission dots
MIN_DIST_KNOWN_PX = 3.0    # minimum clearance from known catalogue pixels (300 m far-field floor)
THIN_D_PX = 2.8            # Poisson-disk spacing of added dots


def load_heatflow_residual_cells(
    json_path: str | Path,
    foot: np.ndarray,
    *,
    resid_col: str = HF_RESID_COL,
    resid_min: float = HF_RESID_MIN,
    layer: str = HF_LAYER_NAME,
) -> dict:
    """Load the runner-clipped USGS Great Basin heat-flow residual wells inside ``foot``.

    Validates that ``json_path`` exists, lists ``layer`` in its schema with ``resid_col``, and
    contains records in the footprint. Projects ``EPSG:32611`` point coordinates to grid ``(row, col)``
    via ``grid.xy_to_rc``. Never reads labels or truth.
    """
    path = Path(json_path)
    raw_bytes = path.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    payload = json.loads(raw_bytes.decode("utf-8"))
    layers_meta = payload.get("schema", {}).get("layers", {})
    if layer not in layers_meta:
        raise ValueError(f"Expected layer {layer!r} not found in {path}")
    attr_fields = layers_meta[layer].get("attribute_fields", {})
    if resid_col not in attr_fields:
        raise ValueError(f"Expected residual field {resid_col!r} missing from {layer} schema")

    foot = np.asarray(foot, dtype=bool)
    H, W = foot.shape
    recs = [r for r in payload.get("records", []) if r.get("source_layer") == layer]
    if not recs:
        raise ValueError(f"No records for layer {layer!r} in {path}")

    mask = np.zeros((H, W), dtype=bool)
    n_in_foot = 0
    n_above_cut = 0
    for r in recs:
        parts = r.get("parts") or []
        if not parts or not parts[0]:
            continue
        x, y = float(parts[0][0][0]), float(parts[0][0][1])
        rr_arr, cc_arr = grid.xy_to_rc(np.array([x]), np.array([y]))
        rr = int(round(float(rr_arr[0])))
        cc = int(round(float(cc_arr[0])))
        if 0 <= rr < H and 0 <= cc < W and foot[rr, cc]:
            n_in_foot += 1
            val = r.get(resid_col)
            try:
                fval = float(val)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fval) and fval >= resid_min:
                n_above_cut += 1
                mask[rr, cc] = True

    return {
        "mask": mask,
        "sha256": sha256,
        "layer": layer,
        "resid_col": resid_col,
        "resid_min": float(resid_min),
        "n_in_bbox": len(recs),
        "n_in_footprint": int(n_in_foot),
        "n_records_above_cut": int(n_above_cut),
        "n_cells_100m": int(mask.sum()),
    }


def load_euler_contact_clusters(
    csv_path: str | Path,
    shape: tuple[int, int],
    *,
    mad_max: float = EULER_MAD_MAX,
    depth_max: float = EULER_DEPTH_MAX,
    n_min: int = EULER_N_MIN,
) -> dict:
    """Load shallow, depth-coherent SI=0 Euler deconvolution clusters (Reid et al., 1990)."""
    path = Path(csv_path)
    raw_bytes = path.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    H, W = shape
    mask = np.zeros((H, W), dtype=bool)
    n_total = 0
    n_kept = 0
    with path.open("r", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            n_total += 1
            if float(r["depth_mad_m"]) > mad_max:
                continue
            if float(r["median_depth_m"]) > depth_max:
                continue
            if int(r["n_solutions"]) < n_min:
                continue
            y = int(round(float(r["row"])))
            x = int(round(float(r["col"])))
            if 0 <= y < H and 0 <= x < W:
                mask[y, x] = True
                n_kept += 1
    return {
        "mask": mask,
        "sha256": sha256,
        "mad_max": float(mad_max),
        "depth_max": float(depth_max),
        "n_min": int(n_min),
        "n_total_clusters": int(n_total),
        "n_kept_clusters": int(n_kept),
        "n_cells_100m": int(mask.sum()),
    }


def load_low_relief_basin_mask(
    lidar_path: str | Path,
    foot: np.ndarray,
    *,
    relief_q: float = LOW_RELIEF_Q,
) -> dict:
    """Load the smooth, low-relief basin-fill mask from the 12-band LiDAR descriptor raster."""
    foot = np.asarray(foot, dtype=bool)
    with rasterio.open(lidar_path) as src:
        desc = [(d or "").split(" - ")[0].strip() for d in src.descriptions]
        if desc[8] != "relief" or desc[11] != "valid":
            raise AssertionError(
                f"Unexpected LiDAR band descriptions at 9/12: {desc[8]!r}, {desc[11]!r}"
            )
        relief = src.read(9).astype(np.float64)
        valid = src.read(12) > 0
    lv = valid & foot
    if not lv.any():
        return {"mask": np.zeros_like(foot, bool), "relief_cut": 0.0, "n_px": 0}
    cut = float(np.quantile(relief[lv], relief_q / 100.0))
    mask = lv & (relief <= cut)
    return {
        "mask": mask,
        "relief_q": float(relief_q),
        "relief_cut": cut,
        "n_px": int(mask.sum()),
        "frac_of_footprint": float(mask.sum() / max(1, int(foot.sum()))),
    }


def build_corroboration_fields(
    foot: np.ndarray,
    *,
    hf_json_path: str | Path,
    euler_csv_path: str | Path,
    lidar_path: str | Path | None = None,
    hf_resid_min: float = HF_RESID_MIN,
    hf_radius_px: float = HF_RADIUS_PX,
    euler_mad_max: float = EULER_MAD_MAX,
    euler_depth_max: float = EULER_DEPTH_MAX,
    euler_n_min: int = EULER_N_MIN,
    euler_radius_px: float = EULER_RADIUS_PX,
    low_relief_q: float = LOW_RELIEF_Q,
    bonus_hf: float = BONUS_HF,
    bonus_euler: float = BONUS_EULER,
) -> dict:
    """Build all label-free corroboration masks and score multipliers on the full grid."""
    foot = np.asarray(foot, dtype=bool)
    hf_info = load_heatflow_residual_cells(hf_json_path, foot, resid_min=hf_resid_min)
    eu_info = load_euler_contact_clusters(
        euler_csv_path,
        foot.shape,
        mad_max=euler_mad_max,
        depth_max=euler_depth_max,
        n_min=euler_n_min,
    )
    hf_halo = (
        distance_transform_edt(~hf_info["mask"]) <= hf_radius_px
        if hf_info["mask"].any()
        else np.zeros_like(foot, bool)
    )
    eu_halo = (
        distance_transform_edt(~eu_info["mask"]) <= euler_radius_px
        if eu_info["mask"].any()
        else np.zeros_like(foot, bool)
    )
    joint_mask = hf_halo | eu_halo
    both_mask = hf_halo & eu_halo
    score_mult = (
        1.0
        + float(bonus_hf) * hf_halo.astype(np.float64)
        + float(bonus_euler) * eu_halo.astype(np.float64)
    )

    low_relief_info = None
    low_relief_euler = np.zeros_like(foot, bool)
    if lidar_path is not None and Path(lidar_path).is_file():
        low_relief_info = load_low_relief_basin_mask(lidar_path, foot, relief_q=low_relief_q)
        low_relief_euler = low_relief_info["mask"] & eu_halo

    return {
        "hf_halo": hf_halo,
        "euler_halo": eu_halo,
        "joint_mask": joint_mask,
        "both_mask": both_mask,
        "low_relief_euler_mask": low_relief_euler,
        "score_mult": score_mult,
        "meta": {
            "heatflow": {k: v for k, v in hf_info.items() if k != "mask"},
            "euler": {k: v for k, v in eu_info.items() if k != "mask"},
            "low_relief": (
                {k: v for k, v in low_relief_info.items() if k != "mask"}
                if low_relief_info is not None
                else None
            ),
            "hf_radius_px": float(hf_radius_px),
            "euler_radius_px": float(euler_radius_px),
            "bonus_hf": float(bonus_hf),
            "bonus_euler": float(bonus_euler),
            "hf_halo_px_in_footprint": int((hf_halo & foot).sum()),
            "euler_halo_px_in_footprint": int((eu_halo & foot).sum()),
            "joint_halo_px_in_footprint": int((joint_mask & foot).sum()),
            "both_halo_px_in_footprint": int((both_mask & foot).sum()),
            "low_relief_euler_px_in_footprint": int((low_relief_euler & foot).sum()),
        },
    }


def _random_matched_offcat(
    pool: np.ndarray,
    base: np.ndarray,
    n_keep: int,
    min_dist: float,
    seed: int,
) -> np.ndarray:
    """Content-blind matched-count independent set in ``pool`` with clearance from ``base``."""
    out = np.zeros_like(pool, dtype=bool)
    if n_keep <= 0 or not pool.any():
        return out
    ys, xs = np.nonzero(pool)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(ys))
    bys, bxs = np.nonzero(base)
    base_tree = cKDTree(np.column_stack([bys, bxs])) if bys.size else None
    kept: list[tuple[int, int]] = []
    for i in order:
        y, x = int(ys[i]), int(xs[i])
        if base_tree is not None and base_tree.query([y, x])[0] < min_dist:
            continue
        if kept:
            ktree = cKDTree(np.array(kept, dtype=float))
            if ktree.query([y, x])[0] < min_dist:
                continue
        kept.append((y, x))
        if len(kept) >= n_keep:
            break
    if kept:
        ky, kx = np.array(kept, dtype=int).T
        out[ky, kx] = True
    return out


def select_corroborated_ridge_dots(
    prob: np.ndarray,
    ridge: np.ndarray,
    active: np.ndarray,
    base: np.ndarray,
    known: np.ndarray,
    cond_mask: np.ndarray,
    *,
    score_mult: np.ndarray | None = None,
    k_cap: int = K_CAP_PER_CELL,
    min_dist_base: float = MIN_DIST_BASE_PX,
    min_dist_known: float = MIN_DIST_KNOWN_PX,
    thin_d: float = THIN_D_PX,
    rng_seed: int = 1000,
) -> dict:
    """Select corroborated sub-threshold ridge dots and two matched controls for one cell.

    Returns:
      * ``added``: corroborated sub-threshold ridge dots (top ``k_cap`` by ``prob * score_mult``,
        thinned via ``thinning.dot_thin(raw, thin_d)``);
      * ``control_sub_ridge``: uncorroborated sub-threshold ridge dots (top ``min(k_cap, n_elig)``
        from ``sub_pool & ~cond_mask`` ranked by ``prob``, thinned via ``dot_thin(craw, thin_d)``);
      * ``control_random``: content-blind random independent set of exact count ``int(added.sum())``
        drawn from ``active & ~base & (d_known >= min_dist_known)``.
    """
    active = np.asarray(active, dtype=bool)
    ridge = np.asarray(ridge, dtype=bool)
    base = np.asarray(base, dtype=bool)
    known = np.asarray(known, dtype=bool)
    cond_mask = np.asarray(cond_mask, dtype=bool)
    prob_f = np.asarray(prob, dtype=np.float64)

    d_base = distance_transform_edt(~base) if base.any() else np.full(active.shape, np.inf)
    d_kn = distance_transform_edt(~known) if known.any() else np.full(active.shape, np.inf)
    sub_pool = ridge & active & (d_base >= min_dist_base) & (d_kn >= min_dist_known)

    elig = sub_pool & cond_mask
    ys, xs = np.nonzero(elig)
    n_elig = int(ys.size)
    k_take = min(int(k_cap), n_elig)

    if k_take > 0:
        if score_mult is not None:
            mult = np.asarray(score_mult, dtype=np.float64)[ys, xs]
            sc = prob_f[ys, xs] * mult
        else:
            sc = prob_f[ys, xs]
        sc = np.nan_to_num(sc, nan=-np.inf, posinf=-np.inf, neginf=-np.inf)
        top = np.argsort(-sc, kind="stable")[:k_take]
        raw = np.zeros_like(elig, dtype=bool)
        raw[ys[top], xs[top]] = True
        added = thinning.dot_thin(raw, thin_d)
    else:
        added = np.zeros_like(elig, dtype=bool)

    # Control 1: uncorroborated sub-threshold ridge (~cond_mask), same pre-thinning cap k_take
    c_elig = sub_pool & ~cond_mask
    cys, cxs = np.nonzero(c_elig)
    ck_take = min(k_take, int(cys.size))
    if ck_take > 0:
        csc = np.nan_to_num(prob_f[cys, cxs], nan=-np.inf, posinf=-np.inf, neginf=-np.inf)
        ctop = np.argsort(-csc, kind="stable")[:ck_take]
        craw = np.zeros_like(c_elig, dtype=bool)
        craw[cys[ctop], cxs[ctop]] = True
        ctrl_sub = thinning.dot_thin(craw, thin_d)
    else:
        ctrl_sub = np.zeros_like(c_elig, dtype=bool)

    # Control 2: content-blind matched-count random dots in active & ~base & (d_kn >= min_dist_known)
    rand_pool = active & ~base & ~known & (d_kn >= min_dist_known)
    ctrl_rand = _random_matched_offcat(rand_pool, base, int(added.sum()), thin_d, rng_seed)

    # Hard integrity assertions
    if (added & base).any():
        raise AssertionError("corroborated added dots overlap base")
    if (added & known).any():
        raise AssertionError("corroborated added dots overlap known catalogue")
    if (added & ~active).any():
        raise AssertionError("corroborated added dots fall outside active cell")
    if added.any() and known.any() and float(d_kn[added].min()) < min_dist_known - 1e-6:
        raise AssertionError("corroborated added dots violate min_dist_known")
    if added.any() and base.any() and float(d_base[added].min()) < min_dist_base - 1e-6:
        raise AssertionError("corroborated added dots violate min_dist_base")
    if (ctrl_sub & base).any() or (ctrl_sub & known).any():
        raise AssertionError("control_sub_ridge overlaps base or known")
    if (ctrl_rand & base).any() or (ctrl_rand & known).any():
        raise AssertionError("control_random overlaps base or known")

    return {
        "added": added,
        "control_sub_ridge": ctrl_sub,
        "control_random": ctrl_rand,
        "n_sub_pool": int(sub_pool.sum()),
        "n_eligible": n_elig,
        "k_take": k_take,
        "n_added": int(added.sum()),
        "n_control_sub_ridge": int(ctrl_sub.sum()),
        "n_control_random": int(ctrl_rand.sum()),
    }
