"""Depth-sliced potential-field lineaments (H39-1, Session 15; frozen in knowledge/47).

Upward continuation is the standard Fourier-domain potential-field transform (Blakely 1995,
*Potential Theory in Gravity and Magnetic Applications*): observing the same field from a
height ``h`` multiplies each Fourier component by ``exp(-|k| h)``, so short-wavelength
(shallow) sources attenuate fastest. A horizontal-gradient (HG) ridge that survives from the
surface to a 2 km continuation level is therefore evidence of a deep-rooted contact; one that
vanishes was shallow. This module turns that into five **label-free** bands from the
competition stack's ``tmi`` (band 14) and ``iso_grav_anom`` (band 13) fields:

  tmi_hg_up1000   HG magnitude of TMI upward-continued 1 km
  tmi_hg_up2000   HG magnitude of TMI upward-continued 2 km
  tmi_persist     hg2000 / (hg2000 + hg_shallow) in [0, 1]  (bounded persistence ratio;
                  hg_shallow = HG of TMI smoothed at sigma = 1 px)
  tmi_tilt_up1000 tilt angle atan2(dT/dz, HG) at the 1 km level, radians in [-pi/2, pi/2]
  grav_hg_up2000  HG magnitude of isostatic gravity anomaly upward-continued 2 km

Named non-fault mimic (knowledge/47): basement lithologic contacts and mafic dike swarms
also produce deep-persistent HG lineaments with zero Quaternary slip.

No function here reads labels or any catalogue-derived raster, so the bands cannot leak
held-out fault systems into a LOSFO split. Invalid/outside-footprint cells are filled by
nearest valid value before the FFT (the same convention as scripts/prepare_data.py) and the
grid is reflection-padded to suppress wrap-around; bands are only ever consumed inside the
footprint. The transform is verified against the analytic exp(-|k|h) decay in
tests/test_depthslice.py.
"""

from __future__ import annotations

import numpy as np
import rasterio
from scipy import fft as sfft
from scipy.ndimage import distance_transform_edt, gaussian_filter

from . import grid

BAND_NAMES = ["tmi_hg_up1000", "tmi_hg_up2000", "tmi_persist", "tmi_tilt_up1000", "grav_hg_up2000"]
UP_HEIGHTS_M = (1000.0, 2000.0)
PAD_PX = 256


def fill_nearest(field: np.ndarray, valid: np.ndarray) -> np.ndarray:
    field = np.asarray(field, dtype=np.float64)
    valid = np.asarray(valid, bool) & np.isfinite(field)
    if not valid.any():
        raise ValueError("no valid cells to fill from")
    if valid.all():
        return field.copy()
    inds = distance_transform_edt(~valid, return_distances=False, return_indices=True)
    return field[tuple(inds)]


def _wavenumber_mag(shape: tuple[int, int], pixel_m: float) -> np.ndarray:
    """|k| in rad/m on the rfft2 frequency grid."""
    H, W = shape
    ky = 2.0 * np.pi * sfft.fftfreq(H, d=pixel_m)
    kx = 2.0 * np.pi * sfft.rfftfreq(W, d=pixel_m)
    return np.sqrt(ky[:, None] ** 2 + kx[None, :] ** 2)


def upward_continue(field: np.ndarray, h_m: float, pixel_m: float = grid.PIXEL_M,
                    pad_px: int = PAD_PX) -> np.ndarray:
    """Upward-continue a complete (filled) field by ``h_m`` metres. Same shape out."""
    f = np.asarray(field, dtype=np.float64)
    if not np.isfinite(f).all():
        raise ValueError("upward_continue needs a filled, finite field")
    p = int(pad_px)
    fp = np.pad(f - f.mean(), p, mode="reflect") if p else f - f.mean()
    F = sfft.rfft2(fp)
    F *= np.exp(-_wavenumber_mag(fp.shape, pixel_m) * float(h_m))
    out = sfft.irfft2(F, s=fp.shape) + f.mean()
    return out[p:p + f.shape[0], p:p + f.shape[1]] if p else out


