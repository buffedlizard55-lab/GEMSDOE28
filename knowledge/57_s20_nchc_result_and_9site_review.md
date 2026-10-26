# Session 20 Scientific Report & Nine-Site Executive Review (`S20-NCHC` / `H43-1`)

- **Date (UTC):** `2026-10-26`
- **Repository / Branch:** `buffedlizard55-lab/GEMSDOE28` (`arena/3a8a5bef-gemsdoe28`)
- **Generated Unique GeoTIFF (All-Finite `[0, 1]`):** [`docs/downloads/gems28-s20-nchc-20261026-d432a1d5d6ee-allfinite.tif`](../docs/downloads/gems28-s20-nchc-20261026-d432a1d5d6ee-allfinite.tif) (`830,586` bytes, SHA-256 `1d629d6c953c94681ecfe51111d4210361f7014b1df41f5fcfa8d81c4f54f853`, `40,071` off-catalogue positive dots, `0` catalogue overlap)
- **Template-NaN Twin & ZIP:** [`gems28-s20-nchc-20261026-d432a1d5d6ee-nan.tif`](../docs/downloads/gems28-s20-nchc-20261026-d432a1d5d6ee-nan.tif) · [`gems28-s20-nchc-20261026-d432a1d5d6ee-nan.zip`](../docs/downloads/gems28-s20-nchc-20261026-d432a1d5d6ee-nan.zip)
- **Unique Portal Name:** `GEMSDOE28-S20-NCHC-20261026-d432a1d5d6ee`
- **Short Submission Note (`93 / 140` chars):** `S20-NCHC nematic+claycap 300m submod B2 40071d | HOLDOUT-DTI 0.1313 vs 0.1444 | DO NOT SUBMIT`
- **Automated Gate Verdict:**
  - **OK TO DOWNLOAD FOR RESEARCH / INSPECTION:** **YES** (`407 / 407` byte/grid/range/hash checks PASS in `scripts/verify_downloads.py`; strict `[0.0, 1.0]` whole-array check PASS; uniqueness PASS across all `112` published 9-site+PR48 rasters and all `118` method rasters incl. historic references; all `28` single-feature leakage canaries PASS with `max AUC = 0.6010 <= 0.90`).
  - **OK TO SUBMIT TO DRIVENDATA PORTAL:** **NO — DO NOT SPEND A WEEKLY SUBMISSION SLOT.** Pooled `HOLDOUT-DTI` (`gems-segment-pooled-v1`, `60,988` withheld positives) was **`0.131263` (`95% CI [0.120346, 0.141838]`)** vs the retrained visible-only 32-band H38 baseline **`0.144433` (`95% CI [0.131520, 0.157926]`)**, paired delta **`-0.013171` (`95% CI [-0.027721, -0.000417]`)**. `scripts/check_promotion.py` automatically rejected promotion (`verdict: "negative"`, `slot_selected: false`). Zero weekly slots were consumed.

---

## 1. Executive Scorecard Across All Nine Focus Repositories (`2026-10-26 UTC`)

Every score label strictly distinguishes **`USER-REPORTED / UNVERIFIED`** (owner-supplied leaderboard claims without a DrivenData submission-page receipt in git), **`HOLDOUT-DTI`** (internal buffered whole-segment hide-and-recover evaluation with evaluator version, withheld positive count, and 95% CI), and **`ORGANIZER-CONFIRMED`** (none in any of the 9 repositories, as no organizer receipt image/JSON is checked in).

