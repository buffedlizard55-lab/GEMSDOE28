# S30 · 2026-10-30 · nine-site review, the 0.2778 mechanism, and a valid unique candidate

**Status in one line:** a valid, unique GeoTIFF was built and independently re-checked. It is **OK to download** and **OK to submit as a valid unique file**. **No score is claimed or estimated.** It is not verified to beat 0.2778, and it shares about two-thirds of its dots with the family it came from.

Companion files: `docs/s30-executive-summary.html` (the page), `evidence/s30_registry_audit.json`, `evidence/s30_candidate_run_card.json`, `evidence/s30_candidate_gate.json`, `evidence/s30_summary_table.json`.

## 1. Scope, sources and labels

- Official sources (fetched 2026-10-30): [problem description, metric, formats](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). Both were read in full. The leaderboard was read through rank 23.
- Owner-published files: 475 GeoTIFFs under `docs/` in the nine repositories (GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36), fetched via the GitHub API into `data/registry_tifs/` (git-ignored) by `scripts/fetch_site_registry.py`. Each is hash-pinned (SHA-256 in `data/registry_tifs/manifest.json`). They are **not** organizer receipts.
- Labels: every score is **USER-REPORTED** (session prompt). No number here is ORGANIZER-CONFIRMED. No holdout DTI is reported for the candidate (see §5).
- Restored inputs: `scripts/restore_data.py` and `scripts/verify_restored_inputs.py` pass locally (grid 3730×3292, EPSG:32611, 100 m, footprint 5,167,373 px). Owner mirror, not organizer-authenticated.

## 2. Verified facts (line by line, reproducible)

| # | Claim | Evidence | Result |
|---|---|---|---|
| F1 | The 0.2778 file is `gemsdoe32-h33-h33-2-b2-…-zeros.tif` | GEMSDOE32 `docs/downloads/` blob `17a76895…` (219,065 bytes), SHA-256 `c55bafc4…` | Found; 37,654 dots, zeros outside |
| F2 | It is a subset of GEMSDOE31 H27-4 solo-d28 (user-reported 0.2708) | Set arithmetic on dot masks | 0 dots added; 2,545 of 40,199 removed |
| F3 | Every removed dot is catalogue-adjacent | Euclidean distance to `labels.tif` catalogue | median 2.0 px, max 2.0 px |
| F4 | No dot of any named file lies on a catalogue pixel | Same | 0 for all nine named files and the candidate |
| F5 | The file is binary inside the footprint | `dot_mask` on every named file | values exactly 0/1 |
| F6 | Official metric = repo metric | Problem page formulas: TPw, FPw (sum over p>0), FNw, DTI with α=0.2, β=0.8, R=3 px | Matches `src/gems27/metric.py` |
| F7 | Official text says outside-bounds values are "null or nan" | Problem page, "Submission format" | Zeros-outside is not the literal wording; zeros are inside the raster bounds and in [0,1] |
| F8 | Official text does **not** mention masking known catalogue pixels | Problem page | The repo's masking assumption is unverified |
| F9 | Two scoring rounds; the Final Round rescoring rewards expert-verified new faults | Problem page, "Competition structure" | Uniqueness is relevant to the prize |
| F10 | 0.4413 cannot appear on the board: the board is sorted by score, #1 0.4544, #2 0.3925 | Public leaderboard, read 2026-10-30 | Flag: the prompt's 0.4413 is not on it |
| F11 | Uniqueness gate fails for all nine named files | Audit: each file has 100% of dots within 3 px of at least one other registry raster; 100–102 of 472 comparable rasters exceed 70% | None of the nine passes |
| F12 | Registry format census | 223 NaN-outside, 246 zeros-outside, 5 mixed, 1 off-grid test file (`GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif`, 32×48) | Audit JSON |
| F13 | One registry raster has NaN **inside** the footprint | `gemsdoe31-csdu-stepover-8cf9dc27-nan.tif` | A candidate cause to test for a range error; not confirmed |

## 3. Why GEMSDOE32 scored 0.2778 (explanation, labelled)