def vertical_derivative_up(field: np.ndarray, h_m: float, pixel_m: float = grid.PIXEL_M,
                           pad_px: int = PAD_PX) -> np.ndarray:
    """dT/dz of the field upward-continued by ``h_m`` (Fourier multiplier |k| e^{-|k|h})."""
    f = np.asarray(field, dtype=np.float64)
    if not np.isfinite(f).all():
        raise ValueError("vertical_derivative_up needs a filled, finite field")
    p = int(pad_px)
    fp = np.pad(f - f.mean(), p, mode="reflect") if p else f - f.mean()
    k = _wavenumber_mag(fp.shape, pixel_m)
    out = sfft.irfft2(sfft.rfft2(fp) * k * np.exp(-k * float(h_m)), s=fp.shape)
    return out[p:p + f.shape[0], p:p + f.shape[1]] if p else out


def hg_mag(field: np.ndarray, pixel_m: float = grid.PIXEL_M) -> np.ndarray:
    gy, gx = np.gradient(np.asarray(field, dtype=np.float64), pixel_m)
    return np.hypot(gx, gy)


def _read_band(path, band_1based: int, expect_prefix: str, foot: np.ndarray):
    with rasterio.open(path) as s:
        desc = (s.descriptions[band_1based - 1] or "").split(" - ")[0].strip()
        if desc != expect_prefix:
            raise ValueError(f"band {band_1based} is {desc!r}, expected {expect_prefix!r}")
        a = s.read(band_1based).astype(np.float64)
        nd = s.nodata
    valid = foot & np.isfinite(a) & (np.abs(a) < 1e30)
    if nd is not None:
        valid &= a != float(nd)
    return fill_nearest(a, valid), valid


def build_depthslice_bands(training_path, foot: np.ndarray) -> dict:
    """Build the five frozen H39-1 bands + the persistence rank used for candidate ranking.

    Returns {"names": BAND_NAMES, "bands": {name: float32 2-D}, "persist_rank01": float32 2-D
    in [0,1] (rank of tmi_persist within the footprint), "valid_frac": {...}}.
    """
    foot = np.asarray(foot, bool)
    tmi, tmi_valid = _read_band(training_path, 14, "tmi", foot)
    grav, grav_valid = _read_band(training_path, 13, "iso_grav_anom", foot)

    hg_shallow = hg_mag(gaussian_filter(tmi, 1.0))
    up1000 = upward_continue(tmi, 1000.0)
    up2000 = upward_continue(tmi, 2000.0)
    hg1000 = hg_mag(up1000)
    hg2000 = hg_mag(up2000)
    persist = hg2000 / np.maximum(hg2000 + hg_shallow, 1e-300)
    tilt = np.arctan2(vertical_derivative_up(tmi, 1000.0), hg1000)
    grav_hg2000 = hg_mag(upward_continue(grav, 2000.0))

    bands = {
        "tmi_hg_up1000": hg1000, "tmi_hg_up2000": hg2000, "tmi_persist": persist,
        "tmi_tilt_up1000": tilt, "grav_hg_up2000": grav_hg2000,
    }
    # Rank of persistence inside the footprint (0..1); deterministic, ties share the mean rank
    # via argsort-of-argsort on the footprint vector (stable and simple at 5.16M px).
    pv = persist[foot]
    order = np.argsort(pv, kind="stable")
    ranks = np.empty(len(pv), dtype=np.float64)
    ranks[order] = np.arange(len(pv))
    persist_rank01 = np.zeros(persist.shape, dtype=np.float32)
    persist_rank01[foot] = (ranks / max(1, len(pv) - 1)).astype(np.float32)

    return {
        "names": list(BAND_NAMES),
        "bands": {k: np.where(np.isfinite(v), v, 0.0).astype(np.float32) for k, v in bands.items()},
        "persist_rank01": persist_rank01,
        "valid_frac": {"tmi": float(tmi_valid[foot].mean()), "iso_grav_anom": float(grav_valid[foot].mean())},
    }


def bands_to_footprint_matrix(built: dict, foot: np.ndarray) -> np.ndarray:
    """(n_footprint, 5) float32 matrix in row-major footprint order (oof_detector contract)."""
    foot = np.asarray(foot, bool)
    return np.column_stack([built["bands"][n][foot] for n in built["names"]]).astype(np.float32)
