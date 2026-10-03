"""Hydrothermal-discharge layer (GDR submission 1391, INGENIOUS) as an *independent* physical signal.

Why this layer is admissible for a far-field *addition* arm
----------------------------------------------------------
Every arm in this repository that transferred an attribute *from* the published fault catalogue *to*
off-catalogue candidates inherited the same ceiling: H33-1 measured only `11.95 %` of emitted dots
within 1 km of a catalogued segment, because candidate dots are emitted off-catalogue *by design*
(`knowledge/21_result_H33-1_refuted_2026-10-03.md` §2). A layer that is not derived from the fault
catalogue cannot inherit that ceiling.

Thermal springs and wells are exactly such a layer. They are a **point process**: a surface
expression of *subsurface permeability*. The competition's label set is a *surface-rupture*
(neotectonic) catalogue; a structure that transmits geothermal fluid but has no mapped Quaternary
scarp is systematically under-represented in it. That is the class the reachability frontier says the
programme must find (`evidence/reachability_frontier.json`: the gap to `0.3195` is ~`1,150` px of
credit that only *added detections* can supply).

Column audit (this is the whole point of the module)
---------------------------------------------------
`gdr_wellspring_in_footprint.csv` carries a `dist_known_fault_px` column that is derived from the
published catalogue. It is **never read** by this module: `SITE_COLUMNS` is an explicit allow-list and
`audit_frame` raises if a catalogue-derived column is requested. Coordinates (`row`, `col`) come from
the GDR record geometry, and `verify_geometry` re-derives them from `utm_x` / `utm_y` through the
competition geotransform so a mis-registered table cannot silently pass.

Provenance and rights
---------------------
Source: GDR submission 1391 (INGENIOUS project, U.S. DOE Office of Energy Efficiency & Renewable
Energy Geothermal Data Repository), mirrored as a hash-pinned public file in `data/` per
`registry/data_manifest.json`. The mirror is integrity-pinned but **not organizer-authenticated**;
`docs/data/sources.csv` and `registry/sources.json` record the official landing page for manual
review. Thermal classes are reported as published; the module does not reinterpret them.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import distance_transform_edt

from . import grid

# Explicit allow-list. `dist_known_fault_px` is catalogue-derived and deliberately absent.
SITE_COLUMNS = ("layer", "name", "thermalclass", "row", "col", "utm_x", "utm_y",
                "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c")
CATALOGUE_DERIVED_COLUMNS = ("dist_known_fault_px",)

# Frozen thresholds for H35-1 (written into knowledge/23 before the run).
TEMP_CUT_PRIMARY_C = 20.0
TEMP_CUT_DOSE_C = 50.0
GEOTHERM_CUT_DOSE_C = 100.0
NEAR_PX_PRIMARY = 3  # 300 m == the DTI kernel radius
NEAR_PX_DOSE = (1, 6)


class ThermalDataError(RuntimeError):
    """Raised when the thermal layer cannot be read or fails a registration check."""


def audit_frame(df: pd.DataFrame) -> dict:
    """Schema/registration audit of a raw GDR frame. Raises on a missing required column."""
    missing = [c for c in SITE_COLUMNS if c not in df.columns]
    if missing:
        raise ThermalDataError(f"thermal table missing required columns: {missing}")
    if not np.isfinite(df[["utm_x", "utm_y"]].to_numpy(float)).all():
        raise ThermalDataError("thermal table has non-finite coordinates")
    rows = ((grid.TRANSFORM[5] - df["utm_y"].to_numpy(float)) / -grid.TRANSFORM[4])
    cols = ((df["utm_x"].to_numpy(float) - grid.TRANSFORM[2]) / grid.TRANSFORM[0])
    d_row = np.abs(np.round(rows) - df["row"].to_numpy(float))
    d_col = np.abs(np.round(cols) - df["col"].to_numpy(float))
    return {
        "n_records_raw": int(len(df)),
        "max_abs_row_residual_px": float(d_row.max()),
        "max_abs_col_residual_px": float(d_col.max()),
        "registration_ok": bool(d_row.max() <= 1.0 and d_col.max() <= 1.0),
        "n_unique_locations": int(df.drop_duplicates(subset=["utm_x", "utm_y"]).shape[0]),
    }


def load_sites(path: Path | str) -> pd.DataFrame:
    """Load the GDR well/spring table with the catalogue-derived column dropped, deduped by location.

    Returns one row per unique site, carrying the *maximum* reported temperature and the *maximum*
    reported geothermometer value across the layers that describe it, so a site is not understated by
    the layer that happens to carry a blank.
    """
    raw = pd.read_csv(path, low_memory=False)
    audit = audit_frame(raw)
    if not audit["registration_ok"]:
        raise ThermalDataError(
            f"thermal table is not on the competition grid: {audit}"
        )
    keep = [c for c in SITE_COLUMNS if c in raw.columns]
    drop = [c for c in CATALOGUE_DERIVED_COLUMNS if c in raw.columns]
    df = raw.drop(columns=drop)[keep].copy()
    for c in ("temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    agg = (
        df.groupby(["utm_x", "utm_y"], as_index=False)
        .agg(
            row=("row", "median"),
            col=("col", "median"),
            temp_c=("temp_c", "max"),
            geothermquartz_c=("geothermquartz_c", "max"),
            geothermchalc_c=("geothermchalc_c", "max"),
            geothermcat_c=("geothermcat_c", "max"),
            n_records=("layer", "size"),
            layers=("layer", lambda s: "|".join(sorted(set(s)))),
        )
        .sort_values(["row", "col"])
        .reset_index(drop=True)
    )
    agg["row"] = agg["row"].round().astype(int)
    agg["col"] = agg["col"].round().astype(int)
    agg.attrs["audit"] = audit
    return agg


def sites_mask(sites: pd.DataFrame, footprint: np.ndarray, *, temp_c_min: float | None = None,
               geotherm_c_min: float | None = None) -> np.ndarray:
    """Rasterise qualifying sites to a boolean grid on the competition template."""
    sub = sites
    if temp_c_min is not None:
        sub = sub[sub["temp_c"].notna() & (sub["temp_c"] >= float(temp_c_min))]
    if geotherm_c_min is not None:
        g = sub[["geothermquartz_c", "geothermchalc_c", "geothermcat_c"]].max(axis=1)
        sub = sub[g.notna() & (g >= float(geotherm_c_min))]
    out = np.zeros(grid.SHAPE, bool)
    r = sub["row"].to_numpy(int)
    c = sub["col"].to_numpy(int)
    inside = (r >= 0) & (r < grid.SHAPE[0]) & (c >= 0) & (c < grid.SHAPE[1])
    out[r[inside], c[inside]] = True
    return out & footprint


def distance_to_sites(mask: np.ndarray) -> np.ndarray:
    """Euclidean distance in pixels to the nearest qualifying site (0 on a site)."""
    return distance_transform_edt(~np.asarray(mask, bool)).astype(np.float32)


def credit_contributions(dots: np.ndarray, truth: np.ndarray) -> np.ndarray:
    """Per-truth-pixel kernel credit of an emission: `k(d(g, dots))` for every truth pixel `g`."""
    dots = np.asarray(dots, bool)
    truth = np.asarray(truth, bool)
    if dots.shape != truth.shape:
        raise ValueError("dots and truth must be equal-shaped grids")
    if not truth.any():
        return np.zeros(0, np.float32)
    if not dots.any():
        return np.zeros(int(truth.sum()), np.float64)
    d = distance_transform_edt(~dots)[truth]
    # float64 deliberately: a marginal gain can be a small difference of two ~O(1e3) sums.
    return np.maximum(1.0 - d / grid.KERNEL_RADIUS_PX, 0.0).astype(np.float64)


def marginal_credit(base: np.ndarray, adds: np.ndarray, truth: np.ndarray) -> float:
    """Credit gained by adding `adds` to `base`, without double counting shared truth pixels."""
    if not np.asarray(adds, bool).any():
        return 0.0
    return float(credit_contributions(np.asarray(base, bool) | np.asarray(adds, bool), truth).sum()
                 - credit_contributions(base, truth).sum())


def stratify(dots: np.ndarray, mask: np.ndarray, *, near_px: float) -> tuple[np.ndarray, np.ndarray]:
    """Split dots into (near a qualifying site, not near one) by raster distance."""
    d = distance_to_sites(mask)
    ys, xs = np.nonzero(np.asarray(dots, bool))
    near = d[ys, xs] <= float(near_px)
    return np.c_[ys[near], xs[near]], np.c_[ys[~near], xs[~near]]
