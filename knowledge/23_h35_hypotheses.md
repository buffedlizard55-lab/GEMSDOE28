# Session 11 (2026-10-03) — the H35 series: addition arms, and the first one that can run today

Status: **preregistration frozen before any H35 seed is spent.** The gate criteria in §5 were written
into this file before `scripts/run_h35_1_thermal_farfield.py` was executed. Seeds `230–234` are
reserved for H35-1. Seeds `180–189` (H32-1), `200–209` (H33-1) and `220–229` (H34) are spent;
`210–214` is the Session-10 LOSFO diagnostic decade.

---

## 1. What the official sources actually say (re-verified this session, with links)

Every claim in this section was read off the official page or the official rules PDF on
2026-10-03. Nothing here is inferred.

| # | Fact | Source (official) |
|---|---|---|
| 1 | Metric is the distance-weighted Tversky index with `alpha = 0.2`, `beta = 0.8`, triangular kernel `R = 300 m`; `k(d) = (1 - d/R)+` | [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) §Performance metric |
| 2 | Submission = single-layer `float32` GeoTIFF, EPSG:32611, 100 m, same bounds, **values between 0 and 1**, outside-bounds null/NaN | same page, §Submission format |
| 3 | **Three submissions per week** — this is the "weekly slot" the standing prompt refers to | [Official Rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) §3.2 |
| 4 | **Two rounds.** Initial Prize Round scores against a *fixed private set of expert-labelled faults not in the USGS database*; Top 5 win \$10K each. Experts then review **every team's** submission, verify new faults, and the expanded label set rescored for the Final Prize Round (Top 5: \$100K/\$70K/\$40K/\$25K/\$15K) | problem page §Competition structure; rules PDF §3.2 |
| 5 | Labels come from the USGS Quaternary Fault and Fold Database **plus** newly identified faults labelled by experts at NLR and USGS | rules PDF §2 |
| 6 | External data is allowed **provided** the competitor holds a licence permitting use in this challenge and sharing with the sponsor | problem page §External datasets; rules PDF §3.7 |
| 7 | Public leaderboard, read 2026-10-03: `#1 DARD 0.3195` (12 submissions), `#2 nchuzhoy 0.3128`, `#3 alexoktaba 0.3042`, `#4 Batik Shirt Brothers 0.2998`, `#5 xiaofanhu 0.2941`; our best (`dotted-h19-5-d2-8`) corresponds to `#15`-class `0.2600` | [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/); `registry/leaderboard_snapshot_2026-10-03.json` matches this read entry-for-entry |

Two consequences that drive the ranking below:

* **Fact 4 changes what a "good" submission is.** The Final Prize Round is scored on an *expanded*
  label set built partly from competitors' own predictions. A submission whose off-catalogue dots are
  *geologically defensible* therefore has option value that the public leaderboard does not price.
  That is the official basis for the bounded Phase-2 arm (H35-4) — not a speculation about scoring.
* **Fact 5 + Fact 1 together define the target.** The label set is a *surface-rupture* catalogue
  (Quaternary fault and fold database). The private test set is *expert-labelled faults absent from
  it*. So the highest-value addition arms are those that observe a **different physical field** than
  scarp mapping, not those that re-weight the catalogue.

---

## 2. Why the programme needs ADD arms (one paragraph, for continuity)

`evidence/reachability_frontier.json`: at the `0.2600` file's budget of `N = 44,090` dots and
`4,836` px of credit, reaching `0.3195` needs `5,942` px — **`+1,151` px, `24.0 %` more credit than
the entire best submission captures**. Thinning removed `15,979` dots for `495.08` px of credit, i.e.
a marginal efficiency of `0.03098` credit/px against a break-even of `0.05485`: **no quantity of the
current dots can close the gap**. `knowledge/22_h34_result.md` §3 then showed the pruning family
(H31-1, H32-2, H33-1, H34) is exhausted: all measured removal efficiencies (`0.034–0.129`) are far
above the live break-even. The only remaining path is **new dots that land on genuinely unmapped
structure**, gated against `tau_live = 0.0548` (not the `0.0193` proxy threshold).

---

## 3. The H35 candidate set (5 hypotheses, none previously implemented)

