# Session 18 — preregistration H42-1 (migration-extrapolated relocation lane), frozen before any fit

**Date:** 2026-10-25 (UTC). **Branch:** `arena/384a5345-gemsdoe28`.
**Budget (parallel-run protocol):** ≤3 experiments, ≤2 h of experiment time.
Exp 1 = vector-field build + leakage canary + label-free shift inventory.
Exp 2 = frozen LOSFO gate (seeds 310–314). Exp 3 = candidate build + uniqueness + validator.
No submission slot is spent or selected by this repository; promotion to a real slot is a
separate selector step. Every number is labelled **HOLDOUT-DTI** (evaluator, withheld
positives, 95 % CI) or **OWNER-REPORTED**; nothing is ORGANIZER-CONFIRMED (no
submission-page receipt exists in this checkout). A projection is never written as a score.

## 0. Why the OWNER-REPORTED 0.2778 file won — re-verified byte-for-byte this session

Education only; the construction is **not** reused as this session's candidate (see §1).
Verified 2026-10-25 in this sandbox after restoring all 17 hash-pinned inputs
(`evidence/restore_audit.json`; prepared-feature SHA-256 `83ed2704…` reproduces Session 14)
and fetching the focus-site rasters from GitHub (`evidence/s18_champion_forensic.json`):

- Champion `gemsdoe32-h33-h33-2-b2-…-e5eb6e7e-zeros.tif` (SHA-256 `c55bafc4…`, the Session-16
  pin) holds 37,654 dots and equals the GEMSDOE28/31 solo file `8acb75e1` (40,199 dots;
  GEMSDOE31 and GEMSDOE28 copies are dot-identical, symmetric difference 0) **minus every
  dot with d(catalogue) ≤ 2 px** (2,545 removed, 0 added, symmetric difference 0).
- The solo file equals `dotted-h19-5-d2-8` (44,090 dots; GEMSDOE25/GEMSDOE30 copies
  dot-identical) minus the ≤ 1 px ring (3,891 removed, symmetric difference 0).
- GEMSDOE36 `9b9ea4e6` (38,854 dots) equals the champion **plus 1,200 dots, 0 removed**.

Mechanism (Session 15/16 analysis, consistent with the byte facts above): the deleted
rings are catalogue-flank shadow of already-mapped faults. The scorer masks catalogue
pixels but charges flank dots 100–200 m away almost full false-positive mass
(DTI α = 0.2, β = 0.8, 300 m triangular kernel; `src/gems27/metric.py`). The
owner-reported ladder 0.2600 → 0.2708 → 0.2778 prices each deleted flank dot at
≈ +2.76×10⁻⁶ DTI, constant across two independent rings — the signature of dots carrying
≈ 0 credit. The converse also held: GEMSDOE36 added 1,200 dots to the champion and the
owner-reported score fell to 0.2750. **The group's best score is emission hygiene on one
unchanged detector surface (H19-5), not new detection.** Continuing the prune (ring 3:
2,171 champion dots at 2 < d_cat ≤ 3 px, counted today) would produce a subset of the
champion — binary-raster φ(champion, solo) = 0.968 on the footprint already exceeds the
0.90 duplicate threshold — so it is barred by the uniqueness rule and is **not built**.
Beating 0.2778 with a unique file therefore requires *new credit above the live
break-even τ ≈ 0.055–0.059 credit/dot* (`metric.inclusion_threshold` at DTI ≈ 0.28,
plus crowding) from differently placed dots, while keeping the champion's hygiene
(2.8 px spacing, no dots within 200 m of the catalogue).

**Can we beat 0.2778?** No arm in this repository has demonstrated the required
≈ +1,150 px of credit at this budget (reachability frontier, `evidence/reachability_frontier.json`).
Session 16's handoff names the one untested lever with a physical reason to place dots
*off* the standard ridge: the migration-**extrapolated** trace. That is this session's lane.
HOLDOUT-DTI success would license a selector decision; it would not prove a live score
above 0.2778. The leaderboard maxima circulating in the task statement (0.4413 and
0.3195) conflict and remain unverified here (flagged in `registry/irregularities.json`).

