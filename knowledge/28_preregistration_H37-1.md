# H37-1 preregistration — Directional (anisotropic) Poisson-disk re-pack

**Status:** preregistration frozen **before any seed in 250–259 is touched**. Per the standing
instruction (knowledge/23 §5): no candidate is built, no submission slot is used, and no
weekly upload is attempted until this gate passes on a fresh decade.

## 1. Hypothesis in one paragraph

The current best submission (`b531dae0a36f`, H36-1 rung-3.0) uses `dot_thin(h19_5, 3.0)` — an
**isotropic** Poisson-disk pack with `min_dist = 3.0 px` (300 m, exactly the DTI kernel radius).
A fault is a 1-D structure embedded in the 2-D grid; the linear DTI kernel saturates along
strike but does *not* across strike. Anisotropic packing — `a_∥ ≥ 2.0 px` along the local
ridge strike and `a_⊥ ≤ 2.0 px` across it — should let the same on-line credit be earned by a
different (and, on bends and tips, larger) set of dots. The H34 isotropic rung ladder is
bounded (`knowledge/22_h34_result.md`); the directional rung space is genuinely larger.

## 2. The variant table (frozen before the run)

| # | Variant | Description |
|---|---|---|
| V0 | `base_oof_d280` | H36-1 reference: `dot_thin(h19_5, 2.8)` |
| V1 | `rung30_unpruned` | `dot_thin(h19_5, 3.0)` — H34 ladder rung |
| V2 | **`dir_3p5_2p0_unpruned`** | anisotropic pack, `(a_∥, a_⊥) = (3.5, 2.0)` |
| V3 | `dir_3p5_2p0_blind_r1` | V2 then H27-4 blind 1-px catalogue-flank prune |
| V4 | `dir_4p0_2p0_unpruned` | anisotropic pack, `(a_∥, a_⊥) = (4.0, 2.0)` — looser along strike |
| V5 | `dir_3p0_2p0_unpruned` | anisotropic pack, `(a_∥, a_⊥) = (3.0, 2.0)` — symmetric 1-D |
| C1 | `control_random_drop_matched_n` | uniform random delete base to V2's exact N |
| C2 | `control_iso_rung30_then_blind_r1` | V1 then H27-4 blind prune (matches V3 except anisotropic) |

The primary candidate is **V3** (`dir_3p5_2p0_blind_r1`); the comparison arms quantify whether
the gain, if any, is layout-specific or generic.

## 3. Frozen gate (must pass all four; otherwise the arm closes)

| # | Criterion | Threshold |
|---|---|---|
| **G1** | Profitability | `mean ΔDTI(V3 vs V0) > 0` AND `seeds_won ≥ 8/10` AND `folds_improved = 4/4` |
| **G2** | Anisotropy matters | `mean ΔDTI(V2) − mean ΔDTI(C1) > +0.0003` (anisotropy beats matched-N random drop) |
| **G3** | Anisotropy beats isotropic at the same N | `mean ΔDTI(V2) − mean ΔDTI(C2) > 0` (anisotropy adds value over isotropic rung-3.0) |
| **G4** | Live break-even | mean `ΔTPw / ΔFPw` (relative to V0) `> tau_live = 0.054852` |

Reading rule, fixed in advance: if **any** criterion fails, the arm closes without confirmation,
retuning, or a candidate GeoTIFF. The DirectionalThinRunner records the per-fold ΔDTI so the
variance can be re-examined on the next fresh decade.

## 4. Seeds, instruments, data — frozen

- **Seeds.** `250–254` (5 seeds × 4 spatial folds = 20 cells, ~3 min CPU; one year of free seed
  decades). `255–259` reserved for H37-2; `260–264` for H37-3.
- **Detector.** `oof_detector.fit_predict_oof_probabilities` with the frozen hyper-parameters
  (`learning_rate=0.1`, `max_iter=100`, `neg_ratio=10`, `seed=2026`) — *identical* to the H36-1
  call, so the candidate is comparable to H36-1 on the *same* OOF probability surface.
- **Strike vector.** `oof_detector.ridge_nms(oof_prob, foot, sigma=1.0)` then
  `oof_detector.ridge_strike_degrees(...)`; the 4-sector strike is ±22.5° accurate, which sets
  the precision floor for the directional gate (a documented limitation).
- **Data.** `data/h19_5_nan.tif`, `data/labels.tif`, `data/sample_submission.tif`,
  `data/prepared/features.npy` — all restored and hash-verified (`evidence/restore_audit.json`).
- **Audit.** Every emitted cell must lie inside the template footprint, equal exactly 1.0
  (binary), be `0` on every catalogue pixel, lie in `[0, 1]` everywhere, and have SHA-256
  recorded in the evidence file.

## 5. Why this is bounded

The repo's analyses (`knowledge/22_h34_result.md`, `knowledge/24_h35_1_result.md`) agree that no
arms in the *addition* family have closed the detection gap to date, and pruning is exhausted.
H37-1 is a *layout* arm — it does not add new bytes, does not add new off-catalogue dots, and
reuses the H36-1 validated instrument. Its ceiling is the H36-1 layout ceiling (already
`+0.0026` on holdout), and its downside is bounded by the matched-`N` random-drop control's
`-0.0017` floor. No weekly slot is used by this arm regardless of outcome.

## 6. Reading discipline

If V3 wins G1 but loses G2 or G3, the gain is generic (any tighter pack), and H37-1 closes
with no candidate TIFF — the rung ladder is already bounded, and a third refinement is not
worth re-running. If V3 wins G1, G2 and G3 but loses G4, the gain is below the *live*
break-even and the arm closes — the repo's threshold discipline requires it. **No retuning
on the same decade; no confirmation until a fresh decade.**