#!/usr/bin/env python3
"""Build the H37-1 submission bundle: metric-aware packing of the scored H19-5 surface.

Protocol: ``knowledge/29_preregistration_H37-1.md``. Gate result: ``evidence/h37_1_holdout.json``
(fresh seeds 250-259; PRIMARY ``cover_prob_r1`` = mean OOF delta DTI **+0.007289** vs the
``d=2.8`` reference and **+0.004614** over the H36-1 incumbent, 10/10 seeds, 4/4 folds, all five
frozen criteria passed; content-blind matched-N control -0.044684; the incumbent itself replicated at
+0.002675 against its own +0.002599 on seeds 240-249).

The holdout measures the *rule* on the out-of-fold detector surface; this artifact applies the *rule*
to the scored surface. Both prongs are asserted before anything is written:

    candidates  = the H19-5 surface as shipped (121,131 px, catalogue-masked)  -> the pool density
                  (2.34 % of the footprint) is the pool the gate's ``cover_prob_pool3x_r1`` probe
                  measured (+0.004661 over the incumbent, 10/10 seeds, 4/4 folds), so the transfer
                  rests on a measured pool, not on an extrapolation from the rich ridge pool;
    weight      = the full-fit detector probability (the emission-time analogue of the gate's OOF
                  field; no holdout exists at scoring time);
    budget      = 41,333 px, i.e. exactly the rung-3.0 count the incumbent starts from, so this is a
                  layout change at matched budget;
    prune       = the unchanged H27-4 blind 1-px catalogue-flank prune.

A second, explicitly NOT-promoted probe is also written: the same rule over the union pool
(H19-5 + the detector's own 1-px ridges). It is expected to look better on the catalogue-internal
proxy and it is exactly the kind of emission a live score has already punished (26GEMSDOE
``dilcond-oof-v1``, a pure detector-product emission, scored 0.1223), so it is recorded for review
rather than shipped as the primary.

Writes the GeoTIFF pairs, the zips, the notes and re-slots ``docs/downloads/manifest.json``.
Reads no hidden truth. Never contacts drivendata.org.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems27 import oof_detector, packing, paths, submission  # noqa: E402
from gems27.thinning import dot_thin  # noqa: E402

RUNG30_PX = 41333
#: Live-anchored operating-point constants from knowledge/27 §3 (H34 closure at the 0.2600 anchor).
LIVE_G = 12225.896
LIVE_GAMMA = 0.12653
INCUMBENT_LIVE_RANGE = (0.2717, 0.2727)
INCUMBENT_N = 37660


def live_dti(credit: float, n_emitted: int, g: float = LIVE_G, gamma: float = LIVE_GAMMA) -> float:
    """Eq. 1 of ``src/gems27/operating_point.py``: DTI = A / (0.8|G| + 0.2(1-gamma)N + 0.2A)."""
    return credit / (0.8 * g + 0.2 * (1.0 - gamma) * n_emitted + 0.2 * credit)


def main() -> int:
    downloads_dir = ROOT / "docs" / "downloads"
    template_path = paths.DATA / "sample_submission.tif"
    labels_path = paths.DATA / "labels.tif"
    d28_path = paths.DATA / "dotted_h19_5_d2_8_nan.tif"

    with rasterio.open(template_path) as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(labels_path) as ds:
        lbl = ds.read(1)
        catalogue = footprint & np.isfinite(lbl) & (lbl > 0.5)
    with rasterio.open(paths.H19_5) as ds:
        raw = ds.read(1)
    h19_5 = footprint & ~catalogue & np.isfinite(raw) & (raw > 0.5)
    with rasterio.open(d28_path) as ds:
        d28 = footprint & ~catalogue & (np.nan_to_num(ds.read(1), nan=0.0) > 0.5)

    assert int(h19_5.sum()) == 121131, f"h19_5 surface {int(h19_5.sum())} != 121,131"
    assert int(d28.sum()) == 44090, f"published d2.8 {int(d28.sum())} != 44,090"
    assert np.array_equal(d28, dot_thin(h19_5, 2.8)), "published d2.8 is not dot_thin(surface, 2.8)"
    rung30 = dot_thin(h19_5, 3.0)
    assert int(rung30.sum()) == RUNG30_PX, f"rung 3.0 {int(rung30.sum())} != {RUNG30_PX}"
    blind_r1 = distance_transform_edt(~catalogue) <= 1.0

    print("Fitting the full-fit detector probability (all published labels)...", flush=True)
    prob = oof_detector.fit_predict_full_probabilities(footprint, catalogue)
    weight = np.where(footprint & ~catalogue, prob, 0.0).astype(np.float32)
    ridge_full = oof_detector.ridge_nms(prob, footprint, sigma=1.0) & footprint & ~catalogue

    pool_h19 = h19_5
    pool_union = h19_5 | ridge_full
    print(f"pools: H19-5 {int(pool_h19.sum()):,} px ({100*pool_h19.sum()/footprint.sum():.2f}% of "
          f"footprint); union {int(pool_union.sum()):,} px", flush=True)

    packed_primary = packing.coverage_greedy(pool_h19, weight, RUNG30_PX)
    assert int(packed_primary.sum()) == RUNG30_PX, (
        f"primary packer emitted {int(packed_primary.sum())} != {RUNG30_PX} "
        "(the budget matcher failed; do not ship a mis-sized emission)")
    pred_primary = packed_primary & ~blind_r1
    assert int(pred_primary.sum()) > 0
    assert not (pred_primary & catalogue).any()

    packed_probe = packing.coverage_greedy(pool_union, weight, RUNG30_PX)
    pred_probe = packed_probe & ~blind_r1

    outputs = []
    for slug, pred, hypothesis, status, note_hyp, note_summary in [
        (
            "h37-1-coverprob-h19-5-r1",
            pred_primary,
            ("H37-1: metric-aware packing of the H19-5 surface - lazy-greedy maximum expected "
             "coverage of the detector probability field under the official 300 m kernel, at the "
             "rung-3.0 budget (41,333 px) with the unchanged H27-4 blind 1-px catalogue-flank prune"),
            ("UNSCORED; passed the frozen H37-1 gate on fresh seeds 250-259: +0.007289 mean OOF "
             "delta DTI vs the d=2.8 reference and +0.004614 over the H36-1 incumbent, 10/10 seeds, "
             "4/4 folds, content-blind matched-N control -0.044684, integrity clean."),
            "H37-1 cover+h19",
            ("OOF dDTI +0.00729 vs d2.8, +0.00461 over H36-1; 10/10 seeds, 4/4 folds "
             "(seeds 250-259); no T-v2"),
        ),
        (
            "h37-1-probe-union-pool-r1",
            pred_probe,
            ("H37-1 probe (NOT promoted): same rule over the union pool (H19-5 + the detector's own "
             "1-px ridges) at the same budget and the same prune"),
            ("UNSCORED PROBE, not slot-approved; recorded because the union pool is the exact pool "
             "the gate's primary used, while the shipped H19-5 pool is the gate's pool3x probe."),
            "H37-1 probe union",
            ("same rule, union pool; NOT promoted - proxy-favoured, detector-content emission"),
        ),
    ]:
        pred_clean = np.where(footprint & ~catalogue & pred, np.float32(1.0), np.float32(0.0))
        cid = submission.scored_content_id(pred_clean, footprint, catalogue)
        nan_name = submission.make_filename("gems28", slug, "20261003", cid, "nan")
        all_name = submission.make_filename("gems28", slug, "20261003", cid, "allfinite")
        nan_path = downloads_dir / nan_name
        all_path = downloads_dir / all_name
        submission.write_geotiff(pred_clean, template_path, nan_path, outside="nan")
        submission.write_geotiff(pred_clean, template_path, all_path, outside="zero")
        zip_path = submission.zip_single(nan_path)
        v_nan = submission.verify_geotiff(nan_path, template_path)
        v_all = submission.verify_geotiff(all_path, template_path)
        if not (v_nan["hard_checks_passed"] and v_all["hard_checks_passed"]):
            raise RuntimeError(f"hard verification failed for {slug}: "
                               f"{v_nan['hard_failures']} / {v_all['hard_failures']}")
        note = submission.make_note(note_hyp, note_summary, cid, family="28GEMSDOE",
                                    status="UNSCORED, not slot-approved")
        if note_summary not in note:
            raise RuntimeError(f"note summary truncated by make_note: {note!r}")
        note_file = f"note-gemsdoe28-{slug}-{cid}.txt"
        (downloads_dir / note_file).write_text(note + "\n", encoding="utf-8")
        outputs.append({
            "slug": slug, "hypothesis": hypothesis, "status": status, "content_id": cid,
            "nan": nan_name, "allfinite": all_name, "zip": zip_path.name,
            "sha256_nan": v_nan["sha256"], "sha256_allfinite": v_all["sha256"],
            "sha256_zip": submission.sha256_file(zip_path),
            "bytes_nan": v_nan["bytes"], "bytes_allfinite": v_all["bytes"],
            "bytes_zip": zip_path.stat().st_size,
            "emitted_px": int(pred_clean[footprint].sum()),
            "format_verified": True, "note": note, "note_file": note_file,
            "pre_prune_px": int((packed_primary if slug.startswith("h37-1-coverprob")
                                 else packed_probe).sum()),
            "prune_px_removed": int((packed_primary if slug.startswith("h37-1-coverprob")
                                     else packed_probe).sum()) - int(pred_clean[footprint].sum()),
            "base_reference_id": "e56ea318af89",
            "base_reference_live_score": 0.26,
            "holdout_evidence": "evidence/h37_1_holdout.json",
            "holdout_preregistration": "knowledge/29_preregistration_H37-1.md",
            "holdout_seeds": "250-259",
            "holdout_mean_gain": 0.007289 if slug.startswith("h37-1-coverprob") else None,
            "holdout_mean_gain_vs_incumbent": 0.004614 if slug.startswith("h37-1-coverprob") else None,
            "holdout_seeds_improved": "10/10" if slug.startswith("h37-1-coverprob") else "n/a",
            "holdout_folds_improved": "4/4" if slug.startswith("h37-1-coverprob") else "n/a",
        })
        print(f"wrote {nan_name}: {outputs[-1]['emitted_px']:,} px, sha256 {v_nan['sha256'][:16]}…",
              flush=True)

    primary = outputs[0]
    probe = outputs[1]

    # ---- live projection, two independent transfer assumptions, both stated as models -------------
    rel_gain = 0.10548 / 0.10086 - 1.0  # primary mean OOF DTI / incumbent mean OOF DTI - 1
    proj_relative = tuple(round(x * (1.0 + rel_gain), 4) for x in INCUMBENT_LIVE_RANGE)
    credit_gain_frac = 504.2 / 471.7 - 1.0  # per-cell mean TP, primary vs incumbent (gate cells)
    credit0 = 4692.24  # H36-1's post-prune credit at the anchor (knowledge/27 §3)
    n_gain_frac = primary["emitted_px"] / INCUMBENT_N - 1.0
    proj_credit = round(live_dti(credit0 * (1.0 + credit_gain_frac),
                                 int(round(INCUMBENT_N * (1.0 + n_gain_frac)))), 4)
    projection = {
        "incumbent_live_range": list(INCUMBENT_LIVE_RANGE),
        "relative_transfer": {
            "assumption": "same relative OOF DTI gain on the live anchor",
            "relative_gain": round(rel_gain, 5),
            "range": list(proj_relative),
        },
        "credit_transfer": {
            "assumption": ("live credit and live emission mass grow by the same fractions the gate "
                           "measured on the proxy (+6.89 % credit, +3.05 % dots), evaluated with Eq. 1 "
                           "at |G| = 12,225.896 and gamma = 0.12653"),
            "range": [round(INCUMBENT_LIVE_RANGE[0] - 0.002 + 0.006, 4), proj_credit],
            "point": proj_credit,
        },
        "half_transfer_conservative": [round(x * (1.0 + rel_gain / 2), 4) for x in INCUMBENT_LIVE_RANGE],
        "verdict": ("MODELLED 0.278-0.286 against the incumbent's modelled 0.2717-0.2727. This is not a "
                    "score: the proxy hides catalogue components interleaved with the known catalogue, "
                    "so a coverage objective aimed at the detector's own field is a priori favoured by "
                    "it (registry/irregularities.json: interleaved-holdout-has-no-far-field-truth)."),
    }

    manifest_path = downloads_dir / "manifest.json"
    old = json.loads(manifest_path.read_text())
    if old.get("primary", {}).get("content_id") == primary["content_id"]:
        refreshed = dict(old)
        refreshed["primary"] = primary
        refreshed["research_candidate"] = probe
        manifest_path.write_text(json.dumps(refreshed, indent=2) + "\n", encoding="utf-8")
    else:
        secondary = old["primary"]
        secondary["status"] = (
            "UNSCORED; previous one-click primary (H36-1, won its own frozen gate on seeds 240-249 at "
            "+0.002599). Demoted by H37-1 on fresh seeds 250-259 (+0.002675 vs +0.007289 vs the same "
            "d=2.8 reference). Still fully audited and the more conservative choice."
        )
        new_manifest = {
            "schema": 1,
            "generated_utc": "2026-10-03",
            "status": ("UNSCORED GEMSDOE28 research/reference artifacts; no GEMSDOE28 upload or "
                       "organizer score is recorded"),
            "provenance_warning": ("All inputs and historical model artifacts are owner-repository "
                                   "mirrors; local SHA-256 integrity does not prove organizer "
                                   "authenticity or score association."),
            "manual_policy": ("No upload, portal call, scheduled check, scraping, API monitoring or "
                              "other automated DrivenData access. All site links are downloads/"
                              "manual-review links only."),
            "primary": primary,
            "secondary": secondary,
            "tertiary": old["secondary"],
            "quaternary": old["tertiary"],
            "quinary_probe": old.get("quinary_probe"),
            # The previous quaternary (H32-1 post-thinning) is kept listed AND audited rather than
            # silently dropped by the re-slot; verify_downloads.py enumerates this slot.
            "conservative_alternative": dict(
                old["quaternary"],
                status=("UNSCORED; the original preregistered H32-1 file (conservative alternative: it "
                        "is the only variant that protects fault tips and shallow SI-0 Euler depth "
                        "clusters). Kept listed and audited after H37-1 re-slotted the ladder."),
            ),
            "research_candidate": probe,
            "promotion_rule": ("The one-click primary is the file that won a frozen fresh-seed gate "
                               "whose criteria were written to knowledge/ before the seeds were spent. "
                               "H37-1: knowledge/29_preregistration_H37-1.md, seeds 250-259."),
        }
        manifest_path.write_text(json.dumps(new_manifest, indent=2) + "\n", encoding="utf-8")

    evidence = {
        "hypothesis": "H37-1 artifact build (metric-aware packing of the scored H19-5 surface)",
        "preregistration": "knowledge/29_preregistration_H37-1.md",
        "gate": "evidence/h37_1_holdout.json",
        "pool_h19_5_px": int(pool_h19.sum()),
        "pool_h19_5_density_pct": round(100 * float(pool_h19.sum()) / float(footprint.sum()), 4),
        "pool_union_px": int(pool_union.sum()),
        "budget_pre_prune_px": RUNG30_PX,
        "blind_r1_removed_primary": int(packed_primary.sum() - pred_primary.sum()),
        "blind_r1_removed_probe": int(packed_probe.sum() - pred_probe.sum()),
        "primary": primary,
        "probe": probe,
        "projection": projection,
        "counts_asserted": {"h19_5": int(h19_5.sum()), "d2_8": int(d28.sum()),
                            "rung30": int(rung30.sum()), "catalogue": int(catalogue.sum())},
    }
    (ROOT / "evidence" / "h37_1_artifact.json").write_text(json.dumps(evidence, indent=2) + "\n",
                                                           encoding="utf-8")
    print(json.dumps({"primary": primary["nan"], "px": primary["emitted_px"],
                      "probe": probe["nan"], "probe_px": probe["emitted_px"],
                      "projection": projection}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
