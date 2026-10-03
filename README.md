# GEMSDOE28 — auditable GEMS research and manual submission workflow

> **Standing starting point.** Before any substantive code, data, model, candidate or review decision, reread this README from top to bottom—especially the full standing brief below. Keep **“Maximize P(Win)”** and **“Own the Outcome”** central. The repository is a research workflow, not an automated submission bot.

**Current state (2026-10-03):** nine hash-pinned owner-mirror inputs are restored to the ignored `data/` directory and locally verified; `scripts/prepare_data.py --force` reproduced the pinned 5,167,373 × 32 feature matrix. The exact predecessor range-error TIFFs were independently re-audited: internal NaNs are a plausible local cause, but the portal root cause is not confirmed. H31-1 protocol revision 2, which corrects the unverified magnetic-unit wording, is committed on this branch at `524bf27` before any classifier fit or holdout. Earlier protocol commit hashes recorded by prior working-copy artifacts are absent from the current Git history and are not treated as verified commits. Git does **not** establish that the earlier label-free Euler build was committed before it ran; this chronology and the checkout-history irregularity are recorded in [`evidence/h31_1_prereg_history_audit.json`](evidence/h31_1_prereg_history_audit.json). The runner requires working protocol bytes to match the committed Git blob exactly. The current label-free Euler feature cache has been rebuilt against revision 2 and the current implementation; the formal local seed audit passes on 34 evidence JSON files, with screen/confirmation ranges still unused. **No H31 classifier fit, holdout score, confirmation, or submission TIFF exists.** The public board snapshot is one-off and does not link either `0.2477` or `0.3195` to this owner or a local raster. No weekly slot has been used by this agent, and the requested PR/merge remains to be completed.

## Quick links

- [One-click manual research TIFF](docs/downloads/gems27-h28-1-edge-coherence-plus-t-v2-h27-4-20261002-1113fba5f6cb-nan.tif) — H28-1 catalogue-holdout reference, **UNSCORED and not slot-approved**. See the short note and exact-file audit in [`docs/downloads/`](docs/downloads/).
- [Submission executive summary and manual checklist](docs/executive-summary.html)
- [Static, source-linked project site](docs/index.html)
- [Current 5-item hypothesis ranking](knowledge/13_current_ranked_hypotheses_2026-10-03.md)
- [Frozen H31-1 Euler preregistration](knowledge/12_preregistration_H31-1_euler.md)
- [Euler input conventions](evidence/euler_input_audit.json), [current label-free Euler feature/depth audit](evidence/h31_1_euler_feature_audit.json), [preserved revision-1 feature audit](evidence/h31_1_euler_feature_audit_revision1.json), [preserved initial feature audit](evidence/h31_1_euler_feature_audit_initial.json), [preregistration chronology audit](evidence/h31_1_prereg_history_audit.json), and [seed-reuse audit](evidence/h31_1_seed_reuse_audit.json)
- [Exact historical range-validator file forensics](evidence/range_validator_forensics_2026-10-03.json)
- [Current leaderboard observation and claim limits](registry/leaderboard_snapshot_2026-10-03.json)
- [Restored input audit](evidence/restore_audit.json) and [hash manifest](registry/data_manifest.json)
- [Full standing brief as a separate reference](knowledge/00_standing_brief.md)

## Values and decision rule

- **Maximize P(Win):** spend time, data and any future submission slots only where a frozen, fair comparison can materially raise win probability. A pleasing catalogue-proxy result is not enough if the proxy cannot see the competition's new far-field labels.
- **Own the Outcome:** keep byte-level provenance, failure records, limitations, exact code/input hashes, manual instructions and post-build checks with each deliverable. Do not substitute a guessed cause, an owner claim or a leaderboard row for an organizer receipt.
- **No slot without evidence:** no hypothesis earns a weekly submission slot until it beats the best comparable same-run spatial holdout, then passes a fresh confirmation with frozen code/parameters and an independent exact-file audit. A proxy pass remains proxy evidence.
- **Human control only:** this repository never logs into, downloads from, uploads to, scrapes, polls or monitors DrivenData. Manual-review URLs are provided; no credentials or owner input are requested from the agent.

