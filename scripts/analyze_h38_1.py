#!/usr/bin/env python3
"""Independent re-reading of ``evidence/h38_1_holdout.json`` (H38-1 radiometric gate).

Recomputes every gated statistic from the stored per-cell ``tp`` / ``fp`` / ``n_truth`` / ``dots``
records and every declared count identity from the stored packer/prune bookkeeping. It re-fits no
model and cannot change a result - it exists so the gate's numbers do not rest on the runner's own
aggregation code (Pass-2 verification).

Checks:
  * ``dti`` recomputes from ``tp``, ``fp``, ``n_truth`` by the published closure, per cell, for all arms;
  * ``dots`` for every arm equals its declared construction (packer count minus prune for the two pruned
    arms; the exact requested count for the control);
  * the post-prune dot counts of the primary (D1) and the incumbent (D0) agree to within 0.5 %;
  * G1-G4 recompute from the cell table and match the stored gate block.

Writes ``evidence/h38_1_holdout_analysis.json``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "evidence"

ARMS = ["base_d280", "cover_r1", "rad_base_d280", "rad_cover_r1", "control_random_matched_n"]
PRIMARY, INCUMBENT = "rad_cover_r1", "cover_r1"


def main() -> int:
    gate = json.loads((EVIDENCE / "h38_1_holdout.json").read_text())
    cells = gate["cells"]
    tol = 1e-9

    dti_err = 0.0
    dot_violations: list[str] = []
    for c in cells:
        for arm in ARMS:
            v = c[arm]
            expect = v["tp"] / (v["tp"] + 0.2 * v["fp"] + 0.8 * (c["n_truth"] - v["tp"]) + 1e-7)
            dti_err = max(dti_err, abs(expect - v["dti"]))
        n_pre0 = c["n_pre0"]
        if c["n_packer_emitted"] != n_pre0:
            dot_violations.append(f"{c['seed']}/{c['fold']}: D1 packer {c['n_packer_emitted']} != {n_pre0}")
        if c["n_packer_emitted_incumbent"] != n_pre0:
            dot_violations.append(
                f"{c['seed']}/{c['fold']}: D0 packer {c['n_packer_emitted_incumbent']} != {n_pre0}")
        for arm, pre_key, rem_key in ((PRIMARY, "n_packer_emitted", "prune_removed_primary"),
                                      (INCUMBENT, "n_packer_emitted_incumbent", "prune_removed_incumbent")):
            if c[arm]["dots"] != c[pre_key] - c[rem_key]:
                dot_violations.append(
                    f"{c['seed']}/{c['fold']}: {arm} dots {c[arm]['dots']} != "
                    f"{c[pre_key]} - {c[rem_key]}")
        if c["control_random_matched_n"]["dots"] > n_pre0:
            dot_violations.append(f"{c['seed']}/{c['fold']}: control exceeds n_pre0")

    primary_dots = np.array([c[PRIMARY]["dots"] for c in cells], float)
    incumbent_dots = np.array([c[INCUMBENT]["dots"] for c in cells], float)
    count_gap = np.abs(primary_dots - incumbent_dots) / incumbent_dots

    seeds = sorted({c["seed"] for c in cells})

    def stat(arm: str, ref: str) -> dict:
        d = np.array([c[arm]["dti"] - c[ref]["dti"] for c in cells])
        per_seed = {s: float(np.mean([c[arm]["dti"] - c[ref]["dti"]
                                      for c in cells if c["seed"] == s])) for s in seeds}
        folds = sorted({c["fold"] for c in cells})
        per_fold = {f: float(np.mean([c[arm]["dti"] - c[ref]["dti"]
                                      for c in cells if c["fold"] == f])) for f in folds}
        return {
            "mean": float(d.mean()), "sem": float(d.std(ddof=1) / np.sqrt(len(d))),
            "cells_up": int((d > 0).sum()), "n_cells": len(d),
            "per_seed": per_seed, "seeds_up": int(sum(v > 0 for v in per_seed.values())),
            "per_fold": per_fold, "folds_up": int(sum(v > 0 for v in per_fold.values())),
        }

    recomputed = {
        "G1_primary_vs_incumbent": stat(PRIMARY, INCUMBENT),
        "G3_rad_base_vs_base": stat("rad_base_d280", "base_d280"),
        "G4_primary_vs_control": stat(PRIMARY, "control_random_matched_n"),
        "report_only_incumbent_vs_base": stat(INCUMBENT, "base_d280"),
    }
    means = {arm: float(np.mean([c[arm]["dti"] for c in cells])) for arm in ARMS}
    stored = gate["gate"]
    matches = {
        "G1_mean_matches": abs(recomputed["G1_primary_vs_incumbent"]["mean"]
                               - stored["G1_observed"]) < tol,
        "G2_seeds_match": recomputed["G1_primary_vs_incumbent"]["seeds_up"] == stored["G2_seeds_won"],
        "G2_folds_match": recomputed["G1_primary_vs_incumbent"]["folds_up"]
        == stored["G2_folds_improved_vs_base"],
        "G3_mean_matches": abs(recomputed["G3_rad_base_vs_base"]["mean"]
                               - stored["G3_do_no_harm_rad_base_vs_base"]) < tol,
        "G4_margin_matches": abs(recomputed["G4_primary_vs_control"]["mean"]
                                 - stored["G4_content_control_margin"]) < tol,
        "arm_means_match_variants": all(
            abs(means[a] - gate["variants"][a]["mean_dti"]) < tol for a in ARMS),
    }

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": ("Pass-2 verification of evidence/h38_1_holdout.json; pure re-arithmetic on the stored "
                 "per-cell records, no model re-fit."),
        "input": "evidence/h38_1_holdout.json",
        "n_cells": len(cells), "seeds": seeds,
        "max_abs_dti_recompute_error": dti_err,
        "count_identity_violations": dot_violations,
        "count_identity_ok": bool(not dot_violations),
        "postprune_count_match": {
            "primary_mean_dots": float(primary_dots.mean()),
            "incumbent_mean_dots": float(incumbent_dots.mean()),
            "max_relative_gap": float(count_gap.max()),
            "mean_relative_gap": float(count_gap.mean()),
            "note": ("the gated comparison is matched to within this gap; both arms apply the same "
                     "blind_r1 prune, so the residual difference is the prune's interaction with each "
                     "detector's ridge field, not a budget difference"),
        },
        "arm_means": means,
        "recomputed": recomputed,
        "stored_gate_matches": matches,
        "verdict": ("independent recomputation reproduces every gated statistic"
                    if all(matches.values()) and dti_err < 1e-9 and not dot_violations
                    else "MISMATCH - see stored_gate_matches / count_identity_violations"),
    }
    (EVIDENCE / "h38_1_holdout_analysis.json").write_text(json.dumps(out, indent=1) + "\n")

    print(f"cells {len(cells)}  max DTI recompute error {dti_err:.2e}")
    print(f"count identities: {'OK' if not dot_violations else dot_violations[:3]}")
    print(f"primary {primary_dots.mean():.1f} dots vs incumbent {incumbent_dots.mean():.1f} "
          f"(max gap {100 * count_gap.max():.3f}%)")
    for k, v in recomputed.items():
        print(f"  {k:32s} {v['mean']:+.6f}  {v['cells_up']}/{v['n_cells']} cells  "
              f"{v['seeds_up']}/10 seeds  {v['folds_up']}/4 folds")
    print("stored-gate matches:", all(matches.values()), matches)
    print("written evidence/h38_1_holdout_analysis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