| Focus Site (`HEAD` inspected `2026-10-26`) | Highest Historical Submission (`USER-REPORTED / UNVERIFIED`) | Latest `2026-10-26` Unique Lane & `HOLDOUT-DTI` | Site Verdict & Submission Readiness | Verified Links |
| :--- | :--- | :--- | :--- | :--- |
| **GEMSDOE24** (`bb1a82c`) | `gems24-h25-1-dotted-h19-5-d1-5` (`60,069` px) — **0.2477** (`USER-REPORTED / UNVERIFIED`) | `gems24-gvc1-negative-geothermal-lineament-submod` — `HOLDOUT-DTI` **0.14876** (`gems-segment-pooled-v1`, 60,988 withheld, CI `[0.13413, 0.16370]`) | Historical raster is duplicate family; latest unique lane marked **DOWNLOAD: YES · SUBMIT: NO**. | [Repo](https://github.com/buffedlizard55-lab/GEMSDOE24) · [Pages](https://buffedlizard55-lab.github.io/GEMSDOE24/) |
| **GEMSDOE25** (`8af3ba1`) | `gems25-dotted-h19-5-d2-8` (`44,090` px) — **0.2600** (`USER-REPORTED / UNVERIFIED`) | Radiometric-offset (`ROD`, `2026-10-26`) tested vs H35 comparator — negative holdout delta | Historical `d=2.8` is `H19-5` thinning; latest `ROD` marked **OK TO SUBMIT: NO**. | [Repo](https://github.com/buffedlizard55-lab/GEMSDOE25) · [Pages](https://buffedlizard55-lab.github.io/GEMSDOE25/) |
| **GEMSDOE27** (`5a4a6b1`) | `gems27-topo-gap-closure-t-v2-on-d1-5` (`61,328` px) — **0.2449** (`USER-REPORTED / UNVERIFIED`; `H29-S` owner-reported `0.2190`) | `H30` chem-deconf (`38,000` px) — `HOLDOUT-DTI` **0.09608** vs `B` `0.10031` / `D` `0.10234` (59,372 withheld, CI delta `[-0.00800, -0.00112]`) | `T-v2` gap-closure hurt live (`-0.0028` vs `0.2477`); `H30` unique (`<=64.8%`) but **DO NOT SUBMIT**. | [Repo](https://github.com/buffedlizard55-lab/GEMSDOE27) · [Pages](https://buffedlizard55-lab.github.io/GEMSDOE27/) |
| **GEMSDOE28** *(this repo + `S20-NCHC`)* | `gems28-h36-1-rung30-blind-r1` (`37,660` px) — **0.2710** (`USER-REPORTED / UNVERIFIED`; `solo-r1` `40,199` px **0.2708**) | **`S20-NCHC` (`d432a1d5d6ee`, `40,071` px)** — `HOLDOUT-DTI` **0.13126** (`gems-segment-pooled-v1`, 60,988 withheld, CI `[0.12035, 0.14184]`) vs `B0` **0.14443** (`S19` `0.08081`, `S18` `0.02038`) | **`S20-NCHC` (`0.1313`) is `GEMSDOE28`'s strongest strictly unique raster (`53.6%` max overlap; won `SW` fold `+0.0134`), but pooled gate failed -> DO NOT SUBMIT.** | [Repo](https://github.com/buffedlizard55-lab/GEMSDOE28) · [Pages](https://buffedlizard55-lab.github.io/GEMSDOE28/) |
| **GEMSDOE30** (`781eea0`) | `gemsdoe30-d28-poisson300m-offcat-44090` (`44,090` px) — **0.2600** (`USER-REPORTED / UNVERIFIED`) | `H-NEARSPLAY` (`662af003`) & `MSDB-1v2` — incomplete full-registry / baseline evidence | `44,090` file is `H19-5 d=2.8` family; current candidates **not cleared for a slot**. | [Repo](https://github.com/buffedlizard55-lab/GEMSDOE30) · [Pages](https://buffedlizard55-lab.github.io/GEMSDOE30/) |
| **GEMSDOE31** (`11c8f6b`) | `gemsdoe31-h27-4-solo-d28` (`40,199` px) — **0.2708** (`USER-REPORTED / UNVERIFIED`) | `H31-M` (`gemsdoe31-holdout-v1`: `0.1350` vs `0.1135`); `CONCORD31` / `MAGREST` (`37,654` px) | `solo-d28` is byte-identical to `GEMSDOE28` `8acb75e1f2cc`; latest artifacts marked **DO NOT SUBMIT**. | [Repo](https://github.com/buffedlizard55-lab/GEMSDOE31) · [Pages](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) |
| **GEMSDOE32** (`69d3abe`) | **`gemsdoe32-h33-h33-2-b2-...-e5eb6e7e-zeros`** (`37,654` px) — **0.2778** (**HIGHEST `USER-REPORTED / UNVERIFIED` ACROSS ALL 9 SITES**) | `R6-1 STEP` (`23fbbb51`, `37,654` px) — **demoted `2026-10-26`** in `69d3abe` after audit found full-catalogue `B=2` leakage prior to holdout | **`e5eb6e7e` (`0.2778`) is the historical 9-site benchmark (already submitted; must NOT be copied). `R6-1` is DO NOT SUBMIT.** | [Repo](https://github.com/buffedlizard55-lab/GEMSDOE32) · [Pages](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) |
| **GEMSDOE33** (`c9a2425`) | `GEMSDOE33-h33d-analog-tip-stepover-r30` (`41,865` px) — **0.2632** (`USER-REPORTED / UNVERIFIED`) | `A33-L1` analog-transfer (`85c94a805a34`, `37,654` px) — failed preregistered holdout gate | Historical `0.2632` is `H19-5` derivative; `A33-L1` marked **NEGATIVE — NOT OK TO SUBMIT**. | [Repo](https://github.com/buffedlizard55-lab/GEMSDOE33) · [Pages](https://buffedlizard55-lab.github.io/GEMSDOE33/) |
| **GEMSDOE36** (`1f92ee9`) | `gemsdoe36-anderson-geothermal-pinn-38854` (`38,854` px) — **0.2750** (`USER-REPORTED / UNVERIFIED`) | **`Lane36-SupGBM` (`f35cb3e4`, `68,302` px)** — **`HOLDOUT-DTI` 0.1777 `[0.164, 0.191]`** (`gems-segment-pooled-v1`, 60,988 withheld) vs `0.1615` champion-analog (`overlap <= 43.7%`, `Spearman = 0.13`) | **Strongest positive `SegmentHoldout` unique lane across all 9 sites** (`slot_selected: false`, awaiting separate human selector step). | [Repo](https://github.com/buffedlizard55-lab/GEMSDOE36) · [Pages](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) |

---

## 2. PhD-Level Explanation: Why `GEMSDOE32` (`e5eb6e7e`, Reported `0.2778`) Won Among the Nine Sites & How to Surpass `0.2778` Toward `0.3195` / `0.4413`

### 2.1 Byte-Exact Forensic Lineage of `0.2778`
Cross-repository byte hashing (`evidence/s18_champion_forensic.json`) proves that the entire `0.1922 -> 0.2778` progression across the 9 focus sites came from **allocation-geometry compression and catalogue-flank hygiene** applied to a **single unchanged probability surface (`H19-5`)**, with zero new fault pixels discovered:

1. `H19-5` solid ridges (`GEMSDOE24` `e27054cf`, `121,131` px): `0.1922` (`USER-REPORTED`)
2. Poisson-disk thinned at $d = 1.5\text{ px}$ (`GEMSDOE24` `989f59505db1`, `60,069` px): `0.2477` (`+0.0555`)
3. Poisson-disk thinned at $d = 2.8\text{ px}$ (`GEMSDOE25` / `GEMSDOE30` `e56ea318af89`, `44,090` px): `0.2600` (`+0.0123`)
4. Pruned of $d_{\text{cat}} \le 1\text{ px}$ ($100\text{ m}$) catalogue flanks (`GEMSDOE28` / `GEMSDOE31` `8acb75e1f2cc`, `40,199` px): `0.2708` (`+0.0108`)
5. Pruned of $d_{\text{cat}} \le 2\text{ px}$ ($200\text{ m}$) catalogue flanks (`GEMSDOE32` `e5eb6e7e`, `37,654` px = `40,199 - 2,545` px, `0` added px): **`0.2778`** (`+0.0070`)
6. `GEMSDOE36` `9b9ea4e6` (`38,854` px = `e5eb6e7e` $\cup$ `1,200` PINN dots): `0.2750` (`-0.0028`, proving those 1,200 added dots performed below marginal break-even).

### 2.2 Exact Distance-Weighted Tversky Calculus Explaining Every Jump
Per the official DrivenData problem specification ([page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)), predictions $p(x) \in [0, 1]$ on non-catalogue footprint pixels $x \in \Omega \setminus C$ are scored against hidden expert-verified faults $G \subset \Omega \setminus C$ via the $R = 300\text{ m}$ ($3\text{ px}$) triangular kernel $k(d) = \max(1 - d/R, 0)$:

$$\text{TP}_w = \sum_{g \in G} \max_{x} p(x)\,k(\|x - g\|), \qquad \text{FP}_w = \sum_{x \in \Omega \setminus C} p(x)\Bigl(1 - \max_{g \in G} k(\|x - g\|)\Bigr), \qquad \text{FN}_w = |G| - \text{TP}_w,$$

$$\text{DTI} = \frac{\text{TP}_w}{\text{TP}_w + \alpha\,\text{FP}_w + \beta\,\text{FN}_w} = \frac{\text{TP}_w}{0.8\,|G| + 0.2\,\text{TP}_w + 0.2\,\text{FP}_w}, \qquad (\alpha = 0.2,\; \beta = 0.8).$$

Differentiating $\text{DTI}$ with respect to adding $\Delta N$ unit-weight dots carrying marginal uncovered true-positive credit $\Delta \text{TP}_w = e_{\text{marg}}\,\Delta N$ (so $\Delta \text{FP}_w \approx (1 - e_{\text{marg}})\Delta N$ on sparse support) yields the **exact marginal break-even theorem**:

$$\frac{\Delta\,\text{DTI}}{\Delta N} > 0 \iff e_{\text{marg}} > \tau(\text{DTI}) = \frac{\alpha\,\text{DTI}}{1 - \alpha\,\text{DTI} + \alpha\,\text{DTI}} \approx \frac{0.2\,\text{DTI}}{1 - 0.2\,\text{DTI}}.$$

- **Why $d = 2.8\text{ px}$ thinning (`121,131 -> 44,090` px) gained `+0.0678` DTI:** Because $\text{TP}_w$ uses a **supremum** ($\max_x$) over the $300\text{ m}$ cone while $\text{FP}_w$ **sums** over every emitted pixel, contiguous 1-px ridges pay $3\times$ the $\text{FP}_w$ denominator tax inside each $300\text{ m}$ disk while $\max_x k(\|x-g\|)$ is already saturated at $\ge 1 - 1.4/3 = 0.533$ by dots spaced $2.8\text{ px}$ apart.
- **Why `B=2` ($d_{\text{cat}} > 200\text{ m}$) pruning (`44,090 -> 37,654` px) gained another `+0.0178` DTI (`0.2600 -> 0.2778`):** Calibration against the spacing-5 uniform lattice (`0.0904` at `204,504` px; `knowledge/07_live_score_inversion.md`) pins hidden truth mass at $|G| \approx 12,226\text{ px}$. At $\text{DTI} = 0.2778$, the break-even credit per dot is $\tau(0.2778) = \mathbf{0.0588}$. Detector ridges within $100\text{–}200\text{ m}$ of mapped catalogue faults are overwhelmingly **lateral blur halos of already-masked catalogue scarps** rather than distinct parallel unmapped faults, earning only $e_{\text{flank}} \approx 0.0034\text{ credit/dot}$ ($17\times$ below break-even). Deleting those $6,436$ flank pixels (`3,891` at $d_{\text{cat}} \le 1\text{ px}$ + `2,545` at $1 < d_{\text{cat}} \le 2\text{ px}$) removed $\sim 1,280$ denominator units while sacrificing almost zero $\text{TP}_w$.

### 2.3 Reconciling `0.3195` vs `0.4413` & How a Genuine New Submission Can Surpass `0.2778`
- **Reconciliation of the two cited leaderboard maxima (`registry/irregularities.json` `s20-public-leaderboard-04413-vs-03195-reconciled`):** One-off read-only verification of the official public DrivenData leaderboard ([leaderboard URL](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)) on `2026-10-26` confirmed that `0.3195` was the earlier `2026-10-03` `#1` public snapshot (`DARD`), whereas by `2026-10-26` the live public leaderboard top 5 reached **`0.4413` (`#1 xiaofanhu`)**, **`0.3916` (`#2 cfld__`)**, **`0.3904` (`#3 Batik Shirt Brothers`)**, **`0.3724` (`#4 BrandenKMurray`)**, and **`0.3553` (`#5 No Fault of Our Own`)**.
- **Why `0.2778` can be substantially exceeded — and what is mathematically required:**
  At $|G| \approx 12,226\text{ px}$ and $N \approx 37,654\text{ px}$, `0.2778` corresponds to capturing only $\text{TP}_w \approx 4,760\text{ px}$ ($\sim 39\%$ distance-weighted recall of $G$), whereas `0.4413` corresponds to $\text{TP}_w \approx 7,500\text{–}8,500\text{ px}$ ($\sim 61\text{–}70\%$ weighted recall). Pruning `H19-5` further (`B=3`) is exhausted and duplicate (`>95%` overlap). Reaching `0.32–0.44+` with a genuinely unique submission requires:
  1. **Multi-scale spatial context & convolutional/operator representation** combining *both* **asymmetric 1st/2nd-order geomorphic break-in-slope scarps** (for Basin-and-Range range-front & piedmont faults) *and* **level-invariant multi-physics potential-field / conductive-base / hydrothermal concordance** (for concealed intrabasinal & Walker Lane strike-slip/stepover faults).
  2. **Survey-artifact de-confounding:** Explicitly separating E–W GeoDAWN flight-line leveling stripes (`200–400 m` spacing, azimuth $90^\circ$) and steep-terrain helicopter drape anomalies ([Glen & Earney, 2024](https://doi.org/10.5066/P93LGLVQ)) plus missing-swath 3DEP LiDAR masks from genuine tectonic lineaments.
  3. **Calibrated DTI-optimal spatial allocation:** Coupling `B=2` ($d_{\text{cat}} > 200\text{ m}$) off-catalogue hygiene with 300 m kernel-coverage allocation (`coverage_greedy`) over calibrated positive probabilities rather than uncalibrated heuristic surfaces.

---

## 3. Session 20 Experimental Results (`S20-NCHC` / `H43-1`) & Fold-Level Discovery

### 3.1 Summary of the Three Preregistered Experiments (`evidence/s20_nchc_*.json`)
1. **Experiment 1 (`evidence/s20_nchc_exp1_surface.json`):**
   - Built the 28-feature level-invariant stack (`s20_nchc_features.npy`, SHA-256 `c62ea017...`, zero raw scalar elevation/gravity/magnetic level bands, `dist_known_fault_px` strictly banned).
   - **Single-feature leakage canary (`SegmentHoldout.canary`):** **ALL 28 FEATURES PASSED** (`0.4937 <= AUC <= 0.6010`, well inside `[0.10, 0.90]`; `topo_tubular_1000m` strongest at `0.6010`, `top2_harmonic_1000m` second at `0.5829`, `geodawn_ew_stripe_150m` neutral/negative at `0.4966`).
   - **Pre-placement OOF surface uniqueness:** **PASSED** across all `112` unique published 9-site+PR48 rasters (`max |Spearman| = 0.1035 <= 0.90`; diagnostic top-37,654 3-px overlap `0.5137 <= 0.70`).
2. **Experiment 2 (`evidence/s20_nchc_exp2_holdout.json`, `gems-segment-pooled-v1`, `60,988` withheld positives):**

| Quadrant Fold | Withheld Truth (`px`) | `S20-NCHC` `HOLDOUT-DTI` (`Emitted`) | `B0` Retrained 32-Band+H38 (`Emitted`) | `B1` Retrained 32-Band `B=2 d=2.8` (`Emitted`) | Paired Delta (`S20 - B0`) | Geological Regime Interpretation |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| **`NW`** | `10,165` | `0.147968` (`9,686`) | `0.149113` (`10,232`) | `0.150293` (`10,669`) | `-0.001145` | Volcanic-tableland / normal-fault mix: near parity (`-0.11%`) with `546` fewer FPs. |
| **`NE_LidarGapHeavy`** | `12,511` | `0.143145` (`10,597`) | `0.172542` (`12,433`) | `0.173849` (`13,089`) | `-0.029397` | Classic Basin-and-Range horst/graben: symmetric Hessian of $\|\nabla z\|$ peaks upslope of piedmont break-in-slope! |
| **`SW` (Walker Lane)** | **`20,534`** | **`0.112115` (`12,359`)** | `0.098698` (`12,634`) | `0.100160` (`13,364`) | **`+0.013416` (WIN)** | **Walker Lane transtensional shear, stepovers & geothermal corridors: `+13.6%` relative DTI win with fewer dots!** |
| **`SE`** | `17,778` | `0.134261` (`9,268`) | `0.172605` (`10,571`) | `0.175007` (`11,075`) | `-0.038344` | Basin-and-Range range-front normal faults: needs signed piedmont inflection ($\partial_{nn} z > 0$) + asymmetric LiDAR upface/downface. |
| **Pooled (`583` 10 km blocks)** | **`60,988`** | **`0.131263`** `[0.1203, 0.1418]` | **`0.144433`** `[0.1315, 0.1579]` | **`0.146082`** `[0.1331, 0.1597]` | **`-0.013171`** `[-0.0277, -0.0004]` | **Pooled gate FAIL -> `verdict: "negative"`, `DO NOT SUBMIT`.** |

3. **Experiment 3 (`evidence/s20_nchc_exp3_emission.json`, `evidence/s20_nchc_run_card.json`):**
   - Full-footprint 5-seed ensemble (`seeds 340–344`) + `B=2` + `coverage_greedy(R=300m)` naturally converged at **`40,071` positive pixels** (`830,586` bytes).
   - **Post-placement uniqueness:** **PASSED** across all `112` published 9-site+PR48 rasters (`max |Spearman| = 0.0583 <= 0.90`, `max 3-px overlap = 0.5363 <= 0.70` vs `52a13184267e` — breaking Session 16's `91.3%` duplicate barrier by `37.7` percentage points!) and across all `118` method rasters incl. historic references (`max 3-px overlap = 0.5835 <= 0.70` via `gems.novelty.compare_prospective_registry`).
   - **Actionable Discovery for Session 21:** `S20-NCHC` proved that level-invariant nematic multi-physics concordance + hydrothermal corridor features + 300 m submodular coverage **breaks the `52a13184267e` duplicate trap AND beats the 32-band baseline by `+0.0134` in the Walker Lane (`SW`)**, while diagnosing the exact missing physical operator for `NE`/`SE` Basin-and-Range range fronts: **signed slope-normal break-in-slope concavity ($\partial_{nn} z > 0$ at the mountain-to-piedmont inflection) + signed LiDAR upface/downface scarp polarity**.
