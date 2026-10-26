"""Session 20 lane S20-NCHC (H43-1): Multi-Scale Nematic Cross-Modal Lineament Concordance
& Hydrothermal Clay-Cap Margin Corridor with 300 m Submodular Kernel Allocation.

Frozen specification: ``knowledge/56_s20_preregistration.md``.

Design invariants
-----------------
1. **Zero catalogue inputs in features:** No function in ``extract_s20_features`` reads ``labels.tif``,
   ``existing_faults.tif``, ``qfaults``, ``sgmc``, ``sb_slip_tendency``, or ``dist_known_fault_px``.
2. **Zero 0th-order regional scalar levels in the classifier:** Raw regional scalar bands
   (``det_elev``, ``rtp``, ``tmi``, ``iso_grav_anom``, ``depth_to_base_surf``, ``cond_surf``) are
   used *only* inside translation- and level-invariant derivative / Hessian-tubular operators and
   never passed as raw scalar levels to the classifier.
3. **Strict fold isolation:** Inside ``SegmentHoldout``, each fold trains exclusively on
   ``fold["train"]`` with ``fold["visible"]`` labels, calibrates probabilities strictly on
   ``fold["train"]``, and applies ``B=2`` off-catalogue hygiene strictly from ``fold["visible"]``
   (``distance_transform_edt(~fold["visible"]) > 2.0``), never touching withheld truth.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter
from sklearn.ensemble import HistGradientBoostingClassifier

from . import grid, packing, paths

S20_FEATURE_NAMES: tuple[str, ...] = (
    "mag_tubular_150m",
    "mag_tubular_400m",
    "mag_tubular_1000m",
    "grav_tubular_400m",
    "grav_tubular_1000m",
    "em_cb_tubular_400m",
    "em_cb_tubular_1000m",
    "topo_tubular_150m",
    "topo_tubular_400m",
    "topo_tubular_1000m",
    "nematic_order_400m",
    "nematic_order_1000m",
    "top2_harmonic_400m",
    "top2_harmonic_1000m",
    "geodawn_ew_stripe_150m",
    "mag_up150_step_300m",
    "claycap_margin_400m",
    "rad_k_metasom_local",
    "rad_uth_redox_step_300m",
    "rad_valid_flag",
    "hydro_qtz_diseq_1500m",
    "hydro_temp_anom_1500m",
    "hydro_hf_resid_1500m",
    "strain_2ndinv_grad_1000m",
    "strain_dilate_norm",
    "seis_ieq_norm",
    "lidar_scarp_composite",
    "lidar_valid_flag",
)

FORBIDDEN_WELLSPRING_COLUMNS = frozenset({"dist_known_fault_px"})
FRANGI_BETA = 0.5
CORRIDOR_QUANTILE = 0.94
BUDGET_FRAC_FOOTPRINT = 0.0095  # ~49,090 dots on the 5,167,373-pixel footprint
CATALOGUE_CLEARANCE_PX = 2.0    # B=2 (>200 m clearance from visible catalogue)
KERNEL_RADIUS_PX = 3.0          # 300 m official competition DTI kernel
MAX_NEG_PER_FOLD = 250_000
PREDICT_CHUNK_ROWS = 400_000


def nearest_fill_2d(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Fill invalid/outside cells from the nearest valid cell for boundary-clean filtering."""
    arr = np.asarray(values, dtype=np.float32)
    mask = np.asarray(valid, dtype=bool) & np.isfinite(arr)
    if not np.any(mask):
        raise ValueError("Cannot nearest-fill a 2D array with zero valid finite cells")
    if np.all(mask):
        return arr.copy()
    idx = distance_transform_edt(~mask, return_distances=False, return_indices=True)
    return arr[tuple(idx)].astype(np.float32, copy=False)


