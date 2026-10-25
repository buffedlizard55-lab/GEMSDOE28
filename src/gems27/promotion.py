"""Fail-closed evidence gate. Format validity alone never authorizes submission.

This checks evidence structure, not scientific truth or provenance authenticity.
Callers must retain independently produced, hash-bound evaluator outputs.
"""
from __future__ import annotations

import math
import re


def finite_number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def promotion_gate(card: dict) -> dict:
    failures = []

    def result():
        return {"verdict": "negative" if failures else "promote", "promotion_eligible": not failures,
                "evidence_schema_passed": not failures,
                "submission_ready": False, "failures": failures, "slot_selected": False,
                "scope": "Evidence schema eligibility only; no independent evidence authentication, slot selection, cap check or organizer acceptance."}

    # Evidence is untrusted JSON. Wrong container types must never crash or pass.
    if not isinstance(card, dict):
        failures.append("run card must be an object")
        return result()

    def section(name):
        value = card.get(name)
        if not isinstance(value, dict):
            failures.append(f"missing or malformed object: {name}")
            return {}
        return value

    def require(ok, reason):
        if not ok:
            failures.append(reason)

    def nonempty_text(value):
        return isinstance(value, str) and bool(value.strip())

    require(nonempty_text(card.get("lane")), "missing assigned method lane")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", str(card.get("raster_sha256", "")))), "missing raster SHA-256")
    require(nonempty_text(card.get("submission_name")), "missing submission name")
    note = card.get("note")
    require(isinstance(note, str) and 0 < len(note) <= 140, "note must contain 1–140 characters")
    require(all(nonempty_text(card.get(key)) for key in ("hypothesis", "mechanism", "non_fault_mimic")),
            "missing scientific hypothesis, mechanism, or named confounder")
    h = section("holdout")
    require(h.get("raster_sha256") == card.get("raster_sha256") and bool(h.get("raster_sha256")),
            "holdout raster hash mismatch")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", str(h.get("baseline_sha256", "")))),
            "missing frozen baseline hash")
    require(h.get("label") == "HOLDOUT-DTI" and bool(h.get("evaluator_version")), "missing versioned HOLDOUT-DTI")
    require(isinstance(h.get("withheld_positives"), int) and not isinstance(h.get("withheld_positives"), bool)
            and h["withheld_positives"] > 0, "missing withheld positives")
    ci = h.get("ci95")
    score = h.get("dti")
    require(finite_number(score) and 0 <= score <= 1, "invalid holdout DTI")
    require(isinstance(ci, list) and len(ci) == 2 and all(finite_number(x) for x in ci)
            and finite_number(score) and 0 <= ci[0] <= score <= ci[1] <= 1, "invalid holdout CI")
    gain = h.get("paired_gain_ci95")
    require(isinstance(gain, list) and len(gain) == 2 and all(finite_number(x) for x in gain)
            and 0 < gain[0] <= gain[1] <= 1, "no positive paired gain CI over frozen current best")
    for key in ("whole_segments", "buffered", "visible_only_features", "pixel_exact_visible_mask", "pooled"):
        require(h.get(key) is True, f"holdout protocol missing: {key}")
    require(h.get("alpha") == 0.2 and h.get("beta") == 0.8 and h.get("kernel_m") == 300
            and h.get("kernel") == "triangular", "wrong metric protocol")
    features = card.get("feature_canaries")
    require(isinstance(features, dict) and bool(features), "no feature-alone canaries")
    if isinstance(features, dict):
        for name, auc in features.items():
            # Inverting a near-perfect feature must not evade the leakage canary.
            require(nonempty_text(name) and finite_number(auc) and 0.10 <= auc <= 0.90,
                    f"invalid or leaking feature: {name}")
    registry = section("registry")
    require(registry.get("complete") is True and bool(re.fullmatch(r"[0-9a-f]{64}", str(registry.get("manifest_sha256", "")))), "registry incomplete")
    members = registry.get("members")
    valid_members = (isinstance(members, list) and bool(members)
                     and all(isinstance(x, str) and re.fullmatch(r"[0-9a-f]{64}", x) for x in members))
    require(valid_members, "missing or invalid registry member identities")
    expected = set(members) if valid_members else set()
    require(not valid_members or len(expected) == len(members), "duplicate registry member identities")
    for stage in ("surface", "dots"):
        comparisons = registry.get(stage)
        require(isinstance(comparisons, list) and bool(comparisons), f"no {stage} registry comparisons")
        if isinstance(comparisons, list):
            identities = []
            for comparison in comparisons:
                if not isinstance(comparison, dict):
                    failures.append(f"malformed {stage} registry comparison")
                    continue
                identity = comparison.get("raster_sha256")
                if isinstance(identity, str):
                    identities.append(identity)
                require(bool(re.fullmatch(r"[0-9a-f]{64}", str(comparison.get("raster_sha256", "")))),
                        f"{stage} registry comparison missing raster identity")
                corr, overlap = comparison.get("spearman"), comparison.get("within_3px_fraction")
                require(finite_number(corr) and -0.90 <= corr <= 0.90,
                        f"{stage} duplicate or undefined correlation")
                # No dots exist at the pre-placement stage. Do not invent their
                # overlap; if supplied it must pass, and it is mandatory on dots.
                if stage == "dots" or overlap is not None:
                    require(finite_number(overlap) and 0 <= overlap <= 0.70,
                            f"{stage} duplicate or undefined overlap")
            require(set(identities) == expected and len(identities) == len(expected),
                    f"{stage} comparisons must cover every registry member exactly once")
    validator = section("validator")
    require(validator.get("raster_sha256") == card.get("raster_sha256"), "validator hash mismatch")
    for key in ("no_nan_inside", "range_0_1", "crs_match", "shape_match", "transform_match", "single_band"):
        require(validator.get(key) is True, f"validator failed or absent: {key}")
    return result()
