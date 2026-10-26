#!/usr/bin/env python3
"""Finalize S21: write verified TIFFs from the v3 emission, extended uniqueness, run card."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, submission  # noqa: E402

res = json.loads((ROOT / "evidence/s21_lane_result.json").read_text())
pooled = res["holdout"]["pooled"]
# primary = whichever of hgb/fusion pooled higher in holdout (pre-declared rule)
primary_key = "hgb" if pooled["hgb"] >= pooled["fusion"] else "fusion"
em = np.load(f"/tmp/s21_em_{'hgb' if primary_key=='hgb' else 'fus'}.npy")
print("primary:", primary_key, "px:", int(em.sum()))
cid = hashlib.sha256(em.astype(np.uint8).tobytes()).hexdigest()[:10]
base = f"gems28-s21-puhgb-20261026-{cid}"
DL = ROOT / "docs/downloads"
tmpl = ROOT / "data/sample_submission.tif"
p_fin = submission.write_geotiff(em.astype(np.float32), tmpl, DL / f"{base}-allfinite.tif", outside="zero")
p_nan = submission.write_geotiff(em.astype(np.float32), tmpl, DL / f"{base}-nan.tif", outside="nan")
p_zip = submission.zip_single(p_nan, DL / f"{base}-nan.zip")
ver = {"allfinite": submission.verify_geotiff(p_fin, tmpl), "nan": submission.verify_geotiff(p_nan, tmpl)}
print("verify hard pass:", ver["allfinite"]["hard_checks_passed"], ver["nan"]["hard_checks_passed"])

# extended uniqueness vs every existing download raster (excluding just-written)
def load_bin(p):
    with rasterio.open(p) as ds: return ds.read(1) > 0
rows = []
for p in sorted(DL.glob("*.tif")):
    if base in p.name: continue
    try: ref = load_bin(p)
    except Exception as e: rows.append({"file": p.name, "error": str(e)}); continue
    if ref.shape != em.shape or not ref.any(): continue
    d = distance_transform_edt(~ref)
    rows.append({"file": p.name, "ref_px": int(ref.sum()),
                 "overlap3px_of_s21": float((d[em] <= 3).mean()),
                 "jaccard": float((em & ref).sum() / max((em | ref).sum(), 1))})
rows.sort(key=lambda r: -r.get("overlap3px_of_s21", 0))
print("max overlap vs", rows[0] if rows else None)

# live-anchored MODEL projection (never a score): anchor = owner-reported champion 0.2778,
# whose construction equals dotted_b2 in holdout; scale by holdout ratio.
anchor = 0.2778
ratio = pooled[primary_key] / pooled["dotted_b2"]
dlo, dhi = res["holdout"]["ci95_delta_hgb"] if primary_key == "hgb" else res["holdout"]["ci95_delta_fus"]
est = anchor * ratio
est_lo = anchor * (pooled["dotted_b2"] + dlo) / pooled["dotted_b2"]
est_hi = anchor * (pooled["dotted_b2"] + dhi) / pooled["dotted_b2"]

note = f"S21 PU-HGB 31-band fresh geography 37654d b2 |HOLDOUT-DTI {pooled[primary_key]:.4f} vs dotted {pooled['dotted_b2']:.4f}"
assert len(note) <= 140, len(note)
(DL / f"note-{base}.txt").write_text(note + "\n")
card = {
  "session": "S21-PUHGB", "date_utc": "2026-10-26", "lane": "Fresh PU-HGB (31-band) detector geography; no H19-5 dots in final raster",
  "hypothesis": "A PU-trained gradient-boosted detector on 19 GeoDAWN + 12 LiDAR-scarp bands finds off-catalogue fault habitat that the single H19-5 surface misses; with champion emission hygiene (2.8px spacing, ring<=2px exclusion, 37,654 budget) it can match/beat the dotted baseline in hide-and-recover holdout.",
  "mechanism": "Catalogued faults occupy a learnable multivariate habitat (magnetic/gravity gradients, strain, conductivity, scarp steps); unmapped faults in the same habitat rank high off-catalogue.",
  "named_nonfault_mimic": "Roads, channels, terrace/paleo-shoreline risers, landslides and mine benches produce LiDAR steps; lithologic contacts produce magnetic/gravity gradients without Quaternary faulting.",
  "holdout": res["holdout"], "forensic_champion_lineage": res["forensic"],
  "uniqueness_extended": {"n_registry_rasters_compared": len(rows), "max_overlap3px": rows[0] if rows else None, "top5": rows[:5],
                          "surface_spearman_vs_key_registry": res["uniqueness"]["hgb"]},
  "validator": ver,
  "files": {"allfinite": p_fin.name, "sha256_allfinite": submission.sha256_file(p_fin), "bytes_allfinite": p_fin.stat().st_size,
            "nan": p_nan.name, "sha256_nan": submission.sha256_file(p_nan), "zip": p_zip.name, "sha256_zip": submission.sha256_file(p_zip),
            "positive_px": int(em.sum()), "content_id": cid},
  "submission_name": f"GEMSDOE28-S21-PUHGB-20261026-{cid}", "note": note, "note_chars": len(note),
  "score_estimate_MODEL_PROJECTION_not_a_score": {
    "anchor_owner_reported_unverified": anchor, "anchor_file": "GEMSDOE32 h33-h33-2-b2 (owner-reported 0.2778, no organizer receipt)",
    "method": "anchor * (pooled HOLDOUT-DTI of S21 / pooled HOLDOUT-DTI of dotted_b2 [=champion construction]) on identical cells",
    "estimate": est, "range_from_delta_ci": [est_lo, est_hi]},
  "verdict": None,  # filled below
}
delta = res["holdout"]["delta_hgb_minus_base"] if primary_key == "hgb" else res["holdout"]["delta_fus_minus_base"]
ci = res["holdout"]["ci95_delta_hgb"] if primary_key == "hgb" else res["holdout"]["ci95_delta_fus"]
uniq_ok = (not rows) or rows[0].get("overlap3px_of_s21", 1) <= 0.70
fmt_ok = ver["allfinite"]["hard_checks_passed"] and ver["nan"]["hard_checks_passed"]
if fmt_ok and uniq_ok and ci[0] > 0:
    card["verdict"] = "promote"
elif fmt_ok and uniq_ok:
    card["verdict"] = "negative-holdout-not-beaten"
else:
    card["verdict"] = "negative-gate-fail"
card["gates"] = {"format_pass": bool(fmt_ok), "uniqueness_pass_le_70pct": bool(uniq_ok),
                 "canary_pass": bool(res["holdout"]["canary_max_abs_dev_from_0.5"] <= 0.40),
                 "holdout_delta": delta, "holdout_delta_ci95": ci,
                 "holdout_beats_baseline_ci_gt_0": bool(ci[0] > 0)}
(ROOT / "evidence/s21_run_card.json").write_text(json.dumps(card, indent=1, default=str))
(ROOT / "docs/data/run_card_s21.json").write_text(json.dumps(card, indent=1, default=str))
(ROOT / f"docs/downloads/checks-{base}.json").write_text(json.dumps({"verify": ver, "gates": card["gates"]}, indent=1, default=str))
print(json.dumps({"verdict": card["verdict"], "gates": card["gates"], "estimate": est, "base": base}, indent=1))
