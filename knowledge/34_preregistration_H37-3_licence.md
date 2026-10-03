# Preregistration — H37-3 far-field test: Euler SI-0 depth coherence as a **positive emission licence**

**Written and committed BEFORE the arm is run and before its seeds are touched.** The companion code
change (`scripts/run_losfo_harness.py --euler-licence`, `tests/test_euler_licence.py`) is committed in
the same commit as this file, so that commit hash is the freeze. Any threshold edited after the run
begins must be declared as a deviation in the result write-up.

## 1. Why this arm, and why far-field

H37-3 is rank 2 of `knowledge/31_hypotheses_session13.md`. H37-1 (rank 1) passed its interleaved gate and
then **failed** its far-field falsification (`knowledge/33`): the interleaved holdout's hidden truth is
100 % catalogue pixels (`evidence/arm_habitat_decomposition.json`), so it cannot see the population that
matters for new credit. Every future ADD arm is therefore gated on the LOSFO far-field harness, never on
the interleaved proxy.

The mechanism under test: USGS/INGENIOUS catalogue faults are a *surface-rupture* compilation. A shallow
magnetic contact with no Quaternary scarp — buried under basin fill, or in a lithology that cannot hold
one — still produces SI = 0 Euler solutions whose locations **and depths agree within a tight
tolerance** (Reid et al. 1990, DOI `10.1190/1.1442774`). The discriminating statistic is the
**within-cluster depth dispersion**, not edge amplitude, which every existing layer already measures.
H31-1 fed Euler rasters into the 41-band GBDT as inputs and failed its screen (`−0.001947`); H32-1/H36-1
use the clusters *defensively* as a prune-protection gate. **No arm in this repository has used depth
coherence as a positive licence to place dots.**

## 2. Fixed definition of the arm (thresholds frozen here)

* **Cluster source (fixed, committed):** `evidence/h31_1_euler_clusters.csv` — 6,309 SI-0
  depth-coherent clusters from the H31-1 run (`src/gems27/euler.py`), columns
  `row,col,median_depth_m,depth_mad_m,n_solutions`, all 6,309 verified inside the 3,730 × 3,292
  footprint grid at `round(row),round(col)`.
* **Licence rule, applied identically to every cell:** keep clusters with
  `depth_mad_m <= 60` **and** `median_depth_m <= 400` **and** `n_solutions >= 8` → **1,435 candidate
  dots** (fixed before the run; 686 at mad ≤ 40, 1,185 at depth ≤ 300).
* **Eligible licence pixels:** candidate pixels that are in `footprint` **and** in `~known` (off the
  catalogue the detector was allowed to see) **and** in `~base` (not already emitted by the raster
  cascade). This makes the arm a *discovery* claim, not a re-emission of mapped faults.
* **Spacing:** greedy in ascending `cluster_id`, keeping a candidate only if it is ≥ `thin_d` = 2.8 px
  from every kept licence dot **and** from every pixel of `base` (the shipped independent-set spacing).
* **Arms evaluated on the identical far-field truth, cell by cell (paired):**
  1. `base` — the frozen raster cascade, exactly the far-field base of `knowledge/33`;
  2. `licence` — `base ∪ licensed dots`;
  3. `random_control` — `base ∪ k` dots where `k` is the *same count* as the licence added for that
     cell, drawn by a seeded (seed·4 + fold + 1000) greedy over the eligible pool
     `active & ~base & ~known` under the same 2.8 px spacing. This separates *licence content* from
     *more dots inside the same off-catalogue region*.
* **Assertions before any number is used:** `licence ∩ base = ∅`; `licence ∩ known = ∅`;
  `|random_control ∩ base| = 0`; and the unchanged base arms must reproduce the stored diagnostic
  (the F5-style integrity check already in the harness output).

## 3. Panel and cost