## 1. THE LANE (single method paragraph — this session stays inside it)

> **H42-1 migration-extrapolated relocation.** From the competition TMI (training band 14)
> and isostatic-gravity (band 13) fields only, compute upward continuations at 0/1/2 km
> (Fourier `exp(−|k|h)`, Blakely 1995, via the shared `depthslice` transform, reused not
> forked), extract the horizontal-gradient ridge at the shallow and 2 km levels with the
> shared `ridge_nms`, and form a label-free **migration vector field** `v(x)` (px per
> 2,000 m): at shallow-ridge pixels, the vector to the nearest 2 km ridge pixel,
> magnitude-clipped to 12 px, Gaussian-smoothed (σ = 2) inside the ridge corridor and 0
> outside it, averaged across the two fields weighted by their three-level ridge
> coherence. A dipping boundary's ridge migrates down-dip as continuation height grows,
> so the boundary's zero-height (surface) trace is extrapolated **up-dip** from the
> shallow ridge: each baseline detector dot at `x` is relocated to
> `x − round(v(x)·clip(depth_to_base_surf(x), 0, 2000 m)/2000 m)`, with the shift capped
> at 3 px, dots that would land outside the footprint, on the (visible) catalogue, or
> within 2 px of it left in place, collisions resolved in raster order, and the result
> re-spaced with the shared `dot_thin(2.8)`. The detector is the repo's unchanged
> 32-band HistGBDT (`oof_detector`, 600 m buffer); ranking is by probability only;
> emission hygiene is `d_cat > 2 px` at build time only (never inside the gate, where
> blocking uses visible faults only). **Named non-fault mimic:** a dipping lithologic
> contact or mafic dike — it migrates identically and has zero Quaternary slip, so a
> relocated dot marks a dipping subsurface boundary, never a proven fault.

Why this could catch a fault missing from USGS/INGENIOUS: a dipping fault buried under
basin fill has no scarp for the catalogue and its potential-field edge at the surface is
laterally offset from its buried top edge; the detector ridge (trained on scarp-bearing
catalogue faults) inherits that offset, while the extrapolated trace estimates where the
plane meets the surface — the line an expert mapper would draw. Differs from H40-1
(Session 16, gate FAIL on spread), which appended migration *scalars as GBDT features*
and still emitted on the GBDT ridge (surface Spearman 0.990 vs baseline); H42-1 never
trains on migration — it changes **placement geometry only**, with sign-flipped and
random-direction controls to falsify the dip-direction claim. Differs from H39-1
depth-slice magnitudes (FAIL), H28-1 static edge coherence, Euler source fitting
(H31-1/H37-3/H38-1), and every pruning/repacking arm (H27-4/H36-1/H37-1), none of
which ever moves a dot off the detector ridge along a potential-field dip vector.

## 2. Five candidate hypotheses, ranked (only #1 is run — the lane)

Ranking rule (as Session 17): expected ΔDTI × uniqueness headroom ÷ implementation cost.
Expected improvement is ordinal judgement, **not** a score projection.