- **What changed relative to its parent.** The 0.2778 file is the 0.2708 field with 2,545 catalogue-adjacent dots removed (F1–F3). Nothing else changed.
- **Mechanism (inference, consistent with the metric).** Under the official DTI, a predicted dot costs α·(1−k(d)) if it lies more than 3 px from a new-fault truth pixel. A dot 1–2 px from a *known* fault is more likely to sit on the known fault's halo than on a new fault. Removing it cuts false-positive mass at weight α=0.2 and costs little recall, because β=0.8 weights missed truth more heavily and few truth pixels lie within 2 px of the catalogue. The sign is therefore expected. The magnitude (+0.0070 user-reported) cannot be computed without the hidden truth.
- **Named non-fault mimic.** Catalogue-halo alignment: predictions that follow the mapped trace's buffer will be scored as hits or misses depending on the offset between the mapped and true fault, not on fault presence. The 300 m kernel tolerates offsets of up to about 3 px. This is the same artefact the official text attributes to rasterisation and misalignment.
- **Why the family plateaus at about 0.27.** The nine named scores span 0.2449–0.2778, and all come from fields of 37k–61k dots built on the same H27-4/H19-5 lineage. Pruning shifts the score by a few thousandths; a new field is needed for a larger change.
- **Repo-internal contradiction, flagged.** `registry/external_pins.json` labels the H33-2 hypothesis "multi-depth MT conductance alignment" and pins USGS ScienceBase MT and heat-flow files. The 0.2778 artefact uses none of them. The label is misleading and should be corrected in the next registry revision.

## 4. The S30 candidate (what was built and why)

File: `docs/candidates/gemsdoe28-s30-catfar65-budgetfill-20261030-zeros.tif`. Current SHA-256 is recorded in `evidence/s30_candidate_run_card.json` and the gate file; that record is the authority. The file is reproducible from `scripts/build_s30_unique_candidate.py` only if the inputs match the pinned hashes.

Construction (fully specified in `scripts/build_s30_unique_candidate.py`):
1. Start from the 0.2778 dots.
2. Keep the 65% farthest from the catalogue (kept dots lie at or beyond 12.04 px). Remove the nearest 35% (median 6.0 px, max 12.04 px).
3. Refill 13,179 new dots at ≥6 px from the catalogue and not on any removed or kept cell. Rank candidates by a reduced-to-pole magnetic ridge prior (gradient magnitude of band 2 `rtp`, σ = 1.5 px); place greedily with 4 px spacing (new dots median 28.8 px from the catalogue).
4. **Per-raster uniqueness budget.** For each of the 472 comparable registry rasters, the running count of dots within 3 px is capped at 68% of 37,654. The cap is enforced during placement (39,224 candidates skipped by the budget), not only checked after.
5. Write float32, single band, zeros outside, via the shared writer `src/gems27/submission.py`. The writer re-reads the file.

Why this rule: the 70% gate is per raster, and 474 registry rasters cover 99.7% of the footprint within 3 px. A "far from every registry dot" rule leaves only 3,182 cells, so the budget is the only workable uniqueness rule. Test: `tests/test_uniqueness.py` (8 tests).

Result: max overlap 0.6800 with GEMSDOE24 mirror `gems24-h24-0-mirror-h19-5-group-best-…-allfinite.tif`. Zero rasters over 70%. Overlap with the parent 0.6717. Overlap with each named file 0.67–0.68.

**Honest reading.** This passes the gate at a 2-point margin. Two-thirds of its dots are the 0.2778 file's dots. The 35% replacement is a bet on the magnetic-ridge prior. Its effect on score is unknown and could be negative, because the removed band may include true adjacent faults (the official text explicitly notes misalignment).

## 5. Validation status (no holdout claim)

