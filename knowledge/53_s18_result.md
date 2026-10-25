# Session 18 result — H42-1 migration-extrapolated relocation: NEGATIVE (falsified with controls)

**Date:** 2026-10-25. **Lane/preregistration:** `knowledge/52_preregistration_H42-1_migration_relocation.md`
(frozen before any fit; Session 16's handed-forward next lane). **Experiments used:** 3/3.
**Slot spent:** none. **Verdict:** `negative` — the unique TIFF built in Exp 3 is
inspection-only (🔴 DO NOT SUBMIT). Every score below is **HOLDOUT-DTI** (local
hide-and-recover proxy) or **OWNER-REPORTED**; nothing is ORGANIZER-CONFIRMED.

## Why 0.2778 won (re-verified byte-for-byte this session; education only)

After restoring all 17 hash-pinned inputs (prepared-feature SHA-256 `83ed2704…`
reproduces Session 14 exactly), the focus-site rasters were fetched from GitHub and
compared pixel-exactly (`evidence/s18_champion_forensic.json`): champion `e5eb6e7e`
(37,654 dots, SHA-256 `c55bafc4…`) = solo `8acb75e1` (40,199 dots; GEMSDOE28 and
GEMSDOE31 copies dot-identical) minus the d(catalogue) ≤ 2 px ring (2,545 removed,
0 added); solo = `dotted-h19-5-d2-8` (44,090 dots; GEMSDOE25/30 dot-identical) minus
the ≤ 1 px ring (3,891 removed); GEMSDOE36 = champion + 1,200 dots, 0 removed. The
group's best owner-reported score is therefore **emission hygiene on one unchanged
H19-5 surface** — flank dots beside mapped faults earn ≈ 0 credit at near-full FP cost
under DTI (α = 0.2, β = 0.8, 300 m kernel), so deleting them pays ≈ +2.76×10⁻⁶ DTI
each (Sessions 15–16). A ring-3 copy would be a subset of the champion
(binary φ(champion, solo) = 0.968 measured today > 0.90 duplicate threshold) and was
not built. Beating 0.2778 *uniquely* needs new credit above τ ≈ 0.059 credit/dot from
differently placed dots. This session tested the one placement lever Session 16 left
open. It failed cleanly (below), so **no, this lane does not beat 0.2778**, and no
projection to that effect is made.

## Experiment 1 — vector field + leakage canary (`evidence/s18_canary.json`) PASS

Six label-free bands alone vs LOSFO seed-310 withheld systems (14,681 hidden px):
max(AUC, 1−AUC) = 0.5032–0.5270 for all (signed migration, coherence, vector magnitude,
shift magnitude) — far below the 0.90 leakage stop; honestly weak univariate signal, as
in S15/S16. Max |Spearman| vs in-stack bands 0.486 (sample 200 k). Label-free inventory
already warned of trouble: the vector field has support on **93.2 %** of the footprint
with median |v| = 5.18 px on support — at 100 m the HG ridge fields are dense, so
nearest-ridge matching is mostly matching *different* nearby ridges, not tracking one
physical edge across continuation levels. 49.7 % of footprint pixels carry a nominal
shift ≥ 0.5 px. The frozen design ran anyway (no mid-stream retuning). (Audit note:
Exp 1 was executed twice before the gate: the first run's supplementary Spearman table
contained NaNs from prepared-stack NaN pixels; a reporting-only finite-pair fix was
applied and the deterministic build re-run — bands and all AUCs identical.)

## Experiment 2 — frozen LOSFO gate, seeds 310–314 (`evidence/s18_h42_losfo_gate.json`) FAIL

HOLDOUT-DTI (shared `run_losfo_harness.eval_set`; `losfo.py` + `metric.py`; whole fault
systems withheld, 600 m buffer, visible-only blocking, pixel-exact masks; pooled;
76,869 withheld cell-truth px over 20 paired cells):

| arm | pooled DTI | Δ vs base | credit/dot | dots |
|---|---:|---:|---:|---:|
| base (detector dots) | 0.105485 | — | 0.04851 | 241,640 |
| **phys (up-dip relocated)** | **0.100528** | **−0.004957** | 0.04817 | 224,714 |
| anti (sign-flipped) | 0.101039 | −0.004446 | 0.04859 | 223,288 |
| rand (seeded rotations) | 0.100020 | −0.005465 | 0.04878 | 218,029 |

Mean paired ΔDTI(phys−base) **−0.004894**, paired-bootstrap 95 % CI
**[−0.006577, −0.003294]** (entirely negative), **1/20 cells** positive, all 5 seed
means negative (−0.0033…−0.0058), all 4 fold means negative (NE worst, −0.0100).
39.7 % of base dots moved ≥ 1 px (cells 31–51 %; mean rounded shift ≈ 1.7 px), so the
test was strong, not underpowered. Gate: **G1 FAIL, G2 FAIL, G3 FAIL** (phys −0.00496
does not beat anti −0.00445 or clear rand −0.00546 by any dip-specific margin),
**G4 FAIL** (0 dots on visible-known ✓, but post-shift re-thinning shrinks the count
7.00 % > 5 % cap), G5 PASS → `gate_passed=false`.

**Reading (falsification, not mere null):** relocating dots in *any* direction —
physical, opposite, or random — costs the same ≈ −0.0044…−0.0055 DTI. The detector
ridge position itself carries the credit, and nearest-ridge migration vectors at 100 m
extract no usable dip signal to improve on it. The H42-1 relocation hypothesis, *with
this vector estimator*, is closed: do not retune sign, scale, cap, or depth source on
seeds 310–314. A future migration attempt would first need same-edge ridge *tracking*
across continuation levels (path-following a single edge as h grows) under a fresh
preregistration on seeds ≥ 320 — and after this result its expected value ranks below
H42-2 (segment-object ranking) and H42-3 (alteration lineaments) in `knowledge/52` §2.

## Experiment 3 — unique TIFF built, inspection-only (`evidence/s18_candidate_build.json`)

`gems28-h42-1-migx-reloc-b1-20261025-290553965159-{nan,allfinite}.tif` (+ single-member
zip), 34,492 dots (37,521 base dots → 17,373 moved ≥ 1 px, 46.3 % → re-thin 34,492).
This file **is** the unique TIF required by the task — generated by the frozen lane,
never copied from any prior submission — and it is labelled **🔴 DO NOT SUBMIT**
because its frozen gate failed. Downloading it for inspection is safe; uploading it
would spend a weekly slot on a falsified idea.

- **Format (answers the portal error "Predicted values must be in range [0, 1]"):**
  both variants pass every hard check in `submission.verify_geotiff` (independent
  re-read): single-band float32, EPSG:32611, 3730 × 3292, template transform/bounds,
  values inside the footprint exactly {0.0, 1.0}, 0 NaN inside the footprint; the
  **all-finite record file has no NaN anywhere** (strict whole-array [0, 1] PASS),
  0 dots on the catalogue, min d_cat > 2 px. SHA-256 in `evidence/s18_run_card.json`.
- **Uniqueness vs the binding scored registry** (ten owner-reported scored rasters of
  GEMSDOE24/25/27/28/30/31/32/33/36, `knowledge/52` §3): **PASS vs every member** —
  binary φ ≤ 0.029, final dots within 3 px ≤ 45.8 % (champion: φ = 0.028, 40.3 %),
  surface Spearman ≤ 0.90. *Disclosed:* 89.9 % of dots lie within 3 px of the unscored
  dense probe blanket `52a13184267e` — the standing `s15-uniqueness-dense-probes`
  irregularity; under the strictest any-download reading no ridge-based file can pass,
  which is why the binding registry is the scored set and the table is published for
  the selector.
- **Evidence schema:** `scripts/check_promotion.py docs/data/run_card_s18.json` →
  `negative`, failing *only* on "no positive paired gain CI" — the paperwork is
  complete; the science failed. That is the intended fail-closed behaviour.

## Run card (summary; machine-readable card: `evidence/s18_run_card.json`)

- Hypothesis/mechanism/mimic: knowledge/52 §1 (dipping contact/dike is the named mimic).
- HOLDOUT-DTI: phys pooled 0.100528, cell-bootstrap 95 % CI [0.088259, 0.113720];
  Δ −0.004957, paired CI [−0.006577, −0.003294]; 76,869 withheld positives.
- Registry: binding PASS (above); raster SHA-256, validator output, unique name
  `GEMSDOE28-h42-1-migx-reloc-b1-290553965159` and the 92-character note are in the card.
- Verdict: **negative**. Negative results are deliverables; no slot selected or spent.

## Preregistration deviation (Pass-2 review finding, disclosed)

`knowledge/52` §1 freezes the combined vector as "averaged across the two fields
weighted by their three-level ridge coherence"; `migration.build_migration_vectors` as
implemented **support-averages** the per-field vectors (mean over fields with a nonzero
corridor vector). Found by re-reading code against preregistration in Pass 2; recorded
in the run card (`preregistration_deviations`) and `registry/irregularities.json`
(`s18-vector-combination-deviation`). The negative verdict is robust to this choice —
phys, anti and rand are equally harmful, so no reweighting of the same mismatched
nearest-ridge vectors can be credited with a dip signal — but strictly, the
coherence-weighted estimator as written remains untested. Substituting it now would be
a new variant on spent seeds and is prohibited; any retry needs a fresh preregistration
on seeds ≥ 320. No other deviation was found: canary bands, gate arms, thresholds,
blocking, budget search, thinning, registry and validator all match `knowledge/52`.

## What would actually beat 0.2778 (updated read)

1. Placement perturbations of the standard ridge are now closed in both forms tested:
   feature-space (H39-1/H40-1, surface ≈ duplicate, gate FAIL) and geometric
   (H42-1, unique, decisively harmful). The ridge location is information; moving off
   it without a same-edge physical track destroys credit at ≈ 0.005 DTI per 40 % moved.
2. The only addition pattern that has ever cleared τ on far-field truth in this repo is
   small, multi-physics-*corroborated* on-ridge addition (H38-1, +0.000747 LOSFO). Its
   scale (200 dots ≈ +0.0007) is two orders below the ≈ +1,150-credit gap to the top,
   so a competitive unique file needs a corroborator with far larger *specific* support.
3. Next preregistration recommendation: **H42-2 segment-object ranking** (knowledge/52
   §2) — it reallocates budget *along* the ridge to long, straight, single-facing
   segments instead of moving dots off it, on fresh seeds ≥ 320, with the LOSFO gate
   and binding-registry uniqueness defined exactly as here. H42-3 (radiometric
   alteration lineaments as objects) is the follow-on corroborator candidate.
4. Data blockers unchanged: GDR 1391 temperature attributes and MT depth slices are
   official and free but unreachable as bytes from this sandbox (egress allowlist);
   the obtainable GEMSDOE30 probe raster is presence-only. The Actions bridge
   (`.github/workflows/fetch-gdr-external-layers.yml`) remains the route to unblock them.

## Three review passes (this session)

- **Pass 1 — implement & verify:** restored all 17 pinned inputs + rebuilt the 32-band
  feature cache (SHA-256 reproduces Session 14); byte-forensic of the nine focus sites'
  top files; froze `knowledge/52` (lane + 5 ranked hypotheses + gate) before any fit;
  Exp 1 canary PASS (AUCs 0.503–0.527); Exp 2 frozen LOSFO gate FAIL with controls;
  Exp 3 built the unique TIF (binding uniqueness PASS, validators PASS); run card +
  `check_promotion.py` (negative on the paired-gain CI only); site + README updated so
  the download/submit answer is obvious at the top of the first screen.
- **Pass 2 — bugs & edge cases:** full test suite 329 passed / 2 skipped; `ruff` clean;
  `scripts/verify_downloads.py` PASS (307 checks, 0 failures); independent re-read of
  both TIF variants, manifest/ZIP/note hash recomputation, and an independent
  within-3 px recomputation vs the champion (0.4034, matches build record); HTTP preview
  served the site and the downloaded all-finite TIF hash-matched the run card. Found and
  disclosed the vector-combination deviation above; fixed a note-length overflow in
  `finalize_s18.py` before it could write a bad card.
- **Pass 3 — request reconciliation:** unique TIF generated (not copied), obvious
  download/submit status, automated inspection only, single frozen lane, surface+dot
  uniqueness vs the scored registry, HOLDOUT-DTI labelling, leakage canary, JSON run
  card, 3-experiment budget, 5 ranked hypotheses with data-obtainability checks,
  executive-summary submission instructions, and the [0, 1] portal-error remedy are all
  satisfied as documented; the scientific verdict is `negative`, so **no file is
  approved and no weekly slot should be spent**. Remaining work and limitations are in
  "What would actually beat 0.2778" above.