Each names its layer(s), the physical signature it targets, why it should catch a fault *missing*
from the USGS/INGENIOUS catalogue rather than one already in it, and what distinguishes it from
everything already in this repository.

### H35-1 — Hydrothermal-discharge conjunction (**ADDITION**) ← *run this session*

* **Layers.** `data/gdr_wellspring_in_footprint.csv` (GDR submission 1391, INGENIOUS): `15,168`
  unique sites in the footprint, `2,477` with a reported temperature, `2,062` at `>= 20 C`, `593` at
  `>= 50 C`, `341` with a quartz geothermometer value; independently re-registered this session
  (session §4). Used *only* as a point process — the catalogue-derived `dist_known_fault_px` column is
  excluded by allow-list (`src/gems27/thermal.py`).
* **Physical signature.** A **point process of thermal discharge** — a surface expression of
  *subsurface permeability*, plus quartz/chalcedony geothermometry as a proxy for reservoir
  temperature. Not an edge/curvature transform; no derivative of the potential field is involved.
* **Why it catches a *missing* fault.** The label set is a **surface-rupture** catalogue (§1 Fact 5).
  A structure that transmits geothermal fluid but has no mapped Quaternary scarp — concealed under
  basin fill, or slipping too slowly to cut a scarp — is exactly what a hot spring marks and what the
  catalogue omits. The arm proposes dots only where the detector already sees a ridge **and** a
  thermal site corroborates it **and** the catalogue is silent.
* **Why it differs from everything in the repo.** It is the first *point-process, non-catalogue*
  physical layer used as an addition licence. H33-1 transferred a *catalogue attribute* onto
  candidates and measured a hard `11.95 %` coverage ceiling (`knowledge/21_result_H33-1`) because
  candidate dots are off-catalogue by design. A layer that is not derived from the catalogue cannot
  inherit that ceiling. Verified additively: all 20 previous owner sites used raster geophysics
  (magnetics, gravity, radiometrics, DEM-derived scarp descriptors) or the catalogue itself.
* **Cost.** LOW — data is already restored and hash-verified; `~7 min` on 2 CPU cores for 5 seeds.
* **Obtainability.** In hand (verified below). No external fetch.

### H35-2 — Heat-flow residual × 2 m temperature-depth probe conjunction (**ADDITION**)

* **Layers.** ScienceBase item `6297d2fad34ec53d276c5b28`, DOI `10.5066/P9BZPVUC`
  (already byte-verified by the Actions runner: `130,154,244 B`, SHA-256 `e7fd62c6…` in
  `registry/external_pins.json`) × the GDR 2 m probes.
* **Physical signature.** **Residual** heat flow — departure from the de-convected background,
  carried as an explicit attribute in that product. It marks conductive upflow the surface-rupture
  catalogue ignores.
* **Why it catches a *missing* fault.** Heat flow is a *point* measurement interpolated to a grid;
  its residual is a *local* conductive anomaly that need not coincide with a mapped scarp.
* **Difference.** Never implemented here; the repo has used magnetics, gravity, radiometrics, MT
  conductance (H33-2) and lidar topography, but never heat flow.
* **Cost.** HIGH. Requires the Actions runner bridge (`scripts/fetch_external_layers.py`).
  **Obtainability check 2026-10-03, in-sandbox:** `sciencebase.gov` → HTTP `000`; not obtainable in
  the agent sandbox. Obtainable **only** through GitHub Actions, which the repo has used before
  (run `37146168753` produced the H33-1 clip). Therefore **not viable as a same-session arm**; it is a
  queued Actions job.

### H35-3 — Drainage-network neotectonics from the 1 m DEMs (**ADDITION**)

* **Layers.** `data/dem_links.json` → `716` USGS 3DEP/Theia 1 m tiles (official bucket URLs); lidar
  descriptor bands in `data/lidar_scarp_features_u8.tif`.
* **Physical signature.** Fluvial response to active uplift: channel offsets, beheaded streams,
  aligned knickpoints. The drainage network integrates deformation continuously, so it can record a
  fault that never produced a scarp.
* **Difference.** The repo has 2 m scarp descriptors and 100 m topographic derivatives, but **no
  channel-network/channel-offset analysis at all**.
