# 47 — Session 15 (2026-10-25): why the 0.2778 champion won, five ranked hypotheses, and the frozen H39-1 gate

**Status: FROZEN before seeds 290–294 are touched.** Branch `arena/5ac802ba-gemsdoe28`.
Every live score below is **OWNER-REPORTED** (owner's task-statement lists, 2026-10-25). No
repository fetched this session contains an organizer submission-page receipt for any of these
files, so **none is labelled ORGANIZER-CONFIRMED**. Local numbers are **HOLDOUT-DTI** with the
evaluator named. Projections are labelled **MODEL** and are never written as scores.

---

## 1. Why `h33-h33-2-b2-…-e5eb6e7e-zeros` (GEMSDOE32) got the group's highest owner-reported score, 0.2778

Verified line by line from bytes this session (`scripts/forensic_champion_s15.py` →
`evidence/s15_champion_forensic.json`; champion SHA-256 `c55bafc4…` matches GEMSDOE32's own
`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json` exactly):

1. **Exact construction.** The champion (37,654 dots) is *byte-for-byte in dot set* the
   GEMSDOE28/31 solo file `8acb75e1f2cc` (40,199 dots, owner-reported 0.2708) with every dot at
   Euclidean distance ≤ 2 px (200 m) from the published catalogue deleted:
   `champion == solo & (d_cat > 2)` with **0 px symmetric difference**. The solo file is itself
   the 0.2600 `dotted-h19-5-d2-8` file (44,090 dots) with the ≤ 1 px ring deleted (3,891 dots,
   0 added). GEMSDOE36's 0.2750 file is the champion **plus 1,200 added dots, 0 removed**.
2. **Mechanism.** The two deleted rings are catalogue-flank *digitisation shadow*: the H19-5
   ridge fires on the LiDAR scarp of an already-mapped fault, offset 100–400 m from the
   rasterised USGS trace (Hermant et al. offsets; §2.3 of README). The live scorer masks only
   the catalogue pixels themselves, so a flank dot 100–200 m beside a mapped fault is charged
   almost full false-positive mass while earning credit only if a *hidden* fault happens to run
   within 300 m of it. The owner-reported ladder says that almost never happens:
   ring 1 (≤100 m, 3,891 dots) removal: **+0.0108** (2.776×10⁻⁶ DTI/dot);
   ring 2 (100–200 m, 2,545 dots) removal: **+0.0070** (2.750×10⁻⁶ DTI/dot).
   The near-identical per-dot yield of two independent rings is the signature of dots carrying
   ≈ 0 credit and ≈ full FP weight — deleting them shrinks the α·FPw denominator term
   (α = 0.2) at no TPw cost. The converse live experiment agrees: GEMSDOE36 *added* 1,200
   conduit dots to the champion and the owner-reported score *fell* to 0.2750 (−0.0028).
3. **Why this beat every smarter idea in the group.** All top group files (0.2477 → 0.2600 →
   0.2708 → 0.2778) are one surface (H19-5 multi-line-corroborated ridge) under successively
   cleaner emission hygiene: Poisson spacing 1.5 → 2.8 px, then flank rings 1 → 2 px. Each step
   removed dots whose marginal credit/dot was below the break-even
   τ(DTI) = 0.2·DTI/(1−0.2·DTI) ≈ 0.055–0.059 at these scores. Detection novelty (new layers,
   new physics) has repeatedly failed to clear τ live (dilcond 0.1223; T-v2 −0.0028;
   GEMSDOE36 additions −0.0028), while *removing provably-worthless mass* has never lost.
4. **Can we beat 0.2778, and how?** The obvious continuation — delete ring 3 (200–300 m,
   2,171 champion dots) — extrapolates to ≈ +0.0060 (**MODEL**, linear per-dot yield of rings
   1–2; not a score). It is **barred as this session's submission** by the parallel-run
   uniqueness rule: a subset of the champion has 100% of its dots within 3 px of a registry
   raster (> 70% = duplicate lane). It is also scientifically weaker than rings 1–2: 200–300 m
   is the last ring inside the 300 m credit kernel, where a genuine unmapped splay parallel to
   a mapped fault would live. Beating 0.2778 *uniquely* therefore requires new credit, not more
   pruning: dots on structure the champion's surface does not contain, at credit/dot > τ ≈ 0.059,
   while keeping the champion's two hygiene lessons (2.8 px spacing; no dots within 200 m of
   the catalogue). The gap to the owner-stated leaderboard top (0.3195 in the standing brief;
   0.4413 in the 2026-10-25 prompt — conflicting snapshots, both unverified here, flagged in
   `registry/irregularities.json`) remains a detection gap of ≈ +1,150 px of credit at this
   budget (README §3.1); no arm in this session claims to close it.