| # | ID — layers / signature | Why a *missing* fault | Mimic | Novelty vs this repo | Cost / data gate |
|---|---|---|---|---|---|
| 1 | **H42-1 migration-extrapolated relocation** — TMI + isostatic gravity upward continuations 0/1/2 km; HG-ridge migration vector × `depth_to_base_surf`-scaled up-dip relocation of detector dots (lane, §1) | Dipping buried fault's surface trace is offset from its shallow potential-field edge; catalogue is scarp-biased and omits it | Dipping contact / dike | First *placement* use of migration; H40-1 used scalars as features only | Low–med (bands ≈ 2 min; gate reuses LOSFO harness). Local restored stack only ✓ |
| 2 | **H42-2 segment-object ranking** — OOF ridge components scored by length × straightness × single-facing consistency (`lidar_upface/downface`, strike bands); budget allocated per segment, not per pixel | Weak-amplitude unmapped scarps integrate to a coherent long segment while per-pixel probability stays sub-threshold | Roads, canals, paleoshorelines (long, straight, faced) | All detectors rank pixels; segment attributes used only for catalogue graph/topology, never emission ranking (`filter_isolated_dots` H27-3 is a radius count, refuted) | Med. Local stack only ✓ |
| 3 | **H42-3 radiometric alteration lineaments as objects** — Hessian ridge of low Th/K (`geodawn_extensions_u8` ThK/UK/UTh + `geodawn_rad_u8` K/Th/U, restored & pinned), collinear ≥ 1 km, as an ADD pool on sub-threshold ridge pixels | Potassic alteration haloes persist along buried fluid conduits whose scarps never formed or were erased | Felsic lithology margins; playa evaporite K; GeoDAWN flight-line striping | Radiometrics used as GBDT pixels (H27-12) and as a halo flag inside failed H35-1; never as a lineament object / emission pool | Low–med. Local GeoDAWN bands ✓ (USGS GeoDAWN, see §5) |
| 4 | **H42-4 drainage-divide asymmetry reversals** — `det_elev` flow network; divide-migration (χ) asymmetry sign reversals aligned across ≥ 3 adjacent basins on a magnetic edge | Concealed normal fault tilts basins and deflects drainage without a preserved scarp | Lithology-controlled erosion; stream capture | No hydrologic-network observable exists in the repo | High (hydrologic conditioning at 100 m; 1 m DEM tiles via `dem_links.json` unverified for coverage). Local band suffices for a screen ✓ |
| 5 | **H42-5 multi-depth MT conductance-boundary migration** — USGS Great Basin MT conductance slices (Bedrosian et al., DOI 10.5066/P9TWT2LU) × gravity | Buried fluid-bearing structure persists under conductive fill with no Quaternary trace | Clay-rich basin margin; saline sediment | Queued H38-3 tests pipe *alignment*, not boundary *migration with depth* | **Not viable this session:** official bytes are pin-recorded (`registry/external_pins.json`) but the sandbox cannot reach sciencebase.gov and no clipped raster exists locally; needs the Actions bridge first ✗ |

Checked and **rejected before ranking** (inventory, no labels touched): GDR 1391 2 m
temperature probes — the official archive exists (DOI 10.15121/1881483, CC BY 4.0;
page fetched 2026-10-25, §5) but its bytes are unreachable from this sandbox, and the
obtainable GEMSDOE30 derived raster `derived_gdr_2m_probes_100m_u8.tif`
(SHA-256 `7ac3cfdf…`, grid-verified today) is a binary probe-*location* mask (2,700 px)
with temperatures discarded — strictly weaker than the well/spring thermal conjunction
already refuted in H35-1 (0.0132 credit/dot vs τ 0.0549). SGMC geologic-map faults as
an emission pool: live-refuted standalone (owner-reported 0.036–0.051) and
leakage-prone in LOSFO because geologic maps already contain held-out traces.

## 3. Frozen protocol (no changes after Exp 1 starts)

- **Shared tools only:** `src/gems27/{grid,metric,losfo,holdout,oof_detector,submission,thinning,depthslice,migration}.py`
  and evaluator `scripts/run_losfo_harness.eval_set` (imported, not forked). New code is
  additive: vector-field + relocation functions in `migration.py` with synthetic tests.
  The task statement's `evaluate_holdout.py`/`submission_writer.py` filenames do not
  exist in this template; the modules above are their shared equivalents (flagged).
