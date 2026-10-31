# S31 · 2026-10-31 UTC — nine-site review, two holdout instruments, and a unique submission TIF

**Decision in one line:** OK TO DOWNLOAD **YES** · OK TO SUBMIT AS A VALID UNIQUE FILE **YES** ·
expected score **MODEL-ESTIMATE 0.197–0.295 (never a score)** · weekly slot = owner's step.
File: `docs/candidates/gemsdoe28-s31-far65-dispfill-20261031-zeros.tif`,
SHA-256 `baf007bd1f360ee3b381584ee67eb15120deb15829f76d8632bfce0b2815e7eb`, 37,654 dots.

Companion artefacts: `docs/s31-executive-summary.html` (the page), `docs/data/s31_summary_table.json`
(machine-readable table), `evidence/s31_prior_placement.json` (E1), `evidence/s31_losfo_refill.json`
(E2), `evidence/s31_candidate_run_card.json` + `evidence/s31_candidate_gate.json` (E3),
`evidence/s31_run_card.json` (session card).

Labels used below: **ORGANIZER-CONFIRMED** (public board page read, dated) · **USER-REPORTED**
(owner pages / session prompt, no receipt) · **MODEL-ESTIMATE** (local arithmetic, never a score)
· **HOLDOUT-DTI** (shared pinned evaluator) · **MEASURED** (computed here from bytes).

## 1. Infrastructure restored this session (all hash-verified)

- `scripts/download_competition_data.sh` → 17 owner-mirrored inputs restored and verified
  (`evidence/restore_audit.json` re-run: PASS); `data/prepared/features.npy` (32 band columns,
  footprint order `flatnonzero`) built by `scripts/prepare_data.py`.
- Shared template restored into `data/shared_template/` with the nine SHA-256 pins from
  `registry/protocol_assets.json` — every pin matched.
- GitHub REST quota for the shared token was exhausted mid-session (HTTP 403, 2026-10-31
  00:54 UTC). Workaround used instead of the REST API: **git protocol** (blob-filtered sparse
  clones of the nine owner repos into `data/site_repos/`) and a new local-only mirror builder
  `scripts/build_registry_from_clones.py` that reproduces `fetch_site_registry.py`'s selection,
  layout and manifest fields (including git blob SHAs via `git hash-object`).
  Result: `data/registry_tifs/manifest.json` with 478 rasters (the S30 audit had 475; the sites
  published 3 more `.tif` files since). The champion's bytes verify: SHA-256
  `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`, blob `17a76895…`,
  219,065 bytes — identical to knowledge/77 F1.
- Calibration lattice `data/s23/lattice.tif` fetched by git at the pinned ref, SHA-256
  `b4570b40…` matched the S28/S29 pin.

## 2. The nine-site table (MEASURED + USER-REPORTED)

Full table with links: `docs/s31-executive-summary.html` §The table and
`docs/data/s31_summary_table.json`. Summary: best claimed of the nine is **GEMSDOE32
`…e5eb6e7e-zeros.tif` = 0.2778 (USER-REPORTED)**; every one of the nine fails the internal
70%/3 px uniqueness rule against at least one other site (max overlaps 0.9998–1.0000;
GEMSDOE25 ≡ GEMSDOE30 identical dot sets, 0.2600 each). None of the nine is a candidate for
download-and-submit; they are reference/education material only.

## 3. Why 0.2778 scored highest, and can we beat it? (PhD-level synthesis, all labels kept)

- **Verified (MEASURED):** the 0.2778 file = GEMSDOE31 H27-4 solo (0.2708) minus 2,545 dots
  within 2 px of the catalogue; nothing added; 37,654 dots; zero on-catalogue dots.
- **Mechanism (metric arithmetic, OFFICIAL metric):** DTI = TPw/(TPw + 0.2·FPw + 0.8·FNw).
  The scored test set is “new faults” not in the USGS catalogue (official text), so a dot on a
  known fault's halo earns no credit for that fault yet pays α=0.2 FP mass; β=0.8 makes each
  missed truth pixel cost 4× a false-positive pixel. Pruning catalogue-flank dots therefore
  reallocates the fixed budget toward cells that can earn credit. The sign is expected; the
  magnitude (+0.0070 USER-REPORTED) is consistent with reallocation, not a new signal.
