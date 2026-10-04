# 39 — Session 14 Results: `H36-1` Far-Field Verification (`F1–F4` PASS) & `H38-1` Multi-Physics Corroboration (`C1–C4` PASS)

**Date:** 2026-10-03 (UTC)
**Preregistration:** `knowledge/44_preregistration_H36_1_and_H38_farfield.md` (frozen in commit `ff85e30` before any seed in `265–279` was touched)
**Evidence artifacts:**
- `evidence/losfo_session14_h36_1_and_h38.json` (LOSFO far-field evaluation on fresh seeds `265–269`, `20` paired cells)
- `evidence/h38_1_interleaved_holdout.json` (4-fold interleaved spatial-CV evaluation on fresh seeds `270–279`, `40` paired cells)
- `evidence/session14_h36_1_and_h38_integrity.json` (`C4` / `F4` same-seed `181` & `240` bit-identity and geometric invariant audit)
- `docs/downloads/gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif` (`37,860` px, SHA-256 `81d5b87bc8424f162a8f56aa9aac8fbe630c61646b9cac24d5ebbdc1b1951783`)

---

## 1. Part A — `H36-1` LOSFO Far-Field Verification Result (`seeds 265–269`, 20 paired cells)

Session 13 (`knowledge/33`) falsified `H37-1` (`max_coverage` packer) on the LOSFO far-field harness (`-0.000037 ± 0.000832` on seeds `210–214`) and restored `H36-1` (`rung30_blind_r1`, `b531dae0a36f`, $N = 37{,}660\text{ px}$) as the one-click primary, queueing the direct LOSFO far-field test of `H36-1` as the #1 task for Session 14 (`knowledge/36` §5.1).

On fresh, untouched LOSFO seeds `265–269` (`20` paired cells; every hidden truth pixel sits at Euclidean distance $\ge 8.0\text{ px} = 800\text{ m}$ from every known training label), **`H36-1` passes all four frozen criteria (`F1–F4`)**:

| Arm (`losfo` honest detector) | Mean Dots / Cell | Sum $\text{TP}_w$ (`20` cells) | Sum $\text{FP}_w$ (`20` cells) | Credit / Dot | Mean Cell DTI | Pooled DTI | Paired $\Delta\text{DTI}$ vs `base` | Cells Up vs `base` | Seeds Up vs `base` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `base` (`thin_d = 2.8`) | `12,033.1` | `11,184.95` | `235,789.25` | `0.04648` | `0.101278` | `0.102978` | `0.000000` | — | — |
| `h27_4_blind_r1_d280` (`base & ~blind_r1`) | `11,453.2` | `11,184.95` | `224,190.25` | `0.04883` | `0.103526` | `0.105225` | **`+0.002249`** | **`20 / 20`** | **`5 / 5`** |
| `rung30_unpruned` (`thin_d = 3.0`) | `11,380.3` | `10,861.76` | `223,011.59` | `0.04772` | `0.100815` | `0.102475` | `-0.000462` | `1 / 20` | `0 / 5` |
| `control_random_drop_matched_n` (`N = 11,380.3`) | `11,380.3` | `10,643.46` | `223,028.13` | `0.04676` | `0.098742` | `0.100453` | `-0.002535` | `0 / 20` | `0 / 5` |
| **`rung30_blind_r1` (`H36-1` primary rule)** | **`10,829.9`** | **`10,861.76`** | **`212,002.59`** | **`0.05015`** | **`0.102990`** | **`0.104648`** | **`+0.001713`** | **`16 / 20`** | **`5 / 5`** |
| `control_random_drop_matched_r1` (`N = 10,829.9`) | `10,829.9` | `10,242.59` | `212,219.58` | `0.04729` | `0.097180` | `0.098760` | `-0.004097` | `0 / 20` | `0 / 5` |

### Frozen `F1–F4` Gate Audit (`seeds 265–269`):
- **`F1` (`rung30_unpruned` vs `control_random_drop_matched_n`) — PASS:**
  `mean ΔDTI = +0.002073` (`17/20` cells positive, `5/5` seeds positive: `265: +0.001947`, `266: +0.001417`, `267: +0.002205`, `268: +0.003218`, `269: +0.001578`). At identical dot count (`11,380.3` dots/cell), Poisson-disk re-packing at $d = 3.0\text{ px}$ preserves `+218.30 px` more far-field truth credit than content-blind random deletion because the Second-Pixel Redundancy Theorem holds along far-field 1D fault traces just as it holds on the full map.
