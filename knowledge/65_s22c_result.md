# S22C result — first fresh lane to pass its frozen holdout gate vs the dotted baseline (2026-10-26)

Session `G28-S22C-20261026` (labelled S22 on its branch; renamed at merge, see §8), branch `arena/f2afeb88-gemsdoe28`. Preregistration (frozen before any
canary/DTI): [`knowledge/64`](64_s22c_preregistration.md). Budget used: **3/3 experiments**.
Every number below is labelled **HOLDOUT-DTI** (local hide-and-recover), **USER-REPORTED**
(owner prompt/sites; no organizer receipt exists in this repository), **ORGANIZER-PUBLIC**
(official DrivenData page fetched 2026-10-26), or **MODEL PROJECTION** (never a score).

## 0. Executive decision

**DOWNLOAD: YES. SUBMIT: SELECTOR DECISION REQUIRED — this session spent no slot.**

One new unique GeoTIFF was generated and it is the first fresh-detector file in this repository
to **pass every frozen scientific gate** (leakage canary, pooled holdout superiority over the
dotted H19-5 baseline with CI > 0, superiority over its per-pixel control, snapshot uniqueness,
exact-file validation). The shared fail-closed `promotion_gate` still blocks on two
*procedural* items that no single session here can honestly satisfy — a synchronized complete
parallel registry, and the buffered-LOSFO protocol flag (this lane was frozen to the S21
quadrant protocol for baseline comparability). The candidate is therefore **eligible for the
separate selector step** (protocol §6), which must also confirm the weekly portal allowance.
Nothing has been uploaded.

| Item | Value |
|---|---|
| **File to download (primary)** | `docs/downloads/gems28-s22-ctxhgb-20261026-e23dabcec6e2-allfinite.tif` (826,194 bytes) |
| SHA-256 | `77934be607d48a4daec5b046009cdabf61d3fdee210aadc75be82ac70f3beb2e` |
| NaN twin / ZIP | `gems28-s22-ctxhgb-20261026-e23dabcec6e2-nan.tif` · `-nan.zip` (single member) |
| Dots | 37,654 (all ridge-selected; 0 on catalogue; min catalogue distance 2.236 px) |
| Format | Single-band float32, EPSG:32611, 3730 × 3292, template transform; primary has **no NaN anywhere**, values exactly {0,1} |
| **HOLDOUT-DTI** (seeds 360–362, 12 cells, 36,596 pooled withheld positives) | lane **0.12018** [0.10471, 0.13649] vs dotted-b2 **0.10519** [0.09191, 0.11915] vs per-pixel control **0.09505** |
| Paired Δ vs baseline | **+0.01498**, 95 % CI **[+0.01067, +0.01932]**, **12/12 cells won** |
| Paired Δ vs control (context value) | **+0.02512**, 95 % CI [+0.01885, +0.03293] |
| **Estimated live score** | **≈ 0.317 [0.307, 0.328] — MODEL PROJECTION** (USER-REPORTED 0.2778 anchor × holdout ratio 1.1424 [1.1033, 1.1801]); **not a score**; transfer caveats in §5 are material |
| Unique vs GEMSDOE32 champion | 42.05 % of dots within 3 px; surface Spearman +0.067 → **unique** (gates: ≤70 %, ≤0.90) |
| Worst registry overlap | 69.92 % vs the *unscored* dense H37-1 probe-union-pool raster — **pass by 0.0008, disclosed** (vs every scored raster ≤48.45 %) |
| Unique portal name | `GEMSDOE28-S22-ctxhgb-e23dabcec6e2` |
| Note (112/140 chars) | `S22 ctxHGB multiscale-context 37654d \| HOLDOUT-DTI 0.1202 vs dotted 0.1052 (+0.0150) seeds360-362 \| e23dabcec6e2` |

## 1. Nine focus-site executive summary (all scores USER-REPORTED / UNVERIFIED)

Exp 1 (`evidence/s22c_forensic.json`) byte-fetched the best file of GEMSDOE30/31/32/33/36 from
GitHub on 2026-10-26 and compared dot-sets exactly. **The entire top of the owner table is one
nested dot family**, not nine independent detectors: H19-5 ridge (121,131) ⊃ dotted d2.8
(44,090) ⊃ solo (40,199) ⊃ champion (37,654), each step a verified subset (symmetric difference
0 at every reconstruction step).

