# H32-1 structural-step coherence — frozen screen result (2026-10-03)

**Status: FROZEN SCREEN FAILURE. Arm closed. No confirmation, no candidate TIFF, no weekly slot.**
Seeds 170–179 were reassigned from the H31-1 confirmation decade to this single preregistered H32-1
screen *before the run*, and are now consumed by it.

## What was tested

Six deterministic, label-free derivative features of the conductivity / conductive-base / strain
group that existing arms used only as scalar values (`src/gems27/structural_step.py`):

| Feature | Transform |
|---|---|
| `struct_depth_grad_300m`, `struct_depth_grad_1000m` | robust-scaled \|∇ depth_to_base_surf\| at 3 px and 10 px Gaussian smoothing |
| `struct_depth_lapneg_1000m` | negative-smoothed Laplacian curvature of `depth_to_base_surf` |
| `struct_cond_depth_concordance_1000m` | both-strong concordance of `cond_surf` and `depth_to_base_surf` derivative magnitudes |
| `struct_cond_depth_orientation_1000m` | \|cos\| orientation agreement between the two gradient fields |
| `struct_strain_step_1000m` | step magnitude of `geod_2ndinv` |

Control arm: the frozen H28-1 six multiscale potential-field edge features, T-v2 graph additions and
the H27-4 r1 flank-shadow prune (38 columns). Candidate arm: identical control plus the six
structural columns (44 columns). Same folds (`make_quadrant_folds`), same model seed 2026, same
T-v2 + r1 recipe in both arms; the runner refuses to run unless the working protocol bytes equal the
committed Git blob.

## Result (`evidence/h32_1_structural_step_holdout.json`)

- 10 preregistered seeds (170–179), 4 spatially blocked folds, 40 paired cells, 350 s wall time.
- Mean candidate-minus-control catalogue-proxy ΔDTI: **−0.001570** (control mean 0.106775 with
  16,390.28 emitted dots and 609.92 credited TP; candidate mean 0.105206 with 16,243.85 dots and
  597.08 TP).
- Folds: NW **+0.00291**, NE_LidarGapHeavy **−0.01352**, SW **+0.00045**, SE **+0.00388** → 3/4.
- Seeds: 3/10 positive (175 largest at +0.0042; 172 worst at −0.0067).
- Gate: mean-gain ≥ +0.0010 **FAIL**, ≥3/4 folds **PASS**, ≥8/10 seeds **FAIL**,
  10/10 preregistered seeds **PASS**, data checks **PASS** → overall **FAIL**.
- Data checks passed: footprint 5,167,373 cells and 60,988 known-fault cells as pinned; structural
  feature cache valid in 5,164,312 cells (99.94 %); all control/candidate probabilities and all six
  structural values finite and inside [0, 1]; source band descriptions `depth_to_base_surf` (15),
  `cond_surf` (17), `geod_2ndinv` (4) match the prepared schema.

The candidate cache is pinned by SHA-256
`4b245b2ce4989d6312871ee378d423a16041ee026749a708f5aef09824b1cf0a`
(`/tmp/gems-data/prepared/h32_1_structural_step_features.npy`, session-scoped, rebuildable with
`scripts/run_h32_1_structural_step_holdout.py`); the control cache is pinned by
`04c5fb77f07dacf35e508ba8668848b4c593840b840a89175ef87644a68b12a2`.

## Reading

The near-null negative result is consistent with the group being an *edge/geometry* group in a
detector that already carries multiscale magnetic and gravity edges plus T-v2 graph additions: the
structural-step columns changed which pixels the detector emitted (dots 16,390 → 16,244) without
improving the credited subset (TP 609.9 → 597.1). The NE_LidarGapHeavy fold, the fold with the
least independent coverage, carried the loss. Per the preregistration this single run closes the
arm: no retuning on 170–179, no confirmation decade, no rerun with altered parameters.

## Effect on the seed ledger

`evidence/h31_1_seed_reuse_audit.json` (updated) now tracks two preregistered decades:
160–169 CONSUMED by the failed H31-1 screen, and 170–179 CONSUMED by this H32-1 screen. The former
H31-1 confirmation decade no longer exists as an unused range. **The next new hypothesis must
preregister a fresh decade (180–189).** The audit cannot rule out undocumented seed use in
unsearched external or sibling workspaces; that scope limit is unchanged.