## 2. Five candidate hypotheses not yet tried in this repository, ranked

Each names layers, signature, why it catches a fault *missing* from the USGS/INGENIOUS
catalogue, the named non-fault mimic, and the difference from everything implemented here.
Ranking: expected ΔDTI × uniqueness headroom ÷ cost. All use only hash-pinned local bytes
(restored and verified this session; prepared stack SHA-256 `83ed2704…`, identical to Session 14).

| Rank | ID | Layers (all local, official-source mirrors) | Signature | Why off-catalogue | Named mimic | Novelty in this repo | Cost |
|---:|---|---|---|---|---|---|---|
| 1 | **H39-1 depth-sliced potential-field lineaments under cover** | `training_features.tif` tmi(14), rtp(2), iso_grav_anom(13); depth_to_base_surf(15) already in stack for cover interaction | Upward continuation (FFT, exp(−\|k\|h)) to h = 1 km & 2 km; horizontal-gradient magnitude at each level + persistence ratio HG(2 km)/HG(shallow) + tilt angle at 1 km. Deep-rooted contacts persist with height; shallow scarp/dike noise attenuates | Faults buried under basin fill have no scarp and no catalogue trace, but their basement offset still bends the deep magnetic/gravity field | **Basement lithologic contacts and mafic dike swarms** (persistent deep lineaments, zero Quaternary slip); GeoDAWN flight-line striping | Stack's only continuation is 150 m (`TMI_up150`, excluded as rank-duplicate of tmi). H32-2 used a shallow/deep *ratio as a prune* and failed; no arm has used deep-level HG ridges as *positive detector evidence* | Low–med (FFT on 3730×3292, analytic test) |
| 2 | H39-2 radiometric alteration *lineaments* (not pixels) | `geodawn_rad_u8` K/Th/U, `geodawn_extensions_u8` ThK/UK/UTh (USGS GeoDAWN, GDR 1591) | Hessian ridge of low Th/K (potassic alteration) required collinear over ≥ 1 km | Alteration haloes outlive scarps along buried fluid conduits | Felsic lithology boundaries; playa evaporite K enrichment | Radiometrics entered only as GBDT pixel features (Session 14a: interleaved pass, far-field unresolved); never as a lineament object | Low |
| 3 | H39-3 drainage-chain collinearity at 100 m | det_elev(12), det_elev_slope(19) | Valley skeleton × 16-direction collinearity vote over 900 m | Scarp-less faults still align/deflect drainage across multiple catchments | Joint sets and strike valleys on dipping strata | All DEM channels here are local windows; the 1 m-DEM version (H33-4) needs the bridge, this 100 m version does not | Low |
| 4 | H39-4 artifact-swap (queued H38-4) | lidar coh100/strike/ex_max, det_elev, tmi_hg, iso_grav_anom_hg | Suppress ultra-linear constant-elevation LiDAR steps with zero potential-field support; reallocate 1-for-1 to corroborated ridge dots at fixed N | Converts zero-credit cultural/shoreline dots into budget for real structure | Is itself the mimic model: **Lake Lahontan strandlines, roads, canals, rail grades** | No arm models the mimics explicitly | Low–med |
| — | B3 flank ring (200–300 m) | labels.tif only | Delete champion dots at d_cat ∈ (2,3] px | — | — | **REJECTED as a lane**: subset of the champion ⇒ 100% dots within 3 px of a registry raster (duplicate). Retained only as the §1.4 MODEL extrapolation | — |

External-data check: H39-1…H39-4 need **no new external data** — every layer is already
restored and SHA-256-verified in `data/` (official sources: USGS GeoDAWN
https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and ;
competition stack https://www.drivendata.org/competitions/306/competition-doe-gems/ ;
method: upward continuation is the standard Fourier-domain potential-field transform —
Blakely, *Potential Theory in Gravity and Magnetic Applications*, Cambridge UP, 1995).

## 3. THE LANE (single method paragraph — this session stays inside it)