* **Cost.** VERY HIGH (716 tiles, GB scale, needs a runner and a multi-hour job).
* **Obtainability check 2026-10-03, in-sandbox:** `prd-tnm.s3.amazonaws.com` → HTTP `000`;
  `earthexplorer.usgs.gov` → `000`. Not obtainable here; a runner job with a large budget.

### H35-4 — Bounded Phase-2 discovery budget (**ADDITION, bounded**)

* **Layers.** None external. Uses the existing emission + the corroboration gates already computed
  (Euler depth clusters, thermal conjunction, ridge coherence).
* **Physical signature.** Not a physical transform: it is a *budget* decision — spend up to
  `~600 px` of multi-corroborated off-catalogue emission, charging at most `0.2 x budget` in Phase-1
  false-positive mass.
* **Why it catches a *missing* fault.** It targets the Final-Prize-Round mechanism verified in §1
  Fact 4: predictions that help experts identify previously unmapped faults are rescored on the
  expanded label set.
* **Difference.** No prior arm reasons about the *two-round* structure; every previous arm optimised
  the public metric only.
* **Cost.** LOW. **Obtainability.** Nothing to fetch. Risk: the payoff is real but *unobservable*
  from the public leaderboard, so it can never be validated here — it may only be *bounded*.

### H35-5 — Vent-corridor structural control (**score/CONFIRMATION**, not a mass addition)

* **Layers.** `data/gdr_volcanic_vents_in_footprint.csv` (`21` vents: `20` basalt, `1` rhyolite;
  `dist_known_fault_px` present but excluded).
* **Physical signature.** Vent alignments record deep structural corridors that localise magmatism.
* **Why it matters.** A monogenetic vent field sitting on an unmapped corridor is a strong,
  independent argument that a fault exists there.
* **Difference.** Never used; the repo has used vents not at all.
* **Cost.** LOW, but **support is tiny** (`21` points) — it can only re-rank or confirm existing
  dots, never license a mass addition. Ranked last for that reason.

---

## 4. Independent verification performed this session (line by line)

1. **Restore chain.** `bash scripts/download_competition_data.sh`
   (`PYTHON=$PWD/.venv/bin/python`) → exit `0` in `117 s`; `17/17` pins `restored-and-verified`
   (`data/restore_receipt.json`); `data/prepared/features.npy` rebuilt, shape `(5,167,373, 32)`,
   `float32`, SHA-256 `83ed2704ee2de03cf8b1c8f2966fcf71813501df97c1c35400e6c0415393f6dc`;
   `evidence/restore_audit.json` written. Scope is stated in that file:
   *"integrity-only local audit; not proof of organizer authenticity, coverage, licensing, or portal
   acceptance"* — the mirrors are owner-supplied, **not organizer-authenticated**.
2. **Tests.** `pytest -q` → `180 passed, 2 skipped` before this session's changes; the new
   `tests/test_thermal.py` adds `10` more (all passing).
3. **Submission artifacts.** `scripts/verify_downloads.py` → `PASS`, `179` checks, `0` failures
   (`evidence/submission_file_audit.json`): `float32`, single band, exact template grid, values in
   `[0, 1]`, zero catalogue overlap.
4. **Thermal layer registration.** `row`/`col` in
   `data/gdr_wellspring_in_footprint.csv` were re-derived from `utm_x`/`utm_y` through the template
   geotransform: max absolute residual **`1.0 px`** for both axes on `27,092` raw records —
   consistent with integer rounding, i.e. the table is on the competition grid. `15,168` unique
   locations after de-duplication.
5. **Data-hygiene irregularities found and recorded** (`registry/irregularities.json`):
   (a) two distinct `thermalclass` spellings, `"Hot"` (`878`) and `"Hot "` (`100`, trailing space);
   (b) the volcanic-vent table writes the **string** `"nan"` into `name`, `age`, and `rock_type`
   columns rather than an empty field. Neither is used by H35-1's gate (it thresholds numeric
   `temp_c`), but both would silently corrupt a naive `value_counts()` or string comparison.
6. **Network reality check (in-sandbox).** `github.com` `200`, `api.github.com` `200`; but
   `raw.githubusercontent.com`, `drivendata.org`, `gdr.openei.org`, `openei.org`, `sciencebase.gov`,
   `*.usgs.gov`, `prd-tnm.s3.amazonaws.com` all return `000`. Official pages were therefore read
   through the separate page-fetch tool, which is not the sandbox network — which is why §1 carries
   direct quotations rather than paraphrase.

