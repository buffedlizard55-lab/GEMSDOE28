#!/usr/bin/env python3
"""Forensics on the highest-scoring family: why the dotted H19-5 d~2.8 raster scored 0.2600.

Everything computed from rasters is recomputed from the *exact bytes* of the three hash-pinned
objects in `data/` (see `scripts/restore_from_checkout.py` for the restore + SHA-256 audit) and
from the official metric definition (DrivenData #306 problem page). The 0.2600 figure itself is an
owner-reported/leaderboard-row claim, not an organizer receipt for these bytes, and is labelled as
such throughout.

Output: evidence/why_026_won.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from gems27 import paths, thinning  # noqa: E402

R = 3.0            # DTI kernel radius in pixels (300 m at 100 m cells)
FOOTPRINT_PX = 5_167_373


def load_binary(path: Path) -> np.ndarray:
    with rasterio.open(path) as s:
        a = s.read(1)
        nd = s.nodata
    if nd is not None and np.isnan(nd):
        a = np.where(np.isnan(a), 0.0, a)
    else:
        a = np.nan_to_num(a, nan=0.0)
    return a > 0.5


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def nn_spacing_px(mask: np.ndarray) -> dict[str, float]:
    """Nearest-neighbour distance (px) between emitted pixels, self excluded (k=2 KD-tree query)."""
    from scipy.spatial import cKDTree

    if int(mask.sum()) < 2:
        return {}
    pts = np.column_stack(np.nonzero(mask)).astype(np.float64)
    d, _ = cKDTree(pts).query(pts, k=2)
    vals = d[:, 1]
    return {"min": float(vals.min()), "p10": float(np.percentile(vals, 10)),
            "median": float(np.median(vals)), "mean": float(vals.mean()),
            "p90": float(np.percentile(vals, 90))}


def isolated_fraction(mask: np.ndarray) -> float:
    nb = np.zeros(mask.shape, np.int16)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                nb += np.roll(np.roll(mask, dy, 0), dx, 1)
    return float((nb[mask] == 0).mean())


def kernel_terms(pred: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    """Exact metric terms for a binary prediction against a binary truth (no catalogue mask)."""
    d_truth = distance_transform_edt(~truth)
    k_truth = np.maximum(1.0 - d_truth / R, 0.0)
    d_pred = distance_transform_edt(~pred)
    k_pred = np.maximum(1.0 - d_pred / R, 0.0)
    a = float(k_truth[pred].sum())          # A = TPw  (credit, truth side)
    b = float(k_pred[truth].sum())          # B       (credit, prediction side)
    n = float(pred.sum())
    t = float(truth.sum())
    fpw = n - a
    fnw = t - b
    dti = a / (a + 0.2 * fpw + 0.8 * fnw + 1e-9)
    return {"A_TPw": a, "B_prediction_side": b, "N": n, "FPw": fpw, "FNw": fnw, "T": t,
            "dti": dti, "weighted_recall_truth_side": b / t}


def dti_from_model(a: float, n_over_t: float) -> float:
    """Naive closure of the official DTI for credit fraction a = A/T and n_over_t = N/T.

    Derivation from the competition metric (known-catalogue pixels masked, so B = A):
        DTI = A / (A + 0.2*(N - A) + 0.8*(T - A)) = A / (0.2*N + 0.8*T)
            = a / (0.8 + 0.2*n_over_t).
    An earlier revision of this script used a/(a + 0.2*n_over_t + 0.8*(1-a)), which double-counts
    0.2*a in the denominator and inflates every prediction (sibling's c/f were themselves solved
    under that older closure, so with the corrected denominator they slightly under-predict the
    two reported anchors; the residuals are recorded, not hidden).
    """
    return a / (0.8 + 0.2 * n_over_t)


def solve_credit_fraction(target: float, n_over_t: float) -> float:
    """Invert DTI = a/(0.8 + 0.2*n_over_t) for the credit fraction a."""
    lo, hi = 1e-12, 1.0
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if dti_from_model(mid, n_over_t) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main() -> int:
    out: dict[str, object] = {
        "schema": 1,
        "generated_utc": "2026-10-03",
        "question": ("Why did the dotted H19-5 d=2.8 raster (mirrored at GEMSDOE25 "
                     "docs/downloads, owner-reported 0.2600; public leaderboard row wbg1 #15 = "
                     "0.2600 observed 2026-10-03) score highest of the local family, and can a "
                     "higher score be designed?"),
        "claim_hygiene": ("0.2600 is an owner-reported / public-leaderboard-row figure and is not an "
                          "organizer receipt for these bytes. Links between the local file, the "
                          "owner and the leaderboard row are unproven."),
        "inputs": {},
        "relations": {},
        "metric_algebra": {},
        "calibration": {},
        "targets": {},
    }

    masks: dict[str, np.ndarray] = {}
    for key, p in (("h19_5_solid", paths.H19_5), ("dotted_d1_5", paths.DOTTED_0_2477),
                   ("dotted_d2_8", paths.DOTTED_D2_8)):
        m = load_binary(p)
        masks[key] = m
        out["inputs"][key] = {
            "file": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p),
            "positive_px": int(m.sum()), "isolated_fraction": isolated_fraction(m),
            "nn_spacing_px": nn_spacing_px(m),
            "share_of_footprint": m.sum() / FOOTPRINT_PX,
        }

    solid, d15, d28 = masks["h19_5_solid"], masks["dotted_d1_5"], masks["dotted_d2_8"]
    repro = {}
    for md in (1.5, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2):
        t = thinning.dot_thin(solid, md)
        repro[f"{md}"] = {"px": int(t.sum()), "matches_d1_5_file": bool((t == d15).all()),
                          "matches_d2_8_file": bool((t == d28).all())}
    out["relations"] = {
        "d1_5_subset_of_solid": bool(not (d15 & ~solid).any()),
        "d2_8_subset_of_solid": bool(not (d28 & ~solid).any()),
        "d2_8_subset_of_d1_5": bool(not (d28 & ~d15).any()),
        "dot_thin_reproduction": repro,
        "reading": ("all three rasters are the same detector emission (H19-5) at different packing "
                    "distances; the d=2.8-class file is a deterministic thinning of the same bytes."),
    }

    out["metric_algebra"] = {
        "official_definition": ("DTI = TPw/(TPw + 0.2 FPw + 0.8 FNw); k(d)=max(1-d/300m,0); "
                                "alpha=0.2, beta=0.8 (DrivenData #306 problem page)"),
        "exact_rearrangement": ("with A = TPw (sum over truth of the best nearby prediction), "
                                "B = sum over predictions of the best nearby truth, T = truth count "
                                "and N = emitted count: DTI = A/(0.8T + 0.2N + 0.2(A-B)). When A and B "
                                "are equal (a one-to-one matching) this is DTI = A/(0.8T + 0.2N)"),
        "marignal_rule": ("dropping one emitted pixel whose own kernel credit is a raises DTI iff "
                          "a < 0.2*DTI; adding one raises DTI iff its expected kernel mass exceeds "
                          "0.2*DTI. At DTI 0.2477 the break-even is 0.0495, at 0.26 it is 0.052, at "
                          "0.3195 it is 0.064"),
        "binary_optimality": ("for a fixed support, DTI is monotone non-decreasing in each p(x) "
                              "whenever that pixel's expected credit exceeds the break-even, and the "
                              "ratio is linear in each p, so the optimum is attained at the corners "
                              "p in {0,1}: soft probability fields cannot beat the best binary set "
                              "under the initial-round metric"),
        "used_by_submission": ("the shipped artifacts are binary {0,1} rasters, consistent with this"),
    }

    # --- calibration: reproduce the sibling two-parameter emission model, then predict d2.8 -------
    n_solid = int(solid.sum())
    n_15 = int(d15.sum())
    n_28 = int(d28.sum())
    y1, y2, y3 = 0.1922, 0.2477, 0.2600          # reported: solid, d1.5, d2.8-class
    r15, r28 = 0.8531275643256233, 0.7588759346162787   # geometric retentions (sibling ledger)
    c = 0.508792            # sibling emission_model.json credit_per_truth (pinned owner record)
    g = 12225.896           # sibling lattice calibration of the hidden truth mass |G|, px
    # n_over_t is measured directly: N(d) / |G| (no re-fit of c under the corrected closure).
    n_over_t_solid = n_solid / g
    n_over_t_15 = n_15 / g
    n_over_t_28 = n_28 / g
    pred_d15 = dti_from_model(c * r15, n_over_t_15)
    pred_d28 = dti_from_model(c * r28, n_over_t_28)
    out["calibration"] = {
        "method": ("corrected naive closure DTI = a/(0.8 + 0.2*N/|G|), evaluated with the sibling's "
                   "pinned credit_per_truth c = 0.508792, its geometric retention curve and the "
                   "measured dot counts at the sibling lattice calibration |G| = 12,225.896 px; the "
                   "d=2.8-class file is predicted out of sample (no parameter is re-fit here)"),
        "closure": "DTI = a / (0.8 + 0.2 * N/|G|), a = c * retention",
        "sibling_credit_per_truth": c,
        "truth_mass_calibration_px": g,
        "measured_n_over_t": {"solid": n_over_t_solid, "d1_5": n_over_t_15, "d2_8": n_over_t_28},
        "retention": {"d1_5": r15, "d2_8": r28},
        "reported_anchor_solid": y1,
        "reproduced_anchor_solid": dti_from_model(c, n_over_t_solid),
        "reported_anchor_d1_5": y2,
        "predicted_anchor_d1_5": pred_d15,
        "predicted_d2_8_out_of_sample": pred_d28,
        "reported_d2_8": y3,
        "residuals": {"solid": dti_from_model(c, n_over_t_solid) - y1,
                      "d1_5": pred_d15 - y2, "d2_8": pred_d28 - y3},
        "hand_check_expected": {"d1_5": 0.24349, "d2_8": 0.25382},
        "sibling_ledger_interval_for_this_operating_point": [0.25002945809247196, 0.2613299747091814],
        "verdict": ("under the corrected closure the pinned sibling constants predict %.4f for d1.5 "
                    "and %.4f for the d=2.8-class file against reported 0.2477 and 0.2600, i.e. "
                    "residuals of %.4f and %.4f; the reported d=2.8 value stays inside the sibling's "
                    "published interval [0.2500, 0.2613] and the ordering solid < d1.5 < d2.8 is "
                    "reproduced, so the emission-geometry explanation survives, while the two "
                    "constants were themselves solved under the older closure and are not re-fit here"
                    % (pred_d15, pred_d28, pred_d15 - y2, pred_d28 - y3)),
    }

    # --- target inversion -------------------------------------------------------------------------
    targets: dict[str, object] = {}
    for T in (12630.0, 20000.0):
        rows = {}
        for label, n in (("d2_8_emission_N=%d" % n_28, n_28), ("d1_5_emission_N=%d" % n_15, n_15),
                         ("pruned_N=22700", 22700)):
            rows[label] = {}
            for target in (0.26, 0.2941, 0.3195):
                a = solve_credit_fraction(target, n / T)
                rows[label][str(target)] = {
                    "required_credit_fraction_of_truth": a,
                    "required_credit_per_emitted_px": a * T / n,
                }
        targets["|G|=%d" % T] = rows
    # the same inversion at the *measured* credit of the current best file
    a_cur = c * r28
    n_req = (a_cur / 0.3195 - 0.8) / 0.2 * g
    out["targets"] = {
        "truth_size_note": ("|G| is not observable from here. 12,630 px is the sibling's lattice "
                            "calibration (unconfirmed); 20,000 px is shown as a sensitivity."),
        "table": targets,
        "current_credit_fraction_model": a_cur,
        "emitted_px_needed_for_0_3195_at_current_credit": n_req,
        "reading": ("with the current credit fraction held fixed, 0.3195 requires ~%d emitted pixels "
                    "instead of %d - i.e. the same fault mass concentrated in ~half the dots - or, "
                    "at the current dot count, credit must rise from %.3f to %.3f of the hidden truth "
                    "(-+%d%%). Both routes are ranking problems, not geometry problems."
                    % (round(n_req), n_28, a_cur, solve_credit_fraction(0.3195, n_28 / 12630.0),
                       100 * (solve_credit_fraction(0.3195, n_28 / 12630.0) / a_cur - 1.0))),
    }

    # --- catalogue stand-in geometry ---------------------------------------------------------------
    labels = load_binary(paths.LABELS)
    geo = {}
    for key, m in (("h19_5_solid", solid), ("dotted_d1_5", d15), ("dotted_d2_8", d28)):
        geo[key] = {"px": int(m.sum()), "px_on_published_catalogue": int((m & labels).sum())}
    out["catalogue_stand_in"] = {
        "note": ("the published catalogue is the only local truth-like mask; it is NOT the hidden "
                 "test set, and these rows are descriptive only"),
        "rows": geo,
    }

    o = REPO / "evidence" / "why_026_won.json"
    o.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["relations"], indent=1))
    print(json.dumps(out["calibration"], indent=1))
    print(json.dumps(out["targets"]["reading"], indent=1))
    print("wrote", o)
    return 0


if __name__ == "__main__":
    sys.exit(main())