| Site | Best file (USER-REPORTED score) | Dots | Unique geography? — measured vs champion | Download-and-submit guidance |
|---|---|---:|---|---|
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (**0.2778**) | 37,654 | — (the champion itself; file SHA-256 `c55bafc4…6fa9`) | Best historical file, but **already the family's extreme prune**; resubmitting it (or any reconstruction) from this repo would be an exact duplicate. Reference only. |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-…-9b9ea4e6-zeros` (**0.2750**) | 38,854 | **No** — contains all 37,654 champion dots exactly + 1,200 more (97.40 % within 3 px) | Duplicate-family. Do not treat as independent confirmation. |
| GEMSDOE28 | `h36-1-rung30-blind-r1-…-b531dae0a36f-nan` (**0.2710**) | 37,660 | **No** — 95.47 % within 3 px of champion | Duplicate-family variant. |
| GEMSDOE31 | `h27-4-solo-d28-…-8acb75e1-nan` (**0.2708**) | 40,199 | **No** — dot-set **identical** to GEMSDOE28 solo (same dot-set SHA-256) | Same dots, two site names. |
| GEMSDOE28 | `h27-4-r1-solo-d2-8-…-8acb75e1f2cc-nan` (**0.2708**) | 40,199 | **No** — champion + ring-(1,2] dots (exact superset) | Parent of the champion. |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-…-cb490425926e` (**0.2632**) | 41,865 | **No** — 92.64 % within 3 px of champion | Duplicate-family variant. |
| GEMSDOE25 | `dotted-h19-5-d2-8-…-e56ea318af89-nan` (**0.2600**) | 44,090 | **No** — champion is its exact subset | Parent of solo/champion. |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-…-91eae1ca` (**0.2600**) | 44,090 | **No** — dot-set **identical** to GEMSDOE25 best (same dot-set SHA-256) | Same dots, two site names. |
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-…-989f59505db1-nan` (**0.2477**) | 60,069 | **No** — 88.48 % within 3 px; denser d=1.5 thinning of the same ridge | Earlier operating point of the same family. |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-…-5512495c6bd1-nan` (**0.2449**) | 61,328 | **No** — 86.72 % within 3 px (d1.5 + 1,259 gap-closure dots that earned ≈0 live credit) | Same family; gap-closure increment falsified live. |
| **GEMSDOE28-S22 (this session, UNSCORED)** | `gems28-s22-ctxhgb-20261026-e23dabcec6e2-allfinite` (**MODEL ≈0.317**, not a score) | 37,654 | **Yes** — 42.05 % within 3 px of champion; exact Jaccard 0.0197; surface Spearman +0.067 | **The only gate-passing unique candidate in the table.** Selector decides the slot (§6). |

**Which single file is "best to submit to obtain a high score"?** Among already-scored files the
champion (0.2778, USER-REPORTED) is best *historically*, but it belongs to GEMSDOE32's lineage
and re-uploading its geography is a duplicate. Among **unique, not-previously-submitted** files,
the S22 candidate above is the only one in any of the nine repos' local evidence that has beaten
the dotted baseline in a frozen holdout with CI > 0 — which is why it, and not another prune of
H19-5, is this session's recommendation *for the selector step*.

## 2. Why 0.2778 is the family maximum (PhD-level answer, byte-verified)

1. **One surface, monotonically better emission.** The ladder 0.1922 (solid) → 0.2477 (d1.5) →
   0.2600 (d2.8) → 0.2708 (−ring ≤1 px) → 0.2778 (−ring ≤2 px) is exactly a sequence of nested
   subsets of the H19-5 ridge (Exp 1, symmetric difference 0 at each step). Nothing new was
   *detected* between 0.1922 and 0.2778; false-positive mass was deleted faster than credit.
2. **The metric makes this profitable.** For binary dots, DTI = TP/(TP + 0.2·FP + 0.8·FN), with
   credit from the 300 m triangular kernel. Dots spaced 2.83 px along a 1-D crest keep ≥0.50
   credit at the midpoint while paying one-third the FP mass of a solid line; and deleting any
   dot set with dTP/dFP below the break-even τ = 0.2·DTI/(1−0.2·DTI) ≈ 0.0588 (at 0.2778)
   *raises* DTI. The champion is the family's best-known crossing of that rule.
