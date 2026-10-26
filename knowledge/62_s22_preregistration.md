# Session 22 preregistration — displaced potential-field piercing markers (`S22-DPMR`)

- **Frozen before implementation/evaluation:** 2026-10-26T21:54:29Z
- **Base commit:** `2c839d10f57ec9b074829e93c84bc39935f52896`
- **Branch:** `arena/eb9644af-gemsdoe28`
- **Budget:** at most 3 experiments and 2 hours of experiment wall time; no competition upload or slot selection
- **Fresh stochastic seeds reserved:** `360–364` (baseline fitting/full-fit only; the selected physical transform is deterministic)
- **Evidence classes:** every local metric will be labelled `HOLDOUT-DTI`; owner-site values remain `USER-REPORTED / UNVERIFIED`; any live-score estimate will be labelled `MODEL PROJECTION — NOT A SCORE`.

## 0. Lane declaration and irregularity

The owner prompt says that the lane is “the single method paragraph below,” but it contains no uniquely identifiable method assignment. This is a material parallel-run irregularity. Because the same prompt requires autonomous completion with no manual input, this session makes a **disclosed self-assignment** and claims no cross-run exclusivity. A bounded, HEAD-pinned nine-site raster snapshot will be taken before placement. If either the surface rank correlation exceeds `0.90` or more than `70%` of the prospective/final dots lie within 3 pixels of any one registry raster, the lane stops as a duplicate.

**S22 lane (the only candidate-producing method):** *Detect a concealed fault corridor from a coherent non-zero lateral registration shift of potential-field piercing markers across that corridor. On robust, band-pass magnetic RTP and isostatic-gravity fields, compare local patches sampled on opposite sides of each of four candidate fault strikes; reward a common ±200–600 m along-strike shift that improves normalized patch correlation over the zero-shift continuation in both modalities, then place 300 m-kernel-aware, catalogue-clear dots on that label-free surface.*

Educational champion forensics, baseline recomputation, validation, documentation and site generation do not create candidate dots and are not alternative lanes.

## 1. Five candidate geological hypotheses ranked before implementation

Ranges below are **pre-run planning judgements**, not scores or projections. “Untried” means no implementation was found in this repository’s `src/`, `scripts/`, or `tests` at the freeze time; it is not a claim about every parallel repository.