- **Holdout (Exp 2):** LOSFO hide-and-recover — whole fault systems (8-connected,
  3 px dilation grouping) withheld per quadrant fold; 600 m buffer erased from training
  labels; catalogue-based quantities in the arm (blocking mask) derived **only from
  visible faults**; visible faults masked pixel-exactly (`active = fold & ~known`);
  pooled DTI α = 0.2, β = 0.8, 300 m triangular kernel. **Seeds 310–314** (verified
  unused: prior decades end at 304; Session 16 reserved ≥ 310 for this lane). 20 paired
  cells; arms per cell: `base` (D0 dotted, thin 2.8), `phys` (relocated, §1), `anti`
  (sign-flipped vectors), `rand` (each shift rotated by a seeded uniform angle,
  magnitudes preserved). Report pooled + mean paired ΔDTI, cell-bootstrap 95 % CI for
  Δ and for pooled candidate DTI, withheld-positive count, moved-dot fraction.
- **Canary (Exp 1):** each candidate band alone — |v|, shift magnitude, signed
  migration (tmi/grav), coherence (tmi/grav) — AUC vs LOSFO seed-310 withheld systems
  (negatives: footprint, non-catalogue, > 6 px from hidden; ≤ 250 k, S16 protocol).
  `max(AUC, 1−AUC) > 0.90` = leakage → stop, verdict negative, no gate.
- **Gate (Exp 2), all required for `promote`:** G1 pooled ΔDTI(phys−base) > 0 **and**
  mean paired Δ ≥ +0.0005; G2 spread ≥ 14/20 cells, ≥ 4/5 seed means, ≥ 3/4 fold means
  positive; G3 falsification: pooled Δphys > Δanti **and** > Δrand; G4 integrity:
  0 relocated dots on visible-known after blocking, pooled |N_phys−N_base|/N_base ≤ 0.05;
  G5 canary pass. Any failure → verdict `negative`, TIFF (Exp 3) is inspection-only.
  No retuning, no extra seeds, no threshold changes after seeing gate output.
- **Uniqueness (Exp 3), checked pre-placement (surface) and post-placement (dots):**
  *Binding registry* = the ten owner-reported **scored** rasters of the nine focus sites
  available as bytes (champion e5eb6e7e; GEMSDOE36 9b9ea4e6; solo 8acb75e1; d2-8
  e56ea318; d1-5 989f5950; T-v2 5512495c; GEMSDOE33 cb490425; DOE28 31e35eee,
  b531dae0, 56a9f473). Pass requires, vs **every** member: binary-raster rank correlation
  (φ; identical to Spearman for binary rasters) ≤ 0.90 **and** ≤ 70 % of final dots
  within 3 px. Surface check: Spearman(full-fit probability surface, registry binary)
  on a 400 k sample ≤ 0.90. *Disclosed, non-binding:* dot overlap vs every other
  `docs/downloads/*-nan.tif` (including unscored probe blankets that no ridge-based file
  can pass — irregularity `s15-uniqueness-dense-probes`); the selector may apply the
  stricter reading. Any binding breach → log duplicate, verdict `negative`, stop.
- **Candidate build (Exp 3):** full-fit D0 probability → `ridge_nms` → pool
  (footprint, off-catalogue, `d_cat > 2 px`) ranked by probability → binary-search
  top-k so `dot_thin(2.8)` lands within 5 % of the champion's 37,654 dots → relocate
  (§1, blocking = full catalogue ∪ {d_cat ≤ 2}) → `dot_thin(2.8)` → write via
  `submission.py` as `-nan` + `-allfinite` + single-member zip. The **all-finite**
  (zeros-outside) file is the download of record: values exactly {0, 1} ⊂ [0, 1], no NaN
  anywhere — the range-safe answer to the portal error "Predicted values must be in
  range [0, 1]" (cause unconfirmed; NaN-outside is the plausible trigger).
  Validator: `submission.verify_geotiff` all hard checks (single-band float32,
  EPSG:32611, 3730 × 3292, template transform, no NaN inside footprint, [0, 1] range)
  on the actual bytes, plus SHA-256 and scored-content ID in the filename.
  Unique name `gems28-h42-1-migx-reloc-b1-<date>-<content-id>-{nan,allfinite}.tif`;
  submission note ≤ 140 characters.