## What is verified now

### Data and preparation

- `registry/data_manifest.json` pins nine owner-mirror inputs by size and SHA-256. Every object is restored under `data/` (git-ignored); local hash, grid, band-order and prepared-matrix checks pass in `evidence/restore_audit.json`.
- Provenance is limited: these are public GitHub mirrors supplied by the repository owner, **not organizer-authenticated competition downloads**. A hash match proves equality to the registered mirror, not organizer byte identity, original downloadability, complete coverage, schema, or licence.
- The 100 m grid is EPSG:32611, 3730 × 3292, with transform `[100,0,243350,0,-100,4508550]`; the sample-mirror footprint has 5,167,373 cells. `scripts/prepare_data.py --force` exited 0 on 2026-10-03 and produced `data/prepared/features.npy`, shape `(5167373,32)`, float32, SHA-256 `83ed2704ee2de03cf8b1c8f2966fcf71813501df97c1c35400e6c0415393f6dc`.
- `scripts/download_competition_data.sh` restores only hash-pinned public owner mirrors, rebuilds the feature matrix, and calls `scripts/verify_restored_inputs.py`. It never contacts DrivenData.

### Scores, provenance and the public board

- `0.2477` is an owner-reported score attached in prior repository records to a local d=1.5 TIFF; no organizer receipt or authoritative owner/file association is available here. Treat it as **unverified**.
- A one-off manual read of the official public leaderboard on 2026-10-03 observed **DARD, rank 1, 0.3195** and **wbg1, rank 15, 0.2600**. This proves those public rows were shown at that observation; it does **not** prove that DARD or wbg1 is this repository's owner, nor does it link either row to any local TIFF. No GEMSDOE28 candidate has an organizer score. See [`registry/leaderboard_snapshot_2026-10-03.json`](registry/leaderboard_snapshot_2026-10-03.json) and the [manual-review page](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- Existing H28-1 holdout evidence reports a +0.00294884 paired DTI improvement on seeds 140–149 relative to its preregistered base. That is catalogue-internal, spatially blocked hide-and-recover evidence—not a public/private competition score and not proof of transfer to expert-created labels.

### H31-1 Euler status — feature audit is not a holdout result

- The current H31-1 protocol is [`knowledge/12_preregistration_H31-1_euler.md`](knowledge/12_preregistration_H31-1_euler.md), revision 2, committed at `524bf27` before any classifier fit or holdout. Earlier working-copy artifacts cite commits `d700cfe` and `9eef66b`, but neither object is present in this checkout's Git history; they are not treated as verified commits. The preserved initial feature audit matches earlier protocol bytes, but this checkout cannot prove those bytes were committed before that label-free solve; that claim is withdrawn. See [`evidence/h31_1_prereg_history_audit.json`](evidence/h31_1_prereg_history_audit.json). The runner rejects Euler solves/fits unless working protocol bytes exactly match the last committed Git blob. Screen seeds are frozen at 160–169; 170–179 are confirmation only if the screen passes. The paired control is the current H28-1 + T-v2 + H27-4 r1 OOF recipe.
- The only magnetic source is owner-mirror band 14 `tmi`; its unit tags are absent and no physical field-unit calibration is claimed. The supplied `tmi_vg`/`tmi_hg` scales are not treated as calibrated. All Euler derivatives are derived from one field; a constant unit conversion cancels from the source/depth solution but does not authenticate physical units. Centered horizontal differences are marked unavailable beside nodata, and nearest-valid fill is used only as FFT context. The current label-free build logged 80.265% vertical-derivative coverage, 5,149,759 valid horizontal-derivative cells, 118,089 accepted SI-0 source solutions and 6,309 aligned/depth-coherent SI-0 clusters. Its three-column feature matrix is shape `(5167373,3)`, float32, SHA-256 `57efbcf2ad32a537c24acd15f6c54fa33fff67979f302cd34f0d5a845caf107c`; the matrix is a local ignored cache, not a submission. SI-1/SI-2 centroid stability remains weak (41.0%/30.2% within 600 m); these are label-free model outputs, not geological validation or holdout results. See the current feature audit.
- USGS GeoDAWN metadata describes magnetic line spacing of 200 m in Area 1 and 400 m in Area 2, with variable terrain clearance. The mirror's 100 m raster cell is not independent 100 m survey detail. SI=0 approximates an effectively infinite-depth contact; real faults can be finite, dipping or complex, and may need higher structural index. Euler does not estimate dip. Magnetic lineament ridges are used only to align Euler-derived solutions; they are not source locations.
- **No H31 classifier was fitted and no H31 holdout was run as of this README.** The formal recursive local seed audit passes: 34 evidence JSON files hashed/scanned, previous local holdout seeds 100–159, reserved ranges 160–169 and 170–179 unused. See [`evidence/h31_1_seed_reuse_audit.json`](evidence/h31_1_seed_reuse_audit.json). This cannot rule out undocumented use in external/sibling workspaces. Before the screen, finish and record implementation/source review, bug/leakage review, and full acceptance review; refresh the seed ledger immediately before fitting. The runner writes an atomic single-use seed claim before fitting; a crashed/interrupted run consumes that range and must not be rerun. A failure stops the arm. A screen pass earns one unchanged confirmation on seeds 170–179 after refreshing the seed audit; neither result alone establishes organizer-label performance.

