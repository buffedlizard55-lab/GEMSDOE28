# S29 · 2026-10-29 UTC — experiments, uniqueness audit, and decision

**Decision: NO NEW TIFF · NO FILE APPROVED · OK TO SUBMIT: NO.** Branch `arena/9a3a5294-gemsdoe28`.
Run card: `evidence/s29_lattice_run_card.json` (canonical; also `docs/data/s29_lattice_run_card.json`). No slot was selected or spent. No competition login, upload, or polling occurred.

All numbers below are **HOLDOUT-DTI** (evaluator `gems-segment-pooled-v1`, 60,988 withheld positives, 95% CI, pooled α=0.2, β=0.8, 300 m triangular kernel = 3 px). None is a leaderboard estimate. Organizer-confirmed facts are labelled as such.

## 1. What was run (3 of 3 experiments; cap reached)

| # | Question | Script / evidence | Result |
|---|---|---|---|
| E1 | Does the holdout separate geology from budget-matched, geology-blind placement? | `scripts/run_s29_null_controls.py` → `evidence/s29_null_controls.json` | random-K 0.067406 [0.064397–0.070308]; calibration lattice 0.074836 [0.071734–0.077850]; paired Δ vs random-K +0.007430 [+0.003574, +0.011603], 4/4 folds; visible-proximity (in-scope, budget-matched) 0.018369 [0.010458–0.027471], Δ −0.049037, 0/4 folds |
| E2 | Does spacing-constrained TCB placement (5 px minimum spacing, strongest-first ridge candidates, visible faults excluded) beat both controls? | `scripts/run_s29_dispersion.py` → `evidence/s29_dispersion_run_card.json` | 0.083813 [0.079788–0.087815]; Δ vs random-K +0.016407 [+0.012040, +0.020894], 4/4; Δ vs lattice +0.008976 [+0.004006, +0.013917], 4/4. Shortfall 0 dots per fold. Canary PASS (threshold 0.90; numeric AUC not recorded by the API). **Global placement overlaps the calibration lattice 100% within 3 px → lane duplicate.** |
| E3 | Is the E2 gain from the TCB ranking, or from ridge geometry plus spacing? | `scripts/run_s29_ridge_control.py` → `evidence/s29_ridge_control_run_card.json` | Same ridge candidates and 5 px spacing, random seeded priority: 0.083234 [0.079988–0.086455]; Δ vs random-K +0.015828, 4/4; Δ vs lattice +0.008398, 4/4. **TCB minus random-priority = +0.000579, unpaired; paired CI not computed (would exceed the cap). Not established.** |

Reference (S28, unchanged): TCB candidate without spacing 0.055374 [0.051817–0.058997]; S25 PCSE 0.0450.

## 2. Interpretation (what the holdout does and does not show)

- **Dispersion is what the holdout rewards.** Even a geology-blind lattice beats random placement (E1). Spacing-constrained ridge placement beats both (E2). The S28 TCB result (0.0554) was lower than the lattice control (0.0748); spacing explains the difference.
- **The TCB ranking is not shown to add anything.** Random priority over the same ridge candidates and spacing scores the same (E3). The honest reading: the holdout credits dots along the ridge network of the TCB surface, not evidence that the TCB operator finds faults.
- **Structural limit.** Visible faults are at least 16 px from every scored quadrant in all four folds (the hidden set is components touching the quadrant or its 15 px collar). Catalogue-proximity strategies (for example the GEMSDOE32 construction, "solo minus 2,545 catalogue-adjacent dots") therefore cannot earn credit under this holdout. The holdout cannot test them.
- **Attribution gap.** The ridge candidates are themselves derived from the TCB surface. A surface-independent ridge null (for example ridges of a Gaussian random field of matched correlation length) is needed before any geology claim. It was not run because the cap was reached.

## 3. Uniqueness and the lane rule

`scripts/audit_lattice_overlap.py` → `evidence/s29_lattice_overlap_audit.json`.

