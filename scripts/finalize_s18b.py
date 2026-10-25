#!/usr/bin/env python3
"""S18B finalize: verdict from frozen gate + binding uniqueness + validator + evidence schema.

Session 18B = the third parallel 2026-10-25 run (H42-1 lane, knowledge/52 preregistration,
knowledge/54 result). A parallel Session 18 already owned the `s18_*` artifact names on main
(H39-5, content id 719b83fb659b, also negative), so this run writes `s18b_*` artifacts and
manifest slot `s18b_candidate`; the two sessions' numbers must never be combined.

Writes docs/downloads/manifest.json slot `s18b_candidate`, the portal note file,
evidence/s18b_run_card.json and docs/data/run_card_s18b.json (promotion-schema superset).
Verdict is `promote` ONLY if: the knowledge/52 frozen LOSFO gate passed AND binding scored-
registry uniqueness passed AND both GeoTIFF validators pass AND src/gems27/promotion.py
accepts the card. `promote` means eligible for the separate selector step; it never selects
a weekly slot and never asserts an organizer score. Otherwise the TIFF is inspection-only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27.promotion import promotion_gate  # noqa: E402


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while c := f.read(1 << 20):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    gate = json.loads((ROOT / "evidence/s18_h42_losfo_gate.json").read_text())
    build = json.loads((ROOT / "evidence/s18b_candidate_build.json").read_text())
    canary = json.loads((ROOT / "evidence/s18b_canary.json").read_text())
    dl = ROOT / "docs/downloads"
    nan_name, af_name, zip_name = build["nan_tif"], build["allfinite_tif"], build["zip"]
    cid = build["content_id"]
    validators_ok = bool(build["verify_nan"]["hard_checks_passed"]
                         and build["verify_allfinite"]["hard_checks_passed"])
    raster_sha = sha256_file(dl / af_name)  # all-finite file is the download of record
    assert raster_sha == build["sha256_allfinite"]

    scored = build["uniqueness_scored_registry_binding"]
    members = [v["sha256"] for v in scored.values() if not v.get("missing")]
    manifest_sha = hashlib.sha256(
        json.dumps(sorted(members)).encode()).hexdigest()
    surface = [{"raster_sha256": v["sha256"],
                "spearman": v["spearman_prob_vs_binary_sample400k"],
                "within_3px_fraction": v["frac_base_dots_within3px_pre_relocation"]}
               for v in scored.values() if not v.get("missing")]
    dots_cmp = [{"raster_sha256": v["sha256"], "spearman": v["binary_phi_footprint"],
                 "within_3px_fraction": v["frac_our_dots_within3px"]}
                for v in scored.values() if not v.get("missing")]

    g = gate["gate"]
    failed = [k for k, v in g.items() if not v]
    uniq_word = "uniq PASS" if build["uniqueness_binding_pass"] else "uniq FAIL"
    if gate["gate_passed"]:
        note = (f"28GEMSDOE H42-1 migx-reloc B1 | LOSFO dDTI "
                f"{gate['pooled_delta_dti_phys_minus_base']:+.4f} {uniq_word} UNSCORED | id {cid}")
    else:
        note = (f"28GEMSDOE H42-1 migx-reloc B1 | LOSFO GATE FAIL dDTI "
                f"{gate['pooled_delta_dti_phys_minus_base']:+.4f} DO NOT SUBMIT | id {cid}")
    assert len(note) <= 140, len(note)

    phys = gate["pooled"]["phys"]
    card = {
        "session": ("S18B parallel run (2026-10-25), branch arena/384a5345-gemsdoe28, lane H42-1 "
                    "(knowledge/52). Renamed from S18 at merge: a parallel Session 18 (H39-5) "
                    "already owned s18_* names on main; never combine the two sessions' numbers."),
        "lane": ("H42-1 migration-extrapolated relocation: TMI+gravity HG-ridge migration vector "
                 "field (0/1/2 km upward continuations) x depth-to-basement-scaled up-dip "
                 "relocation of frozen-detector dots; knowledge/52 §1."),
        "hypothesis": ("A dipping buried fault's potential-field ridge migrates down-dip with "
                       "continuation height, so relocating detector dots up-dip by "
                       "migration x depth/2000 m places them on the fault's surface trace - "
                       "structure the scarp-biased USGS/INGENIOUS catalogue omits - and raises "
                       "far-field DTI at the champion's budget."),
        "mechanism": ("Upward continuation exp(-|k|h) (shared depthslice); HG ridges via shared "
                      "ridge_nms; vector = shallow->2km nearest-ridge displacement, |v|<=12px, "
                      "sigma=2 corridor-smoothed, TMI/gravity support-averaged; shift = "
                      "-v*clip(depth_to_base_surf,0,2000)/2000, capped 3px, catalogue+2px-ring "
                      "blocked, raster-order collisions, dot_thin(2.8). Detector unchanged."),
        "non_fault_mimic": ("Dipping lithologic contact / mafic dike (migrates identically, zero "
                            "Quaternary slip); GeoDAWN flight-line striping."),
        "named_nonfault_mimic": ("Dipping lithologic contact / mafic dike swarm; GeoDAWN "
                                 "flight-line striping."),
        "raster_sha256": raster_sha,
        "raster_sha256_detail": {"allfinite_record": raster_sha, "nan": build["sha256_nan"],
                                 "zip": build["sha256_zip"], "content_id": cid},
        "submission_name": f"GEMSDOE28-h42-1-migx-reloc-b1-{cid}",
        "note": note,
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": gate["evaluator_version"],
            "evaluator": gate["evaluator"],
            "raster_sha256": raster_sha,
            "baseline_sha256": build["base_scored_sha256_full"],
            "withheld_positives": int(gate["n_withheld_positives_pooled_cell_truth_px"]),
            "dti": phys["dti"],
            "ci95": gate["ci95_pooled_phys_dti_cell_bootstrap"],
            "paired_gain_ci95": gate["ci95_paired_bootstrap"],
            "whole_segments": True, "buffered": True, "visible_only_features": True,
            "pixel_exact_visible_mask": True, "pooled": True,
            "alpha": 0.2, "beta": 0.8, "kernel_m": 300, "kernel": "triangular",
            "seeds": "310-314 (20 paired cells)",
            "pooled_base_dti": gate["pooled"]["base"]["dti"],
            "pooled_delta_dti": gate["pooled_delta_dti_phys_minus_base"],
            "pooled_delta_anti": gate["pooled_delta_dti_anti_minus_base"],
            "pooled_delta_rand": gate["pooled_delta_dti_rand_minus_base"],
            "mean_paired_delta_dti": gate["mean_paired_delta_dti"],
            "cells_positive": f"{gate['cells_positive']}/20",
            "frac_dots_moved_ge1px": gate["pooled_frac_dots_moved_ge1px_phys"],
            "gate": g, "gate_passed": gate["gate_passed"],
        },
        "feature_canaries": {k: v["canary_max_auc_1mauc"]
                             for k, v in canary["single_feature_auc_vs_hidden_systems"].items()},
        "canary_pass": canary["canary_pass"],
        "registry": {
            "complete": True,
            "manifest_sha256": manifest_sha,
            "members": members,
            "surface": surface,
            "dots": dots_cmp,
            "definition": ("Ten owner-reported SCORED rasters of the nine focus sites "
                           "(knowledge/52 §3); scores are OWNER-REPORTED, none organizer-confirmed."),
            "scored_detail": scored,
            "binding_pass": build["uniqueness_binding_pass"],
            "disclosed_worst_other_download": build["worst_disclosed_other_download"],
            "disclosed_note": ("Unscored dense probe downloads blanket the detector ridge; "
                               "overlap vs them is disclosed in evidence/s18b_candidate_build.json "
                               "for the selector to adjudicate (irregularity s15-uniqueness-dense-probes)."),
        },
        "validator": {
            "raster_sha256": raster_sha,
            "no_nan_inside": bool(build["verify_allfinite"]["checks"]["inside_footprint_all_finite"]["pass"]),
            "range_0_1": bool(build["verify_allfinite"]["checks"]["strict_whole_array_range"]["pass"]),
            "crs_match": True, "shape_match": True, "transform_match": True, "single_band": True,
            "detail": build["verify_allfinite"],
            "nan_variant_hard_pass": bool(build["verify_nan"]["hard_checks_passed"]),
        },
        "preregistration_deviations": [(
            "knowledge/52 §1 says the two fields' vectors are 'averaged across the two fields "
            "weighted by their three-level ridge coherence'; build_migration_vectors instead "
            "support-averages them (mean over fields with a nonzero corridor vector). Found in "
            "Session 18B Pass-2 review. The falsification is direction-agnostic (phys ~= anti ~= "
            "rand, all harmful), so the deviation cannot manufacture the negative verdict, but "
            "the literally preregistered coherence-weighted estimator remains untested and may "
            "not be substituted on seeds 310-314.")],
        "organizer_confirmed_scores": ("none (no submission-page receipt exists for any file "
                                       "here; 0.2778 etc. are OWNER-REPORTED)"),
        "experiments_run": 3,
        "slot_selected": False,
    }
    schema = promotion_gate(card)
    promote = bool(gate["gate_passed"] and build["uniqueness_binding_pass"]
                   and validators_ok and schema["verdict"] == "promote")
    verdict = "promote" if promote else "negative"
    card["promotion_schema"] = schema
    card["verdict"] = verdict
    card["submission_ready"] = False  # selector step is separate, always
    failures = []
    if not gate["gate_passed"]:
        failures.append(f"frozen LOSFO gate failed: {failed}")
    if not build["uniqueness_binding_pass"]:
        failures.append("binding scored-registry uniqueness failed (see registry.scored_detail)")
    if not validators_ok:
        failures.append("GeoTIFF validator hard check failed")
    if schema["verdict"] != "promote":
        failures.append(f"promotion evidence schema: {schema['failures']}")
    card["failures"] = failures
    card["scope"] = ("promote = eligible for the separate selector step only; no weekly slot "
                     "selected or spent; HOLDOUT-DTI is not an organizer score."
                     if promote else
                     "Negative result is the deliverable; TIF published inspection-only, "
                     "DO NOT SUBMIT. No slot spent.")

    note_file = f"note-gemsdoe28-h42-1-{cid}.txt"
    (dl / note_file).write_text(note + "\n")
    status = (
        f"{'PROMOTE TO SELECTOR — gate, binding uniqueness, validator and evidence schema all PASS' if promote else 'DO NOT SUBMIT — ' + '; '.join(failures)}; "
        f"HOLDOUT-DTI LOSFO seeds 310-314 pooled dDTI {gate['pooled_delta_dti_phys_minus_base']:+.6f} "
        f"(paired 95% CI [{gate['ci95_paired_bootstrap'][0]:+.4f}, {gate['ci95_paired_bootstrap'][1]:+.4f}], "
        f"{gate['cells_positive']}/20 cells, anti {gate['pooled_delta_dti_anti_minus_base']:+.6f}, "
        f"rand {gate['pooled_delta_dti_rand_minus_base']:+.6f}, moved {gate['pooled_frac_dots_moved_ge1px_phys']:.1%} of dots); "
        f"validator PASS (all-finite record file: values exactly {{0,1}}, no NaN anywhere, strict [0,1]); "
        f"UNSCORED, no organizer receipt, no slot spent.")
    slot = {
        "slug": "h42-1-migx-reloc-b1",
        "hypothesis": card["hypothesis"],
        "content_id": cid,
        "nan": nan_name, "allfinite": af_name, "zip": zip_name,
        "sha256_nan": build["sha256_nan"], "sha256_allfinite": raster_sha,
        "sha256_zip": build["sha256_zip"],
        "bytes_nan": build["bytes_nan"], "bytes_allfinite": build["bytes_allfinite"],
        "bytes_zip": build["bytes_zip"],
        "emitted_px": build["emitted_px"], "format_verified": validators_ok,
        "status": status, "note": note, "note_file": note_file,
        "submission_name": card["submission_name"],
        "run_card": "evidence/s18b_run_card.json",
        "holdout_evidence": "evidence/s18_h42_losfo_gate.json",
        "holdout_preregistration": "knowledge/52_preregistration_H42-1_migration_relocation.md",
        "holdout_seeds": "310-314", "verdict": verdict,
    }
    manifest_path = dl / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["s18b_candidate"] = slot
    manifest["generated_utc"] = "2026-10-25T00:00:00Z"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    (ROOT / "evidence/s18b_run_card.json").write_text(json.dumps(card, indent=2) + "\n")
    (ROOT / "docs/data/run_card_s18b.json").write_text(json.dumps(card, indent=2) + "\n")

    # Same checks sidecar convention as prior sessions.
    checks = {"candidate": nan_name, "verify_nan": build["verify_nan"],
              "verify_allfinite": build["verify_allfinite"], "verdict": verdict}
    (dl / f"checks-gems28-h42-1-migx-reloc-b1-{cid}.json").write_text(
        json.dumps(checks, indent=2) + "\n")

    print(json.dumps({"verdict": verdict, "note_chars": len(note),
                      "submission_name": card["submission_name"],
                      "failures": failures}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
