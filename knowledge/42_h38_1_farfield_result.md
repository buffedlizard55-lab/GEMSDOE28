# H38-1 far-field result — the interleaved gain does not survive LOSFO (no artifact built)

**Verdict: no transfer licence.** On the frozen LOSFO decade `220-224` (`evidence/losfo_rad_farfield.json`,
20 cells, 776.3 s, `integrity_violations: []`) the radiometric-augmented detector's count-matched
coverage emission beats the frozen detector's by **+0.000959 mean ΔDTI with a 95 % interval of
±0.004469** — 13/20 cells, **2/5 seeds**, 2/4 folds, and **4/20 cells worse by more than 0.005**. The
gate's interleaved gain was `+0.002869` (10/10 seeds, 4/4 folds on seeds `280-289`). The far-field
interval is 1.5× the interleaved effect, so the honest reading is *unresolved, not positive*, and the
frozen F1 rule ("≤ 2/20 cells below −0.005") fails on the heavy tail.

**No H38-1 file was built.** `scripts/build_h38_1_submissions.py` exists and was written before the
far-field result, but it was **not executed**: `knowledge/40` §4 makes F1 the licence, and the licence
was not earned. The one-click primary stays with H36-1.

## 1. Numbers

| arm | detector | emission | mean DTI | mean dots | credit/dot | recall_w |
|---|---|---|---:|---:|---:|---:|
| `thin_d28_D0` | D0 | raster thinning at `d=2.8` (reference rule) | 0.09983 | 12,099.7 | 0.0454 | 0.1460 |
| `cover_n_D0` | D0 | coverage packing at `n_pre_D0` | 0.10571 | 11,436.0 | 0.0499 | 0.1518 |
| `thin_d28_D1` | D1 | raster thinning at `d=2.8` | 0.10118 | 12,122.2 | 0.0464 | 0.1494 |
| **`cover_matched_D1`** | D1 | coverage packing at `n_pre_D0` (PRIMARY) | 0.10667 | 11,436.0 | 0.0505 | 0.1537 |
| `cover_n_D1` | D1 | coverage packing at `n_pre_D1` | 0.10678 | 11,437.0 | 0.0506 | 0.1538 |

| criterion | value | verdict |
|---|---|---|
| **F1** mean ΔDTI(`cover_matched_D1` − `cover_n_D0`) ≥ 0 | **+0.000959** (95 % CI ±0.004469; 13/20 cells, 2/5 seeds, 2/4 folds) | mean yes, **heavy tail no** (4 cells < −0.005) |
| **F2** report-only `thin_d28_D1` − `thin_d28_D0` | +0.001348 (10/20 cells, 3/5 seeds, 2/4 folds) | recorded |
| **F3** integrity | 0 violations; every arm emitted its requested count; determinism replicated | PASS |
| **F4** D0 arms within ±0.004 of the probe's means | `cover_n_D0` 0.10571 vs 0.111635 (−0.00592); `thin_d28_D0` 0.09983 vs 0.106476 (−0.00664) | **FAIL → run void as a licence** |

## 2. The F4 failure is a mis-calibrated band in my own prereg, and it is disclosed as such

`knowledge/40` §3 F4 anchored the instrument to the earlier probe's five-seed means with a ±0.004
tolerance. Two facts measured *after* the freeze show that band was naive:

* the probe's own **seed-level** spread is SD `0.00999` (`thin_d28`) and `0.00802` (`cover_n`), so the
  standard error of a five-seed mean is `0.0036-0.0045` and the difference of two independent
  five-seed means has SD ≈ `0.0058` — the band was smaller than the noise of the quantity it compares;
* on the *per-cell* test instead of the mean test, the new decade's cells are inside the probe's
  observed range (`cover_n` 20/20, `thin_d28` 19/20), and the underlying geometry matches
  (hidden truth 75,223 px vs 76,356 px; `n_pre` 11,436.0 vs 11,338.9).

So F4 voided the run, not the pipeline: the same code produced the same kind of numbers on a normal
decade, and the run's own F3 integrity is clean. Registered as
`h38-1-farfield-f4-band-miscalibrated`, with the recalibration rule for any future freeze: the
tolerance must be derived from the observed seed-level SD (≈ `1.96 · s / √n` per arm), not chosen ad hoc.

**This run therefore cannot certify anything either way, and it is not re-run on this decade.** The
number that matters is nonetheless recorded, because the alternative — deleting a seen result because
its guard-rail misfired — is worse than publishing it with its status attached.

## 3. What this run does establish

* **The cover-vs-raster far-field effect replicated on an independent decade.** `cover_n_D0 −
  thin_d28_D0` = **+0.005881** with **5/5 seeds and 4/4 folds** (15/20 cells) against the earlier
  probe's `+0.005275` on seeds `215-219`. This is now the most strongly replicated far-field result in
  the repository, and it belongs to the *all-ridge* coverage construction identified in
  `knowledge/39` — not to the pool-restricted arm that `knowledge/33` falsified, and not to the packing
  used in the shipped H37-1 file.
* **That replicated rule is still not promotable on today's evidence.** Its far-field credit density is
  `0.0499` (D0) / `0.0505` (D1) against the live break-even `τ = 0.054852` at the `0.26` anchor; the
  rule improves *where the dots go*, not yet *what the field knows*. Registered as
  `cover-rule-far-field-gain-replicated-not-gated`: to promote it the repository needs a frozen
  interleaved gate **and** a pre-declared second far-field decade with ≥ 10 seeds, because the
  instrument's resolution on a 5-seed decade is ±0.0045.
* **The radiometric channels' far-field effect is smaller than the instrument can resolve.** Both
  emission rules move the same way (`+0.0010` coverage, `+0.0013` raster) and both are inside noise.
  Combined with the gate (`+0.0029` interleaved, `+0.0063` for the reference rule), the pattern is
  consistent with the channels carrying real but small-scale information whose far-field expression is
  not established. Recorded as an information result with a measured ceiling, not as a refutation of
  the radiometric prior.

## 4. Consequences

1. No H38-1 TIFF, no manifest change, no site download change, no weekly slot. `knowledge/41` stands as
   the gate record with its verdict amended to "interleaved pass, far-field unresolved".
2. H38-1 moves from "candidate" to "**open, far-field-unresolved**": the next measurement that would
   change its status is a properly powered far-field decade (≥ 10 seeds), not another interleaved gate.
3. The top-ranked next arm is now the **all-ridge coverage packing construction with the frozen D0
   detector** (twice-replicated far-field gain, `5/5` seeds in both runs), which needs its own frozen
   interleaved gate before any file is built. `knowledge/37` §ranking is updated accordingly in
   `registry/next_hypotheses.json:session14_addendum`.
4. The three cross-cutting findings of the session stand on their own: the far-field attribution
   (`knowledge/39`), the two harness errata (`knowledge/38` §§7-8), and the confirmation that the
   competition's own band 6 is a radiometric total-count channel that the detector had been silently
   missing.