### Historical range-validator error: best local explanation, not portal proof

The exact predecessor GEMSDOE25 NaN and all-finite TIFFs were retrieved from their pinned commit and SHA-256 verified. Against the current hash-pinned owner-mirror template, the old NaN file contains **2,344,929 NaNs inside** the footprint; its finite interior values are within `[0,1]`. Ordinary range/all-finite checks reject NaN, so internal NaNs are a strong local explanation for the earlier error. The all-finite predecessor file passes a whole-array numeric range check but contains **625,805 positive pixels outside** the footprint and is not a valid replacement. The organizer validator and exact earlier response payload are unavailable, so its root cause is still **unconfirmed**. Full byte/count evidence: [`evidence/range_validator_forensics_2026-10-03.json`](evidence/range_validator_forensics_2026-10-03.json).

## Manual submission path and artifact status

The Pages front page makes the single-band GeoTIFF the most prominent action and displays its unique content-addressed filename, short note, SHA-256, file-format report, holdout scope, and **UNSCORED** status. The current primary research reference is the H28-1 artefact linked above; it is **not** authorized for a weekly slot by this README. A separate zero-outside all-finite file is only a manual-review fallback; it is not assumed portal-compatible. See `docs/downloads/manifest.json` and run `python scripts/verify_downloads.py` for the exact local format/grid/range/footprint/ZIP/note audit. Do not upload automatically or claim that local checks guarantee portal acceptance.

A human choosing to submit must manually review the official competition page and rules, select the exact candidate file, add its registered short note, manually upload it through the organizer's portal, and preserve the exact returned file/receipt/score. The agent will not perform those actions.

## Ranked research and frozen protocol

- The current five-hypothesis inventory is [`knowledge/13_current_ranked_hypotheses_2026-10-03.md`](knowledge/13_current_ranked_hypotheses_2026-10-03.md), mirrored in `registry/next_hypotheses.json`. It covers layers, signatures, missing-catalogue rationale, differences from previous work, uncertain DTI planning ranges, costs, confounders, and data/access gates.
- The exact SI/window/offset/uncertainty filters, source-coordinate clustering, fold/draw/model/response, paired control, screen/confirmation seed ranges, and promotion gates for Euler are frozen in [`knowledge/12_preregistration_H31-1_euler.md`](knowledge/12_preregistration_H31-1_euler.md). No threshold is to be tuned on a holdout seed.
- Official/primary review links appear in the protocol and [`registry/sources.json`](registry/sources.json). A catalog listing does not establish that a binary can be downloaded, has the assumed schema or coverage, or is licensed for the intended use. Access failures remain “unknown” unless proven otherwise.

## Development and audit commands