- **Model closure (MODEL-ESTIMATE, `evidence/live_inversion.json` blind-lattice calibration):**
  with implied hidden truth G = 12,226 px and budget N = 37,654, closure gives
  score = TPw/17,311.5. Champion 0.2778 ⇒ TPw ≈ 4,809 (0.128 credit/dot). Public board #1
  0.4544 (ORGANIZER-CONFIRMED, board read 2026-10-31) ⇒ TPw ≈ 7,867 at the same budget
  (0.209 credit/dot): a ≈3,058-credit-px detection gap. **Beating 0.2778 requires new
  detection signal; beating 0.4544 requires roughly doubling the family's enrichment.**
- **Tested this session:** three genuinely new priors (joint RTP×gravity lineament coherence;
  geodetic shear∧dilatation strain ridges; depth-to-basement step edges) plus the S30 RTP-ridge
  refill prior, on both holdout instruments (below). **All four lose to budget-matched uniform
  dispersion.** So the family's plateau is not addressable by placement priors we can validate
  here; the honest S31 candidate keeps the champion's far-65% dots and replaces only the
  S30 ridge refill (E2: 0.0248 vs 0.0535 uniform) with a dispersed complement.

## 4. Hypotheses ranked before implementation (protocol requirement)

| Rank | ID | Layers (verified band descriptions) | Signature | Why it could catch a catalogue-missing fault | Difference from implemented work | Non-fault mimic | Cost | Data status |
|---|---|---|---|---|---|---|---|---|
| 1 | H-S31-1 JPX | `rtp` (band 2), `iso_grav_anom` (band 13) | geometric mean of percentile ranks of both fields' smoothed gradients — two independent potential fields must agree | a contact visible in magnetics *and* gravity is a real boundary; either field alone is sensor noise | no prior arm used a two-field conjunction of these bands | igneous contacts, basin-edge density contrasts | low | local (restored) |
| 2 | H-S31-2 GSD | `geod_shearrate` (band 7), `geod_dilaterate` (band 8) — GPS/InSAR strain rates per official band descriptions | conjunction of smoothed shear and dilatation ridges | the catalogue is scarp-mapped; creeping buried faults strain the surface without scarps | no prior arm used the geodetic bands | plate-wide smooth strain, aquifer extraction | low | local |
| 3 | H-S31-3 CS | `depth_to_base_surf` (band 15) | gradient magnitude of smoothed depth-to-basement | basin-bounding faults step the basement | S26-TCB used conductivity covariance (negative); this is a step-edge, not covariance | playa edges, lithologic contacts | low | local |
| 4 | H-S31-4 heat-flow × probes | USGS ScienceBase heat-flow zip (DOI 10.5066/P9BZPVUC), GDR 2 m probes | residual heat flow at lineament conjunctions | convectively removed background leaves upflow residuals over hidden upflow faults | not run: ScienceBase/gdr.openei.org unreachable from this sandbox | groundwater discharge | medium | **blocked (network)** — obtainable officially, not here |
| 5 | H-S31-5 drainage neotectonics | USGS 3DEP 1 m DEM tiles (official, free) | channel offsets, knickpoint trains | channels record post-scarp-diffusion deformation | no flow-network arm ever run | lithologic knickpoints | high (GB-scale) | blocked by budget |

Top three were run (protocol: validate the top candidate before any slot). Results: §5.

## 5. Experiments (3 of 3; every number is HOLDOUT-DTI)

**E1 — buffered interleaved hide-and-recover** (`scripts/run_s31_prior_placement.py`, evaluator
`gems-segment-pooled-v1`, 60,988 withheld positives, 15 px buffer, α 0.2, β 0.8, 300 m kernel,
K = 37,654 dots/fold, seed 20261031):

| Arm | HOLDOUT-DTI | 95% CI | Paired Δ vs random-K (folds) |
|---|---|---|---|
| uniform random control | 0.069858 | 0.066737–0.072882 | — |
| rtp_ridge (S30 refill prior) | 0.035388 | 0.027731–0.043316 | −0.034470 (0/4), CI −0.042968–−0.026196 |
| joint_px (H-S31-1) | 0.041607 | 0.034807–0.048742 | −0.028251 (0/4) |
| gsd_strain (H-S31-2) | 0.046069 | 0.038334–0.053998 | −0.023789 (0/4) |
| cs_step (H-S31-3) | 0.032458 | 0.027087–0.038203 | −0.037400 (0/4) |