- **`F2` (Far-field removal efficiency $e_{\text{far}}(2.8 \to 3.0) < \tau_{\text{live}} = 0.054852$) — PASS:**
  Moving from $d = 2.8\text{ px}$ to $d = 3.0\text{ px}$ removes `12,777.66` units of $\text{FP}_w$ while losing only `323.19` units of $\text{TP}_w$, giving a pooled far-field removal efficiency of:
  $$e_{\text{far}}(2.8 \to 3.0) = \frac{323.191}{12{,}777.659} = \mathbf{0.025293} < \tau_{\text{live}} = 0.054852 \quad (19 / 20\text{ cells below }\tau_{\text{live}}).$$
  Note why raw cell DTI for `rung30_unpruned` alone is `-0.000462` on the 20% single-fold LOSFO split (`D_cell = 0.1013`, where $\tau_{\text{cell}} = 0.02067$) even though $e_{\text{far}} = 0.02529 < \tau_{\text{live}} = 0.054852$: a 20% held-out slice has only $1/5$ of the full hidden truth density, so its cell break-even bar is $0.02067$, whereas on the full map at $D_{\text{live}} = 0.2600$ the break-even bar is $\tau_{\text{live}} = 0.054852$ (`2.17×` higher than $e_{\text{far}} = 0.02529$).
- **`F3` (`rung30_blind_r1` one-click primary vs `base`) — PASS:**
  `rung30_blind_r1` improves raw LOSFO cell DTI by **`+0.001713`** (`16/20` cells positive, `5/5` seeds positive: `265: +0.001101`, `266: +0.002087`, `267: +0.001291`, `268: +0.002756`, `269: +0.001328`), beats its matched-count random drop control by **`+0.005810` (`20/20` cells)**, and achieves a pooled removal efficiency of:
  $$e_{\text{far}}(\text{rung30\_blind\_r1}) = \frac{323.191}{23{,}786.659} = \mathbf{0.013587} \ll \tau_{\text{live}} = 0.054852 \quad (20 / 20\text{ cells below }\tau_{\text{live}}).$$
- **`F4` (`h27_4_blind_r1_d280` triangle-inequality zero-loss guarantee) — PASS:**
  `h27_4_blind_r1_d280` removes `11,599.0` pure false-positive dots while losing **exact zero** far-field truth credit (`sum_tp_removed = 0.0` across all `20/20` cells), improving LOSFO DTI by **`+0.002249` (`20/20` cells, `5/5` seeds)**.

---

## 2. Part B — `H38-1` & `H38-2` Multi-Physics Corroboration Results

### 2.1 LOSFO Far-Field Gate (`seeds 265–269`, 20 paired cells)

| Arm (`losfo` honest detector) | Added Dots (`20` cells) | Arm Credit / Dot | Sub-Ridge Ctrl Credit / Dot | Random Ctrl Credit / Dot | Mean Paired $\Delta\text{DTI}$ vs Ref | Mean $\Delta\text{DTI}$ vs Sub-Ridge Ctrl | Mean $\Delta\text{DTI}$ vs Random Ctrl | Cells Up vs Ref | Seeds Up vs Ref | `C1` | `C2` ($\ge 0.05485$) | `C3a` | `C3b` | **`ALL_PASS`** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|
| **`h38_1_joint` (`H38-1` on `base_d28`)** | **`1,468`** | **`0.07724`** | `0.04098` | `0.02333` | **`+0.000792`** | **`+0.000446`** | **`+0.000761`** | **`17 / 20`** | **`4 / 5`** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **`h38_1_joint_on_r30_r1` (`H38-1` on `H36-1`)** | **`1,536`** | **`0.06993`** | `0.03227` | `0.02681` | **`+0.000747`** | **`+0.000587`** | **`+0.000649`** | **`16 / 20`** | **`4 / 5`** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| `h38_1a_heatflow` (`hf_resid >= 50` alone) | `1,357` | **`0.08827`** | `0.04225` | `0.01657` | `+0.000918` | `+0.000552` | `+0.000964` | `14 / 20` | `4 / 5` | FAIL (`14/20`) | PASS | PASS | FAIL (`14/20`) | FAIL |
| `h38_1b_euler_lineament` (`d_eu <= 3.0` alone) | `1,288` | `0.04277` | `0.04245` | `0.02659` | `+0.000245` | `-0.000135` | `+0.000164` | `12 / 20` | `4 / 5` | FAIL | FAIL | FAIL | FAIL | FAIL |
| `h38_2_low_relief_euler` (`relief <= P35 & d_eu <= 3`) | `1,120` | `0.01398` | `0.04375` | `0.02841` | `-0.000045` | `-0.000446` | `-0.000113` | `5 / 20` | `1 / 5` | FAIL | FAIL | FAIL | FAIL | FAIL |