* Instrument: `scripts/run_losfo_harness.py --seeds 260-264 --euler-licence <csv> --out
  evidence/losfo_h37_3_licence.json`, defaults otherwise (`--dilate-px 3`, `--buffer-px 6` i.e. 600 m,
  `--thin-d 2.8`). 5 seeds × 4 quadrant folds = **20 paired cells**, the same size and power as the
  H37-1 far-field test (`knowledge/32`).
* **Seed spend: 260–264 by this test. 265–269 remain free and unspent.** The LOSFO decade 210–214 is not
  touched by this arm; this test uses the harness *without* `--packing-variants`, so the H37-1 far-field
  result cannot be recomputed or diluted.
* Expected runtime ≈ 12–14 min (the H37-1 far-field run was 757 s for 20 cells with three extra packing
  arms; this adds one cheap arm per cell and reuses the same detector fits).

## 4. Criteria (all frozen now)

| id | criterion | threshold |
|---|---|---|
| **C1** | transfer: mean paired ΔDTI(`licence` − `base`) > 0 | > 0 **and** ≥ 15/20 cells positive **and** ≥ 4/5 seeds positive |
| **C2** | pays at the live bar: pooled credit per added dot | ≥ **0.0548** (`τ_live` = 0.2·DTI/(1 − 0.2·DTI) at the incumbent live 0.2600/0.2635) |
| **C3** | content, not extra dots: mean paired ΔDTI(`licence` − `random_control`) > 0 | > 0 **and** ≥ 15/20 cells positive |
| **C4** | integrity | base arms reproduce the stored diagnostic; the §2 assertions hold |

Reported regardless of outcome: mean and per-seed ΔDTI with a t-based 95 % interval (tcrit 2.093,
19 df), added-dot counts, credit per added dot, and the same statistics against the far-field break-even
`τ_far = 0.2·DTI_far/(1 − 0.2·DTI_far)` ≈ 0.0203, so the reader can see both bars (far-field and live).

## 5. Pre-committed interpretation

* **C1 ∧ C2 ∧ C3 pass** → H37-3 is a *validated ADD arm*: it earns credit off-catalogue at a rate that
  would pay on the live board. Next step is a submission variant on the shipped file plus its own frozen
  interleaved gate; it does **not** displace the one-click primary by itself (the primary's rule is the
  frozen gate in `docs/downloads/manifest.json`).
* **C1 ∧ C3 pass, C2 fails** → *far-field positive, below the live break-even*: no slot; the arm is kept
  as a research candidate and the honest statement is that it does not pay at the current operating
  point. This is the expected outcome class given H35-1's `0.0132` credit/dot.
* **C1 fails** → **H37-3 REFUTED**; rank-3 H37-2 becomes the next arm and `knowledge/31`'s ledger is
  updated to say so.
* **C3 fails while C1 passes** → the credit is generic "more dots along the detector field", not the
  Euler content; the *mechanism* is refuted even though the number is positive, and the arm is not
  promoted.
* Any other combination is reported as-is, without re-thresholding.

## 6. Scope and limits declared in advance

* The harness packs the detector's own ridge pool for `base`; it does **not** pack the shipped H19-5
  surface. The far-field statement is therefore about the *rule* and the *added content*, evaluated
  end-to-end on a pool where every arm is measurable. A positive result licenses a build on the shipped
  file; it does not by itself measure the shipped file.
* The cluster input is fixed and committed, so this test has exactly one degree of freedom (the spacing
  greedy), and the licence rule's three thresholds were chosen from the *pre-run* distribution printed
  in `knowledge/31` (median depth 296 m, P90 614 m, median mad 47.8 m), not from this panel's truth.
* LOSFO removes whole fault systems with a 600 m buffer; it is a *hard* far-field protocol. Passing it
  is necessary, not sufficient, for live transfer.
* No hallucination: every threshold above is either a constant already committed in the repository, a
  distribution already published in `knowledge/31`, or a count printed from the frozen CSV before the
  run (`1,435` candidates for the licence rule; `6,309` total).