- **Run card:** one JSON card (`evidence/s18_run_card.json`, mirrored to
  `docs/data/run_card_s18.json`) with hypothesis, mechanism, named mimic, HOLDOUT-DTI +
  CI, registry correlation/overlap, raster SHA-256, validator output, submission name +
  note, verdict `promote`/`negative`; checked with `scripts/check_promotion.py`.
  `promote` means *eligible for the separate selector step* — never an instruction to
  spend a weekly slot, and never an organizer score.

## 4. Irregularities carried into this session (flagged, not papered over)

1. The task statement contains no separately delimited lane paragraph; this session
   adopts Session 16's explicitly handed-forward next preregistration (§0) as its single
   lane and freezes it above before any fit.
2. All "scores" for focus-site files, including 0.2778, are OWNER-REPORTED; the
   GEMSDOE32 page snapshot in the cross-site audit states no organizer score for its
   artifacts. No receipt exists anywhere in the fetched repositories.
3. Leaderboard maxima 0.4413 vs 0.3195 conflict; neither is adopted as fact. This
   sandbox cannot fetch drivendata.org (egress allowlist: GitHub + package registries).
4. Competition inputs are owner-mirror bytes, hash-pinned but not
   organizer-authenticated; DrivenData itself is never contacted by any script here.
5. `knowledge/51` (Session 17) calls the historical H38-1 file "promote / OK to
   download", while the merged site/README safety notice says no file is approved.
   This session follows the stricter merged notice for all historical files.

## 5. Official sources (manual-review links; fetched or pinned as noted)

- Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/
  (problem/format page 967; leaderboard) — not fetchable from the sandbox; manual review.
- Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf — manual review.
- Reference solution (verified via GitHub API 2026-10-25):
  https://github.com/drivendataorg/gems-prize-reference-solution
- DOE GDR 1391 INGENIOUS compilation, DOI 10.15121/1881483, CC BY 4.0 (page fetched
  2026-10-25; lists the 2 m probe, paleo-geothermal, volcanics and Qfaults archives):
  https://gdr.openei.org/submissions/1391
- USGS GeoDAWN airborne magnetic/radiometric surveys:
  https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- USGS Great Basin heat flow (DeAngelo et al. 2022), DOI 10.5066/P9BZPVUC;
  MT conductance (Bedrosian et al.), DOI 10.5066/P9TWT2LU; slip/dilation tendency
  (Siler 2022), DOI 10.5066/P9YL58W6 — pins in `registry/external_pins.json`.
- Reid et al. (1990) Euler deconvolution, DOI 10.1190/1.1442774; Blakely (1995)
  *Potential Theory in Gravity and Magnetic Applications* (upward continuation
  `exp(−|k|h)`), as implemented in `src/gems27/depthslice.py`.
- EPSG:32611 (WGS 84 / UTM 11N): https://epsg.io/32611 — grid constants are re-verified
  against the template on every load (`src/gems27/grid.py`).

---

**Post-merge addendum (does not alter the frozen text above):** this run is relabeled
**Session 18B** — a parallel Session 18 (H39-5, `knowledge/52_preregistration_H39-5_extrapolated.md`)
already owned the `s18_*` artifact names on `main`. Artifacts of this preregistration are
`evidence/s18b_canary.json`, `evidence/s18_h42_losfo_gate.json`,
`evidence/s18b_candidate_build.json`, `evidence/s18b_run_card.json` (manifest slot
`s18b_candidate`); result: `knowledge/54_s18b_h42_1_result.md`; scripts renamed
`build_s18b_extra.py` / `run_s18b_losfo_gate.py` / `build_s18b_candidate.py` /
`finalize_s18b.py`. Both parallel lanes reserved seeds 310–314 and both failed their
frozen gates; never combine their numbers (`s18b-session-label-collision`).
