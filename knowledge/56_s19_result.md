# S19-RADLIN result — LOSFO gate PASSED, strict uniqueness FAILED, verdict negative

**2026-10-26. Three experiments used; lane closed. No slot spent, no upload.**

## Download and disposition

New output: [`gems28-s19-radlin-cover-20261026-6fa38f9d317b-allfinite.tif`](../docs/downloads/gems28-s19-radlin-cover-20261026-6fa38f9d317b-allfinite.tif)

- **Download for reproducibility: YES. Submit to competition: NO — 🔴 DO NOT SUBMIT.**
  The file passed its frozen scientific (LOSFO) gate and exact-file validation, but failed
  the frozen strict uniqueness rule against a dense unscored probe raster (below).
  Under the preregistered rule that failure is a duplicate-stop; the banner does not
  negotiate after the result is known.
- Name: `GEMSDOE28-S19-RADLIN-6fa38f9d317b`
- Note (97/140): `S19 RADLIN coverage 37654 dots; LOSFO passed but uniqueness vs dense probe FAILED; DO NOT SUBMIT.`
- All-finite SHA-256: `8534701e5d91572a39dba5e9d132e1c747aeab2f5223015a96ee96ace292493b`
  (NaN variant `de21416d03f8baf8c70e56cb0f90272ac7660ef23af89f301f2c5a545dea93c6`).
- Automated exact-file checks (shared `verify_geotiff`, plus independent
  `scripts/verify_downloads.py`: **407 checks, 0 failures** over all manifest downloads):
  one float32 band; 3,730 × 3,292; EPSG:32611; transform `[100,0,243350,0,-100,4508550]`;
  whole array finite and in [0,1]; values {0,1}; 37,654 dots; zero catalogue dots.
  Local checks against the pinned owner-mirror template are NOT organizer authentication
  and do not guarantee portal acceptance. The all-finite (zeros-outside) variant is the
  download named above because it cannot trigger a whole-array NaN/range reading; the
  official format text describes null/NaN outside bounds, and no claim is made that the
  compatibility variant supersedes it.

## Why the reported GEMSDOE32 leader improved (byte-verified, conditional)

`evidence/s18_champion_forensic.json` (re-verified this session: all nine focus-site
artifacts fetched and SHA-256-matched): the `e5eb6e7e-zeros` raster is exactly solo-r1
minus its 2,545 dots at catalogue distance ≤2 px, zero added. With
`DTI = TP/(0.2·(TP+FP) + 0.8·|G|)`, deleting dots whose lost credit per removed FP is
below the break-even `0.2·DTI/(1−0.2·DTI)` raises DTI — emission hygiene, not a new
detector. Score causation on private expert labels cannot be measured here; all
0.2477–0.2778 values remain **OWNER-REPORTED**, none **ORGANIZER-CONFIRMED**.

**Best submission among the nine focus sites, stated plainly:** by owner-reported score
the GEMSDOE32 champion (0.2778, 37,654 dots) is the family's best *reported* artifact,
followed by GEMSDOE36 (0.2750), GEMSDOE28 H36-1 (0.2710) and GEMSDOE31/28 solo (0.2708).
None of them is a file this project may submit as its own: they are previous submissions,
and copying or ring-pruning any of them is a >95% duplicate. The only honest "submit
this" answer today is **none** — see the disposition above.

## Experiment 1 — surface, canary, pre-placement uniqueness

Label-free ThK lineament surface (`src/gems27/radlin.py`, frozen in `knowledge/55`):
valid ThK pixels 5,166,085; ridge pixels 918,545; score max 0.620.
Leakage canaries vs LOSFO seed-320 withheld systems (74,025 withheld positives over the
gate seeds; canary positives are seed-320's hidden set, 250,000 sampled negatives >600 m
from hidden truth): score AUC 0.4998, bonus AUC 0.5134, inverted-ThK field AUC 0.5024 —
all far below the 0.90 leakage stop. Near-chance AUC is **not** evidence the lineament
field is useful; it only clears leakage.
Pre-placement registry check (declared scope: local `*-nan.tif` downloads + byte-verified
focus-9 forensic copies): max |Spearman| 0.0027, max top-pool within-3 px overlap 26.4%.
**PASS** — placement proceeded.

