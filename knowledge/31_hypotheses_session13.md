# Session 13 (2026-10-03) — H37 candidate set: five ranked arms, one already validated

Status: the ranking below was written **after** the H37-1 exploration and gate (both complete) and
**before** any of H37-2…H37-5 spends a seed. Seeds `250–259` are spent by H37-1; the next arm takes
`260–269`. Nothing here contacts DrivenData; no submission slot has been used.

Ranking rule (unchanged since Session 10): the gap to the leader is a **detection** gap
(`evidence/reachability_frontier.json`: reaching `0.3195` from the `0.2600` budget needs `+1,151 px` of
credit, `24 %` more than the whole submission captures), so *addition* arms outrank *pruning* arms, and
an arm that has never been measured is ranked below one that has. Cost is the second key.

| Rank | ID | Class | Measured / prior expected ΔDTI | Cost | Data gate (checked this session) |
|---:|---|---|---|---|---|
| 1 | **H37-1** metric-aware packing (VALIDATED) | EMISSION | **+0.007289** OOF vs `d=2.8`, **+0.004614** vs the H36-1 incumbent, 10/10 seeds, 4/4 folds | low (done) | local; shipped |
| 2 | **H37-3** Euler SI-0 depth-coherence as an emission licence | ADD | prior `+0.0005…+0.0100` (untested) | low | local (`evidence/h31_1_euler_clusters.csv`, 6,309 clusters) |
| 3 | **H37-2** concealed-fault conjunction (potential-field lineament × smooth, low-relief fill) | ADD | prior `+0.001…+0.008` on LOSFO; **cannot be tested on the interleaved proxy** | medium | local bands 1–19 + `lidar_scarf_features_u8.tif` |
| 4 | **H37-5** artifact-morphology suppression with reallocation | PRUNE→reallocate | prior `+0.000…+0.004` | low | local (descriptor bands 1–9) |
| 5 | **H37-4** offset geomorphic datum (pluvial shoreline / fan piercing lines) | ADD | prior `+0.001…+0.010` (highest novelty, highest variance) | high | **needs absolute elevation**: USGS 3DEP 1 m DEM tiles via `data/dem_links.json` (716 links) — free, official, public domain; obtainable through the GitHub Actions bridge (see §6) |

---

## H37-1 — metric-aware packing (**VALIDATED THIS SESSION**)

* **Layers.** None new. Candidate pool = the shipped H19-5 surface (121,131 px, catalogue-masked);
  weight field = the 32-band detector's fitted probability.
* **Signature.** Not a physical transform: a **coverage-optimal selection** of the existing candidate
  pixels under the official 300 m triangular kernel, i.e. the metric used as the packing objective.
* **Why it changes what is emitted off-catalogue.** It does not add geology; it stops discarding the
  best-covering candidates in favour of the lowest raster index. Measured: +4.58 % relative proxy DTI
  at a matched count, 10/10 seeds, 4/4 folds (`knowledge/30_h37_1_result.md`).
* **Difference from everything in the repo.** `dot_thin` (and every previous rung arm, H34/H36-1) is
  content-blind and was shown in H36-1 to be a *layout* rule worth ±0.0026. No previous arm read the
  detector's probability at selection time.

## H37-3 — Euler SI-0 depth-coherence as an **emission** licence (ADD)

* **Layers.** `tmi` (band 14) and its self-consistent derivatives (bands 3 `tmi_hg`, 9 `tmi_vg`);
  `evidence/h31_1_euler_clusters.csv` — the 6,309 retained SI = 0 depth-coherent clusters (depth
  median 296 m, P10 155 m, P90 614 m) from `src/gems27/euler.py`.
* **Physical signature.** A **depth-labelled structural assertion** per Reid et al. (1990,
  DOI `10.1190/1.1442774`, link for manual review): a cluster whose Euler solutions agree on location
  *and* depth within a tight tolerance is a contact-like source (SI = 0 → fault contact); one whose
  estimated depths scatter is an artefact of a window crossing several sources. The discriminating
  statistic is therefore the **within-cluster depth dispersion** and the median depth — not the edge
  amplitude, which is what every current layer already measures.
* **Why it should catch a fault missing from the catalogue rather than one already in it.** The
  catalogue is a *surface-rupture* compilation (rules PDF §2). A shallow magnetic contact that has no
  Quaternary scarp — buried under basin fill, or in a lithology with no surface expression — still
  produces SI-0 Euler solutions. The emission licence is: cluster present, depth shallow, candidate
  off-catalogue, and the base surface does not already emit there.