Leakage canary PASS (max pooled AUC 0.5302 < 0.90). Pre-placement surface Spearman vs registry
density: max 0.2785 < 0.90 (lane gate pass). **Verdict: NEGATIVE for all four priors.**

**E2 — LOSFO far-field** (`scripts/run_s31_losfo_refill.py`, leave-fault-system-out, 600 m
buffer, truth ≥ 8 px from anything the placement could read, seeds 210–212, K = 9,414 dots/fold
in the ≥6 px habitat — the exact habitat a shipped file occupies):

| Arm | Mean HOLDOUT-DTI (3 seeds) | Δ vs uniform |
|---|---|---|
| uniform control | 0.053522 | — |
| gsd_strain | 0.030707 | −0.022816 (0/3) |
| joint_px | 0.029203 | −0.024319 (0/3) |
| cs_step | 0.025693 | −0.027830 (0/3) |
| rtp_ridge (S30 refill prior) | 0.024834 | −0.028688 (0/3) |

**Verdict: NEGATIVE for all priors; uniform dispersion wins where the refill lives.** Known
limit: LOSFO truth is still mapped fault (upper bound for unmapped truth).

**E3 — candidate build + independent gate** (`scripts/build_s31_unique_candidate.py` →
`scripts/s31_candidate_gate.py`, different algorithm): PASS/PASS (§1 file). Max overlap 0.67998
≤ 0.70 against 475 comparable registry rasters (0 over gate), overlap vs the 0.2778 parent
0.66877, vs the S30 candidate 0.67998 (independently recomputed from bytes in a third pass).
Validator: float32, single band, EPSG:32611, 3730×3292, values {0,1} inside, zeros finite
outside, no NaN/inf anywhere → the portal range error cannot occur.

## 6. Score estimation (labels)

No calibrated leaderboard estimate exists for a new file. The table's per-site numbers are
USER-REPORTED. The S31 candidate carries MODEL-ESTIMATE 0.197–0.295 from the blind-lattice
closure (retention r ∈ [0.65, 1] of the champion's TP + blind credit 0.0222/dot for the
13,179 complement dots). The upper end only reproduces the champion if the removed 35% carried
zero credit — unknown. **A projection is never a score.**

## 7. Leaderboard and irregularities (ORGANIZER-CONFIRMED, read this session 2026-10-31)

Public board: #1 0.4544 · #2 0.3925 · … · #50 (last) **0.3195** (team kpomazi, 36 submissions).
- FLAGGED: the prompt's “0.3195 is the highest score right now” is inconsistent with the board
  (0.3195 is rank 50). Prior sessions that reported “0.3195 not in ranks 1–47” were correct and
  the number does exist — on the last row.
- FLAGGED: “0.4413” does not appear anywhere on the board (sorted descending it would sit
  between 0.4544 and 0.3925).
- FLAGGED: the portal error “Predicted values must be in range [0, 1]” is still not matched to
  any specific file; all nine site-best files pass the local [0,1] check; one registry raster
  (`gemsdoe31-csdu-stepover-8cf9dc27-nan.tif`) has NaN *inside* the footprint — the leading
  suspect. S31 ships zeros-outside all-finite files only.
- FLAGGED: GitHub REST rate limit for the shared account hit HTTP 403 at 2026-10-31 00:54 UTC
  (affects any session still using `gh api` heavily).
- Open owner decision carried from S30: does the internal 70%/3 px rule include the GEMSDOE13
  calibration lattice (a geology-blind control that is not a submission)? This session follows
  the merged S30 convention: registry = the nine owner sites.

## 8. What still blocks a top-prize run

1. **No receipt-based calibration.** Every score this repo holds is USER-REPORTED; one
   organizer receipt from a submitted file would replace the MODEL-ESTIMATE range with a
   measured anchor. Requires the owner to submit and report the receipt.
2. **The 0.4544 detection gap.** Modeled as ≈3,058 credit px — only a new physical signal
   closes it. Highest-priority untested signal (heat-flow × probe conjunction, H-S31-4) is
   blocked by sandbox network policy; restore the ScienceBase zip (DOI 10.5066/P9BZPVUC) on a
   connected machine into `data/` with SHA-256 pin `e7fd62c6963ab390…` per
   `registry/external_pins.json` to unlock it.
3. **Honest-holdout problem.** Both instruments here measure mapped-fault proxies; none
   measures “unmapped-fault” skill. A transfer calibration needs several receipts, or the
   organizer's documented private-round methodology.