---

## 5. H35-1 frozen gate (written before the run; all four criteria must pass)

Instrument: **LOSFO** (`src/gems27/losfo.py`) — leave-fault-system-out with a 600 m label buffer, the
only protocol in this repository whose truth is genuinely off-catalogue. Seeds `230–234`, 4 quadrant
folds, `thin_d = 2.8` (the rung of the current live best), `budget_frac = 0.0245` (unchanged from the
standing detector so the base emission is comparable).

Statistic: for every cell, take the candidate pool
`ridge AND active AND NOT base` and split it by distance to the nearest `temp_c >= 20 C` site.
`credit` is the **marginal** credit `TPw(base + adds) - TPw(base)`, so a dot next to an existing dot
earns nothing rather than double-counting shared truth pixels.

| # | Criterion | Threshold |
|---|---|---|
| **G1** | profitability | pooled marginal credit per thermal-added dot `>= tau_live = 0.054852` (at the `0.2600` anchor) |
| **G2** | differential | thermal credit/dot `>` matched-count random control drawn from candidates `> 6 px` from any thermal site, pooled, and the thermal arm wins `>= 4/5` seeds |
| **G3** | support | `>= 200` thermal-added dots per seed on average |
| **G4** | end-to-end | pooled mean `delta DTI > 0` on the paired cells when the thermal dots are added to the base emission |

Dose-response reported but **not gating**: `temp_c >= 50 C`, geothermometry `>= 100 C`, radii `1 px`
and `6 px`. Direction control is built into G2 (the random draw is the same size and from the same
candidate pool).

**Reading rule, fixed in advance.** If `G1` passes but the measured efficiency sits below `tau_live`,
the arm is closed and nothing is promoted — a below-break-even addition lowers the live score.
If the gate passes, the arm earns a *candidate* build only; it still does not touch a weekly slot
(three per week, §1 Fact 3) until the file passes `verify_downloads.py` and the delta survives a
confirmation decade.

**Disclosures.**
* The held-out systems in LOSFO are *mapped* faults whose geophysical expression is, by selection,
  detectable — so the measured credit/dot is an **upper bound** on performance against genuinely
  unmapped faults. This is stated in `src/gems27/losfo.py` and repeated in the evidence file.
* The 32 feature bands are not re-derived with held-out systems removed. The thermal layer is not
  catalogue-derived (verified by allow-list), but the magnetic/gravity bands may carry a catalogue
  imprint this protocol cannot remove.
* One throwaway seed (`240`) is used **once** for a pipeline smoke test before the frozen run; it is
  disclosed in the evidence file and is outside every reserved decade.
* No seed in `180–229` is reused; `210–214` remains the diagnostic decade.

---

## 6. Ranking (expected DTI improvement × cost, per the standing instruction)

| Rank | ID | Class | Expected `delta DTI` | Cost | Data obtainable today? |
|---:|---|---|---|---|---|
| 1 | **H35-1** thermal-discharge conjunction | ADD | unknown, gated at `0.0548` credit/dot; only arm that can move the detection gap this session | LOW (`~7 min`, data in hand) | **YES — in hand, hash-verified** |
| 2 | **H35-4** bounded Phase-2 discovery budget | ADD (bounded) | unobservable on the public LB; option value only | LOW (no fetch) | YES — nothing to fetch |
| 3 | **H35-2** heat-flow residual × probes | ADD | could be large: a *different* physical field | HIGH (Actions bridge) | NO in-sandbox; YES via Actions |
| 4 | **H35-3** drainage-network neotectonics | ADD | highest ceiling, 716 tiles | VERY HIGH | NO in-sandbox; Actions only |
| 5 | **H35-5** vent-corridor structural control | CONFIRM | re-ranking only (`21` points) | LOW | YES — in hand |

Per Core Value 1 (**Maximize P(Win)**) and the standing instruction *"never spend a weekly submission
slot on an idea that hasn't beaten the current holdout best"*: no submission slot is used by any H35
arm in this session. The only rule-compliant path is validation first; §5 is that validation.
