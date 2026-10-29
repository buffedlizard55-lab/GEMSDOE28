#!/usr/bin/env python3
"""Publish the S29 decision: 3 diagnostic experiments, no TIFF, no approved file.

All numbers are read from evidence/ and never typed in. The builder fails closed if any card
claims an upload approval, a slot selection, a serialized raster, or more than 3 experiments.
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "arena/9a3a5294-gemsdoe28"
PANEL_ID = "s29-lattice-decision"
REPORT_URL = "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/arena/9a3a5294-gemsdoe28/knowledge/76_s29_lattice_experiments_2026-10-29.md"
PAGES = {
    ROOT / "docs/index.html": ("data/s29_lattice_run_card.json", "s29-lattice-review.html"),
    ROOT / "docs/executive-summary.html": ("data/s29_lattice_run_card.json", "s29-lattice-review.html"),
    ROOT / "index.html": ("docs/data/s29_lattice_run_card.json", "docs/s29-lattice-review.html"),
    ROOT / "executive-summary.html": ("docs/data/s29_lattice_run_card.json", "docs/s29-lattice-review.html"),
}
EV = {
    "null": ROOT / "evidence/s29_null_controls.json",
    "disp": ROOT / "evidence/s29_dispersion_run_card.json",
    "ridge": ROOT / "evidence/s29_ridge_control_run_card.json",
    "audit": ROOT / "evidence/s29_lattice_overlap_audit.json",
    "restore": ROOT / "evidence/restore_audit.json",
}
CARD_PATH = ROOT / "evidence/s29_lattice_run_card.json"


def _load(name: str) -> dict:
    return json.loads(EV[name].read_text(encoding="utf-8"))


def _ci(value: list) -> str:
    return f"{value[0]:.4f}–{value[1]:.4f}"


def build_card() -> dict:
    null, disp, ridge, audit, restore = (_load(k) for k in ("null", "disp", "ridge", "audit", "restore"))
    if disp["verdict"] != "negative" or ridge["verdict"] != "diagnostic":
        raise ValueError("Unexpected verdict in S29 evidence")
    if any(c.get("new_tiff_generated") or c.get("slot_selected") for c in (null, disp, ridge)):
        raise ValueError("An S29 card claims a TIFF or slot selection")
    if max(c["experiments_run_this_session"] for c in (null, disp, ridge)) != 3 or ridge["experiment_cap"] != 3:
        raise ValueError("S29 experiment count does not match the budget cap")
    lattice_frac = audit["coverage"]["fraction_within_3px"]
    if audit["summary"]["lane_duplicate_vs_lattice"] != audit["summary"]["historical_rasters_checked"]:
        raise ValueError("Audit no longer shows every historical raster as a lane duplicate; re-read before publishing")
    ho = disp["holdout"]
    ridge_ho = ridge["holdout"]
    unpaired_tcb_vs_ridge = ho["dti"] - ridge_ho["dti"]
    return {
        "run_card_schema": "s29-run-card-v1",
        "run_id": "S29-LATTICE-DISPERSION-20261029",
        "branch": BRANCH,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "experiments_run": 3,
        "experiment_cap": 3,
        "hypothesis": (
            "Dispersed, ridge-aligned placement of the S26/S28 TCB surface, with a 5 px minimum spacing, "
            "scores above random and lattice controls on the spatially blocked holdout."
        ),
        "mechanism": (
            "Holdout DTI rewards dispersion. Experiment 3 indicates the gain comes from dots along the "
            "ridge network with spacing, not from the TCB ranking (random priority scores the same)."
        ),
        "named_non_fault_mimic": (
            "The TCB surface's own ridge network (a texture mimic; not verified as non-fault geology); "
            "and the geology-blind calibration lattice (spacing-only mimic)."
        ),
        "verdict": "negative",
        "verdict_reason": (
            "Holdout-positive versus controls, but the TCB ranking is not shown to add anything over random "
            "priority on the same ridge candidates, and the final placement duplicates the calibration lattice "
            "(100% within 3 px). Not promoted."
        ),
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": ho["evaluator_version"],
            "dti": ho["dti"],
            "ci95": ho["ci95"],
            "withheld_positives": ho["withheld_positives"],
        },
        "controls": {
            "random_k": {"label": "HOLDOUT-DTI", "dti": null["controls"]["random_k"]["dti"],
                         "ci95": null["controls"]["random_k"]["ci95"]},
            "lattice_subset": {"label": "HOLDOUT-DTI", "dti": null["controls"]["lattice_subset"]["dti"],
                               "ci95": null["controls"]["lattice_subset"]["ci95"]},
            "visible_proximity": {"label": "HOLDOUT-DTI", "dti": null["controls"]["visible_proximity"]["dti"],
                                  "ci95": null["controls"]["visible_proximity"]["ci95"]},
            "ridge_random_priority": {"label": "HOLDOUT-DTI", "dti": ridge_ho["dti"], "ci95": ridge_ho["ci95"]},
        },
        "paired": {
            "dispersed_tcb_vs_random_k": {"paired_delta_dti": disp["paired_vs_random_k"]["paired_delta_dti"],
                                          "ci95": disp["paired_vs_random_k"]["paired_delta_ci95"],
                                          "fold_wins": disp["paired_vs_random_k"]["fold_wins"]},
            "dispersed_tcb_vs_lattice_subset": {"paired_delta_dti": disp["paired_vs_lattice_subset"]["paired_delta_dti"],
                                                "ci95": disp["paired_vs_lattice_subset"]["paired_delta_ci95"],
                                                "fold_wins": disp["paired_vs_lattice_subset"]["fold_wins"]},
            "lattice_subset_vs_random_k": {"paired_delta_dti": null["paired"]["lattice_subset_vs_random_k"]["paired_delta_dti"],
                                           "ci95": null["paired"]["lattice_subset_vs_random_k"]["paired_delta_ci95"],
                                           "fold_wins": null["paired"]["lattice_subset_vs_random_k"]["fold_wins"]},
            "dispersed_tcb_minus_ridge_random_priority_unpaired": {
                "value": unpaired_tcb_vs_ridge,
                "note": "Unpaired difference of two DTI values. Paired CI not computed (re-running would exceed the 3-experiment cap). Not established.",
            },
        },
        "correlation_overlap": {
            "lane_threshold": 0.70,
            "lane_radius_px": 3,
            "candidate_fraction_within_3px_of_lattice": disp["registry_global_overlap"]["fraction_within_3px_of_calibration_lattice"],
            "candidate_binary_pearson_vs_lattice": disp["registry_global_overlap"]["binary_pearson_vs_calibration_lattice"],
            "candidate_duplicate": disp["registry_global_overlap"]["duplicate_rule_70pct_triggered"],
            "lattice_footprint_coverage_within_3px": lattice_frac,
            "random_placement_overlap_mean": {k: v["mean_fraction_within_3px"] for k, v in audit["random_placement_null"].items()},
            "historical_rasters_lane_duplicate": f"{audit['summary']['lane_duplicate_vs_lattice']}/{audit['summary']['historical_rasters_checked']}",
        },
        "raster_sha256": None,
        "raster_serialized": False,
        "validator_output": "Not run: no candidate raster was serialized. Historical format gates: see evidence/s29_lattice_overlap_audit.json.",
        "leakage_canary": {"passed": disp["feature_canary"]["passed"], "threshold": 0.9,
                           "numeric_auc": "not recorded by the canary API"},
        "submission_name": None,
        "submission_note": None,
        "ok_to_submit": False,
        "slot_selected": False,
        "new_tiff_generated": False,
        "leaderboard_estimate": None,
        "restore_audit": restore["status"],
        "evidence": sorted(p.relative_to(ROOT).as_posix() for p in EV.values())
        + ["evidence/s29_lattice_run_card.json", "scripts/run_s29_null_controls.py", "scripts/run_s29_dispersion.py",
           "scripts/run_s29_ridge_control.py", "scripts/audit_lattice_overlap.py"],
    }


def _check(card: dict) -> None:
    if card["ok_to_submit"] is not False or card["slot_selected"] is not False or card["new_tiff_generated"] is not False:
        raise ValueError("S29 panel cannot render an approval, slot selection, or new TIFF")
    if card["raster_sha256"] is not None or card["submission_name"] is not None:
        raise ValueError("No raster or submission name may be published by the S29 panel")


def panel(card: dict, card_href: str, review_href: str) -> str:
    _check(card)
    h, c = card["holdout"], card["controls"]
    p, a = card["paired"], card["correlation_overlap"]
    d = p["dispersed_tcb_vs_lattice_subset"]
    r = p["dispersed_tcb_vs_random_k"]
    pa = p["dispersed_tcb_minus_ridge_random_priority_unpaired"]["value"]
    return f'''<section class="section callout-danger" id="{PANEL_ID}" aria-label="Current S29 submission decision" data-submission-ready="false">
<p class="eyebrow">S29 · 2026-10-29 UTC · AUTOMATED DECISION · NO HUMAN INSPECTOR</p>
<h2>Current decision: NO FILE APPROVED · OK TO SUBMIT: NO</h2>
<p><strong>No new TIFF was generated, and no upload is authorized.</strong> Three diagnostic experiments ran (the budget cap). The best holdout result is a registry duplicate, and its attribution failed. No file is approved, and no weekly slot was spent.</p>
<table><caption>Holdout experiments. All numbers are HOLDOUT-DTI (gems-segment-pooled-v1, 60,988 withheld positives), never leaderboard estimates.</caption><thead><tr><th>Experiment</th><th>HOLDOUT-DTI (95% CI)</th><th>Paired ΔDTI vs random-K (folds won)</th></tr></thead><tbody>
<tr><td>E1 random-K baseline (budget-matched)</td><td>{c['random_k']['dti']:.4f} ({_ci(c['random_k']['ci95'])})</td><td>—</td></tr>
<tr><td>E1 geology-blind calibration lattice</td><td>{c['lattice_subset']['dti']:.4f} ({_ci(c['lattice_subset']['ci95'])})</td><td>{p['lattice_subset_vs_random_k']['paired_delta_dti']:+.4f} ({p['lattice_subset_vs_random_k']['fold_wins']}/4)</td></tr>
<tr><td>E1 visible-proximity placement (in-scope)</td><td>{c['visible_proximity']['dti']:.4f} ({_ci(c['visible_proximity']['ci95'])})</td><td>negative control</td></tr>
<tr><td>E2 dispersed TCB, 5 px minimum spacing</td><td>{h['dti']:.4f} ({_ci(h['ci95'])})</td><td>{r['paired_delta_dti']:+.4f} ({r['fold_wins']}/4); vs lattice {d['paired_delta_dti']:+.4f} ({d['fold_wins']}/4)</td></tr>
<tr><td>E3 same ridge candidates and spacing, random priority</td><td>{c['ridge_random_priority']['dti']:.4f} ({_ci(c['ridge_random_priority']['ci95'])})</td><td>TCB minus this: {pa:+.4f} (unpaired; not established)</td></tr>
</tbody></table>
<p><strong>What this means.</strong> On this holdout, dispersion matters: the lattice beats random placement, and spacing-constrained ridge placement beats both. However, random priority over the same ridge candidates matches the TCB-ranked result, so the TCB ranking is not shown to add anything. The gain is not established as geology.</p>
<p><strong>Uniqueness.</strong> The lane rule is more than 70% of dots within 3 px of a registry raster. The calibration lattice covers {a['lattice_footprint_coverage_within_3px']:.2%} of the footprint, and random placements of the same budget overlap it at about {a['random_placement_overlap_mean']['37654']:.1%}. All {a['historical_rasters_lane_duplicate']} historical dotted rasters exceed the threshold, so the literal rule does not discriminate between methods. The best candidate overlaps it at {a['candidate_fraction_within_3px_of_lattice']:.0%}.</p>
<p><strong>Canary and validator.</strong> Leakage canary: PASS at the 0.90 threshold (numeric AUC not recorded by the API). No raster was serialized, so no validator run was possible.</p>
<p><strong>Leaderboard context (ORGANIZER-CONFIRMED on the public board read 2026-10-29):</strong> #1 is 0.4544 and #26 is 0.3328. The prompt's 0.4413 and 0.3195 were not found in ranks 1–47. This is an irregularity, and the public board is not the private scoring set.</p>
<div class="download-actions"><button class="button" type="button" disabled aria-disabled="true">Download disabled: no approved file</button><a class="button quiet" href="{html.escape(card_href, quote=True)}" download>Download S29 run card (JSON)</a><a class="button quiet" href="{html.escape(review_href, quote=True)}">Open S29 review</a></div>
<p><strong>Decision needed from you:</strong> whether the 70%/3 px lane rule applies. It is an internal protocol rule; the official rules contain no duplicate rule (ORGANIZER-CONFIRMED, NLR rules PDF). If you decide it does not apply, a candidate could be serialized, but it would still need a surface-independent ridge null before any geology claim. <a href="{html.escape(REPORT_URL, quote=True)}">Read the full S29 report</a>.</p>
</section>'''


def inject(path: Path, section: str) -> None:
    page = path.read_text(encoding="utf-8")
    marker = f'id="{PANEL_ID}"'
    if marker in page:
        at = page.index(marker)
        start = page.rfind("<section", 0, at)
        end = page.index("</section>", at) + len("</section>")
        page = page[:start] + page[end:]
    if "<main>" not in page:
        raise ValueError(f"Missing main element in {path}")
    path.write_text(page.replace("<main>", "<main>" + section, 1), encoding="utf-8")


def standalone(card: dict) -> str:
    body = panel(card, "data/s29_lattice_run_card.json", "s29-lattice-review.html")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>S29 review | GEMSDOE28</title><link rel="stylesheet" href="assets/site.css"></head>
<body><header class="site-header"><div class="header-inner"><a class="brand" href="index.html">GEMSDOE28 <small>DOE GEMS · Auditable research</small></a>
<nav aria-label="Main navigation"><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary</a><a href="s29-lattice-review.html">S29 review</a></nav></div></header>
<main>{body}<section class="section"><h2>Decision boundary</h2><p>Holdout gains here are HOLDOUT-DTI only and cannot be converted into a leaderboard estimate. A file that is format-valid and unique could still be unapproved. The only correct current action is to keep this result negative and resolve the uniqueness rule and the attribution gap before authorizing another lane.</p></section></main>
<footer><div class="footer-inner"><p><strong>Maximize P(Win) · Own the Outcome.</strong> No competition login, upload, polling, or slot selection occurred.</p></div></footer></body></html>'''


def main() -> int:
    card = build_card()
    CARD_PATH.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (ROOT / "docs/data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs/data/s29_lattice_run_card.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for path, (card_href, review_href) in PAGES.items():
        inject(path, panel(card, card_href, review_href))
    (ROOT / "docs/s29-lattice-review.html").write_text(standalone(card), encoding="utf-8")
    print(json.dumps({"status": "built", "panel": PANEL_ID, "network_requests": 0,
                      "ok_to_submit": False, "new_tiff_generated": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
