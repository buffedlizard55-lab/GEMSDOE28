# Preregistration — H33-1 kinematic reactivation favourability gate

**Registered 2026-10-03 (Session 10), before any fitting and before any seed spend.**
Seed decade **200–209** (reserved in `knowledge/18_new_hypotheses_H33_series_2026-10-03.md`; the
LOSFO diagnostic this session uses its own decade 210–214 and consumes nothing here).

This document is frozen. If the runner changes it after the data lands, the SHA-256 recorded in the
evidence JSON will differ and the run is invalid.

---

## 0. Data precondition — **no seed may be spent until this is satisfied**

H33-1 needs the USGS slip-/dilation-tendency release. Its status as of this preregistration:

| Fact | Value | How verified |
|---|---|---|
| Release | Siler, C.D. (2022), *Slip and dilation tendency analysis of Quaternary faults, Great Basin*, DOI [10.5066/P9YL58W6](https://doi.org/10.5066/P9YL58W6) | DOI recorded in `registry/external_pins.json` |
| ScienceBase item | [6296974dd34ec53d276bb33d](https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d) | item id in `registry/external_pins.json` |
| File | `Shapefile_Full Study.zip` | filename in `registry/external_pins.json` |
| Bytes / SHA-256 | `35,912,323` / `5d6213f7763002d369c40b281c31d22113f9c48c482e10ca469e0f6f6b985163` | **runner-recorded** 2026-10-03, `evidence/external_layer_inventory.json` → `sciencebase_availability.sb_slip_tendency_shapefile_full.status = AVAILABILITY_FETCHED` |
| Bytes actually held locally | **none** | the availability probe streams and discards; nothing was written to `--out` |
| Sandbox reachability of sciencebase.gov | **000 (unreachable)** | `curl` this session, exit 35 TLS; also `doi.org` 000, `api.datacite.org` 000, `drivendata.org` 000; `api.github.com` 200, `pypi.org` 200 |

**Gate:** the derived clip `docs/data/sb_slip_tendency_in_footprint.json` must exist, its schema must
list attribute fields consistent with slip tendency and dilation tendency, and
`n_features_in_bbox > 0`. Until then H33-1 is **not runnable** and no seed is spent. The bridge that
produces it is `scripts/fetch_external_layers.py --derived all` +
`.github/workflows/fetch-gdr-external-layers.yml`, covered end-to-end (stream → hash → pin compare →
archive → clip → write) by `tests/test_external_bridge_derived.py` and
`tests/test_external_clip.py`, exercised here on a `file://` pin because the science host is
unreachable from the sandbox.

**Not re-verified this session:** the *interpretation* of the release (that it carries a slip-tendency
and a dilation-tendency attribute per fault segment) rests on the 2026-10-03 agent read of the
DataCite/ScienceBase record recorded in `knowledge/18`. `api.datacite.org` returns 000 from this
sandbox, so that reading could not be repeated. It is treated as **unconfirmed until the derived
schema lists the fields**; the schema file is the check, and the run must print it.

---

## 1. Physical hypothesis

Faults oriented favourably with respect to the contemporary stress field accumulate slip (high slip
tendency `Ts`) or open (high dilation tendency `Td`) under the present-day extensional regime. In the
Great Basin that regime is measurable independently from geodesy, which the competition raster
already provides as the bands `geod_2ndinv` (second invariant of the strain-rate tensor),
`geod_dilaterate` and `geod_shearrate`.

**Claim.** Among the off-catalogue candidate dots already emitted by the holdout-best base, those
sitting on *unfavourably oriented, low-strain* structure are enriched in false positives relative to
those on favourably oriented, high-strain structure. Pruning the former raises DTI; pruning the
latter lowers it.

**Why this could find faults the catalogue misses.** The Qfaults/INGENIOUS compilation is
geomorphically biased — a fault enters it when a mapper can see a scarp. A favourably oriented fault
in active E–W extension keeps accumulating strain whether or not its scarp survives, and is the class
expert mappers add during Phase-2 review. An unfavourably oriented lineament is more likely a
lithological or relict contact. This is a *statement about which candidate dots are faults*, which no
amplitude-based layer in the repository tests.

**Difference from everything already implemented here.** `H28-4`/SRCOH used shear-rate × seismicity
density (refuted, 0/4 folds). No arm has used stress-orientation kinematics (`Ts`/`Td`) or this
product. This is a **gate on emission**, not a feature injection — `H31-1`'s Euler channel was
injected as GBDT features and failed (`-0.001947`, 1/4 folds), whereas the same channel used as a
protection gate passed (`H32-1`, `+0.001272`, 4/4 folds). The lesson is applied, not repeated.

---

## 2. Design (frozen)

**Protocol.** The repository's frozen 4-fold spatially-blocked hide-and-recover harness
(`src/gems27/holdout.py`): four quadrants, 20 % of 8-connected catalogue components hidden per
quadrant per seed, known catalogue masked from evaluation. Paired cell-for-cell against the control.

**Control (`base`).** The H32-1 holdout-best base arm: 4-fold out-of-fold
`HistGradientBoostingClassifier` on the 32-band label-free matrix, ridge NMS, `PRE_THIN_FRAC`
budget, `thin_d = 2.8`. Identical hyper-parameters, buffer and seeds to `scripts/run_h32_1_holdout.py`
so the comparison is to the current holdout best, not to a re-derived base.

**Favourability score (label-free, computed per cell).** For each base dot:
1. `strike` from the nearest OOF ridge orientation within 5 px.
2. `Ts`, `Td` of the nearest catalogued segment whose strike differs by < 20° and which lies within
   10 px, interpolated by inverse-distance over up to 3 such segments. Dots with no such neighbour
   get a **neutral** score (never pruned, never protected) — the gate must not punish absence of
   data.
3. `strain` = footprint-quantile rank of `geod_2ndinv` at the dot.
4. `fav` = mean percentile rank of (`Ts`, `Td`) × `strain` percentile rank, in [0, 1].

**Variants (all four evaluated on every cell):**

| Variant | Rule |
|---|---|
| `base_oof_d28` | control, unchanged |
| `h33_1_prune_p10` | **primary**: remove the bottom decile of base dots by `fav` |
| `h33_1_prune_p05` | remove the bottom 5 % (dose check) |
| `control_top_p10` | **direction control**: remove the *top* decile by `fav` |

**Seeds.** 200–209 inclusive, 10 seeds × 4 folds = 40 paired cells. One use. If the run is
interrupted the decade is burned and the next arm takes 220–229.

---

## 3. Analysis and promotion gate (frozen, numeric)

Reported per variant: mean paired ΔDTI over seed means, `seeds_won`/10, `folds_improved`/4,
`delta_dots_per_seed`, and `removed_credit_per_removed_fp`.

**`h33_1_prune_p10` is promoted only if all of the following hold:**

1. `mean_dti_gain >= +0.0010`
2. `folds_improved >= 3` of 4
3. `seeds_won >= 8` of 10
4. `removed_credit_per_removed_fp < metric.inclusion_threshold(base_mean_dti)` — the pruned pixels
   must be below the break-even credit density, i.e. pruning them must be *correct*, not merely
   convenient
5. `control_top_p10.removed_credit_per_removed_fp >= h33_1_prune_p10.removed_credit_per_removed_fp`
   — the direction control must be worse, confirming the sign of the physics rather than a generic
   "fewer dots is better" effect
6. `>= 60 %` of base dots receive a non-neutral `fav` score (coverage precondition; a gate that only
   sees 10 % of the emission cannot be interpreted)

**On failure:** record the result, do not retune, do not re-run on a fresh decade, do not build a
candidate TIFF, spend no slot. This is what happened to `H31-1` and `H32-2` and it is the correct
outcome.

**On pass:** still no slot until (a) an exact-file audit passes `scripts/verify_downloads.py` and
(b) the candidate is built by a committed script, not by hand.

---

## 4. Expected magnitude, and why this arm cannot win the competition alone

`evidence/reachability_frontier.json` (this session, identity-checked against
`src/gems27/metric.dti_binary` to `2.2e-16`) puts the gap to the public leaderboard #1 at
**+1,151 px of DTI credit at the current 44,090 px budget — 24.0 % more credit than the best
owner-anchored submission captures, 9.42 points of the calibrated |G| = 12,226 px.** Every arm in
this repository, including H33-1, is a *pruning* arm and moves DTI by ~0.001–0.010. H33-1's
registered expected range is **+0.0005 to +0.0030**. It is worth running because it is cheap and
because a gate that survives becomes a reusable component of later emission policies; it is **not**
a path to 0.3195, and this document does not claim it is. Closing that gap requires an *addition* arm
that places new dots on unmapped faults — see `knowledge/20_strategy_after_reachability_frontier.md`.

---

## 5. Geological and methodological limitations (stated up front)

1. **`Ts`/`Td` are model outputs, not measurements.** They assume a stress tensor and a friction
   coefficient; a fault's true reactivation potential also depends on pore pressure, which the
   release cannot see. A low-`Ts` label is evidence against, not proof of absence.
2. **Borrowing from catalogued segments.** The score is transferred from the nearest similarly
   oriented *mapped* segment. Where the mapped network is sparse or its strikes are unrepresentative,
   the score is unreliable — hence the neutral default and the 60 % coverage precondition.
3. **The holdout proxy is catalogue-internal.** `evidence/arm_habitat_decomposition.json` shows 100 %
   of its hidden truth lies at distance 0 from the published catalogue, so a pass here measures
   performance against *mapped* faults held out locally, not against genuinely unmapped ones. The
   LOSFO diagnostic (`evidence/losfo_farfield_diagnostic.json`) quantifies that inflation; if H33-1
   passes the interleaved gate it should be re-checked under LOSFO before a slot is considered.
4. **Strike from ridge orientation is a 4-sector quantisation** (`oof_detector.ridge_nms`), i.e.
   ±22.5°. The 20° matching tolerance is therefore at the edge of the instrument's resolution; a
   sensitivity run at 30° is a legitimate robustness check but is *not* part of the frozen gate.
5. **Owner-reported scores are not receipts.** All live figures quoted anywhere in this repository,
   including 0.2600 and 0.3195, are owner-reported or public-leaderboard readings and are not linked
   to a specific TIFF by the organizer.