3. **Catalogue-adjacent dots are (near-)zero-credit live.** Inverting the nested pairs
   (44,090 @ 0.2600 → 40,199 @ 0.2708 → 37,654 @ 0.2778) shows the ≤1 px and (1,2] px rings earn
   far below break-even: they trace the digitisation shadow of already-catalogued faults, while
   the private expert truth was compiled to be *new* structures. Pruning them is free DTI.
4. **Why nothing else in the owner corpus is close:** every independent fresh detector tried to
   date (per-pixel HGBs, single-operator surfaces) has lower credited coverage per dot than the
   H19-5 multi-expert ridge (S21: 0.0839 vs 0.1062 HOLDOUT-DTI). Emission hygiene cannot rescue a
   weaker surface, and re-emitting H19-5 cannot exceed ≈0.285 (the B3 prune bound; a 100 %
   within-3 px duplicate — measured in Exp 1, **not shipped**).

**Can a submission scoring higher than 0.2778 be generated?** Only with new *credited coverage*
on faults the catalogue lacks: at 37,654 dots, moving 0.2778 → 0.3195 needs ≈ +1,130 weighted
credit px; the verified 2026-10-26 public-leaderboard top is **0.4437** (ORGANIZER-PUBLIC,
xiaofanhu, 31 submissions; #2 0.3916, #3 0.3904 — fetched this session from the official
leaderboard page). That gap is a detector-class gap (learned spatial-context models ± 1 m DEMs),
not an emission gap. S22 is this repo's first context-aware step in that direction; its holdout
margin (+14.2 % relative) is real but an order of magnitude smaller than the leaderboard gap.

## 3. S22C lane result (HOLDOUT-DTI, frozen gate — `evidence/s22c_holdout.json`)

Lane per `knowledge/64`: 32-band shared stack + 32 context features (Gaussian σ2/σ5 means and
|∇σ2| of 10 bands; structure-tensor coherence of `lidar_step_max`, `tmi_hg`); HGB (S21
hyperparameters); ridge-NMS-restricted greedy emission (2.8 px, d_visible > 2, fold budget).
Mimic: roads/canals/shorelines/terraces/contacts. Seeds 360–362 × 4 quadrants = 12 cells;
baseline dots often *exceeded* the lane budget (up to +8 %) yet lost every cell.

| Check | Result | Gate |
|---|---|---|
| Leakage canary, worst single-feature AUC (64 features, cell 360-NW) | **0.7200** (`ctx_lidar_relief_g5`) | PASS (≤0.90) — physiographic habitat, label-free by construction |
| Pooled HOLDOUT-DTI lane / control / dotted-b2 | **0.12018 / 0.09505 / 0.10519** | — |
| Δ lane − baseline [95 % CI] | **+0.01498 [+0.01067, +0.01932]** | **PASS** |
| Δ lane − control [95 % CI] | **+0.02512 [+0.01885, +0.03293]** | **PASS** (context is the active ingredient) |
| Surface AUC (lane, cell range) | 0.612–0.782 | — |
| Pre-placement Spearman vs 30 registry dot-sets (200k sample) | max \|ρ\| **0.1507** (H19-5 parent) | PASS (≤0.90) |
| Final dots within 3 px of any one registry raster | worst **0.6992** (unscored H37-1 union-pool); champion **0.4205** | PASS (≤0.70), margin 0.0008 disclosed |
| Validator (shipped bytes, independent re-read; audit slot checks 30/30) | hard PASS both variants; primary no-NaN-anywhere {0,1} | PASS |
| Shared `promotion_gate` (fail-closed schema) | **negative** — only `buffered` (quadrant ≠ LOSFO buffer) + `registry incomplete` | Selector-level items, §6 |

## 4. The [0,1] portal error and the exact (selector) submission steps

- The portal error *"Predicted values must be in range [0, 1]"* remains **undiagnosed** (validator
  not public). The primary file removes every *local numeric* cause: whole array finite, values
  exactly {0.0, 1.0}, zeros outside the footprint, no nodata tag. The official format text
  (ORGANIZER-PUBLIC, fetched 2026-10-26) asks for null/NaN outside bounds; the NaN twin matches
  the sample submission literally. Owner history reports zeros variants scored identically, but
  that is **not** an organizer receipt — if the portal rejects the all-finite file, submit the
  NaN twin (or its ZIP) and record which bytes were accepted.