## Experiment 2 — frozen LOSFO gate (seeds 320–324)

**HOLDOUT-DTI**, evaluator `run_losfo_harness.eval_set v2 → metric.dti_binary`
(hash bundle in `evidence/s19_holdout.json`). Whole fault systems hidden with a 600 m
buffer, four quadrants, 20 cells, **74,025 pooled withheld positives / 46,711 unique**.

| Arm | HOLDOUT-DTI | 95% CI | credit/dot |
|---|---:|---|---:|
| S19 candidate (RADLIN-weighted coverage) | **0.10737** | [0.08803, 0.12631] | 0.05132 |
| H38-1 baseline recomputed (rung30 + joint) | 0.10193 | [0.08261, 0.12086] | 0.04865 |
| Paired gain | **+0.00544** | **[+0.00128, +0.00925]** | — |

All six frozen gates pass (gain >0.001, lower CI >0, 3/4 folds — NE fold −0.00052 —
5/5 seeds, buffered >6 px everywhere, zero visible-catalogue dots). Matched dot counts
per cell (218,167 both arms).

**Attribution limit (do not over-read):** this gate tests the candidate *as frozen*.
Prior work (`knowledge/39`) measured the all-ridge coverage construction alone at
+0.0052/+0.0059 far-field — the same magnitude as this gain. This experiment therefore
does **not** isolate a contribution of the RADLIN ThK bonus over plain coverage packing,
and no such claim is made. The canary AUCs (~0.50) say the lineament field alone has no
discriminative power against catalogue truth; any RADLIN contribution would be through
placement weighting, unmeasured separately. Catalogue-mapped hidden systems are also
not a sample of truly unmapped faults, and only four geographic bootstrap blocks exist.

## Experiment 3 — build, validator, final uniqueness

Full-fit detector, coverage packing to exactly 37,654 dots at >2 px from the full
catalogue (781,821 eligible ridge pixels). Validator: PASS both variants.
Final-dot uniqueness vs the declared registry:

| Comparator scope | Max within-3 px | Max sample Spearman |
|---|---:|---:|
| Scored focus-9 artifacts (byte-verified) | **44.5%** (GEMSDOE27) | 0.037 |
| All local registry rasters | **93.4%** (H37-1 probe-union, unscored) | 0.695 |

The strict frozen rule — >70% within 3 px of **any** registry raster ⇒ duplicate, log
and stop — fires on the H37-1 probe-union blanket (38,545 dots spread over the
H19-5 ∪ detector-ridge union, a research probe that was never a scored submission),
and also on two other dense research rasters (74.2%, 71.2%). **Verdict: negative.**
Logged as `s19-uniqueness-dense-probe-blanket` in `registry/irregularities.json`.

## What this does and does not establish

- It establishes a reproducible, buffered, whole-system holdout gain of the frozen
  candidate over the registered H38-1 recipe, at matched count, with no leakage canary
  triggered and an exactly valid file. That is the strongest local scientific result
  in this repository's S18-style protocol to date — and it still earns no slot, because
  uniqueness is a co-equal gate, not a tiebreaker.
- It does not establish that the file would score above 0.2778 (or any value) on the
  organizer leaderboard: HOLDOUT-DTI is a local catalogue-recovery proxy, the
  attribution limit above applies, and no organizer receipt exists.
- The open question for a future preregistered session (fresh seeds ≥325, decided
  *before* placement): should unscored dense probe blankets count as uniqueness
  comparators, or only scored/submitted rasters? If the latter had been frozen, this
  candidate would have passed uniqueness at 44.5%. That question must not be answered
  retroactively for this raster.

## Next steps (ranked)

1. Preregister the registry-scope question and, if probes are excluded with reasons
   recorded in advance, re-run an RADLIN-weighted coverage candidate on fresh seeds
   ≥325 — or accept the strict scope and design placement that also escapes probe
   blankets (e.g. off-ridge placement with a positive LOSFO result, which two prior
   migration lanes failed to produce).
2. Isolate the RADLIN bonus: candidate-as-frozen vs identical coverage with bonus=0,
   paired on fresh seeds, before claiming any alteration mechanism.
3. Keep the slot with the separate selector; reconcile the parallel-run registry
   across sessions so uniqueness scope is synchronized, not snapshot-local.