- **Holdout DTI: not computed, and not applicable.** The candidate uses the registry field for its uniqueness budget, which the repo's hide-and-recover holdout does not model. The holdout's truth is catalogue-internal, so it would also penalise near-catalogue predictions the wrong way. The repo's S28/S29 history already shows holdout gains that failed to transfer. A "beat the holdout best" promotion gate therefore cannot be met for this file. Its verdict is set accordingly.
- **Leakage canary:** not applicable (no model is trained).
- **Surface check (before placement):** Spearman between the ridge prior and the registry density map = 0.315 (gate 0.90). Pass.
- **Binary rank correlation:** tied ranks for dot rasters, so the 0.90 rank gate is structurally uninformative here and reported as not applicable. The 70% overlap gate is the operative test.
- **Independent gate:** `scripts/s30_candidate_gate.py` re-reads the bytes, recomputes every overlap with a nearest-neighbour KD-tree (not the builder's distance transform), and agrees to four decimals. All hard checks pass (grid, CRS, transform, bounds, float32, single band, zeros outside, values in [0,1], no NaN or inf, zero catalogue dots).

## 6. Hypotheses (ranked; required by the protocol before implementation)

Ranking is by expected DTI improvement and cost, given what is verified. Expected improvement is qualitative because no holdout exists for any of them.

1. **H-S30-A (implemented, §4): catalogue-distance retention with budgeted field-complement refill.** Layers: GEMSDOE32 dots, `labels.tif` catalogue, training-feature band `rtp`. Signature: dots are kept by distance to the catalogue, and new dots follow reduced-to-pole ridges. Why it could catch a catalogue-missing fault: new dots sit in cells the registry field does not cover. Difference from the repo: the uniqueness budget is new. Cost: low (done). Verdict: valid and unique; score unknown.
2. **H-S30-B: pruning radius sweep on the solo field (3, 5, 7 px).** Extends F3. Layers: GEMSDOE31 solo dots and the catalogue. Cost: low, but it is a slot experiment. The holdout cannot adjudicate it (§5). Not a unique file on its own, because any pure subset of a registry raster is a duplicate.
3. **H-S30-C: MT conductance surfaces (ScienceBase, DOI 10.5066/P9TWT2LU).** Layers: `gb_conductance_surface_tp.tif` (pinned SHA-256 `8cc1a224…`) and `gb_conductance_middle_crust_tp.tif` (pinned `e8cfd731…`), both listed in `registry/external_pins.json`. Signature: conductive pathways along faults. Why it could catch a missing fault: conductance is independent of the magnetic catalogue. Cost: medium. Obtainability: the USGS item is public, but this sandbox cannot reach sciencebase.gov, and the pinned bytes are not restored locally. **Not yet viable without the official bytes.**
4. **H-S30-D: heat-flow residual plus probe conjunction (ScienceBase, DOI 10.5066/P9BZPVUC).** Layers: `heat_flow_maps_and_supporting_data_for_the_Great_Basin_USA.zip` (pinned SHA-256 `e7fd62c6…`, not restored here). A derived in-footprint heat-flow vector table already exists at `docs/data/sb_heat_flow_in_footprint.csv` (4,217 data rows). Earlier sessions recorded heat-flow hypotheses (`knowledge/18_new_hypotheses_H33_series_2026-10-03.md`, `knowledge/37_ranked_hypotheses_session14_2026-10-03.md`). **This session did not re-check their outcomes.** Cost: medium. Status: partly available; a re-test must reuse the recorded results rather than repeat them.
5. **H-S30-E: anti-consensus placement (field-complement only, no retained dots).** A pure complement file would be unique, but the field covers 99.7% of the footprint, so almost no complement exists under a strict rule. Implausible as stated; rejected.

Implementation order recommended: B (cheap, local), then C only after the official bytes are restored and the pinned hash matches. D should start from the recorded earlier results, not from scratch.

## 7. Limitations and access still needed

- **No submission receipt.** The organizer's score for any file is unknown to this repository. Obtaining it requires the user to submit and report the receipt. The agent does not automate DrivenData login.
- **No holdout that matches the leaderboard.** Holdout DTI ~0.05 versus leaderboard ~0.27 shows the proxy does not transfer. A better proxy needs organizer labels or a documented private-round calibration.
- **Catalogue masking is unverified** (F8). Resolving it changes the value of every pruning rule.
- **Sandbox network.** Only github.com, api.github.com, codeload, npm and pypi are reachable. ScienceBase is blocked, so layers C and D cannot be restored here.
- **Weekly cap unknown.** The submission page's weekly allowance is not visible to the agent.
- **Single-candidate uniqueness.** The gate is applied to 472 registry rasters only. Files the owner has not published, and other teams' files, are not covered.

## 8. Run card

See `evidence/s30_candidate_run_card.json` and the JSON card at the end of the README S30 block.