- **Exact steps for the selector (owner), when and if approved:** (1) confirm remaining weekly
  allowance on the authenticated submission page (rules PDF states 3/week; account state unknown
  here); (2) *New submission → File to submit* → `gems28-s22-ctxhgb-20261026-e23dabcec6e2-allfinite.tif`
  (or the NaN ZIP); (3) paste the 112-char note from §0; (4) submit once; (5) save the receipt and
  bind it to SHA-256 `77934be6…beb2e` in this repo before ever calling any number
  ORGANIZER-CONFIRMED; (6) remember the single chosen GeoTIFF is re-scored in the Final round.

## 5. Why the ≈0.317 projection must not be read as a promise (Pass-2 scepticism)

1. **Near-catalogue concentration.** S22's median dot is 8 px from the catalogue (champion:
   19.6 px); 17.8 % of its dots sit in ring (2,3] (champion 5.8 %). Live inversion proved ring
   ≤2 px ≈ 0 credit; ring (2,5] live credit is *unmeasured*. Catalogue-internal holdout rewards
   near-catalogue emission (hidden components are neighbours of visible ones) in a way the
   expert-new-fault live truth may not. This is the single largest transfer risk and biases the
   ratio projection upward by an unknown amount.
2. **Habitat, not just scarps.** The strongest canaries are relief/elevation context (AUC ≈0.72):
   part of the lane's skill is "faults live in ranges", which the H19-5 ensemble encodes too but
   with different dot placement. Basin-floor blind faults (geothermally important) may be
   systematically under-dotted — relevant to Final-round discovery value.
3. **Uniqueness margin.** 0.6992 vs the H37-1 union-pool raster passes by ≈30 dots. That raster
   is an unscored union of many detectors' pools (any competent detector overlaps it heavily);
   against all *scored* rasters the lane is comfortably unique. A stricter coordinator could
   still flag it; disclosed here rather than hidden.
4. **Anchor risk.** 0.2778 itself is USER-REPORTED. If the true champion association differs,
   the projection scales with the error.
5. **Protocol scope.** Quadrant component-hide has no LOSFO buffer; the frozen comparison is
   apples-to-apples vs S21's baseline numbers (0.10519 here vs 0.10621 in S21 on seeds 350–352),
   but a buffered LOSFO confirmation on fresh seeds is the recommended next validation before
   risking a scarce slot late in the competition.

Net judgement: the lane is a genuine, measured improvement over everything this repo has
previously validated — and still most likely a ~0.26–0.33 live file, below the 0.33–0.44
leaderboard cluster. Its discovery-rich fresh geography (58 % of dots >3 px from the champion)
is exactly the profile the Final Prize Round rewards.

## 6. Irregularities flagged

