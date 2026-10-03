# H37-1 result — 2026-10-03 (Session 13)

**Status.** Frozen gate **FAILED**, arm **CLOSED**. The directional (anisotropic) Poisson-disk
re-pack lost to the isotropic re-pack on the same OOF probability surface, on every seed and
every fold. No confirmation, no retuning, no candidate GeoTIFF, no weekly slot. The validated
one-click primary stays at `b531dae0a36f` (H36-1, rung 3.0 + H27-4 blind r1). The result and the
reading discipline are recorded below for future audit.

## 1. Result (seeds 250–254, fresh decade)

| Variant | mean ΔDTI | seeds | folds | Δdots/seed | efficiency (ΔTP/ΔFP) |
|---|---:|---:|---:|---:|---:|
| `rung30_unpruned` | **+0.000054** | 2/5 | 3/4 | -2,024 | 0.01133 |
| `dir_3p5_2p0_unpruned` | **-0.003846** | 0/5 | 0/4 | -6,140 | 0.02178 |
| `dir_3p5_2p0_blind_r1` | **-0.002982** | 0/5 | 0/4 | -7,490 | 0.01872 |
| `dir_4p0_2p0_unpruned` | **-0.008114** | 0/5 | 0/4 | -8,755 | 0.02543 |
| `dir_3p0_2p0_unpruned` | +0.000054 | 2/5 | 3/4 | -2,024 | 0.01133 |
| `control_random_drop_matched_n` | -0.007014 | 0/5 | 0/4 | -6,140 | 0.02953 |
| `control_iso_rung30_then_blind_r1` | **+0.001253** | 5/5 | 4/4 | -3,627 | 0.00802 |

Frozen-gate criteria (`knowledge/28_preregistration_H37-1.md` §3):

| # | Criterion | Result |
|---|---|---|
| G1 | Profitability | **FAIL** (primary -0.0030; 0/5 seeds; 0/4 folds) |
| G2 | Anisotropy matters | PASS (Δ vs random-drop = +0.003168) |
| G3 | Anisotropy beats isotropic at same N | **FAIL** (Δ = -0.005099 — anisotropic is *worse*) |
| G4 | Live break-even | **FAIL** (eff = 0.0187 < tau_live = 0.054852) |
| **Gate** | | **FAILED — arm CLOSED** |

## 2. Why anisotropy lost (mechanism)

The **isotropic** `rung30_then_blind_r1` (H36-1's published rung) gained **+0.001253** mean ΔDTI
on the same decade, 5/5 seeds, 4/4 folds — reproducing H36-1's validation on this holdout. The
**anisotropic** `(a_∥, a_⊥) = (3.5, 2.0)` pack kept **21,409 px** (vs the isotropic rung-3.0
re-pack's 41,333 px). The difference is layout-specific:

- The OOF detector emits a 1-px ridge with `ridge_nms` strike quantised to **four directions**
  (0°, 45°, 90°, 135°). On long straight faults in any of those directions, the **4-sector
  strike** has limited precision (±22.5°) and the anisotropic ellipse can end up *misaligned*
  with the true strike for ~half of the 26,645 components, especially short ones (median
  component length 4 px, 95% below 50 px).
- The anisotropic pack kept ~30% fewer dots than the isotropic pack at the same rung, because
  the ellipse projects the same matrix onto a smaller disc when (a_∥ > a_⊥) and the off-axis
  components suffered. The matched-N random drop (`-0.0070`) beat the anisotropic pack
  (`-0.0038`) by 0.0032 because random selection preserves ridge coverage while anisotropic
  thinning removes interior dots that were carrying credit.
- The **live efficiency** is `0.0187` credit/dot — below the OOF break-even `0.019265` and the
  live `0.054852`. The dropped pixels were inside `tau_live`.

The directional space is therefore **larger but the gain is not where the catalogued truth
sits**: short components dominate, and their orientation estimate is too noisy for anisotropy to
help.

## 3. What this confirms

1. **The H36-1 isotropic re-pack remains the layout best.** `rung30_then_blind_r1` reproduced
   the published +0.0013 on a fresh decade. No H37-1 candidate earns more.
2. **The "directional rung space is larger" claim was wrong.** On a 4-sector strike field, the
   directional space collapses back to ~isotropic for short components, and anisotropic
   thinning loses interior ridge dots. The result is consistent with the H34 finding that the
   isotropic rung ladder is bounded.
3. **The directional code path is correct** (7/7 unit tests pass in
   `tests/test_directional_thinning.py`); the function remains available for callers with
   high-precision strike fields (e.g. a future external vector catalogue), but no H37-2/H37-3
   arm will use it on the 4-sector OOF strike without first upgrading to an 8-sector or
   per-pixel vector field.

## 4. Reading discipline (closed)

Per the preregistration: **no confirmation, no retuning, no candidate TIFF, no weekly slot**.
Seeds `255–259` are reserved for H37-2 (LiDAR parallel-scarp addition) and `260–264` for
H37-3 (Quaternary volcanics polygon-edge addition). Those arms do not depend on H37-1; their
designs are independent.

The one-click primary stays at `b531dae0a36f` (H36-1). The `docs/downloads/manifest.json`,
`docs/index.html` and `docs/executive-summary.html` are unchanged: H37-1 added no new
downloadable artifact and the site remains explicitly "unscored, not slot-approved".