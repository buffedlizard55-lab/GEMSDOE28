# H35-6 preregistration — adjudicating the candidate ladder on fresh seeds `235–239`

Status: **frozen before execution.** This file was written after the H35-1 gate was launched but
**before** seeds `235–239` were touched. No result from `235–239` existed at the time of writing.

## 1. Why this arm exists (an irregularity found by review, not a new geological idea)

This session's review found a live **Maximize P(Win)** defect on our own site. The page promotes
`c3aeda1d31a3` (H32-1 post-thinning) as the one-click primary. But that file is **dominated on every
published statistic** by the file in the tertiary slot:

| Statistic (same base `d=2.8`, same seeds `180–189`, same 4 folds) | `c3aeda1d31a3` primary | `31e35eee884e` secondary | `8acb75e1f2cc` tertiary |
|---|---:|---:|---:|
| mean OOF `delta DTI` | +0.001272 | +0.001399 | **+0.001766** |
| worst seed gain | +0.000907 | +0.000854 | **+0.001370** |
| folds improved | 4/4 | 4/4 | 4/4 |
| fold NW | +0.001023 | +0.000956 | **+0.001600** |
| fold NE (lidar-gap heavy) | +0.002293 | +0.002041 | **+0.003190** |
| fold SW | +0.000272 | +0.000505 | **+0.000487** |
| fold SE | +0.001498 | +0.002094 | **+0.001787** |
| removed credit per removed FP | 0.00402 | 0.48930 | **0.00598** |
| hybrid projection on the `0.2600` anchor | 0.26650 | 0.26850 | **0.27013** |

The tertiary is better in **every fold** and in the **worst seed** as well as the mean. The H34
operating-point study independently reaches the same place from the other direction: it re-judged the
archived pruning arms against the *live* threshold `tau = 0.05499` and returned
`live_verdict = PRUNE` for H32-1 mid-segment flank shadow (`e = 0.004`, `DTI after 0.26680`),
H32-2 deep magnetic de-screening (`e = 0.03435`, `DTI after 0.26510`) and H27-4 `d_cat <= 200 m`
(`e = 0.008`), and it found the optimal packing rung to be `3.0` with `dti_after 0.26346` for pure
re-thinning. Everything with `e < 0.0549` pays.

**So why is the dominated file the one advertised for a weekly slot?** The honest answer is
selection bias, and it is exactly the reason this arm exists:

* `c3aeda1d31a3` is the output of a **preregistered** arm whose gate was frozen in
  `knowledge/14_preregistration_H32-1.md` before its seeds were spent.
* `8acb75e1f2cc` is the best of **four** variants scored on **one** holdout run (seeds `180–189`).
  Picking the maximum of four correlated variants and then treating that maximum as a genuine
  `+0.0005` edge over the runner-up is a multiple-comparison error. The *family* effect (pruning pays
  at this operating point) is solid; the **ranking inside the family is not**.

Two consequences follow, and they point in opposite directions. Either we keep promoting the
preregistered file and knowingly leave a better-supported candidate on the bench, or we promote the
best-looking variant on evidence that was used to select it. Both are defensible; neither is decided
by the data we already have. That is what a fresh decade is for.

## 2. The decision this arm must make

One question, with an operational answer:

> **Which single file should the human operator download and submit for the next weekly slot?**

The standing rule is *"never spend a weekly submission slot on an idea that has not beaten the current
holdout best"*. All four files beat the `d=2.8` control, so the rule is satisfied by all of them; the
rule does **not** say which one to send. This arm produces that answer, or explicitly declines to.

## 3. Frozen protocol

| Item | Value |
|---|---|
| Script | `scripts/run_h32_1_holdout.py` — **unmodified, frozen**, the same script that produced the `180–189` table |
| Seeds | **`235–239`** (5 fresh seeds; `230–234` belong to H35-1, `180–189`/`190–199`/`200–209`/`220–229` are spent) |
| Folds | the script's four spatial quadrants (`NW`, `NE_LidarGapHeavy`, `SW`, `SE`) with its 600 m buffer collar |
| Variants | `h32_1_post_d28` (=`c3aeda1d31a3`), `h32_1_pre_d28` (=`31e35eee884e`), `h27_4_blind_r1_d28` (=`8acb75e1f2cc`), `control_prune_protected_only_d28` |
| Output | `evidence/h35_6_candidate_headtohead.json` |
| New code | **none.** Verified with `git diff` that this arm changes no source file. |

Using the frozen script unchanged is the whole point: it is the only way the `235–239` numbers are
directly comparable with the `180–189` numbers that created the problem.

## 4. Promotion rule (frozen before the run)

Let `G(v)` be variant `v`'s mean OOF `delta DTI` on `235–239`, `s(v)` its seeds won out of 5, `f(v)`
its folds improved out of 4.

1. **Promote** the variant with the largest `G(v)` to the site's one-click primary **iff** it also has
   `s(v) >= 4` and `f(v) >= 3`. Otherwise **no change**: the current primary stays and the arm is
   reported as inconclusive.
2. **Demote risk check.** If `G(control_prune_protected_only_d28) >= G(winner)`, the family gain is
   generic "prune harder" mass removal rather than a selective prune, and the result is reported as
   such — the winner is still promoted (the operator submits one file and the model still says the
   winner is the best of them), but the site must say the selectivity claim is unsupported.
3. **Confirmation is not required.** Unlike a new geological arm, this is a *choice among four
   pre-existing, already-frozen files*; the fresh decade is used to break a tie, not to establish a
   new effect. Five seeds is the budget; no extension, no re-run on another decade, whatever the
   outcome. If it is inconclusive, it stays inconclusive.
4. **No new raster is built by this arm.** It changes which existing audited file is advertised. Any
   file it promotes must already pass `verify_downloads.py` (`179/179`) before the site changes.

## 5. What would make this arm wrong

* **Family-wise error survives.** Five seeds is a small sample; a `+0.0005` gap is close to the
  `+/-0.0005` seed-to-seed spread already visible in `180–189`. Rule 1's `s >= 4`/`f >= 3` guard is
  the only protection, and it is weak. Stated here so the result is read as a *decision under
  uncertainty*, not a measurement.
* **The proxy is still a proxy.** The holdout hides published catalogue pixels; the live test set is
  expert-labelled faults *outside* that catalogue. `registry/irregularities.json` already carries
  `proxy-blind-to-far-field` at **high** severity for this reason, and `interleaved-holdout-has-no-
  far-field-truth`. A fresh decade reduces selection bias; it does **not** make the proxy unbiased.
* **Both leading candidates could be worse than the `0.2600` file.** The live-anchored model says
  otherwise (`tau = 0.05499` versus measured `e <= 0.006`), but the model's anchors are owner-reported
  scores, not organizer receipts.

## 6. Disclosure

* Five seeds and one script run are spent on an *adjudication*, not on a new physical hypothesis.
  This is deliberate: the alternative was to spend a weekly slot on a file chosen by an unblinded
  maximum-of-four.
* The review that generated this arm is recorded in `evidence/review_passes.md`; the defect it found
  is registered in `registry/irregularities.json`.
* No result from seeds `235–239` was inspected, computed, or cached before this file was written.
