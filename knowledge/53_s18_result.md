# Session 18 result — H39-5 migration-extrapolated placement: NEGATIVE (holdout gate)

**Date:** 2026-10-25. **Lane/preregistration:** `knowledge/52_preregistration_H39-5_extrapolated.md`
(frozen before any fit). **Experiments used:** 3/3. **Slot spent:** none. **Verdict: `negative`.**
Run card: `evidence/s18_h39_5_run_card.json` (= `docs/data/run_card_s18_2026-10-25.json`).

**Bottom line for the operator: NO FILE IS APPROVED TO SUBMIT.** This session generated a
genuinely unique, format-valid TIF (`719b83fb659b`, first candidate in Sessions 15–18 to pass
the strict uniqueness rule), but the frozen holdout rejected its geology decisively. It is
published inspection-only with a 🔴 DO NOT SUBMIT banner. Downloading it for the portal would
spend a weekly slot on dots measured to earn *less* than the weakest dots they replaced.

## Why 0.2778 won, and whether it can be beaten (the standing question)

Established in Sessions 15–17 and not re-litigated here (`knowledge/50`, `knowledge/51` §1;
this session re-fetched both scored rasters and verified their bytes against the published
audit SHA-256 pins — champion `c55bafc4…`, GEMSDOE36 `e1589102…`): the GEMSDOE32 champion
(37,654 dots, **OWNER-REPORTED** 0.2778; no organizer receipt exists in any fetched
repository, so it is not ORGANIZER-CONFIRMED) is byte-identical to the 0.2708 solo file
minus every dot within 2 px of the catalogue. The 0.2477 → 0.2600 → 0.2708 → 0.2778 ladder
is one unchanged detection surface under successively cleaner **emission hygiene**
(Poisson spacing 1.5 → 2.8 px; catalogue-flank rings 1 → 2 px), at a constant
≈ +2.76×10⁻⁶ DTI per deleted flank dot — the signature of dots carrying ≈ 0 credit at
≈ full false-positive weight under the 300 m triangular kernel. It won by *removing
provably worthless mass*, not by detecting anything new; and its obvious continuation
(ring 3) is a > 95 % duplicate of the champion, barred by the uniqueness protocol.

**Can a unique file beat it?** The arithmetic from `knowledge/51` still binds: at the
champion's budget, +0.04 DTI needs ≈ +1,150 px of new credit — roughly 2,600–3,400 new
dots earning 0.4–0.5 credit each, or a much larger swapped population earning above the
break-even τ ≈ 0.055–0.059 credit/dot. This session tested the last physically-motivated
*placement* idea in the queue (below) and it earns below break-even. The honest answer
remains: **not with any mechanism yet demonstrated in this repository family.** What this
session *did* change is the other half of the problem — see "The one positive finding".

## Experiment 1 — pool + canary + pre-placement uniqueness (`evidence/s18_canary.json`)

Label-free surfaces from TMI (band 14) and gravity (band 13). **Canary PASS** (no leakage):
single-feature AUC vs. LOSFO seed-310 withheld systems = 0.499 / 0.499 / 0.499
(TMI / gravity / union) — no leakage, and honestly ≈ no univariate signal at the
extrapolated positions. Eligible pool (|v| ≥ 2 px, d_cat > 2 px): 858,170 px.
Displacement magnitudes are large: on shallow ridges, median |v| = 6.3 px (TMI) and
9.9 px (gravity), p90 = 15.8 / 26.6 px — for ridges that vanish by 2 km, "nearest deep
ridge" is an unrelated ridge, not a migration vector (this is the mechanism's weak point,
quantified before the gate, correctly not retuned after it).
**Pre-placement uniqueness PASS:** max |Spearman(lane surface, registry binary)| = 0.0037;
top-37,654 thinned pool dots are only **24.4 %** within 3 px of the densest registry probe
(vs. 79.9 % / 91.3 % for the S15/S16 detector emissions) and 19.4 % vs. the scored champion.
Off-ridge placement really does leave the ridge blanket.

*Implementation disclosure:* the first Exp1 invocation crashed with a `NameError` on a
leftover line **after** writing its evidence; the line was removed and Exp1 rerun cleanly.
The surface archive is byte-identical across both runs (SHA-256 `caa1127b…`); the JSON
differs only in its `seconds` field. Logged as `s18-exp1-rerun-nameerror`.

