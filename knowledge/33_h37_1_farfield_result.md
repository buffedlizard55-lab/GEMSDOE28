# H37-1 far-field falsification result (LOSFO packing diagnostic, seeds 210–214)

**Verdict: F1 FAILS. The +0.007289 interleaved gain of the H37-1 packing rule does not transfer to
faults that are absent from the catalogue. The far-field effect is `−0.000037` with a 95 % interval of
`±0.000832` — statistically indistinguishable from zero and at least nine times smaller than the
interleaved effect. The pre-committed demotion path of `knowledge/32` therefore applies.**

Evidence: `evidence/losfo_packing_farfield.json` (1,065 lines of per-cell records), produced by
`scripts/run_losfo_harness.py --seeds 210-214 --packing-variants` after the freeze commit `7e637c9`.
Runtime 757.3 s. Runner SHA-256 `cbc0c8d8…`; `losfo.py` and `oof_detector.py` hashes are unchanged
from the stored run.

## 1. Instrument integrity (F5)

**F5(a) PASSED exactly.** The unmodified base arms reproduce the stored diagnostic
(`evidence/losfo_farfield_diagnostic.json`) to eight decimals:

| quantity | new run | stored run |
|---|---|---|
| `losfo` mean DTI | 0.09973627 | 0.09973627 |
| `losfo` sum TP | 11160.55399598 | 11160.55399598 |
| `losfo` credit/dot | 0.04649901 | 0.04649901 |
| `losfo` mean dots | 12000.850 | 12000.850 |
| `leaky` mean DTI | 0.10154756 | 0.10154756 |
| `leaky` sum TP | 11291.30299215 | 11291.30299215 |

So the added arms did not perturb the base path: every difference below is ordering or objective only.

**F5(b/c) PASSED.** All arms are subsets of the single candidate pool and of `active`; the script
asserts `thinning.dot_thin(pool, 2.8) & active == base` before packing; the control arm has an explicit
seeded order and reproduces across runs.

## 2. Frozen criteria

| criterion | result | verdict |
|---|---|---|
| **F1** mean ΔDTI(`max_coverage` − `base`) > 0 under `losfo` | **−0.000037** (95 % CI ±0.000832), 9/20 cells up | **FAIL** |
| **F2** mean ΔDTI(`max_coverage` − `random_order`) ≥ +0.0005 under `losfo` | **+0.002091** (95 % CI ±0.001075), 18/20 cells, 5/5 seeds | PASS* |
| **F3** ≥ 15/20 cells and ≥ 4/5 seeds positive for F1 | 9/20 cells, 3/5 seeds | **FAIL** |
| **F4** report-only `leaky` contrast | `max_coverage` − `base` **+0.000322** (±0.001011), 12/20 cells | recorded |
| **F5** integrity | base arms reproduce exactly (above) | PASS |

\* F2's pass is **not** a clean ordering result and must not be quoted as one: the ordering arms are
*capacity-limited*. Visiting the pool in probability or random order, the maximal independent set under
`distance < 2.8 px` tops out at **10,975** / **10,992** dots, whereas the raster cascade reaches the
requested **12,001**. The coverage-greedy arm has no spacing constraint and hits **12,001 exactly**, so
the only exactly matched-count comparison in this run is `max_coverage` vs `base` — the one that fails.
`random_order` is worse than `base` mainly because it emits 8.4 % fewer dots.

## 3. What the run establishes

* **The interleaved gain is a catalogue-adjacency effect.** In the interleaved protocol 100 % of the
  hidden truth is catalogue pixels (`evidence/arm_habitat_decomposition.json`: habitat A truth = 0,
  habitat B truth = 120,983), so that protocol can only reward dots placed next to the published
  catalogue. The LOSFO protocol removes whole fault systems with a 600 m buffer and places every truth
  pixel ≥ 8 px from anything the detector saw. On that truth the rule is worth nothing.
* **It is a tight zero, not an underpowered null.** With 20 cells the paired interval is ±0.000832; an
  effect of the interleaved size (+0.007289) would have been detected with an order of magnitude of
  margin. The far-field effect is bounded above by +0.0008, i.e. < 11 % of the interleaved claim.