| Rank | Hypothesis; exact layers | Physical signature | Why it can reveal a catalogue-missing fault | Difference from existing local work | Named non-fault mimic | Expected HOLDOUT-DTI improvement / cost / data gate |
|---:|---|---|---|---|---|---|
| **1 (selected)** | **S22-H1 displaced potential-field piercing-marker registration**; cached `rtp` and `iso_grav_anom` from the prepared 32-band stack | Across four trial fault strikes, opposite-side band-pass patches match better after one common non-zero ±2–6 px along-strike translation than with zero translation; multi-scale and magnetic–gravity agreement suppress a lone contact edge | A buried strike-slip/oblique fault can offset pre-existing magnetic or density contacts while having no young surface scarp; the predicted corridor is the cross-cutting displacement plane, not either contact | Existing edge, Euler, migration and nematic modules score contact strength/location; repository search found no cross-corridor patch-registration/displacement transform | Intrusive branching/contact geometry; acquisition seams; chance texture repetition | **Planning `+0.005…+0.020` / medium CPU.** Required bytes are already represented by the hash-pinned competition mirror; no new external source |
| **2** | **Patch encoder–decoder segmentation**; all 32 cached physical channels | Learned 0.3–5 km spatial texture and continuity, optimized with Tversky-style loss | Weak but spatially coherent scarps/lineaments can be invisible to a per-pixel tree | No trained neural model exists locally; official reference solution establishes this as a relevant model class, not a copied owner raster | Roads, channels and catalogue mapping style | **Planning `+0.010…+0.040` / high.** 100 m stack is obtainable; honest four-fold CPU training is unlikely inside two hours and no GPU is available, so not selected |
| **3** | **Signed piedmont break-in-slope × LiDAR scarp polarity**; `det_elev`, `det_elev_slope`, LiDAR `upface_max`, `downface_max`, `cross_max`, gravity context | Ordered slope-normal concavity and asymmetric crest/toe polarity at basin-facing range fronts | Degraded or sediment-covered normal-fault scarps retain asymmetric profile curvature after sharp relief is erased | Prior ASCP/vesselness used symmetric/local strength; no frozen lane has combined signed piedmont-normal profile order with shoreline suppression | Lahontan shorelines, terrace risers, fan toes and road cuts | **Planning `+0.004…+0.015` / medium.** Cached layers available; proposed previously but not implemented as this signed operator |
| **4** | **Cross-scale phase-coherent shallow-source termination**; `rtp`, `tmi`, `tmi_vg`, `TMI_up150` | A lineament endpoint persistent in shallow magnetic gradients but attenuated/rotated after upward continuation | A shallow buried fault tip can terminate/offset a magnetic boundary without mapped rupture | Different from scalar upward-continuation ratios and Euler point clusters: tests phase/termination persistence | Lava-flow margin, cultural magnetic source, flight-line levelling | **Planning `+0.002…+0.010` / medium.** GeoDAWN extension mirror is obtainable and pinned; not selected because prior magnetic-only lanes transferred poorly |
| **5** | **Depth-decoupled MT conductance column**; official USGS multi-depth conductance slices plus `cond_surf` | Upper-crustal conductive-gradient alignment that decorrelates from lower-crustal terrane fabric | A blind fluid-bearing brittle fault can be conductive without a mapped Quaternary scarp | No multi-depth MT column is implemented locally | Graphitic shale, saline playa brine, regional terrane boundary | **Planning `0…+0.008` / high.** Specific official source: USGS data release DOI `10.5066/P9TWT2LU`; the required five slice bytes are absent and the official host is outside this sandbox allowlist, so this is **not presently viable** |

**Selection rule:** S22-H1 has the highest expected information gain per unit implementation cost among candidates that can be tested now without new external data. S22-H2 has the largest upside but cannot honestly reach the required buffered holdout standard on the available CPU budget.

## 2. Frozen S22-H1 implementation

### 2.1 Label-free surface

1. Read only `rtp` and `iso_grav_anom` columns from `data/prepared/features.npy`; nearest-fill non-finite source cells for convolution, robust-standardize each field over the competition footprint, and clip to `[-5,5]`.
2. For each field form band-pass maps `G_1(F) - G_8(F)` and `G_2(F) - G_12(F)` (pixels; 100 m/pixel), then robust-scale local gradient magnitude/support to `[0,1]`.
3. Trial integer fault-strike unit directions `(0,1)`, `(1,1)`, `(1,0)`, `(1,-1)`. For each, sample patches centered `3 px` to either side of the corridor normal. Compute 9×9 local normalized cross-correlation (NCC) between opposite-side band-pass maps at zero shift and at signed along-strike displacements `d ∈ {-6,-4,-2,+2,+4,+6}` pixels.
4. Per field/scale/strike/shift evidence is `clip(NCC_d - NCC_0, 0, 1)` multiplied by the geometric mean of opposite-side gradient support. Require scale persistence by geometric mean across the two scales. At each exact strike/shift combine magnetic and gravity evidence as `0.70*sqrt(M*G) + 0.30*max(M,G)`; the `0.30` term permits a marker absent from one modality while preserving a cross-modal preference. The surface is the maximum over the frozen strike/shift set, robust-scaled to `[0,1]`, zero outside the footprint. No catalogue, prior submission, score or label is an input.
5. Feature-alone leakage canaries are run on the magnetic evidence, gravity evidence and fused surface before trusting any result. `max(AUC,1-AUC) > 0.90` stops the run pending leakage proof.

### 2.2 Surface and dot uniqueness

