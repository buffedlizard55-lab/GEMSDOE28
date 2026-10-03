# H32-2 Result — shallow-over-deep magnetic gradient de-screening: FROZEN GATE FAIL (2026-10-03)

**Status: CLOSED NEGATIVE RESULT.** No confirmation run, no retuning on seeds 190–199, no
submission candidate, no weekly slot. Preregistration: `knowledge/16_preregistration_H32-2.md`;
evidence: `evidence/h32_2_holdout.json` (valid run) and
`evidence/h32_2_holdout_run1_invalid_2026-10-03.json` (run-1 sentinel defect, preserved).

## What ran

The repaired runner (see the Run-1 integrity correction in the preregistration) evaluated the
upward-continuation attenuation ratio `R = G1 / (G150 + 1e-3)` built from `tmi_hg`
(training_features) and `|∇H(TMI_up150)|` (geodawn_extensions_u8 band 4), with the repository's
frozen 4-fold spatial-CV OOF detector at d=2.8 on fresh seeds 190–199 (40 cells).

- R field is well formed after sentinel repair: dot-population percentiles p10 = 0.852,
  p50 = 1.025, p90 = 1.256 (≈1 as designed; rank thresholds invariant to grid scale offsets).
- Base control mean DTI = 0.094506 (seeds 190–199), 48,932.5 dots/seed before pruning.
- OOF inclusion threshold at that base = **0.019265**; live-0.2600 threshold = 0.054852.

## Gate outcome (all frozen criteria, primary variant `h32_2_p10_d28`)

| Criterion | Requirement | Observed | Verdict |
|---|---|---|---|
| 1. mean paired ΔDTI | ≥ +0.0010 | **−0.003767** | FAIL |
| 2. folds improved | ≥ 3/4 | 0/4 | FAIL |
| 3. seeds won | ≥ 8/10 | 0/10 | FAIL |
| 4. removed credit/FP < OOF threshold | < 0.019265 | 0.034350 | FAIL |
| 5. direction control ≥ primary efficiency | ≥ 0.034350 | 0.038273 | PASS |
| 6. R finite ≥ 95 % footprint | ≥ 0.95 | 1.00 | PASS |

`h32_2_p05_d28` is equally negative (−0.001776, 0/10 seeds, 0/4 folds).

## Interpretation (recorded, not used to override the gate)

1. **The physical direction is supported, the magnitude is not.** The direction control — pruning
   the *shallowest* (top-R) dots — loses *more* credit per removed FP (0.038273) than pruning the
   deepest (0.034350), consistent with shallow magnetic contacts being better fault proxies. But
   the deep class still carries ≈1.78× the OOF inclusion threshold, so on this proxy it is not
   removable false-positive mass.
2. **Why the proxy may understate the effect (for the record only):** catalogue-proxy truth sits
   100 % on the published catalogue (`evidence/arm_habitat_decomposition.json`); pluton-margin
   dots are far-field and the proxy's catalogue holdouts were already shown to mis-price far-field
   changes by ~100× (T-v2 live refutation, `evidence/live_inversion.json`). A *live* test would be
   the only way to revisit this — and the frozen gate forbids spending a weekly slot on a failed
   screen, so H32-2 stays closed.
3. **Contrast with H32-1 (PASS):** the profitable prune class is the 100 m catalogue-flank shadow
   (0.0040 credit/FP), an order of magnitude weaker than deep-magnetic dots. Future prune arms
   should target classes below ~0.01 credit/FP.

## Implementation nuance disclosed (does not change the verdict)

The preregistration said non-finite R is "treated as maximally shallow (never pruned)". After the
sentinel repair, cells where `tmi_hg` itself is the nodata sentinel get `R = 0` (neutral/deep) and
are therefore *eligible* for pruning rather than protected. Measured impact: only **16 of 44,090**
d=2.8 dots (0.036 %) sit on invalid `tmi_hg` cells, and the gate failed by −0.0038 mean ΔDTI with
0/10 seeds on both variants and in both prune directions, so this nuance cannot alter the FAIL.

## Consequences

- Seeds 190–199 are consumed by this closed arm. The next new arm uses 200–209 (H27-16's
  tentative reservation is superseded accordingly).
- `registry/next_hypotheses.json` is updated: H32-2 moves to the tested/refuted ledger; the new
  H33-series candidates (knowledge/18) take the untried ranking.
- No GeoTIFF was built for H32-2 and none will be.
