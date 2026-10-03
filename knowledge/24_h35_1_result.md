# H35-1 result — hydrothermal-discharge conjunction: **CLOSED ON ITS OWN EVIDENCE**

Run `2026-10-03T20:16:41Z`. Instrument: leave-fault-system-out (LOSFO), 600 m label buffer, 4
quadrant folds, seeds `230–234`, `thin_d 2.8`. Evidence: `evidence/h35_1_thermal_farfield.json`
(450 s). Script: `scripts/run_h35_1_thermal_farfield.py`. Frozen criteria:
`knowledge/23_h35_hypotheses.md` §5, written before the run.

## 1. Headline

**3 of 4 frozen criteria failed.** `gate_passed: false`, `status: CLOSED_ON_OWN_EVIDENCE`.

| # | Criterion | Required | Observed | Result |
|---|---|---|---|---|
| **G1** | Profitability | `>= tau_live = 0.054852` credit per added dot | **0.013195** | **FAIL** (4.2x short) |
| **G2** | Differential vs matched-count random control | thermal `>` control pooled, and `>= 4/5` seeds | thermal **0.013195** vs control **0.023781**; **1/5** seeds won | **FAIL** |
| **G3** | Support | `>= 200` thermal-added dots per seed | **6,856.8** | PASS |
| **G4** | End-to-end | pooled mean `delta DTI > 0` | **-0.001805** (control `+0.000354`) | **FAIL** |

Per the frozen reading rule: the arm is closed. **No candidate TIFF was built, no submission slot is
touched, and no retuning is permitted.** Seeds `230–234` are spent.

## 2. The dose-response is flat, so there is nothing to rescue

Every pre-declared dose variant was reported; none was allowed to gate. Every one of them sits at or
below the control, and all are 2.6-5x below `tau_live`:

| Variant | added dots (20 cells) | credit / dot | mean `delta DTI` |
|---|---:|---:|---:|
| `temp_c >= 20 C`, radius 6 px (primary) | 34,284 | 0.013195 | -0.001805 |
| `temp_c >= 50 C` | 8,049 | 0.015812 | -0.000227 |
| geothermometry `>= 100 C` | 7,065 | 0.011717 | -0.000376 |
| radius 1 px | 7,100 | 0.020949 | +0.000124 |
| radius 6 px | 106,584 | 0.010640 | -0.007373 |
| **matched-count random control** | 34,284 | **0.023781** | +0.000354 |

Two readings that must be kept apart:

* **Temperature is the wrong axis.** Going from every warm site to only the `>= 50 C` sites raises
  credit/dot from 0.0132 to 0.0158, and the quartz geothermometer (a *deeper, hotter* proxy) makes it
  *worse* (0.0117). If the physical hypothesis ("hot discharge marks an unmapped permeable
  structure") were simply noisy, a harder filter would sharpen it. It does the opposite.
* **Radius behaves monotonically, and the direction is informative.** At radius 1 px the arm reaches
  0.0209 — its best value, still 2.6x short — and *at the widest radius it gets worse* (0.0106). So
  the thermal layer's faint association with the detector's ridges is a *sub-pixel coincidence* that
  dissolves as you widen. Widening is exactly what a genuine geological control would strengthen.

## 3. Mechanism: the thermal layer cannot address the gap because it is co-located with what the detector already emits

The candidate pool was defined as `ridge AND active AND NOT base`, so this arm could only add dots the
existing emission had not already claimed. The measured failure is therefore specific and
interpretable:

* Great Basin hydrothermal discharge is overwhelmingly **basin-margin, fault-controlled** (that is why
  the catalogue has the faults it has, and why the blended detector already fires along those
  margins). The base emission has therefore *already spent its budget* on the structure those springs
  mark.
* What remains near a thermal site is **redundant neighbouring slop** — pixels adjacent to dots that
  already carry the credit. The instrument charges marginal credit, so redundant neighbours earn
  almost nothing (0.0132).
* The random control draws from candidates `> 6 px` from any thermal site. Those are *off-margin*
  candidates, and they earned **more** (0.0238). That is the whole result in one number: **on this
  grid, being adjacent to a mapped-margin hot spring is a mild negative indicator for the credit a
  new dot can still earn.**

## 4. What this does *not* prove (stated so the record is not over-read)

* LOSFO truth is **mapped** fault geometry held out by system. Its own module documentation and
  `registry/irregularities.json` (`proxy-blind-to-far-field`, severity **high**) say the protocol
  cannot represent expert-labelled faults absent from the catalogue. The claim "a concealed
  permeability structure with no scarp is marked by this spring" is therefore **untested** by this
  run — what is tested is the strictly weaker claim that such dots would also pay against mapped
  geometry, and they do not.
* Because LOSFO *is* an upper bound, failing it is decisive for the arm as constructed: a dot that
  cannot earn credit against the geometry we can see will not earn credit against geometry we cannot.
* The layer itself is not impugned. It is the **conjunction** (thermal site AND ridge AND not-base,
  used as an addition licence) that fails, and the failure has a clean mechanism (§3). The layer may
  still be useful for *stratified analysis* of the existing emission, which costs no budget.
* Independent irregularity, unchanged by this run: `data/gdr_wellspring_in_footprint.csv` carries
  `dist_known_fault_px`, a **catalogue-derived** column. The arm used an explicit allow-list
  (`src/gems27/thermal.py`) and never read it (`catalogue_derived_columns_used: []`,
  `excluded_columns: ["dist_known_fault_px"]`). Any future user of this table must do the same or the
  result is self-fulfilling.

## 5. Standing effect

* **Arm closed.** No candidate TIFF, no weekly slot, no confirmation decade, no retuning. Recorded,
  not salvaged.
* **The ADD-family prior is now worse than it was this morning.** H35-1 is the first addition arm to
  be *measured* end-to-end. Its result (0.0132 credit/dot, **below** its own random control and below
  the generic far-field rate of 0.0465 measured in `evidence/losfo_farfield_diagnostic.json`) is
  independent evidence for the same conclusion the reachability frontier reached from the pruning
  side: at this operating point, **new dots are not cheap**, and a layer must be *very* specific to
  beat `tau_live = 0.0548`.
* **Where the remaining probability mass sits.** The H34 operating point study says the profitable
  moves are removals with `e < 0.055` — all three archived pruning arms returned `live_verdict:
  PRUNE` (H32-1 flank shadow `e = 0.004`; H32-2 deep magnetic de-screening `e = 0.03435`; H27-4
  `d_cat <= 200 m` `e = 0.008`) — and the optimal packing rung is `3.0`, not `2.8`. That is where the
  next slot should come from, and it is a **better-supported** direction than any further addition
  arm. This result is the reason the follow-on arm this session is an *adjudication of the pruning
  ladder* (`knowledge/25_preregistration_H35-6_candidate_adjudication.md`) rather than another
  speculative physical layer.

## 6. Reproduce

```bash
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h35_1_thermal_farfield.py \
    --seeds 230-234 --out evidence/h35_1_thermal_farfield.json
```

A single throwaway seed (`240`) was used once for a pipeline smoke test before the frozen run and is
disclosed in §5 of the preregistration; it is outside every reserved decade. Its measured credit/dot
(0.01736, control 0.02380) is directionally identical to the frozen result. The smoke output is
deliberately **not committed** — `evidence/_scratch/` is gitignored so that intermediate run artifacts
never enter the repository — and its numbers are reproduced here so the disclosure survives without
the file. The frozen five-seed result above is the only evidence this arm rests on.