def robust_scale_in_mask(
    arr: np.ndarray,
    foot: np.ndarray,
    *,
    q_lo: float = 5.0,
    q_hi: float = 99.0,
    active: np.ndarray | None = None,
) -> np.ndarray:
    """Map [q_lo, q_hi] over active in-footprint pixels into [0, 1], zero outside."""
    vals_mask = np.asarray(foot, dtype=bool) if active is None else (np.asarray(foot, dtype=bool) & np.asarray(active, dtype=bool))
    vals_mask = vals_mask & np.isfinite(arr)
    out = np.zeros(arr.shape, dtype=np.float32)
    if not np.any(vals_mask):
        return out
    lo, hi = np.percentile(arr[vals_mask], [q_lo, q_hi])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo + 1e-12:
        return out
    out[vals_mask] = np.clip((arr[vals_mask] - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)
    return out


def frangi_tubular_and_director(
    field_filled: np.ndarray,
    foot: np.ndarray,
    sigma_px: float,
    *,
    beta: float = FRANGI_BETA,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute scale-normalized Frangi tubular ridgeness of ||grad G_sigma(field)|| and
    geographic double-angle strike director ``(cos 2*theta_geo, sin 2*theta_geo)``.

    Geographic strike ``theta_geo`` is measured clockwise from grid North (-row towards +col):
      * N-S ridge (theta_geo = 0 deg)   -> (cos 2*theta, sin 2*theta) = (+1,  0)
      * NE-SW ridge (theta_geo = 45 deg)-> (cos 2*theta, sin 2*theta) = ( 0, +1)
      * E-W ridge (theta_geo = 90 deg)  -> (cos 2*theta, sin 2*theta) = (-1,  0)
      * NW-SE ridge (theta_geo = 135deg)-> (cos 2*theta, sin 2*theta) = ( 0, -1)
    """
    smooth_base = gaussian_filter(np.asarray(field_filled, dtype=np.float32), sigma=float(sigma_px), mode="nearest")
    gy0, gx0 = np.gradient(smooth_base)
    edge_mag = np.hypot(gx0, gy0).astype(np.float32)
    del smooth_base, gy0, gx0

    sigma_hess = max(1.0, 0.5 * float(sigma_px))
    edge_smooth = gaussian_filter(edge_mag, sigma=sigma_hess, mode="nearest")
    del edge_mag

    gy, gx = np.gradient(edge_smooth)
    hyy, hyx = np.gradient(gy)
    hxy, hxx = np.gradient(gx)
    hyx = (0.5 * (hyx + hxy)).astype(np.float32)
    del edge_smooth, gy, gx, hxy

    tr = hxx + hyy
    diff = hyy - hxx
    disc = np.hypot(diff, 2.0 * hyx)
    lam_min = 0.5 * (tr - disc)
    lam_max = 0.5 * (tr + disc)

    # Order eigenvalues by absolute magnitude: |lam1| >= |lam2|.
    abs_min = np.abs(lam_min)
    abs_max = np.abs(lam_max)
    min_dom = abs_min >= abs_max
    lam1 = np.where(min_dom, lam_min, lam_max)
    lam2 = np.where(min_dom, lam_max, lam_min)

    bright_ridge = (lam1 < -1e-12) & np.asarray(foot, dtype=bool)
    rb_sq = np.zeros(hxx.shape, dtype=np.float32)
    rb_sq[bright_ridge] = (lam2[bright_ridge] / (lam1[bright_ridge] - 1e-12)) ** 2

    raw_tubular = np.zeros(hxx.shape, dtype=np.float32)
    scale_factor = float(sigma_px * sigma_px)
    inv_two_beta_sq = 1.0 / (2.0 * float(beta) * float(beta))
    raw_tubular[bright_ridge] = (
        scale_factor * (-lam1[bright_ridge]) * np.exp(-rb_sq[bright_ridge] * inv_two_beta_sq)
    ).astype(np.float32)

    tubular = robust_scale_in_mask(raw_tubular, foot, q_lo=5.0, q_hi=99.0)
    denom = np.maximum(disc, 1e-12).astype(np.float32)
    cos2_geo = np.where(foot, diff / denom, 0.0).astype(np.float32)
    sin2_geo = np.where(foot, (-2.0 * hyx) / denom, 0.0).astype(np.float32)
    return tubular, cos2_geo, sin2_geo


def nematic_concordance_and_harmonic(
    weights: list[np.ndarray],
    cos2_list: list[np.ndarray],
    sin2_list: list[np.ndarray],
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return 4-modality nematic scalar order parameter S in [0, 1] and top-2 harmonic ridgeness."""
    if not (len(weights) == len(cos2_list) == len(sin2_list) >= 2):
        raise ValueError("weights, cos2_list, and sin2_list must have matching length >= 2")
    qx = np.zeros(foot.shape, dtype=np.float32)
    qy = np.zeros(foot.shape, dtype=np.float32)
    wsum = np.zeros(foot.shape, dtype=np.float32)
    for w, c2, s2 in zip(weights, cos2_list, sin2_list):
        qx += w * c2
        qy += w * s2
        wsum += w
    nematic = np.zeros(foot.shape, dtype=np.float32)
    active = np.asarray(foot, dtype=bool) & (wsum > 0.05)
    nematic[active] = np.clip(np.hypot(qx[active], qy[active]) / (wsum[active] + 1e-6), 0.0, 1.0)

    stacked = np.stack(weights, axis=0)
    # Sort descending along axis 0 to take the top two modalities at every pixel.
    part = np.partition(stacked, kth=stacked.shape[0] - 2, axis=0)
    w_second = part[-2]
    w_first = part[-1]
    top2_harm = np.zeros(foot.shape, dtype=np.float32)
    mask = np.asarray(foot, dtype=bool)
    top2_harm[mask] = np.sqrt(np.maximum(w_first[mask] * w_second[mask], 0.0)).astype(np.float32)
    return nematic, top2_harm


def load_wellspring_plumes(
    csv_path: str | Path,
    foot: np.ndarray,
    *,
    sigma_px: float = 15.0,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Build 1.5 km Gaussian hydrothermal plumes from GDR well/spring temperatures & quartz
    geothermometry without EVER reading ``dist_known_fault_px``.
    """
    usecols = ["row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c"]
    assert FORBIDDEN_WELLSPRING_COLUMNS.isdisjoint(usecols)
    df = pd.read_csv(csv_path, usecols=usecols)
    H, W = foot.shape
    rows = np.clip(pd.to_numeric(df["row"], errors="coerce").fillna(-1).to_numpy(dtype=np.int64), 0, H - 1)
    cols = np.clip(pd.to_numeric(df["col"], errors="coerce").fillna(-1).to_numpy(dtype=np.int64), 0, W - 1)
    temp = pd.to_numeric(df["temp_c"], errors="coerce").to_numpy(dtype=np.float32)
    qtz = pd.to_numeric(df["geothermquartz_c"], errors="coerce").to_numpy(dtype=np.float32)
    chalc = pd.to_numeric(df["geothermchalc_c"], errors="coerce").to_numpy(dtype=np.float32)

    chem_t = np.where(np.isfinite(qtz), qtz, chalc)
    meas_base = np.where(np.isfinite(temp), temp, 20.0)
    diseq = np.where(np.isfinite(chem_t), np.maximum(0.0, chem_t - meas_base), 0.0).astype(np.float32)
    temp_anom = np.where(np.isfinite(temp), np.maximum(0.0, temp - 25.0), 0.0).astype(np.float32)

    diseq_grid = np.zeros((H, W), dtype=np.float32)
    temp_grid = np.zeros((H, W), dtype=np.float32)
    np.maximum.at(diseq_grid, (rows, cols), diseq)
    np.maximum.at(temp_grid, (rows, cols), temp_anom)
    diseq_grid[~foot] = 0.0
    temp_grid[~foot] = 0.0

    diseq_plume = robust_scale_in_mask(
        gaussian_filter(diseq_grid, sigma=float(sigma_px), mode="constant", cval=0.0),
        foot,
        q_lo=50.0,
        q_hi=99.5,
    )
    temp_plume = robust_scale_in_mask(
        gaussian_filter(temp_grid, sigma=float(sigma_px), mode="constant", cval=0.0),
        foot,
        q_lo=50.0,
        q_hi=99.5,
    )
    meta = {
        "n_rows": int(len(df)),
        "n_diseq_cells": int((diseq_grid > 0).sum()),
        "n_temp_anom_cells": int((temp_grid > 0).sum()),
        "forbidden_columns_excluded": sorted(FORBIDDEN_WELLSPRING_COLUMNS),
    }
    return diseq_plume, temp_plume, meta


def load_heatflow_residual_plume(
    json_path: str | Path,
    foot: np.ndarray,
    *,
    sigma_px: float = 15.0,
) -> tuple[np.ndarray, dict]:
    """Build 1.5 km Gaussian conductive heat-flow residual plume from USGS P9BZPVUC."""
    payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
    H, W = foot.shape
    hf_grid = np.zeros((H, W), dtype=np.float32)
    n_pos = 0
    for rec in payload.get("records", []):
        if rec.get("source_layer") != "USGS_gbHeatFlowWells_wEstimates.shp":
            continue
        parts = rec.get("parts") or []
        if not parts or not parts[0]:
            continue
        val = rec.get("hf_resid")
        try:
            fval = float(val)
        except (TypeError, ValueError):
            continue
        if not np.isfinite(fval) or fval <= 0.0:
            continue
        x, y = float(parts[0][0][0]), float(parts[0][0][1])
        rr_arr, cc_arr = grid.xy_to_rc(np.array([x]), np.array([y]))
        rr, cc = int(round(float(rr_arr[0]))), int(round(float(cc_arr[0])))
        if 0 <= rr < H and 0 <= cc < W and foot[rr, cc]:
            if fval > hf_grid[rr, cc]:
                hf_grid[rr, cc] = float(min(fval, 500.0))
            n_pos += 1
    plume = robust_scale_in_mask(
        gaussian_filter(hf_grid, sigma=float(sigma_px), mode="constant", cval=0.0),
        foot,
        q_lo=50.0,
        q_hi=99.5,
    )
    return plume, {"n_positive_records_in_footprint": int(n_pos), "n_cells": int((hf_grid > 0).sum())}


def build_s20_feature_stack(
    *,
    prepared_features_path: Path | None = None,
    prepared_meta_path: Path | None = None,
    template_path: Path | None = None,
    lidar_path: Path | None = None,
    extensions_path: Path | None = None,
    wellspring_path: Path | None = None,
    heatflow_json_path: Path | None = None,
    out_npy_path: Path | None = None,
) -> dict:
    """Materialize the 28-column ``s20_nchc_features.npy`` from the cached template feature stack
    and SHA-verified label-free extensions, streaming column-by-column under 500 MB RAM.
    """
    feat_path = prepared_features_path or paths.PREPARED_FEATURES
    meta_path = prepared_meta_path or paths.PREPARED_META
    tmpl_path = template_path or paths.TEMPLATE
    lid_path = lidar_path or paths.LIDAR
    ext_path = extensions_path or paths.EXTENSIONS
    ws_path = wellspring_path or paths.WELLSPRING
    hf_path = heatflow_json_path or paths.SB_HEAT_FLOW_JSON
    out_path = out_npy_path or (feat_path.parent / "s20_nchc_features.npy")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    band_names: list[str] = list(meta["names"])
    idx_map = {name: i for i, name in enumerate(band_names)}
    foot = grid.load_footprint(tmpl_path)
    ys, xs = np.nonzero(foot)
    n_foot = int(ys.size)
    base_X = np.load(feat_path, mmap_mode="r")
    if base_X.shape[0] != n_foot:
        raise ValueError(f"Footprint mismatch: {base_X.shape[0]} vs {n_foot}")

    def unpack_band(name: str) -> np.ndarray:
        arr2d = np.full(foot.shape, np.nan, dtype=np.float32)
        arr2d[ys, xs] = base_X[:, idx_map[name]]
        return nearest_fill_2d(arr2d, foot)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    X_out = np.lib.format.open_memmap(
        out_path, mode="w+", dtype=np.float32, shape=(n_foot, len(S20_FEATURE_NAMES))
    )
    col_idx = {name: i for i, name in enumerate(S20_FEATURE_NAMES)}

    def write_col(name: str, arr2d: np.ndarray) -> None:
        vals = np.asarray(arr2d[ys, xs], dtype=np.float32)
        if not np.isfinite(vals).all():
            raise ValueError(f"Non-finite values in S20 feature {name}")
        X_out[:, col_idx[name]] = vals

    # 1. Magnetics (rtp): 150 m, 400 m, 1000 m + E-W flight-line artifact diagnostic
    rtp_fill = unpack_band("rtp")
    mag_150, mag_c150, _ = frangi_tubular_and_director(rtp_fill, foot, 1.5)
    write_col("mag_tubular_150m", mag_150)
    ew_stripe = np.where(foot, mag_150 * (np.maximum(0.0, -mag_c150) ** 2), 0.0).astype(np.float32)
    write_col("geodawn_ew_stripe_150m", ew_stripe)
    del mag_150, mag_c150, ew_stripe

    mag_400, mag_c400, mag_s400 = frangi_tubular_and_director(rtp_fill, foot, 4.0)
    mag_1000, mag_c1000, mag_s1000 = frangi_tubular_and_director(rtp_fill, foot, 10.0)
    write_col("mag_tubular_400m", mag_400)
    write_col("mag_tubular_1000m", mag_1000)

    # 2. Isostatic gravity: 400 m, 1000 m
    grav_fill = unpack_band("iso_grav_anom")
    grav_400, grav_c400, grav_s400 = frangi_tubular_and_director(grav_fill, foot, 4.0)
    grav_1000, grav_c1000, grav_s1000 = frangi_tubular_and_director(grav_fill, foot, 10.0)
    del grav_fill
    write_col("grav_tubular_400m", grav_400)
    write_col("grav_tubular_1000m", grav_1000)

    # 3. Subsurface conductive base interface: 400 m, 1000 m
    cb_fill = unpack_band("depth_to_base_surf")
    cb_400, cb_c400, cb_s400 = frangi_tubular_and_director(cb_fill, foot, 4.0)
    cb_1000, cb_c1000, cb_s1000 = frangi_tubular_and_director(cb_fill, foot, 10.0)
    del cb_fill
    write_col("em_cb_tubular_400m", cb_400)
    write_col("em_cb_tubular_1000m", cb_1000)

    # 4. Detrended piedmont topography: 150 m, 400 m, 1000 m
    topo_fill = unpack_band("det_elev")
    topo_150, _, _ = frangi_tubular_and_director(topo_fill, foot, 1.5)
    write_col("topo_tubular_150m", topo_150)
    del topo_150
    topo_400, topo_c400, topo_s400 = frangi_tubular_and_director(topo_fill, foot, 4.0)
    topo_1000, topo_c1000, topo_s1000 = frangi_tubular_and_director(topo_fill, foot, 10.0)
    del topo_fill
    write_col("topo_tubular_400m", topo_400)
    write_col("topo_tubular_1000m", topo_1000)

    # 5 & 6. 4-Modality Nematic Director Order Parameter & Top-2 Cross-Modal Harmonic Ridgeness
    nem_400, harm_400 = nematic_concordance_and_harmonic(
        [mag_400, grav_400, cb_400, topo_400],
        [mag_c400, grav_c400, cb_c400, topo_c400],
        [mag_s400, grav_s400, cb_s400, topo_s400],
        foot,
    )
    write_col("nematic_order_400m", nem_400)
    write_col("top2_harmonic_400m", harm_400)
    del mag_400, grav_400, cb_400, topo_400, mag_c400, grav_c400, cb_c400, topo_c400
    del mag_s400, grav_s400, cb_s400, topo_s400, nem_400, harm_400

    nem_1000, harm_1000 = nematic_concordance_and_harmonic(
        [mag_1000, grav_1000, cb_1000, topo_1000],
        [mag_c1000, grav_c1000, cb_c1000, topo_c1000],
        [mag_s1000, grav_s1000, cb_s1000, topo_s1000],
        foot,
    )
    write_col("nematic_order_1000m", nem_1000)
    write_col("top2_harmonic_1000m", harm_1000)
    del mag_1000, grav_1000, cb_1000, topo_1000, mag_c1000, grav_c1000, cb_c1000, topo_c1000
    del mag_s1000, grav_s1000, cb_s1000, topo_s1000, nem_1000, harm_1000

    # 8 & 10-11. GeoDAWN extensions: TMI_up150 shallow-source differential & ThK / UTh alteration
    with rasterio.open(ext_path) as ext_ds:
        thk_u8 = ext_ds.read(1)
        uth_u8 = ext_ds.read(3)
        up150_u8 = ext_ds.read(4)

    up_valid = foot & (up150_u8 > 0)
    rtp_mu, rtp_sd = float(rtp_fill[up_valid].mean()), float(rtp_fill[up_valid].std() + 1e-6)
    up_f = up150_u8.astype(np.float32)
    up_mu, up_sd = float(up_f[up_valid].mean()), float(up_f[up_valid].std() + 1e-6)
    shallow_diff = np.zeros(foot.shape, dtype=np.float32)
    shallow_diff[up_valid] = ((rtp_fill[up_valid] - rtp_mu) / rtp_sd) - ((up_f[up_valid] - up_mu) / up_sd)
    shallow_fill = nearest_fill_2d(shallow_diff, up_valid)
    sgy, sgx = np.gradient(gaussian_filter(shallow_fill, sigma=3.0, mode="nearest"))
    write_col("mag_up150_step_300m", robust_scale_in_mask(np.hypot(sgx, sgy), foot, active=up_valid))
    del rtp_fill, up150_u8, up_f, shallow_diff, shallow_fill, sgy, sgx, up_valid

    rad_valid = foot & (thk_u8 > 0) & (uth_u8 > 0)
    thk_fill = nearest_fill_2d(thk_u8.astype(np.float32), rad_valid)
    k_metasom = gaussian_filter(thk_fill, sigma=20.0, mode="nearest") - gaussian_filter(
        thk_fill, sigma=2.0, mode="nearest"
    )
    write_col("rad_k_metasom_local", robust_scale_in_mask(k_metasom, foot, q_lo=10.0, q_hi=99.0, active=rad_valid))
    del thk_u8, thk_fill, k_metasom

    uth_fill = nearest_fill_2d(uth_u8.astype(np.float32), rad_valid)
    ugy, ugx = np.gradient(gaussian_filter(uth_fill, sigma=3.0, mode="nearest"))
    write_col("rad_uth_redox_step_300m", robust_scale_in_mask(np.hypot(ugx, ugy), foot, active=rad_valid))
    write_col("rad_valid_flag", rad_valid.astype(np.float32))
    del uth_u8, uth_fill, ugy, ugx, rad_valid

    # 9. Smectite clay-cap lateral margin gradient (cond_surf)
    cond_fill = unpack_band("cond_surf")
    cgy, cgx = np.gradient(gaussian_filter(cond_fill, sigma=4.0, mode="nearest"))
    write_col("claycap_margin_400m", robust_scale_in_mask(np.hypot(cgx, cgy), foot))
    del cond_fill, cgy, cgx

    # 12. Hydrothermal well/spring silica disequilibrium, thermal anomaly, and heat-flow residual plumes
    diseq_plume, temp_plume, ws_meta = load_wellspring_plumes(ws_path, foot, sigma_px=15.0)
    hf_plume, hf_meta = load_heatflow_residual_plume(hf_path, foot, sigma_px=15.0)
    write_col("hydro_qtz_diseq_1500m", diseq_plume)
    write_col("hydro_temp_anom_1500m", temp_plume)
    write_col("hydro_hf_resid_1500m", hf_plume)
    del diseq_plume, temp_plume, hf_plume

    # 13. Strain-rate gradient, dilatation rate, and seismicity intensity
    strain_fill = unpack_band("geod_2ndinv")
    st_gy, st_gx = np.gradient(gaussian_filter(strain_fill, sigma=10.0, mode="nearest"))
    write_col("strain_2ndinv_grad_1000m", robust_scale_in_mask(np.hypot(st_gx, st_gy), foot))
    del strain_fill, st_gy, st_gx

    dil_fill = unpack_band("geod_dilaterate")
    write_col("strain_dilate_norm", robust_scale_in_mask(dil_fill, foot, q_lo=2.0, q_hi=98.0))
    del dil_fill

    ieq_fill = unpack_band("ieq_n100a15")
    write_col("seis_ieq_norm", robust_scale_in_mask(ieq_fill, foot, q_lo=5.0, q_hi=99.0))
    del ieq_fill

    # 14. 1 m LiDAR composite scarp prominence & explicit coverage flag
    with rasterio.open(lid_path) as lid_ds:
        valid_2d = foot & (lid_ds.read(12) > 0)
    lidar_valid_1d = valid_2d[ys, xs]
    lidar_step_1d = np.nan_to_num(base_X[:, idx_map["lidar_step_max"]].astype(np.float32), nan=0.0)
    lidar_coh_1d = np.clip(
        np.nan_to_num(base_X[:, idx_map["lidar_coh100"]].astype(np.float32), nan=0.0) / 255.0,
        0.0,
        1.0,
    )
    step_2d = np.zeros(foot.shape, dtype=np.float32)
    step_2d[ys, xs] = np.where(lidar_valid_1d, lidar_step_1d * (0.5 + 0.5 * lidar_coh_1d), 0.0)
    write_col("lidar_scarp_composite", robust_scale_in_mask(step_2d, foot, active=valid_2d))
    write_col("lidar_valid_flag", valid_2d.astype(np.float32))
    del step_2d, valid_2d, lidar_valid_1d, lidar_step_1d, lidar_coh_1d

    X_out.flush()
    X_out = None

    digest = hashlib.sha256()
    with out_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            digest.update(chunk)
    return {
        "path": str(out_path),
        "shape": [n_foot, len(S20_FEATURE_NAMES)],
        "dtype": "float32",
        "sha256": digest.hexdigest(),
        "feature_names": list(S20_FEATURE_NAMES),
        "wellspring_meta": ws_meta,
        "heatflow_meta": hf_meta,
    }


def fit_predict_prior_calibrated_hgb(
    X_foot: np.ndarray,
    foot: np.ndarray,
    train_mask_2d: np.ndarray,
    pos_mask_2d: np.ndarray,
    *,
    seed: int,
    max_neg: int = MAX_NEG_PER_FOLD,
) -> tuple[np.ndarray, dict]:
    """Fit ``HistGradientBoostingClassifier`` strictly on ``train_mask_2d`` with prior-preserving
    negative importance weights and predict continuous fault-corridor probabilities on ``foot``.
    """
    train_1d = np.asarray(train_mask_2d[foot], dtype=bool)
    pos_1d = np.asarray((train_mask_2d & pos_mask_2d)[foot], dtype=bool)
    neg_1d = train_1d & ~pos_1d

    pos_idx = np.flatnonzero(pos_1d)
    neg_idx = np.flatnonzero(neg_1d)
    if pos_idx.size == 0 or neg_idx.size == 0:
        raise ValueError(f"Training split lacks positives ({pos_idx.size}) or negatives ({neg_idx.size})")

    rng = np.random.default_rng(int(seed))
    if neg_idx.size > max_neg:
        neg_take = np.sort(rng.choice(neg_idx, size=int(max_neg), replace=False))
        neg_weight = float(neg_idx.size) / float(neg_take.size)
    else:
        neg_take = neg_idx
        neg_weight = 1.0

    sel = np.concatenate([pos_idx, neg_take])
    y_train = np.concatenate([
        np.ones(pos_idx.size, dtype=np.int32),
        np.zeros(neg_take.size, dtype=np.int32),
    ])
    sample_weight = np.concatenate([
        np.ones(pos_idx.size, dtype=np.float32),
        np.full(neg_take.size, neg_weight, dtype=np.float32),
    ])
    X_train = np.asarray(X_foot[sel], dtype=np.float32)

    clf = HistGradientBoostingClassifier(
        loss="log_loss",
        learning_rate=0.05,
        max_iter=300,
        max_leaf_nodes=63,
        max_depth=6,
        min_samples_leaf=100,
        l2_regularization=5.0,
        random_state=int(seed),
    )
    clf.fit(X_train, y_train, sample_weight=sample_weight)
    del X_train, y_train, sample_weight

    n_foot = X_foot.shape[0]
    prob_1d = np.empty(n_foot, dtype=np.float32)
    for start in range(0, n_foot, PREDICT_CHUNK_ROWS):
        stop = min(start + PREDICT_CHUNK_ROWS, n_foot)
        prob_1d[start:stop] = clf.predict_proba(np.asarray(X_foot[start:stop], dtype=np.float32))[:, 1].astype(
            np.float32
        )

    prob_2d = np.zeros(foot.shape, dtype=np.float32)
    prob_2d[foot] = prob_1d
    info = {
        "seed": int(seed),
        "n_train_pos": int(pos_idx.size),
        "n_train_neg_total": int(neg_idx.size),
        "n_train_neg_sampled": int(neg_take.size),
        "neg_importance_weight": float(neg_weight),
        "n_iter": int(clf.n_iter_),
    }
    return prob_2d, info


def allocate_corridor_submodular(
    prob_2d: np.ndarray,
    domain_mask_2d: np.ndarray,
    visible_catalogue_2d: np.ndarray,
    *,
    budget_frac: float = BUDGET_FRAC_FOOTPRINT,
    corridor_quantile: float = CORRIDOR_QUANTILE,
    clearance_px: float = CATALOGUE_CLEARANCE_PX,
    radius_px: float = KERNEL_RADIUS_PX,
) -> tuple[np.ndarray, dict]:
    """Allocate binary dots inside ``domain_mask_2d`` using strictly visible-only ``B=2`` clearance
    and ``gems27.packing.coverage_greedy`` over the top corridor quantile.
    """
    domain = np.asarray(domain_mask_2d, dtype=bool)
    vis = np.asarray(visible_catalogue_2d, dtype=bool)
    if np.any(vis):
        d_vis = distance_transform_edt(~vis)
        allowed = domain & (d_vis > float(clearance_px))
    else:
        allowed = domain.copy()

    n_domain = int(domain.sum())
    n_target = int(round(float(budget_frac) * n_domain))
    if n_target <= 0 or not np.any(allowed):
        return np.zeros(prob_2d.shape, dtype=np.float32), {
            "n_domain": n_domain,
            "n_target": n_target,
            "n_candidates": 0,
            "n_selected": 0,
            "corridor_cut": None,
        }

    corridor_cut = float(np.quantile(prob_2d[allowed], float(corridor_quantile)))
    candidates = allowed & (prob_2d >= corridor_cut) & (prob_2d > 0.0)
    weight = np.where(candidates, prob_2d, 0.0).astype(np.float32)
    selected = packing.coverage_greedy(candidates, weight, n_target=n_target, radius_px=float(radius_px))
    pred = selected.astype(np.float32)
    return pred, {
        "n_domain": n_domain,
        "n_target": n_target,
        "n_candidates": int(candidates.sum()),
        "n_selected": int(selected.sum()),
        "corridor_cut": corridor_cut,
    }