### 2.2 Per-Quadrant Fold Breakdown on LOSFO (`seeds 265–269`)

| Quadrant Fold | `h38_1_joint` Mean $\Delta\text{DTI}$ | `h38_1_joint` Credit / Dot | `h38_1_joint_on_r30_r1` Mean $\Delta\text{DTI}$ | `h38_1_joint_on_r30_r1` Credit / Dot |
|---|---:|---:|---:|---:|
| `NW` | **`+0.000756`** | `0.06013` | **`+0.000532`** | `0.04372` |
| `NE_LidarGapHeavy` | **`+0.000588`** | `0.06048` | **`+0.000776`** | **`0.07110`** |
| `SW` | **`+0.000363`** | `0.05000` | **`+0.000265`** | `0.03927` |
| `SE` | **`+0.001461`** | **`0.13998`** | **`+0.001417`** | **`0.13042`** |

### 2.3 Standing 4-Fold Interleaved Spatial-CV Holdout (`seeds 270–279`, 40 paired cells)

| Arm (`oof_detector` 4-fold spatial CV) | Added Dots (`40` cells) | Arm Credit / Dot | Sub-Ridge Ctrl Credit / Dot | Random Ctrl Credit / Dot | Mean Paired $\Delta\text{DTI}$ vs Ref | Cells Up (`/40`) | Seeds Up (`/10`) | Folds Up (`/4`) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`h38_1_joint` (`H38-1` on `base_d28`)** | **`2,961`** | **`0.06440`** | `0.02518` | `0.01043` | **`+0.000656`** | **`27 / 40`** | **`9 / 10`** | **`4 / 4`** |
| **`h38_1_joint_on_r30_r1` (`H38-1` on `H36-1`)** | **`3,161`** | **`0.05269`** | `0.02746` | `0.01814` | **`+0.000543`** | **`27 / 40`** | **`8 / 10`** | **`4 / 4`** |
| `h38_1a_heatflow` (`hf_resid >= 50` alone) | `2,772` | **`0.06784`** | `0.02481` | `0.01813` | `+0.000666` | `26 / 40` | `9 / 10` | `4 / 4` |
| `h38_1b_euler_lineament` (`d_eu <= 3.0` alone) | `2,485` | `0.02768` | `0.02470` | `0.02010` | `+0.000114` | `21 / 40` | `7 / 10` | `3 / 4` |
| `h38_2_low_relief_euler` (`relief <= P35 & d_eu <= 3`) | `2,192` | `0.02684` | `0.02489` | `0.02184` | `+0.000081` | `19 / 40` | `7 / 10` | `3 / 4` |

---

## 3. Physical Synthesis: Why `H38-1` Succeeded Where `H35-1`, `H35-4`, and `H37-3` Failed