```bash
# Restore only the pinned public owner mirrors; no DrivenData contact
GEMS_DATA_DIR="$PWD/data" python scripts/restore_data.py --group all --data-dir "$PWD/data"
GEMS_DATA_DIR="$PWD/data" python scripts/prepare_data.py --force
GEMS_DATA_DIR="$PWD/data" python scripts/verify_restored_inputs.py --data-dir "$PWD/data" --manifest "$PWD/registry/data_manifest.json"

# Run unit tests; raster-dependent tests need the restored local inputs
pytest -q
ruff check .

# Label-free Euler transform only; this does not fit the holdout classifier
python scripts/run_euler_cluster_holdout.py --features-only

# Formal local seed audit after feature build and immediately before each eligible stage
python scripts/audit_euler_seed_reuse.py

# Only after implementation/source, bug/leakage, and full acceptance reviews, run screen once
python scripts/run_euler_cluster_holdout.py --seeds 160-169
# If screen passes, refresh the seed audit (which now records the consumed screen seeds)
python scripts/audit_euler_seed_reuse.py
# Confirmation is gated inside the script and allowed only after an unchanged screen pass
python scripts/run_euler_cluster_holdout.py --seeds 170-179 --confirm

# Audit all current manual downloads against the local template and manifests
python scripts/verify_downloads.py
```

## Full standing brief (preserved in this README; reread before every substantive change)

Continue GEMSDOE28 toward an auditable GEMS submission workflow. Preserve the complete user brief in the repository README and make rereading it a standing starting point. Keep **“Maximize P(Win)”** and **“Own the Outcome”** central. Treat reported **0.2477** and **0.3195** figures as unverified claims unless organizer evidence supports the specific claim; a public leaderboard row alone does not link that score to the owner or a local TIFF. Do not automate DrivenData access or monitoring.

Review prior repository history, code, and evidence before proposing work. Rank **3–5 genuinely untried geological hypotheses**, describing layers, physical signature, why each could find faults missing from the catalogue, differences from prior work, uncertain expected DTI planning ranges, cost, and data/access status. The specific Euler interest is **depth-labeled magnetic-source solutions and clusters**, not treating gradient peaks as source locations: test whether magnetic Euler solutions and shallow clusters align with candidate lineaments, with explicit structural-index and geological limitations. Verify scientific and data-source claims from primary/official sources; a listing alone does not establish downloadability, schema, coverage, or licence.

Preregister design, folds/draws, model, response, analysis, and promotion gate before fitting. Compare on a spatially blocked hide-and-recover holdout with the best comparable same-run control; distinguish proxy evidence from competition performance. No idea gets a weekly submission slot without reproducible holdout superiority, confirmation, and exact-file audit.

Build a manual-only submission path, source-linked Pages site, concise executive summary/instructions, prominent single-band GeoTIFF download, unique content-addressed filename, and short note/comment. Verify the competition grid and `[0,1]` constraints; investigate the prior range-validator error rather than assuming its cause. Run implementation/source review, bug/leakage review, then full acceptance review; record passes. The requested PR and merge to `main` have **not** yet occurred.

### Standing user constraints

- Work autonomously; do not ask the owner for manual inputs or credentials. Verify line-by-line using official/trusted sources and provide manual-review links. Do not hallucinate; flag irregularities.
- Read the full brief and preserve it in README; reread it as the standing project objective.
- Keep the Arena AI Core Values **“Maximize P(Win)”** and **“Own the Outcome”** central.
- Prioritize a competition submission TIFF and make a one-click download obvious; include a submission executive summary and a unique note/comment.
- Do not spend a weekly submission slot on an idea that has not beaten the current comparable spatially blocked holdout best.
- Run multiple implementation/review passes and verify against the original requirements.
- Do not present proxy or owner-reported metrics as organizer-verified results or a leaderboard win.
- Euler research must target depth-labeled magnetic-source solutions/clusters, not use edge or gradient peaks as source locations; state structural-index caveats.
- Keep large restored datasets/caches out of Git; use hash-pinned provenance and label owner mirrors as unauthenticated.
- User requested a PR and merge onto `main`; neither has occurred. This session remains on its fixed Arena branch until the work is ready for a PR.
