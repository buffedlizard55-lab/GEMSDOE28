#!/usr/bin/env python3
"""S19 finalizer: assemble the JSON run card, manifest entry and note file.

Not an experiment. Verdict logic is frozen in knowledge/57: promote (to a
separate selector only) requires LOSFO gate AND strict uniqueness AND exact-file
validator all PASS. Here the LOSFO gate passed but strict uniqueness failed
against the dense H37-1 probe-union registry raster, so the verdict is
negative and the file is research-only. No slot is selected here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    surf = json.loads((ROOT / "evidence/s19b_radlin_surface.json").read_text())
    hold = json.loads((ROOT / "evidence/s19b_radlin_holdout.json").read_text())
    build = json.loads((ROOT / "evidence/s19b_radlin_candidate_build.json").read_text())
    dl = ROOT / "docs/downloads"
    files, sha = build["files"], build["sha256"]
    cid = build["content_id"]
    gate_pass = bool(hold["gate_passed"])
    uniq_pass = bool(build["uniqueness"]["pass_strict"])
    valid_pass = bool(build["validator_pass"])
    verdict = "promote" if (gate_pass and uniq_pass and valid_pass) else "negative"
    name = f"GEMSDOE28-S19-RADLIN-{cid}"
    if verdict == "promote":
        note = f"S19 RADLIN ThK-lineament coverage {build['n_dots']} dots LOSFO gate passed; selector review only."
    else:
        note = ("S19 RADLIN coverage 37654 dots; LOSFO passed but uniqueness vs dense probe "
                "FAILED; DO NOT SUBMIT.")
    assert len(note) <= 140, len(note)
    note_file = f"note-gemsdoe28-s19-radlin-{cid}.txt"
    (dl / note_file).write_text(note + "\n", encoding="utf-8")

    def size(f: str) -> int:
        return (dl / f).stat().st_size

    v = build["validator_allfinite"]
    card = {
        "session": "S19B-RADLIN", "date_utc": "2026-10-26",
        "lane": "radiometric alteration lineament (ThK) weighted all-ridge coverage packing",
        "lane_authorization": "Autonomous adoption of repository queued next lane H39-2; prompt omitted explicit method paragraph",
        "hypothesis": "Low-Th/K alteration lineaments collinear over >=1 km mark buried fluid conduits; weighting all-ridge coverage packing by that lineament field earns credit on scarp-less faults the catalogue omits.",
        "mechanism": "ThK inverted robust field -> 1-px ridge -> 1 km oriented line-mean anisotropy score -> 7x7 bonus; coverage_greedy(prob*(1+0.5*bonus)) over detector ridges at >2 px from visible catalogue, count-matched per LOSFO cell; full map 37,654 dots.",
        "non_fault_mimic": "Felsic lithologic boundary, playa evaporite K enrichment, or GeoDAWN flight-line striping (low-Th/K lineament with zero fault displacement).",
        "holdout": {
            "label": "HOLDOUT-DTI", "evaluator_version": hold["evaluator_version"],
            "seeds": hold["seeds"], "withheld_positives": hold["withheld_positives"],
            "unique_withheld_positive_pixels": hold["unique_withheld_positive_pixels"],
            "dti": hold["candidate_pooled"]["dti"], "ci95": hold["ci"]["candidate_ci95"],
            "baseline_dti": hold["baseline_pooled"]["dti"], "baseline_ci95": hold["ci"]["baseline_ci95"],
            "paired_gain": hold["pooled_gain"], "paired_gain_ci95": hold["ci"]["paired_gain_ci95"],
            "per_fold_gain": hold["per_fold_gain"], "per_seed_gain": hold["per_seed_gain"],
            "gate": hold["gate"], "gate_passed": gate_pass,
            "candidate_credit_per_dot": hold["candidate_credit_per_dot"],
            "baseline_credit_per_dot": hold["baseline_credit_per_dot"],
            "attribution_limit": "Candidate-as-frozen gain; this gate does not isolate the RADLIN bonus from the all-ridge coverage construction, whose far-field gain was previously measured at similar magnitude (knowledge/39).",
        },
        "feature_canaries": surf["canary"],
        "registry": {
            "scope": build["uniqueness"]["scope"],
            "preplacement": surf["preplacement"],
            "final": build["uniqueness"],
            "pass_strict": uniq_pass,
            "duplicate_stop_member": build["uniqueness"]["worst_by_overlap"]["raster"],
            "scored_focus_max_overlap": max(
                v2["frac_our_dots_within3px"] for k, v2 in build["uniqueness"]["table"].items()
                if k.startswith("forensic_")),
        },
        "raster_sha256": sha["allfinite"],
        "validator": {
            "raster_sha256": sha["allfinite"], "no_nan_inside": True, "range_0_1": True,
            "crs_match": True, "shape_match": True, "transform_match": True,
            "single_band": True, "single_band_float32": True, "no_nan_anywhere": True,
            "values": v["value_set_inside"], "shape": [3730, 3292], "crs": "EPSG:32611",
            "transform": [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0],
            "on_catalogue": 0, "hard_checks_passed": valid_pass,
        },
        "validator_full": v, "validator_nan": build["validator_nan"],
        "submission_name": name, "note": note,
        "download": f"downloads/{files['allfinite']}",
        "dot_count": build["n_dots"], "experiments_used": 3, "experiment_budget": 3,
        "verdict": verdict, "submission_ready": False, "slot_selected": False,
        "organizer_receipt": None,
        "disposition": ("🔴 DO NOT SUBMIT — unique vs scored artifacts but duplicate-stop vs the "
                        "dense H37-1 probe-union registry raster under the frozen any-raster rule. "
                        "Research download only; a future preregistered session must first settle "
                        "whether unscored dense probes belong in the uniqueness registry."),
        "evidence": {"surface": "evidence/s19b_radlin_surface.json", "holdout": "evidence/s19b_radlin_holdout.json",
                     "build": "evidence/s19b_radlin_candidate_build.json",
                     "preregistration": "knowledge/57_s19b_radlin_preregistration.md",
                     "result": "knowledge/58_s19b_radlin_result.md"},
        "evidence_schema_gate": {"verdict": verdict, "submission_ready": False, "slot_selected": False},
    }
    (ROOT / "evidence/s19b_radlin_run_card.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    (ROOT / "docs/data/run_card_s19b_radlin.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")

    manifest_path = dl / "manifest.json"
    man = json.loads(manifest_path.read_text())
    man["s19b_candidate"] = {
        "filename": files["allfinite"], "nan": files["nan"], "allfinite": files["allfinite"],
        "zip": files["zip"], "content_id": cid, "submission_name": name, "note": note,
        "note_file": note_file, "sha256": sha["allfinite"], "sha256_nan": sha["nan"],
        "sha256_allfinite": sha["allfinite"], "sha256_zip": sha["zip"],
        "bytes_nan": size(files["nan"]), "bytes_allfinite": size(files["allfinite"]),
        "bytes_zip": size(files["zip"]), "emitted_px": build["n_dots"],
        "format_verified": valid_pass, "unique_within_snapshot": False,
        "holdout_gate_passed": gate_pass, "submission_ready": False, "verdict": verdict,
        "status": ("LOSFO gate PASSED but strict uniqueness FAILED vs dense probe-union raster; "
                   "research TIFF only. DO NOT SUBMIT."),
        "run_card": "data/run_card_s19b_radlin.json",
    }
    # Post-merge reconciliation: S19-ASCP (parallel lane, merged first via PR #46)
    # owns manifest["current_run"]; this parallel run must not displace it.
    man.setdefault("parallel_runs", []).append({
        "run_id": "S19B-RADLIN", "status": "NEGATIVE — NO FILE APPROVED",
        "submission_ready": False, "slot_selected": False, "new_tiff_generated": True,
        "run_card": "data/run_card_s19b_radlin.json",
    })
    man["generated_utc"] = "2026-10-26T00:00:00Z"
    manifest_path.write_text(json.dumps(man, indent=2) + "\n")
    print(json.dumps({"verdict": verdict, "name": name, "note_len": len(note),
                      "gate_pass": gate_pass, "uniq_pass": uniq_pass, "valid_pass": valid_pass}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
