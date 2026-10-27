#!/usr/bin/env python3
"""Fail-closed read-only audit of an inherited candidate and a registry control.

Reuses the pinned shared novelty/validator. No model, surface, dot placement,
submission writer, network request or weekly slot is exercised. A duplicate
returns exit 1, with a negative report replacing any earlier green output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27.evidence_json import loads  # noqa: E402
from gems27.registry_feasibility import coverage_bounds  # noqa: E402
from gems27.shared_template import load_shared, verify_assets  # noqa: E402

CONTROL_FILE = "inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
CONTROL_SOURCE = (
    "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/"
    "07345ea0604953d7efb858d9cfbc21e20c7aca0b/" + CONTROL_FILE
)
HISTORICAL = ROOT / "docs/downloads/gems28-s22-ctxhgb-20261026-e23dabcec6e2-allfinite.tif"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_binary(path, template):
    with rasterio.open(template) as t, rasterio.open(path) as s:
        if (s.count, s.shape, s.crs, s.transform) != (1, t.shape, t.crs, t.transform):
            raise ValueError(f"Raster grid differs from trusted template: {path}")
        fp = np.isfinite(t.read(1))
        a = s.read(1)
    if not np.isfinite(a[fp]).all() or not np.isin(a[fp], [0, 1]).all():
        raise ValueError(f"Expected finite binary footprint: {path}")
    return fp, fp & (a > 0)


def audit(args):
    assets = verify_assets()
    if not assets["passed"]:
        raise ValueError("Shared template integrity failed")
    shared = load_shared()
    registry = loads(args.registry.read_text())
    control_rows = [r for r in registry["unique_rasters"] if r["file"] == CONTROL_FILE]
    if len(control_rows) != 1:
        raise ValueError("Exactly one registered spacing-5 control required")
    row = control_rows[0]
    if sha(args.control) != row["sha256"]:
        raise ValueError("Control file SHA-256 differs from the shared registry")
    footprint, reference = read_binary(args.control, args.template)
    foot_hash = hashlib.sha256(reference[footprint].astype("<f4").tobytes()).hexdigest()
    if foot_hash != row["footprint_sha256"]:
        raise ValueError("Control footprint values differ from the shared registry")
    bounds, _ = coverage_bounds(
        footprint, reference, budget=args.budget, min_spacing_px=args.min_spacing,
    )
    # The shared tool is authoritative for the unspaced counting bound. The
    # local extension independently adds the spacing partition capacity only.
    control_classification = shared.novelty.classify_space_filling_control(
        footprint, reference, candidate_dot_count=args.budget,
    )
    if not (
        bounds["covered_pixels"] == control_classification["footprint_3px_covered_pixels"]
        and bounds["uncovered_pixels"] == control_classification["footprint_3px_uncovered_pixels"]
        and np.isclose(bounds["unspaced_overlap_lower_bound"],
                       control_classification["pigeonhole_min_overlap_for_candidate_size"])
    ):
        raise AssertionError("Geometry extension disagrees with pinned shared novelty")

    _, dots = read_binary(args.candidate, args.template)
    registered = {**row, "cache_path": str(args.control.resolve())}
    # This is the inherited FINAL raster, not its missing pre-placement surface.
    comparison = shared.novelty.compare_registry(
        dots.astype(np.float32), footprint, [registered], ROOT,
        dots=dots, template_path=args.template,
    )
    validator = shared.submission.check_variants(args.candidate, args.template)
    summary = comparison["rows"][0]
    duplicate = bool(summary["duplicate"])
    return {
        "schema": "registry-feasibility-audit-v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "label": "GEOMETRY-AUDIT (not HOLDOUT-DTI or an organizer score)",
        "status": "DUPLICATE_STOP" if duplicate or bounds["target_budget_impossible"] else "NECESSARY_CONDITION_ONLY",
        "control": {
            "file": CONTROL_FILE, "sha256": row["sha256"], "footprint_sha256": foot_hash,
            "source": CONTROL_SOURCE, "registry_member_id": row["id"],
            "shared_registry_path": str(args.registry.relative_to(ROOT)) if args.registry.is_relative_to(ROOT) else str(args.registry),
            "shared_registry_sha256": sha(args.registry),
        },
        "bounds": bounds,
        "shared_control_classification": control_classification,
        "inherited_candidate": {
            "path": str(args.candidate.relative_to(ROOT)) if args.candidate.is_relative_to(ROOT) else str(args.candidate),
            "sha256": sha(args.candidate), "dots": int(dots.sum()),
            "final_dot_comparison": comparison,
            "duplicate_under_literal_rule": duplicate,
            "preplacement_surface_tested": False,
            "preplacement_surface_status": "Not available; a final binary raster must not be relabeled as a pre-placement surface.",
            "format_validator": validator,
            "disposition": "DO NOT SUBMIT; historical promote claim cannot override this literal-rule failure" if duplicate else "No promotion inferred",
        },
        "shared_assets": assets,
        "code_sha256": {
            "scripts/audit_registry_feasibility.py": sha(Path(__file__)),
            "src/gems27/registry_feasibility.py": sha(ROOT / "src/gems27/registry_feasibility.py"),
        },
        "new_tiff_generated": False,
        "geological_experiments_run": 0,
        "new_holdout_run": False,
        "submission_ready": False,
        "slot_selected": False,
        "scope": "One registered comparator is sufficient to reject a lane; this is not a complete global registry or a proof against every possible smaller dot budget.",
        "next_action": "Stop the inherited lane. Do not omit the control or relocate predictions into lattice holes. Resolve the registry protocol before scientific promotion.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=ROOT / "data/sample_submission.tif")
    parser.add_argument("--control", type=Path, default=ROOT / "data/s23/lattice.tif")
    parser.add_argument("--registry", type=Path, default=ROOT / "data/research/shared_priority_registry.json")
    parser.add_argument("--candidate", type=Path, default=HISTORICAL)
    parser.add_argument("--budget", type=int, default=37654)
    parser.add_argument("--min-spacing", type=float, default=2.8)
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/s23_registry_feasibility.json")
    args = parser.parse_args(argv)
    try:
        result = audit(args)
    except (OSError, KeyError, TypeError, ValueError, AssertionError) as exc:
        result = {"status": "BLOCKED", "error": str(exc), "submission_ready": False,
                  "new_tiff_generated": False, "slot_selected": False, "geological_experiments_run": 0}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "output": str(args.out),
                      "submission_ready": False, "slot_selected": False}, indent=2))
    return 0 if result["status"] == "NECESSARY_CONDITION_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
