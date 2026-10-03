# Session 14 (2026-10-03) — H38 candidate set: five ranked arms, one gated this session

Status: written **before** H38-2…H38-5 spends a seed. H38-1 is preregistered separately in
`knowledge/38_preregistration_H38-1.md` and gated this session on the fresh hypothesis-gate decade
`260–269`. The LOSFO measurement in `evidence/losfo_cover_probe.json` uses a **separate LOSFO decade
(215–219)**, the convention established by `knowledge/32` §2 ("the harness's dedicated LOSFO decade …
consumes no hypothesis-gate decade"); no hypothesis gate may later be run on `215–219`.

> **Renumbering note (2026-10-03, merge with `main`).** This session's files were renumbered after a "
> parallel session merged `knowledge/36_session13_closeout.md`: Session-14 hypotheses = `knowledge/37`,
> H38-1 preregistration = `knowledge/38`, far-field attribution = `knowledge/39`, H38-1 far-field
> preregistration = `knowledge/40`, H38-1 gate result = `knowledge/41`, H38-1 far-field result =
> `knowledge/42`. The `evidence/*.json` records written before the renumber keep the original path
> strings inside their provenance fields (`knowledge/36_...` → `knowledge/37_...` etc.); the records
> themselves are intentionally unmodified.

## 0. What changed the ranking rule this session

`knowledge/33` (merged from `main`) falsified the transfer of the H37-1 packing gain: interleaved
`+0.007289`, far field `−0.000037 ± 0.000832` (LOSFO, 9/20 cells). The operative conclusion is in
`knowledge/33` §3: *the detector field, not the packer, is the limiting factor*, and honest far-field
credit/dot (`0.0465`) is below the live break-even (`τ = 0.054852`).

Ranking rule for this session, in priority order:

1. **New information outranks new processing of the same information.** Every processing arm in this
   repository (H34 rung, H36-1 re-pack, H37-1 packing, H31-1/H32-1/H28-1 derived features) manipulates
   the same 32 bands or the same catalogue-trained field; the one far-field measurement of a processing
   gain came back zero.
2. **Local, hash-pinned data outranks bridge-gated data**, because only the former can be validated in
   this sandbox today.
3. Cost is the tiebreak.

## 1. The H38 set

| Rank | ID | Class | Expected ΔDTI | Cost | Data gate (checked this session) |
|---:|---|---|---|---|---|
| 1 | **H38-1** radiometric alteration information recovery | FEATURES (new physics) | `+0.000…+0.004` | low | **local, hash-pinned** (`geodawn_rad`, `geodawn_extensions`) — gated this session |
| 2 | **H38-3** joint magnetic ∧ gravity Euler SI-0 depth concordance | LICENCE (ADD), carries H37-3 forward | `+0.000…+0.006` | medium | local (`tmi` + `iso_grav_anom` + `src/gems27/euler.py`) |
| 3 | **H38-2** depth-sliced magnetic lineaments under cover (upward continuation ≥ 1 km) | FEATURES (new transform) | `+0.000…+0.008` | medium | local (`tmi`, `rtp`, `depth_to_base_surf`, `lidar relief`) |
| 4 | **H38-4** lineament-support licence from the detector field | EMISSION (object-level) | `−0.001…+0.003` | low-medium | local (no new layer) |
| 5 | **H38-5** microseismicity lineaments from the ANSS/ComCat catalogue | FEATURES (external ADD) | unknown, potentially large | high | **bridge-gated**: `earthquake.usgs.gov` returns HTTP `000` in-sandbox; the Actions runner has general internet (`fetch-vector-faults` precedent) |

---

## H38-1 — Radiometric alteration information recovery (K, Th, U and the Th/K, U/K, U/Th ratios)

* **Layers.** `data/geodawn_rad_u8.tif` bands K, Th, U (and TC, excluded here as redundant — see
  below); `data/geodawn_extensions_u8.tif` bands `ThK`, `UK`, `UTh`. Six channels are injected:
  K, Th, U, ThK, UK, UTh. `TMI_up150` is **excluded** because it is rank-identical to the in-stack
  `tmi` band (Spearman `+0.984`, measured this session); `rad_TC` is **excluded** because it is the
  competition's own band 6 (`tc`) under another name.
* **Verified provenance (this session, from the bytes on disk).**
  - GeoDAWN is a **USGS + DOE Geothermal Technologies Office** airborne magnetic and radiometric
    survey of the northwestern Great Basin (EDCON-PRJ contractor, 2021–2022), distributed free and
    publicly by the GDR: <https://gdr.openei.org/submissions/1591>; conference description:
    <https://pubs.usgs.gov/publication/70261199>.
  - The competition's own feature mirror is named `gems-geodawn-numerical-features.tif`
    (`data/manifest.json`), i.e. the competition stack **is** the GeoDAWN numerical-feature product;
    the radiometric ratio/upward-continued grids are the same contractor family, not a third-party
    interpolation.
* **The measurement that makes this a *recovery*, not an addition.** `training_features.tif` band 6
  (`tc - Tilt angle or total curvature ... magnetic field derivative for edge detection`) is
  **rank-identical to GeoDAWN radiometric total count**: Spearman `+1.000` over the `5,164,300`
  in-footprint cells where both are finite. `scripts/prepare_data.py` currently **excludes** band 6
  (irregularity `tc-band-mislabelled`) from the 32-band matrix, so the detector is denied the one
  radiometric channel the organisers shipped and is given no radiometric information at all. Because
  total count is only a lossy combination of K, U and Th, injecting the three channels and the three
  standard ratios is strictly more informative than restoring band 6 alone.
* **Physical signature.** Potassic (sericite/illite/clay) alteration and uranium enrichment along
  permeable damage zones: the standard *K/eTh* and *U/eTh* radiometric ratios. Reference literature
  (peer-reviewed, page-checked this session): Shives et al. and Gnojek & Prichystal as summarised in
  <https://www.nature.com/articles/s41598-024-52912-9> ("low (eTh/K%) ratios are good indicators of
  hydrothermally altered zones"), and <https://www.sciencedirect.com/science/article/abs/pii/S0969804322003967>
  (K enrichment, F-parameter and Th-normalised K/eU anomalies over hydrothermalised zones). USGS's own
  survey description records that GeoDAWN potassium concentrations correlate with mapped geologic
  boundaries and reveal variation *within* units mapped as one (<https://publications.mygeoenergynow.org/grc/1034804.pdf>,
  Fig. 9 caption).
* **Why it should catch a fault missing from the catalogue rather than one already in it.** Alteration
  haloes persist after a surface rupture is degraded, buried or destroyed; they mark the fluid pathway,
  not the scarp. The catalogue is a surface-rupture compilation, so a buried, alteration-marked
  conduit is exactly the population it omits.
* **How it differs from everything already implemented.** No arm in this repository uses any
  radiometric channel; the 32-band matrix contains none. H28-1 (potential-field edges) and H31-1
  (Euler rasters) injected features *derived from bands already in the matrix* and both failed their
  frozen screens (`−0.001570`, `−0.001947`); H35-1 used a point process (springs) and was refuted at
  `0.0132` credit/dot against `τ = 0.0549`. This arm injects **new physical measurements** that cannot
  be derived from any existing band.
* **Honest prior, stated before the run.** Univariate rank AUC of every candidate band against
  catalogue pixels is weak and mostly *negative*: K `0.440`, Th `0.451`, U `0.477`, TC `0.448`,
  ThK `0.485`, UK `0.536`, UTh `0.541`, and near-fault corridor (0–600 m) vs far (>1200 m) gives the
  same ordering (UTh `0.5485`, UK `0.5362`). So the *a priori* expectation is small; the arm's value is
  that it is a decisive, cheap test of the one class the repository has never tested.
* **Gate.** `knowledge/38_preregistration_H38-1.md`, runner `scripts/run_h38_1_holdout.py`, fresh decade
  `260–269`.

## H38-3 — Joint magnetic ∧ gravity Euler SI-0 depth concordance (carries H37-3 forward)

* **Layers.** `tmi` (band 14) and `iso_grav_anom` (band 13), each with self-consistent derivatives via
  `src/gems27/euler.magnetic_derivatives`; the retained SI-0 clusters from
  `evidence/h31_1_euler_clusters.csv` (6,309 clusters; depth median `296 m`, P10 `155 m`, P90 `614 m`).
* **Physical signature.** A *depth-labelled* structural assertion that two independent potential
  fields make at the same place and the same depth. Reid et al. (1990, DOI `10.1190/1.1442774`) is the
  method; the discriminating statistic is within-cluster agreement in (x, y, z), not edge amplitude.
* **Why off-catalogue.** A buried contact with no Quaternary scarp still produces SI-0 solutions; the
  catalogue records traces, not contacts.
* **Difference from the repo.** Every Euler product here is `tmi`-only; H31-1 injected Euler rasters
  into a 41-band GBDT (failed its screen); H32-1 used the `tmi` clusters **defensively** as a
  protection gate during pruning. No arm has ever used Euler depth as a **positive** licence, and none
  has required two fields to agree — which is the prompt's own "two unrelated methods agreeing"
  criterion applied inside a single arm.
* **Risk.** Depth-band units in the magnetic versus gravity fields are not interchangeable
  (`euler-magnetic-units-depth-band-unresolved` is an open high-severity irregularity); the arm must
  therefore calibrate each field's depth scale separately before concordance is meaningful.

## H38-2 — Depth-sliced magnetic lineaments under cover (upward continuation ≥ 1 km)

* **Layers.** `tmi` (14), `rtp` (2), `depth_to_base_surf` (15), `lidar relief` (8) and `coh100` (9).
* **Physical signature.** Upward continuation to 1–3 km suppresses sources shallower than the
  continuation height; curvilinear maxima of the *horizontal gradient of the continued field* mark
  basement/contact structure. Conditioning on thick cover (high `depth_to_base_surf`, low LiDAR relief
  and coherence) selects the population a surface-rupture map cannot contain.
* **Why off-catalogue.** A fault buried under basin fill has, by definition, no surface expression.
* **Difference from the repo.** The stack contains `TMI_up150` (a 150 m continuation, rank `+0.984`
  with `tmi`, measured this session) — too shallow to separate basin-fill structure and
  informationally equivalent to a band already present. No arm computes a deeper continuation, and no
  arm conditions potential-field lineaments on cover thickness.
* **Cost/risk.** FFT continuation on an irregular footprint needs NaN-safe padding and an edge
  taper; the transform must be validated against an analytic continuation before use.

## H38-4 — Lineament-support licence from the detector field (object-level emission)

* **Layers.** None new: the detector probability field and its NMS ridge mask
  (`oof_detector.ridge_nms`), plus `lidar strike` for orientation.
* **Physical signature.** Curvilinear continuity. A dot is licensed only where the probability field
  has coherent linear support over an extended segment (structure-tensor anisotropy / local Hough
  support), i.e. where the field looks like a *trace* rather than a blob.
* **Why it can help off-catalogue.** It cannot add physics; it converts per-pixel evidence into the
  object class the catalogue actually contains, and suppresses isolated detector maxima at imaged
  edges and junctions that carry no trace.
* **Difference from the repo.** H37-1 packs dots for coverage but never models linearity; H32-1's
  structural-step features are per-pixel derivatives on terrain. No arm in the repository uses a
  line-support operator, and none has been tested far-field except by H37-1 (which failed).
* **Risk.** Direct evidence from `knowledge/33`: far-field credit/dot at this operating point is below
  break-even, so a re-weighting of the same field must first raise *which* dots are chosen, not merely
  re-order them.

## H38-5 — Microseismicity lineaments from the ANSS/ComCat catalogue (external)

* **Layers.** USGS/ANSS Comprehensive Earthquake Catalog (ComCat) hypocentres, projected to the
  100 m grid, declustered; the in-stack `deq_n100a15` / `ieq_n100a15` bands are 100 km-radius kernel
  products and cannot resolve a 5–10 km lineament.
* **Physical signature.** Alignment of relocated small-magnitude hypocentres along a planar trend
  within the seismogenic layer — active structure that may never have ruptured to the surface.
* **Why off-catalogue.** A fault can be seismically active and still unmapped if it has no
  geomorphic expression; the catalogue is a surface-rupture map.
* **Difference from the repo.** No arm uses seismicity beyond the two coarse in-stack kernel bands;
  H31-1/H32-1 fed derivatives of the *terrain* and *magnetics*.
* **Data gate — named and checked.** USGS FDSN event service (`https://earthquake.usgs.gov/fdsnws/event/1/`):
  free, public domain, no authentication (verified: "The USGS Earthquake Catalog API … No
  authentication required", `https://earthquake.usgs.gov/fdsnws/event/1/`). **However**, the host is
  unreachable from this sandbox (`HTTP 000`), so the arm can only be run through the repository's
  GitHub Actions bridge, following the `fetch-vector-faults` precedent (NBMG ArcGIS REST, runner-side).
  It is therefore ranked last despite the largest potential information gain: it is the only H38 arm
  that cannot be validated in this session.

---

## 2. What is validated in this session

* **H38-1** is gated on the spatially-blocked interleaved holdout, fresh decade `260–269`
  (`knowledge/38`, `scripts/run_h38_1_holdout.py`, `evidence/h38_1_holdout.json`).
* **The dose/layout far-field question** raised by `knowledge/33` §3 ("the dose axis is deliberately
  not re-run here") is measured in `evidence/losfo_cover_probe.json` on LOSFO decade `215–219`:
  raster-order thinning at `d=2.8` and `d=3.0`, greedy maximum coverage at the same emitted count as
  `d=3.0`, and the 1.5× dose — four arms, identical truth, paired cells.
* No weekly submission slot is used by either measurement. A slot may only be considered for an arm
  that has passed its frozen gate **and** been measured far-field, per the rule `knowledge/32` applied.

## 8. Addendum after the runs (2026-10-03, end of session) — statuses, not new claims

* **H38-1** was gated on **seeds 280–289**, not 260–269: two harness errata voided the first two
  decades (`knowledge/38` §§7–8, both disclosed before their re-run). The gate passed
  (`evidence/h38_1_holdout.json`, G1 `+0.002869`, 9/10 seeds, 4/4 folds) and the far-field transfer test
  (seeds 220–224) did **not** license a file: `+0.000959 ± 0.004469`, 2/5 seeds, 4/20 cells below
  `−0.005` (`knowledge/42`). Status: **interleaved pass, far-field unresolved, no artifact.**
* **Ranking update.** The twice-replicated far-field gain of the **all-ridge coverage packing
  construction with the frozen D0 detector** (`+0.005275` on 215–219 and `+0.005881`, 5/5 seeds, 4/4
  folds on 220–224) makes that construction the top-ranked unshipped arm; it still needs its own frozen
  interleaved gate and a pre-declared ≥ 10-seed far-field decade. H38-1's radiometric information sits
  second, pending a properly powered far-field decade. H38-4/H38-3/H38-2/H38-5 are unchanged in order
  and remain unfrozen; H38-3 is still blocked by the Euler depth-unit irregularity and H38-5 by the
  sandbox's inability to reach `earthquake.usgs.gov` (the Actions bridge is the only route).
* `registry/next_hypotheses.json:session14_addendum` carries the same ranking with the seed ledger.