1. Lane self-assignment (prompt's method paragraph absent) — disclosed in `knowledge/64` §0.
2. All nine-site scores USER-REPORTED; GEMSDOE25-best ≡ GEMSDOE30-best and GEMSDOE28-solo ≡
   GEMSDOE31-best are identical dot-sets under different site names (dot-set SHA equality).
3. GEMSDOE36's "PINN" file is champion + 1,200 dots (97.40 % within 3 px) despite the
   independent-method name.
4. Archive audit (S22 run): 720 checks, 2 failures — legacy `h40-1-thermal-vent` /
   `h41-1-thermal-spring` *allfinite* files carry a `nodata=NaN` tag over zero outside values
   (values themselves are clean). Historical bytes left untouched; coverage failure inherited
   from S21-AUDIT is otherwise fixed (all 46+ TIFFs now registered, incl. the S21 pair).
5. `registry/current_session.json` still describes the older G28-A51 session (hash-bound
   historical evidence; not rewritten — same constraint S20V hit).
6. Inputs are owner-supplied GitHub mirrors, SHA-256-pinned (17/17 restored+verified this
   session), not organizer-authenticated downloads. No DrivenData contact was made by any script.

## 7. Three passes, limitations, next steps

- **Pass 1 (implement+verify):** restored 17/17 pinned inputs; rebuilt shared 32-band cache;
  Exp 1 forensic on fetched champion-family bytes; froze `knowledge/64`; built 32 context
  features; canary + 12-cell gate (Exp 2); final build + validator + 30-raster uniqueness
  (Exp 3); run card, manifest registration, download audit (S22 slot 30/30 PASS).
- **Pass 2 (bugs/assumptions):** checked train-label isolation (other-quadrant only),
  visible-only catalogue distances, negative-pool construction, baseline budget disadvantage
  (conservative), fill rule (0 fills used), value set {0,1} by re-read, ZIP single-member
  byte-identity via shared writer, note length (112), content-addressed naming; measured the
  near-catalogue concentration and downgraded the projection language accordingly; ran the
  strict shared `promotion_gate` and kept its fail-closed output instead of relabelling it.
- **Pass 3 (requirements):** nine-site table with file/score/uniqueness ✓; why-0.2778 +
  beat-it analysis ✓; 5 ranked hypotheses with layers/signatures/mimics/costs/data-gates ✓
  (`knowledge/64`); unique TIF with obvious disposition ✓; automated non-human validation ✓;
  HOLDOUT vs USER-REPORTED vs MODEL labelling ✓; JSON run card ✓; 3/3 experiments, 0 slots ✓.
- **Next steps (prioritised):** (1) buffered LOSFO confirmation of the S22 surface on fresh
  seeds (370+) + distance-stratified credit audit to price the (2,5] ring; (2) S22-H2 tiny
  U-Net on GPU hardware (the remaining route toward 0.39–0.44); (3) far-field-weighted training
  (down-weight near-catalogue positives) as a *new* preregistered lane if (1) confirms ring
  decay; (4) fix or retire the two nodata-tagged legacy allfinite files; (5) selector decision
  on the S22 slot with portal-cap verification.

**Maximize P(Win) · Own the Outcome.**

## 8. Merge addendum (PR #63) — parallel S22 sessions, rename to S22C, seed collision

While this session ran, three parallel same-prompt sessions merged to `main` (PRs #57–#61):
**S22-SIGN** (signed piedmont break-in-slope — this session's hypothesis #3), **S22-MOFR**
(marker-offset piercing points — hypothesis #4), and **S22-AUDIT** (archive registration +
scorecard). All are **negative / DO NOT SUBMIT** (SIGN: local-proxy candidate mean 0.0547 vs
baseline 0.1219, paired −0.0673, gate fail, `evidence/s22_run_card.json`, plus an S22-AUDIT
erratum voiding its canary/CI claims; MOFR: HOLDOUT-DTI 0.03385 vs baseline 0.14399,
`evidence/s22_mofr_run_card.json`). Hypotheses #3 and #4 of `knowledge/64` are therefore now
*tried and negative* — do not re-propose them as untried. S22-AUDIT independently performed the
same archive-registration fix as this session's Exp-3 follow-up; at merge, main's
`s22_archive_*` manifest entries were kept and this session's duplicate `archive_*` entries were
dropped (the registration script is preserved as `scripts/register_legacy_downloads_s22c.py`,
a no-op after the merge).

**Rename:** this run was labelled "S22" on its branch and independently claimed seeds
**360–362** — the same seeds S22-SIGN claimed from the same base commit. This is a disclosed
parallel seed collision (same pattern as S20 340–344). Because the shared split code is
deterministic in the seed, both sessions withheld the *same* components (36,596 pooled
positives — the figure S22-AUDIT's erratum independently sums from SIGN's detail rows), so the
two holdouts are directly comparable as *paired geography tests* but are **not** independent
seed replicates; never pool them. To avoid filename collisions this session is **S22C** from the
merge onward (`knowledge/64`/`65`, `evidence/s22c_*`, `scripts/*s22c*`,
`docs/session22c-result.html`, manifest key `s22c_candidate`). The candidate TIFF, portal name
and note are content-bound and unchanged. Original run-card bytes were renamed, not rewritten;
fields inside it that name `knowledge/62` or the pre-merge downloads-manifest SHA-256 refer to
the branch-time state.

**Post-merge uniqueness regeneration** (merge duty, not a fourth experiment): computed after
merging `main` and recorded in `evidence/s22c_merge_addendum.json` — final-dot overlap and
surface Spearman of the S22C candidate vs the S22-SIGN and S22-MOFR TIFFs, plus the merged
archive audit. The S22C frozen-gate verdict above is unchanged; if the merged comparison were
to breach the 0.70/0.90 duplicate stops, this addendum (not a silent edit) is where the
reclassification would be recorded.