Take a HEAD-pinned snapshot of every published submission-grid TIFF in `docs/downloads/`, `submissions/`, and `archive/legacy_candidates/` across GEMSDOE24/25/27/28/30/31/32/33/36, plus local pre-run TIFFs. Deduplicate identical bytes. Compare full-footprint surface Spearman correlation and an unmasked prospective 37,654-dot placement to every raster. Stop before holdout if `|rho| > 0.90` or directed 3-pixel overlap `> 0.70` against any one raster. Repeat on final catalogue-cleared dots. Snapshot completeness is bounded to these pinned paths/repositories; it is not global parallel-run completeness.

### 2.3 Placement

For a domain mask, sort positive surface cells descending with stable row-major ties and greedily retain cells at Euclidean separation `>=2.8 px` until `round(37,654 * domain_area / full_footprint_area)` dots. Eligible cells must be inside the domain and farther than `2 px` from the **visible catalogue for that fold** (full public catalogue only for final emission). No historical dot is seeded, copied, protected or filtered.

### 2.4 Holdout and frozen comparators

- Restore and hash-check the shared template pinned in `registry/protocol_assets.json`; call its `scripts/evaluate_holdout.py` rather than implementing a private metric/evaluator.
- Shared evaluator: `gems-segment-pooled-v1`; hide whole fault systems, 1,500 m buffer, four spatial quadrants, visible-only catalogue features/masks, pixel-exact visible masking, pooled DTI with `alpha=0.2`, `beta=0.8`, 300 m triangular kernel. Report withheld positives and a 10 km spatial-block bootstrap 95% CI.
- Primary comparator: retrained-per-fold visible-only 32-band H38 baseline, reconstructed under the same folds. Secondary comparator: retrained visible-only 32-band `d=2.8`, `B=2` champion analogue. No full-catalogue prior raster is scored as a holdout baseline.
- Frozen superiority gate: candidate pooled DTI minus primary baseline must be positive and its paired 95% CI lower bound must be strictly above zero. Otherwise verdict is `negative` and no slot is selected.

### 2.5 Final artifact and estimate

Experiment 3 runs only if the surface did not drift. Fit nothing to hidden holdout outcomes. Place full-footprint dots using the same frozen rule, then call the pinned shared `scripts/submission_writer.py` to create a single-band float32 all-finite GeoTIFF with zero outside, exact template CRS/shape/transform and values in `[0,1]`; create a sample-convention NaN twin only as a research fallback. Independently re-read exact bytes, hash them, compare final dots to the registry and create a note of at most 140 characters.

A live estimate, if reported, is `MODEL PROJECTION — NOT A SCORE`: `0.2778 × (candidate HOLDOUT-DTI / secondary champion-analogue HOLDOUT-DTI)` on identical folds, with a range propagated from the paired block-bootstrap interval. The `0.2778` anchor remains `USER-REPORTED / UNVERIFIED`; no organizer receipt exists here.

## 3. Three-experiment ledger and stop conditions

1. **Exp 1:** deterministic surface + three single-feature canaries + pre-placement registry checks. Stop on leakage or lane drift.
2. **Exp 2:** shared whole-system buffered HOLDOUT-DTI against both retrained comparators; no hyperparameter change after reading it.
3. **Exp 3:** frozen full placement + shared writer + exact validator + final registry checks + run card. A negative TIFF remains a reproducibility artifact explicitly marked **DO NOT SUBMIT**.

Any exception, missing input/provenance, elapsed experiment time ≥2 hours, third experiment completion, duplicate threshold breach, or failed exact validator closes the lane. No DrivenData login, upload, authenticated quota query or competition slot is used.

## 4. Source boundaries for manual review

- Official competition problem/metric and label framing: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official open reference implementation: https://github.com/drivendataorg/gems-prize-reference-solution
- Official USGS GeoDAWN landing page: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- Official DOE GDR INGENIOUS release: https://gdr.openei.org/submissions/1391
- Official USGS MT source DOI: https://doi.org/10.5066/P9TWT2LU

These links support manual review. In this environment only GitHub hosts are network-allowlisted; source URLs already recorded by prior repository audits are not falsely described as freshly fetched in this session. Hash matches to owner mirrors prove byte identity to those mirrors, not organizer authentication.