**H39-1: depth-persistence-weighted re-detection.** From the label-free `tmi` and
`iso_grav_anom` fields, compute upward continuations to 1 km and 2 km and from them five
extra bands (HG at 1 km, HG at 2 km, persistence ratio, 1 km tilt angle, gravity HG at 2 km);
append them to the frozen 32-band matrix; retrain the repository's existing buffered
quadrant GBDT detector unchanged; rank ridge candidates by
`prob × (0.5 + persistence_rank01)` so deep-persistent lineaments — the signature of a
basement fault under cover, laterally offset from any surface scarp — are preferred at fixed
budget; emit with the existing top-budget ridge + `dot_thin(2.8)` rule. The champion's
catalogue-flank exclusion (no dots within 200 m of the *visible* catalogue) is applied only
at final build time as disclosed hygiene, never inside the gate (where the visible catalogue
is the LOSFO-masked label set). Named mimic: basement lithologic contacts / dike swarms.

## 4. Frozen gate (Experiment 2 of ≤ 3; Experiment 1 is the label-free canary, §5)

* **Evaluator:** `scripts/run_losfo_harness.py` (extended once, in-template, with
  `--s15-depthslice`; default behaviour byte-identical) driving `src/gems27/losfo.py` +
  `src/gems27/metric.py` — whole fault systems withheld (300 m dilation grouping), 600 m
  buffer erased from training labels, every catalogue-derived quantity (the detector's
  labels; the known-mask) derived from visible faults only, visible faults masked
  pixel-exactly, pooled DTI at α = 0.2, β = 0.8 with the 300 m triangular kernel.
  Feature-leakage note: the five extra bands are functions of geophysics rasters only and
  never read labels, so not re-deriving them per split cannot leak held-out systems.
* **Seeds:** 290–294 (5 seeds × 4 folds = 20 paired cells). Ledger: 290+ free
  (`registry/next_hypotheses.json:session14_addendum`); no prior evidence file uses them.
* **Arms (identical truth, identical emission code):** `D0` = frozen 32-band LOSFO detector;
  `D1` = D0 + 5 depth-slice bands with persistence-weighted ranking (**primary**);
  `D1_nw` = D1 without the ranking weight (diagnostic, same fitted probabilities);
  `leaky` = harness's unmasked control (inflation reference only).
* **Primary contrast:** D1 − D0. **Pass requires ALL of:**
  G1 pooled ΔDTI > 0 **and** mean paired ΔDTI ≥ +0.0010;
  G2 ≥ 14/20 cells, ≥ 4/5 seed means, ≥ 3/4 fold means positive;
  G3 D1 pooled credit/dot ≥ D0 pooled credit/dot;
  G4 integrity: 0 emitted dots on visible catalogue in every cell; pooled |N_D1 − N_D0|/N_D0 ≤ 0.10;
  G5 canary (§5) clean: every extra band's single-feature AUC ≤ 0.90.
  The 95% CI (paired bootstrap over cells) is **reported** in the run card regardless.
* **Reading rule:** pass ⇒ build the §6 candidate and verdict `promote` (to the selector
  step; this session does not spend a slot). Fail ⇒ verdict `negative`, candidate TIF still
  generated for inspection but banner-marked **DO NOT SUBMIT**. No retuning on 290–294.

## 5. Experiment 1 — leakage canary + uniqueness forecast (runs before the gate)

(a) Analytic FFT test: continuation of a synthetic harmonic decays as exp(−|k|h) to < 1e-6.
(b) Each extra band alone: AUC of band value at withheld-system pixels vs a fixed footprint
sample on LOSFO seed 290's split *assignment only* (no detector training; assignment is a
function of seed + catalogue geometry, disclosed). AUC > 0.90 ⇒ leakage until proven
otherwise ⇒ stop. (c) Spearman of each extra band vs in-stack `tmi_hg`/`tmi` (duplicate
check, the `TMI_up150` lesson). (d) Full-fit D0 vs D1 surface Spearman and prospective dot
overlap vs the champion at matched budget — geometric forecast only, no performance claim.

## 6. Build (Experiment 3, only the emission analogue of the gated arm)

Full-fit D1 detector (all labels — emission-time analogue), ridge NMS, persistence-weighted
top-budget pool sized to land at 37,654 ± 5% dots after `dot_thin(2.8)` and the disclosed
build-time exclusion `d_cat > 2 px`; written via `src/gems27/submission.py` (NaN-outside +
all-finite zeros variant + single-member ZIP). Validator: no NaN inside footprint, values in
[0,1], CRS/shape/transform exact vs template, 0 dots on catalogue. Uniqueness vs registry
(all `docs/downloads/*-nan.tif` + champion e5eb6e7e + GEMSDOE36 9b9ea4e6, education copies):
Spearman(surface, each binary registry raster) and fraction of dots within 3 px of each —
**ship-eligible only if every value ≤ 0.90 / ≤ 70% respectively**; otherwise log duplicate
and mark DO NOT SUBMIT.