- Registered calibration lattice (GEMSDOE13 control; SHA-256 `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2`; source `buffedlizard55-lab/GEMSDOE24@07345ea`) covers **99.8713%** of the 5,167,373-cell footprint within 3 px (6,649 uncovered).
- Random placements of the same budget overlap the lattice at 99.86% (10,000 dots), 99.87% (22,163), and 99.87% (37,654), mean over 10 seeds. A literal 70% threshold therefore fails random placement.
- **All 52 historical dotted GeoTIFFs in `docs/downloads/` fail the lane rule** (overlap 99.29%–100%). The literal rule does not discriminate between methods on this registry.
- The rule is internal (the user's parallel-run protocol). **The official rules contain no uniqueness or duplicate-submission rule** (see §5).

## 4. Answers to the user's specific questions

**Why GEMSDOE32 (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, 0.2778) scored highest.** USER-REPORTED / UNVERIFIED. No organizer receipt binds the score to a file. The repo's construction note: GEMSDOE32 = GEMSDOE31 solo geography minus 2,545 catalogue-adjacent dots (README S27/S23). A plausible mechanism, not proven: removing dots near known faults reduces false-positive mass under the asymmetric α=0.2 / β=0.8 penalty. E1–E3 add that spacing and dot arrangement strongly move holdout DTI. Those results are holdout-based and do not establish the leaderboard cause.

**Is a higher score achievable?** Not established by this run. The public board shows higher scores exist (#1 0.4544; ORGANIZER-CONFIRMED read below). The best holdout route found here (0.0838) is a duplicate of the calibration lattice and is not attributable to geology, so it is not a candidate.

**Score-string discrepancy: 0.2777 vs 0.2778.** Only 0.2778 appears in the repository records. 0.2777 has no source here and is treated as a transcription or rounding variant of the same user-reported number. Neither is organizer-confirmed.

**Leaderboard anchors (0.4413 vs 0.3195).** The public board read on 2026-10-29: #1 xiaofanhu **0.4544**; #2 cfld__ 0.3916; #26 newway **0.3328**. Neither 0.4413 nor 0.3195 appears in ranks 1–47. The README's S27b note records "#26 = 0.3195"; that observation predates today's read and the board has since moved. The conflict is recorded as an irregularity, not resolved.

**Portal error "Predicted values must be in range [0, 1]".** Root cause unknown (README S23; the portal validator is closed-source). Locally, all 52 historical rasters have values in [0, 1] inside the footprint, so the in-range check is not the local failure mode. Observed format difference: the all-finite variants have no nodata tag and write 0 outside the footprint; the NaN twins write NaN outside. The organizer text allows "nodata/NaN outside bounds," so this is a conformance question to test only with a deliberate, approved upload, not automatically.

## 5. Official sources (ORGANIZER-CONFIRMED unless noted)

- Competition problem page, metric and format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ — distance-weighted Tversky, α=0.2 (FP), β=0.8 (FN), triangular kernel R=300 m; one float32 single-band GeoTIFF with values in [0,1], EPSG:32611, 100 m; nodata/NaN outside bounds. No uniqueness rule.
- Landing (dates, prizes): https://www.drivendata.org/competitions/306/competition-doe-gems/ — end Dec. 3, 2026, 11:59 p.m. UTC; Initial Prize $50,000; Final Prize $250,000.
- Leaderboard (snapshot read 2026-10-29): https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Official rules (NLR, Sept 2026): https://www.nlr.gov/docs/fy26osti/96647.pdf (redirects to docs.nlr.gov). Chunks 0–6 read. Relevant terms: §3.2 one submission per entity, up to three per week (per website); §3.5 one submission is selected across both rounds; §3.6.2 choice made without private-set scores; §3.6.4 DOE is the final decision-maker; A.1 posting deadline 5:00 p.m. ET on the deadline date; A.4 public submission elements carry a license to DOE and DrivenData, and confidential material must be marked; A.5 representation that the submission is an original work; A.10 submitted materials are DOE records subject to FOIA; A.13 program policy factors include "technological or programmatic diversity"; A.16 return of funds for inaccurate information. The rules contain no duplicate-submission rule. A.13 diversity is a judging factor, not a ban.
- HeroX rules resource pointer: https://www.herox.com/GEMSPrize/resource/2274

## 6. Hypotheses (untried), ranked by expected improvement and cost

1. **H-S29-A — surface-independent ridge null** (top). Tests whether any ridge network with 5 px spacing earns the E2 gain. Cost: low (about 2 minutes compute). It is a control, not a candidate. It must pass before any geology claim. Not run (cap).
2. **H-S29-B — spacing sweep** R ∈ {3, 5, 8, 12} px for dispersed ridge placement. Shows where the holdout gain saturates. Cost: low. Expected improvement: unknown.
3. **H-S29-C — 3 px spacing** (matches the kernel). Cost: low. High duplicate risk, same as E2.
4. **H-S29-D — catalogue-adjacent removal** (GEMSDOE32 construction). Cost: a weekly slot. **Not testable on this holdout** (structural limit, §2). Lowest priority.

No slot is used for any of them. The top hypothesis must pass its holdout control before a slot is considered.

## 7. Limitations

- HOLDOUT-DTI is an internal proxy. It is not the leaderboard, the private set, or the final round.
- Visible-fault holdout cannot test catalogue-proximity strategies (§2).
- E3 difference is unpaired; the TCB ranking contribution is not established.
- Canary reports pass/fail only; numeric AUC not recorded for the surface canary.
- Data restored from owner-supplied, hash-pinned public mirrors, not organizer-authenticated (`evidence/restore_audit.json`, PASS on local hashes, grid, and bands; no network access during audit).
- The user's verbatim full prompt was not available in this session's context; README §S29 records the requirements as preserved in session memory. Please paste the full prompt if the verbatim text must be stored.

## 8. Irregularities flagged

See `registry/irregularities_s29.json` (entries `s29-*`; kept separate because `registry/irregularities.json` is byte-pinned by an S23 audit binding): leaderboard anchor conflict; 0.2777 unsourced; allfinite zero-outside format variance (27 files outside-footprint not NaN; 25 without nodata tag); lattice lane rule non-discriminating; attribution failure; branch-name mismatch in the S28 builder; canary numeric AUC not recorded.