* **How it differs from everything already implemented.** H31-1 fed three Euler rasters into a 41-band
  GBDT and failed its screen (`−0.001947`); H32-1/H36-1 used the clusters **defensively** as a
  *protection* gate during pruning. No arm in this repository has used depth coherence as a **positive**
  licence to place dots. The prompt's Euler mandate is satisfied more directly by this arm than by the
  gate it currently serves.
* **Risk, stated in advance.** H35-1 (a point-process licence) failed at `0.0132` credit/dot against
  `τ_live = 0.0549`, and the base emission already fires along the magnetic ridges that host most
  catalogue faults. The expected value is low-to-moderate; the cost is low, which is why it is rank 2.

## H37-2 — concealed-fault conjunction: potential-field lineament × smooth, low-relief fill (ADD)

* **Layers.** Bands 1 `mag_anom`, 2 `rtp`, 13 `iso_grav_anom`, 15 `depth_to_base_surf`, 17 `cond_surf`;
  the LiDAR descriptor bands 3 `step_max`, 9 `relief`, 10 `coh100`.
* **Physical signature.** A **cross-field conjunction on a substrate that cannot express a scarp**: a
  magnetic/gravity-gradient/conductivity lineament whose surface expression is *absent by construction*
  (measured relief in the lowest tercile). The signature is the *absence* of terrain relief together
  with the *presence* of a subsurface lineament.
* **Why it should catch a fault missing from the catalogue rather than one already in it.** This
  session measured the emission's own terrain bias directly, and it is large: emitted dots have median
  LiDAR `relief` rank **60 / 255** against **32 / 255** for the footprint (10th–90th percentile:
  emitted `0–82`, footprint `0–96`). The shipped surface is therefore structurally blind to concealed
  faults in basin fill — the exact population a surface-rupture catalogue omits, and the target the DOE
  GEMS programme exists to find.
* **How it differs from everything already implemented.** Every arm in this repository starts from a
  **terrain** ridge (scarp/curvature/ridge crest) or from a process point; none starts from a
  potential-field lineament *conditioned on terrain smoothness*. H32-1's structural-step screen used
  `depth_to_base_surf` derivatives but as classifier features on the same terrain-ridge emission.
* **Honest limit, in advance.** The interleaved proxy cannot see this population (its truth is
  catalogue geometry at distance 0), so a proxy failure would **not** refute it and a proxy pass would
  not confirm it. It must be gated on LOSFO (§7) and its results reported as far-field only.

## H37-5 — artifact-morphology suppression with reallocation (PRUNE + reallocate)

* **Layers.** LiDAR descriptor bands 1 `ex_max`, 3 `step_max`, 8 `cross_max`, 9 `relief`, 10 `coh100`,
  11 `strike`; band 12 `det_elev`.
* **Physical signature.** Linear features with **impossible structural morphology**: near-constant
  width, near-constant strike over kilometres, no cross-cutting relationships, and (for
  infrastructure) a persistent radius-of-curvature that no fault trace sustains. Roads, canals,
  pipelines, fence lines, agricultural terracing and constructional pluvial-lake shoreline benches all
  produce one-pixel-scale linear relief that scarp detectors cannot separate from a fault scarp.
* **Why it should catch a fault missing from the catalogue rather than one already in it.** It does not
  catch one; it *frees budget*. The measured mechanism is the Session-10 frontier: at this operating
  point the marginal dot must clear `τ_live = 0.0548` credit per pixel. Every pixel spent on an
  artefact is a pixel not spent on structure, so a validated artefact class is worth its removal
  efficiency in *reallocated* dots — which is how the H27-4 flank prune paid (removed efficiency
  0.0098 ≪ τ).
* **How it differs from everything already implemented.** H27-4 pruned by **catalogue proximity**,
  H33-1 by **catalogue-attribute transfer** (kinematic favourability; refuted, `11.95 %` coverage
  ceiling), H32-1 by **structural-step features**, H36-1 by **packing geometry**. None used
  *morphology of the feature itself* as the discriminator.
* **Risk.** Four pruning arms have already failed (H31-1, H32-2, H33-1, H34); this one must beat the
  `τ_live` test on its removed class before it may be promoted, and even then it is bounded by the
  pruning ceiling.