## Experiment 2 — frozen LOSFO gate, seeds 310–314 (`evidence/s18_h39_5_losfo_gate.json`) FAIL

HOLDOUT-DTI (shared `run_losfo_harness.eval_set`; α=0.2, β=0.8, 300 m triangular kernel,
pooled; 76,869 withheld truth px over 20 paired cells; whole fault systems, 600 m buffer,
visible-only catalogue features, pixel-exact visible-fault mask):

| arm | pooled DTI | credit/dot | dots |
|---|---:|---:|---:|
| D0 (frozen detector) | 0.105485 | 0.04851 | 241,640 |
| D1 (35 % extrapolated swap) | 0.094754 | 0.04353 | 241,640 |

Pooled Δ **−0.010731**, mean paired **−0.011027**, 95 % CI **[−0.01460, −0.00743]**,
2/20 cells positive, every seed mean negative (−0.0077 … −0.0159), every fold mean
negative (NE −0.0169, SE −0.0132, NW −0.0100, SW −0.0040). All 84,566 target swaps filled
with real extrapolated dots (0 backfilled), counts matched exactly, 0 dots on the visible
catalogue. Gates: **G1 FAIL, G2 FAIL, G3 FAIL**, G4 PASS, G5 PASS → `gate_passed=false`.
This is not a spread failure or a borderline CI: pooled TP falls by 1,205 px at identical
N, i.e. the extrapolated dots are worse than the *weakest 35 %* of ordinary detector dots.
The preregistration forbids retuning on these seeds; none was done. H39-5 as specified
(full-vector, unclipped extrapolation) is **refuted** — and the Exp1 diagnostics say why:
median jumps of ~860 m put most novel dots outside the 300 m credit kernel of any fault,
exactly what a dipping-contact/dike mimic (or a vanished ridge) would produce.

## Experiment 3 — build + validator + uniqueness (`evidence/s18_candidate_build.json`)

`gems28-h39-5-extrap-swap35-20261025-719b83fb659b-nan.tif`, 37,521 dots
(base 37,521 → 24,389 kept + 13,132 extrapolated, 0 backfilled; min d_cat > 2 px).
**Validator: all hard checks PASS** on both variants (single-band float32, EPSG:32611,
3730×3292, template transform; values exactly {0,1} inside the footprint; 0 NaN inside;
all-finite variant has no NaN anywhere — the range-safe answer to the owner's earlier
"Predicted values must be in range [0, 1]" portal error, whose root cause remains
unconfirmed). Independently re-read and re-hashed after the build: SHAs in the run card
match the bytes on disk.
**Uniqueness: PASS (strict)** — worst registry raster is the dense unscored probe
`52a13184267e` at **68.3 %** of final dots within 3 px (limit 70 %; S15/S16 were
79.9 % / 91.3 %); vs. the scored champion 34.0 %; lane-surface |Spearman| ≤ 0.0037
pre-placement and 0.0147 vs. the detector probability surface. Pass-3 verification
(`evidence/s18_focus_sites_overlap.json`, `scripts/check_s18_focus_sites.py`) extended
the check to the remaining focus-site scored rasters, all byte-verified: GEMSDOE33
`cb490425926e` 36.1 %, GEMSDOE25/30 `d2-8` 36.5 %, GEMSDOE24 `d1-5` 37.9 % — all pass. This file is **not a copy**
of any previous submission; it is the first generated candidate here to clear the
protocol's duplicate rule against every local registry raster including the probes.

**Verdict `negative`** because promotion requires gate ∧ uniqueness ∧ validator
(`knowledge/52`): uniqueness and format cannot rescue rejected geology.

## The one positive finding (and what it unlocks)