* **Coverage of the field ≠ credit on the truth.** `max_coverage` improved the achieved field coverage
  over `base` (15,570.2 → 15,670.8 under `losfo`, +0.65 %) at identical dot count, yet the DTI did not
  move — the extra covered mass is in places where the far field has no truth.
* **The raster cascade is a good far-field packer.** `.dot_thin`'s row-major visiting order is
  space-filling: it extracts more dots from the same pool under the same spacing constraint than either
  alternative order (12,001 vs 10,975 / 10,992), and it ties or beats them on far-field DTI.
* **The detector field, not the packer, is the limiting factor.** The honest far-field credit per dot
  at this operating point is 0.046499 (and 0.048297 for the prob-ordered arm) against the live
  break-even τ = 0.054852: at `d = 2.8` the far-field population does not pay for new dots under any
  packing rule tested here.

## 4. Decision taken (and the letter of the preregistration)

`knowledge/32` §5 committed in advance: *F1 fails → the artifact stays built and audited but is
demoted, the site and README carry the far-field number next to the interleaved one, and the arm's
status becomes "catalogue-local, not far-field validated".* That is what was done:

* `docs/downloads/manifest.json`: **primary returns to H36-1** (`b531dae0a36f`, the file whose
  projection is anchored to the live-measured dose ladder); **H37-1 moves to secondary** carrying the
  far-field result in its description and on the site.
* The site's H37-1 card and the README carry both numbers: interleaved `+0.007289`, far field
  `−0.000037 ± 0.000832`.
* The live projection for H37-1 is **withdrawn**: the modelled `0.278–0.286` assumed the interleaved
  effect would transfer. The honest statement is that H37-1 is expected to differ from H36-1 only in
  proportion to that part of the live truth which lies beside the published catalogue — a share the
  repository has never measured, and one the live record suggests is small (81.4 % of the 0.2477
  emission's dots are ≥ 300 m from the catalogue and those dots demonstrably earned credit).

**Deviation register.** The demotion is the preregistered action, but it is worth stating plainly for
the owner's own decision: the far-field test does **not** show H37-1 is *worse* than H36-1 — it shows
the extra claim is unsupported (`−0.000037 ± 0.000832`, a tie). An owner who judges the live scoring
population to be substantially catalogue-adjacent may legitimately prefer the H37-1 file; it remains
fully audited, one click away, and labelled with both numbers. Registered as
`h37-1-farfield-effect-is-zero` in `registry/irregularities.json`.

## 5. What this does not establish

* It does not test H36-1. The incumbent's re-layout is a *dose* change (rung 2.828 → 3.0 at fewer dots)
  whose support is the live-anchored ladder, and it has never been run through LOSFO. Its far-field
  behaviour is **unknown**, and the same demotion logic could in principle apply to it. Queued as a
  future diagnostic (the harness can now answer it in one run).
* It does not test the shipped *pool*: the harness packs the detector's own ridge pool, while the
  artifact packs the H19-5 surface. The far-field statement is about the *rule*, on the pool where the
  rule is measurable end-to-end.
* It does not re-test the dose axis (1.5×N), which the interleaved gate already recorded as fold-fragile
  (3/4 in `evidence/h37_1_holdout.json`) and which was deliberately excluded from this freeze.
* It says nothing about the two-field contrast as a *detector* measure: the stored and reproduced
  ratios (`losfo/leaky` DTI 0.9822, credit 0.9884) are unchanged, i.e. this repository's GBDT detector
  generalises far field almost as well as it interpolates — the failure here is the packing objective's,
  not the detector's.

*No-hallucination statement: every number in this document is read from
`evidence/losfo_packing_farfield.json`, `evidence/losfo_farfield_diagnostic.json`,
`evidence/arm_habitat_decomposition.json`, `evidence/h37_1_holdout.json` or the committed source of
`scripts/run_losfo_harness.py`; nothing was fetched from the network and no figure is estimated beyond
the explicit intervals shown.*