## H37-4 — offset geomorphic datum (pluvial shoreline and fan-surface piercing lines) (ADD)

* **Layers.** Absolute elevation (see the data gate below) + descriptor bands 3 `step_max`, 4/5
  `lapneg_max`/`lappos_max`, 10 `coh100`; band 12 `det_elev` only as a *detrended* fallback.
* **Physical signature.** A **piercing-point offset**: a constructional datum that is planar over
  kilometres (a pluvial-lake shoreline bench or a fan surface) and that is demonstrably *offset* or
  warped across a line. This is the classic neotectonic measurement — the datum is the instrument, and
  the offset is the evidence — and it is not a derivative or curvature transform of the terrain.
* **Why it should catch a fault missing from the catalogue rather than one already in it.** A fault
  that offsets a young planar datum is active **by definition**, yet it may have no mappable scarp:
  the scarp can be destroyed by agriculture, burial, or bioturbation, and the offset survives. The
  catalogue records traces, not offsets.
* **How it differs from everything already implemented.** H19-5, H28-1, H28-2, H32-1 and H36-1 all
  emit from *ridges and edges of the terrain*. No arm tests *lateral continuity of a datum*, and none
  requires a datum at all.
* **Data gate — named and checked, as required.** Absolute elevation is **not** in the competition
  stack: band 12 is `det_elev`, i.e. *detrended* elevation (verified from the raster's own band
  descriptions this session), and the 12-band LiDAR descriptor raster carries only relative
  morphometry (`relief` is a 300 m-normalised local relief, not an elevation). The specific free,
  official source needed is the **USGS 3D Elevation Program (3DEP) 1 m bare-earth DEM tile
  collection**, which this repository already inventories as `data/dem_links.json` (716 tile links
  extracted from the organiser-supplied DEM link list; the descriptor raster was derived from 706 of
  them). Public domain. **Obtainability check performed this session:** `prd-tnm.s3.amazonaws.com`
  is unreachable from this sandbox (HTTP 000) but the repository's GitHub Actions runner fetches
  exactly this class of source — `gh run list` shows `fetch-gdr-external-layers` completing
  successfully on `main` (run `37156270805`, 2 m 11 s), so the bridge is operational and this data is
  obtainable without any manual step. Until a DEM tile clip is committed to `docs/data/`, this arm is
  **not runnable** and is ranked last.

---

## 6. Obtainability ledger for this session's data claims

| Claim | How it was checked | Result |
|---|---|---|
| Absolute elevation is absent from the competition stack | rasterio band descriptions of `data/training_features.tif` (19 bands) and `data/lidar_scarp_features_u8.tif` (12 bands), read this session | band 12 = `det_elev - Detrended elevation - topography with regional trends removed`; no absolute-elevation band in either file |
| 3DEP 1 m DEM tiles are inventoried and free/official | `data/dem_links.json` (716 links, hash-pinned in `registry/data_manifest.json`) + `knowledge/05_sources_and_verification.md` | present; USGS 3DEP is public domain |
| The Actions bridge can fetch official external layers autonomously | `gh run list` (this session) | `fetch-gdr-external-layers` success, 2 m 11 s, on `main` |
| The Euler cluster layer used by H37-3 exists locally | `evidence/h31_1_euler_clusters.csv` (committed) and `src/gems27/euler.py` | present, 6,309 clusters |
| GDR 1391 paleo-geothermal layers (H37-4 alternative) are free/official | `registry/sources.json`, `registry/external_pins.json`, bridge workflow | listed and pinned, but no committed paleo clip — arm not runnable yet |

## 7. The one measurement that outranks all four geological arms

**LOSFO far-field re-run of H37-1.** The four arms above are hypotheses; the H37-1 result is a
measurement with a 4.6e-3 margin and one unresolved alternative explanation (proxy preference for a
coverage objective aimed at a catalogue-trained field). `scripts/run_losfo_harness.py` is the only
instrument in this repository whose truth is ≥ 800 m from anything the detector saw (600 m buffer
erased around every held-out fault system). Extending it by one variant is the highest-value next
action, and it is cheap: the committed harness runs 5 seeds × 4 folds in ~13 minutes.

Stop rules for the numbers above: no arm may be retuned against the seeds that refuted it; any
addition arm must clear `τ_live` on LOSFO *and* on the interleaved proxy before a slot is considered;
the interleaved proxy alone can never promote an arm whose target population it cannot see.