1. **De-convected conductive heat-flow residual (`hf_resid`, DeAngelo et al., 2022) vs raw well temperature (`H35-1`):**
   `H35-1` (`knowledge/24`) used raw well/spring temperatures (`gdr_wellspring_in_footprint.csv`), which are dominated by shallow lateral outflow plumes in basin-fill aquifers and normal-gradient deep oil/gas wells, earning only `0.0132` / `0.0431` credit/dot (`< 0.05485`). By contrast, `USGS_gbHeatFlowWells_wEstimates.shp` (`DeAngelo et al., 2022`, DOI [10.5066/P9BZPVUC](https://doi.org/10.5066/P9BZPVUC)) subtracts a regional 2D-LOESS conductive heat-flow surface (`hf_est`) from measured borehole conductive heat flow (`hf_meas`), isolating `hf_resid >= 50 mW/m²` — localized vertical hydrothermal upflow along permeable fault conduits. On LOSFO far-field truth, `h38_1a_heatflow` alone earns **`0.08827` credit/dot** (`2.09×` the uncorroborated sub-threshold ridge `0.04225` and `5.33×` random `0.01657`).
2. **Lineament-pinned SI=0 Euler contact clusters (`d_eu <= 3.0` on `ridge_nms`) vs raw Euler centroids (`H37-3`):**
   `H37-3` (`knowledge/35`) emitted at raw rounded Euler cluster centroids `(round(row), round(col))` and earned `0.03116` credit/dot because a $1\text{ km} \times 1\text{ km}$ Euler window has a `100–300 m` down-dip horizontal offset from the surface fault trace (`Reid et al., 1990`, DOI [10.1190/1.1442774](https://doi.org/10.1190/1.1442774)). Pinning emission to the 100 m `ridge_nms` crest within `300 m` (`3 px`) of the shallow SI=0 Euler cluster (`h38_1b_euler_lineament`) raises far-field marginal efficiency by **+37.3%** (`0.03116 -> 0.04277` credit/dot), and in the `SW` quadrant fold earns **`0.07456` credit/dot** (where `h38_1a_heatflow` alone was weak at `0.02271` due to sparser borehole coverage in `SW`!).
3. **Why the joint multiplicative corroboration (`h38_1_joint`) passes all 4 criteria (`17/20` cells on `base`, `16/20` on `H36-1`, `4/4` folds):**
   `h38_1a_heatflow` is strongest in `SE` (`0.1931` c/dot), `NW` (`0.0782` c/dot), and `NE_LidarGapHeavy` (`0.0610` c/dot) but sparser in `SW` (`0.0227` c/dot, leaving it at `14/20` cells). Conversely, `h38_1b_euler_lineament` is strongest in `SW` (`0.0746` c/dot). Ranking `(hf_halo | euler_halo)` on `sub_pool` by $p(x)\,[1 + 0.5\,\mathbb{I}(\text{hf\_halo}) + 0.5\,\mathbb{I}(\text{euler\_halo})]$ prioritizes double-corroborated lineaments first and fills well-sparse quadrants (`SW`) with Euler-corroborated lineaments, achieving **`0.07724` credit/dot (`17/20` cells, `4/4` folds)** on `base` and **`0.06993` credit/dot (`16/20` cells, `4/4` folds, `+0.002460` total ΔDTI over `base`)** on `H36-1` (`rung30_blind_r1`).
4. **Why `H38-2` (`low_relief_euler`) is refuted (`-0.000045`, `0.01398` credit/dot, `5/20` cells):**
   Restricting Euler-corroborated ridges to the flattest alluvial basins (`relief <= P35`) fails because the hidden truth in `labels.tif` is itself drawn from the scarp-biased USGS Quaternary compilation (`knowledge/35`). Even when a buried basin fault exists geophysical-magnetically, if it was never mapped in the USGS compilation, it is scored as a false positive against `labels.tif`.

---

## 4. Full-Map Submission Package & Slot Disposition

Per `knowledge/38` §4.3, `scripts/build_h38_1_hf_euler_submissions.py` built and verified the full-map `H38-1` package on top of `H36-1` (`37,660` px + `200` globally `2.8 px`-thinned corroborated ridge dots = `37,860` px):
- **Primary (`docs/downloads/manifest.json` `"primary"`):** `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` (`37,660` px, SHA-256 `5556aa14…`), now carrying its verified LOSFO far-field record (`F1–F4` ALL PASS on `seeds 265–269`, `+0.001713` far-field ΔDTI, $e_{\text{far}} = 0.01359 < 0.054852$) alongside its interleaved record (`+0.002599` on `seeds 240–249`). Kept at `"primary"` because all `37,660` pixels come strictly from the live-scored `H19-5` (`0.2600`) surface.
- **Secondary (`docs/downloads/manifest.json` `"secondary"`):** `gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif` (`37,860` px, SHA-256 `81d5b87b…`), `-allfinite.tif` (`529d9e1b…`), `.zip` (`681f0e67…`), and `note-gemsdoe28-h38-1-hf-euler-r30-r1-56a9f473edc7.txt` (`196` chars), which passed **both** the LOSFO far-field gate (`C1–C4` ALL PASS, `+0.000747` over `H36-1`, `0.06993` credit/dot) **and** the 10-seed interleaved gate (`+0.000543` over `H36-1`, `8/10` seeds, `4/4` folds).