Sessions 15–16 concluded the detector ridge network is a uniqueness ceiling: any
re-derived detector re-emits the same ridge pixels and fails the > 70 % rule against the
dense probes. H39-5 breaks that ceiling *mechanically*: a 35 % off-ridge swap at matched
count lands at 68.3 %, and the pure extrapolated pool sits at 24.4 %. **Uniqueness is no
longer the binding constraint — credit is.** The swap machinery
(`migration.extrap_swap`, shared module, unit-tested) is surface-agnostic: any future
label-free surface whose novel dots earn > τ ≈ 0.059 credit/dot on LOSFO far-field truth
can now be emitted uniquely at the champion's budget. The ranked queue in `knowledge/52`
stands, with H39-2 (radiometric alteration lineaments, low-Th/K Hessian ridges ≥ 1 km)
next; its preregistration should add an Exp1 *signal floor* (e.g. canary AUC and a
pool-credit screen on the canary seed) so a signal-free surface stops before five LOSFO
seeds are spent — the clearest process lesson of this run. A displacement-clipped
(|v| ≤ 5 px, persistent ridges only) extrapolation variant is a *different* lane requiring
its own preregistration and fresh seeds ≥ 320; it is not a retune of this one and is not
recommended ahead of H39-2, because the canary gives no evidence the clipped subset
carries signal either.

## Site / safety fixes shipped with this result

Pass-2 review found the parallel Session 17 panel had reintroduced "OK to download — the
operator decides whether to submit" language for historical files, contradicting the
first-screen NO FILE APPROVED banner (the same defect class as
`submission-ui-mixed-disposition-2026-10-25`). Fixed in `scripts/build_site.py`: the
status table now answers "NONE" up front, lists the S18 candidate first as
🔴 DO NOT SUBMIT, marks H36-1/H38-1 "NOT APPROVED TO SUBMIT — inspection only", and the
Session 17 one-click panel is relabeled a historical artifact. Regression test:
`test_session18_candidate_is_unique_valid_but_do_not_submit`. Logged as
`s18-site-mixed-disposition`.

## Limitations and next steps

1. All scores cited for other sites remain OWNER-REPORTED; the 0.4413 vs. 0.3195
   leaderboard maxima in circulation still conflict and were not re-verified (no
   DrivenData access from this environment; nothing was uploaded, polled or scraped).
2. Inputs are hash-pinned owner mirrors, not organizer-authenticated downloads
   (`bridge-hashes-not-authenticated`). Prepared-features SHA reproduced Session 16's
   pin exactly (`83ed2704…`), so cross-session comparability holds.
3. LOSFO truth is still *mapped* faults held out by construction; absolute HOLDOUT-DTI
   overstates performance on genuinely unmapped faults (`src/gems27/losfo.py` header).
   The D1–D0 paired comparison is the meaningful quantity, and it is decisively negative.
4. Seeds 310–314 are consumed for this placement family. Next lane: H39-2 with an
   Exp1 signal floor; fresh seeds ≥ 320; same G1–G5 gate, uniqueness and validator rules.
5. GitHub Pages publication remains subject to the previously logged legacy-build
   error; raw `github.com/.../raw/main/...` links are the trustworthy route.

**Sources (official, for manual review):** competition
https://www.drivendata.org/competitions/306/competition-doe-gems/ · problem page
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ · rules
https://docs.nlr.gov/docs/fy26osti/96647.pdf · leaderboard
https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ ·
reference solution https://github.com/drivendataorg/gems-prize-reference-solution ·
USGS GeoDAWN https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and ·
INGENIOUS/GDR 1391 https://gdr.openei.org/submissions/1391 · GEMSDOE32 champion page
https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html · CRS https://epsg.io/32611 ·
Tversky index https://en.wikipedia.org/wiki/Tversky_index · Blakely (1995) *Potential
Theory in Gravity and Magnetic Applications*, Cambridge University Press (upward
continuation exp(−|k|h)).

## Merge reconciliation note (added before PR merge)

`main` advanced in parallel with its own "Session 18" safety review (0 experiments;
`evidence/current_run_card.json`), colliding on `evidence/s18_run_card.json`. Resolution:
the safety review keeps that path; this experiment's card moved to
`evidence/s18_h39_5_run_card.json` with references updated (`s18-session-label-collision`).
The merged site keeps main's locked current pages and archive architecture; the H39-5
panel renders in the archive with the same 🔴 DO NOT SUBMIT verdict. Adding the
`s18_candidate` manifest slot changed `docs/downloads/manifest.json`, so the safety
review's hash-bound card was re-pinned with its own recorder
(`scripts/record_current_review.py`, semantics unchanged). Post-merge verification:
424 tests passed, 2 skipped; ruff clean; downloads audit 337 checks PASS. No evidence
from either run was recomputed or combined.
