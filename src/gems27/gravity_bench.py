"""Buried range-front gravity-bench masks for the H35-4 ADD arm (Session 11).

Pure, deterministic, label-free transforms. A bench pixel couples a strong isostatic-gravity
horizontal gradient (a basement density step seen through the fanglomerate apron) with low LiDAR
scarp amplitude and low local relief (no preserved surface rupture). A mesa pixel is the known
H19-5 false-positive mode: a contour-following erosional volcanic rim with a crisp LiDAR step and
a magnetic edge but no basement density step; both H35-4 arms exclude it as a shared quality
floor, so the gate tests bench-vs-non-bench rather than bench-vs-known-junk.

Band names below are the CORRECTED names (registry/irregularities.json
`lidar-feature-name-mismatch`): the Session-8 H32-3 sketch cited `lidar_step_max`/`lidar_rough50`
at positions 2/5, but the embedded raster descriptions (asserted by scripts/prepare_data.py) put
`step_max` at band 3 and carry no roughness band at all - `relief` (band 9) is the texture leg.

Frozen constants live in `knowledge/26_preregistration_H35-4.md`; this module takes them as
explicit arguments with the frozen values as defaults.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio

SENTINEL = 1e30  # frozen training-raster validity rule (|v| < 1e30), cf. H32-2 run-1 lesson

# Raster bands, 1-based (embedded descriptions asserted by scripts/prepare_data.py).
GRAV_BAND = 18   # iso_grav_anom_hg
TMI_BAND = 3     # tmi_hg
STEP_BAND = 3    # step_max
RELIEF_BAND = 9  # relief
VALID_BAND = 12  # valid (255 = valid, 0 = invalid, 1-254 = edge artifacts)

# Frozen by knowledge/26 (H35-4 preregistration).
GRAV_Q = 75.0        # bench needs grav_hg >= p75 (over footprint-valid)
STEP_Q = 50.0        # bench needs step_max <= p50 (over lidar-valid footprint)
RELIEF_Q = 50.0      # bench needs relief <= p50 (over lidar-valid footprint)
MESA_STEP_Q = 90.0   # mesa exclusion: step_max >= p90 ...
MESA_TMI_Q = 90.0    # ... tmi_hg >= p90 ...
MESA_GRAV_Q = 50.0   # ... grav_hg <= p50 (no basement step under the rim)
BUDGET_FRAC = 0.03   # additions = 3% of base dots (noise-sized from H35-1, see prereg)
THIN_D = 2.8
FAR_PX = 3.0


def training_valid(arr: np.ndarray) -> np.ndarray:
    """Frozen validity rule for training_features bands: finite and below the sentinel."""
    a = np.asarray(arr, dtype=np.float64)
    return np.isfinite(a) & (np.abs(a) < SENTINEL)


def lidar_valid(valid_band: np.ndarray) -> np.ndarray:
    """LiDAR coverage: the `valid` band is 255 on valid terrain, 0 off it.

    Verified this session: valid>0 covers 75.37% of the footprint and agrees with step_max>0 at
    99.97%, i.e. step_max = 0 marks invalid terrain in practice (no flat-valid ambiguity).
    """
    return np.asarray(valid_band) > 0


def bench_mesa(*, grav: np.ndarray, tmi: np.ndarray, step: np.ndarray,
               relief: np.ndarray, valid: np.ndarray, foot: np.ndarray,
               grav_q: float = GRAV_Q, step_q: float = STEP_Q, relief_q: float = RELIEF_Q,
               mesa_step_q: float = MESA_STEP_Q, mesa_tmi_q: float = MESA_TMI_Q,
               mesa_grav_q: float = MESA_GRAV_Q) -> dict:
    """Build the bench and mesa masks. Quantiles are over valid footprint pixels, label-free."""
    foot = np.asarray(foot, bool)
    gv = training_valid(grav) & foot
    tv = training_valid(tmi) & foot
    lv = lidar_valid(valid) & foot
    if not gv.any() or not tv.any() or not lv.any():
        z = np.zeros(foot.shape, bool)
        return {"bench": z, "mesa": z, "cuts": {}, "fracs": {"bench": 0.0, "mesa": 0.0}}
    g = np.asarray(grav, dtype=np.float64)
    t = np.asarray(tmi, dtype=np.float64)
    s = np.asarray(step, dtype=np.float64)
    r = np.asarray(relief, dtype=np.float64)
    cuts = {
        "grav_hi": float(np.quantile(g[gv], grav_q / 100.0)),
        "grav_lo": float(np.quantile(g[gv], mesa_grav_q / 100.0)),
        "tmi_hi": float(np.quantile(t[tv], mesa_tmi_q / 100.0)),
        "step_lo": float(np.quantile(s[lv], step_q / 100.0)),
        "step_hi": float(np.quantile(s[lv], mesa_step_q / 100.0)),
        "relief_lo": float(np.quantile(r[lv], relief_q / 100.0)),
    }
    bench = lv & gv & (g >= cuts["grav_hi"]) & (s <= cuts["step_lo"]) & (r <= cuts["relief_lo"])
    mesa = lv & gv & tv & (s >= cuts["step_hi"]) & (t >= cuts["tmi_hi"]) & (g <= cuts["grav_lo"])
    n_foot = int(foot.sum())
    return {"bench": bench, "mesa": mesa & ~bench, "cuts": cuts,
            "fracs": {"bench": float(bench.sum() / n_foot),
                      "mesa": float((mesa & ~bench).sum() / n_foot),
                      "lidar_valid": float(lv.sum() / n_foot)}}


def load_gravity_bench(training_path: str | Path, lidar_path: str | Path,
                       footprint: np.ndarray) -> dict:
    """Read the frozen H35-4 legs from the local rasters (label-free, no truth contact).

    Band indices are fail-loud: the embedded descriptions must match the CORRECTED names or
    this raises instead of silently ranking on the wrong physics.
    """
    def short(d: str | None) -> str:
        # Same normalization as scripts/prepare_data.py: 'name - long gloss' -> 'name'.
        return (d or "").split(" - ")[0].strip()

    foot = np.asarray(footprint, bool)
    with rasterio.open(training_path) as src:
        desc = [short(d) for d in src.descriptions]
        if desc[GRAV_BAND - 1] != "iso_grav_anom_hg":
            raise AssertionError(f"training band {GRAV_BAND} is {desc[GRAV_BAND - 1]!r}, "
                                 "expected 'iso_grav_anom_hg' - band layout drifted")
        if desc[TMI_BAND - 1] != "tmi_hg":
            raise AssertionError(f"training band {TMI_BAND} is {desc[TMI_BAND - 1]!r}, "
                                 "expected 'tmi_hg' - band layout drifted")
        grav = src.read(GRAV_BAND).astype(np.float64)
        tmi = src.read(TMI_BAND).astype(np.float64)
    with rasterio.open(lidar_path) as src:
        desc = [short(d) for d in src.descriptions]
        for band, want in ((STEP_BAND, "step_max"), (RELIEF_BAND, "relief"),
                           (VALID_BAND, "valid")):
            if desc[band - 1] != want:
                raise AssertionError(f"lidar band {band} is {desc[band - 1]!r}, expected "
                                     f"{want!r} - band layout drifted")
        step = src.read(STEP_BAND).astype(np.float64)
        relief = src.read(RELIEF_BAND).astype(np.float64)
        valid = src.read(VALID_BAND)
    out = bench_mesa(grav=grav, tmi=tmi, step=step, relief=relief, valid=valid, foot=foot)
    cuts = out["cuts"]
    return {"bench": out["bench"], "mesa": out["mesa"], "grav_hg": grav,
            "bench_px": int(out["bench"].sum()), "mesa_px": int(out["mesa"].sum()),
            "bench_frac_of_footprint": out["fracs"]["bench"],
            "mesa_frac_of_footprint": out["fracs"]["mesa"],
            "lidar_valid_frac_of_footprint": out["fracs"]["lidar_valid"],
            "grav_cut": cuts["grav_hi"], "step_cut": cuts["step_lo"],
            "relief_cut": cuts["relief_lo"], "step_hi_cut": cuts["step_hi"],
            "tmi_hi_cut": cuts["tmi_hi"], "grav_lo_cut": cuts["grav_lo"],
            "training_bands": {"grav_hg": GRAV_BAND, "tmi_hg": TMI_BAND},
            "lidar_bands": {"step_max": STEP_BAND, "relief": RELIEF_BAND,
                            "valid": VALID_BAND}}
