# Session 10 — the reachability frontier, a far-field harness, and the re-ranked strategy

Generated 2026-10-03. Every number below is reproducible from a committed script and an evidence
file named in the same sentence. Scores remain owner-reported / public-leaderboard readings, never
organizer receipts.

---

## 1. What beating 0.3195 actually costs, in pixels

`scripts/reachability_frontier.py` → `evidence/reachability_frontier.json`.

The official metric (DrivenData #306 problem page; `src/gems27/metric.py`) is
`DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw)`. Writing `FPw = N − MPw` and `ρ = MPw/TPw` gives the
equivalent closed form used by the inversion. **That equivalence is checked numerically, not
assumed**: `verify_identity()` rebuilds 23 truth/prediction grids (empty truth, empty prediction,
prediction ≡ truth, single coincident dot, 1-D traces with stray false positives) and compares the
closed form against `metric.dti_binary`. Max absolute residual **2.22e-16**, and the substitution
`FPw = N − MPw` holds in every case. `tests/test_reachability_frontier.py` then re-derives every
reported requirement by substituting it back into the identity.

At the calibrated truth size |G| = 12,226 px (blind-lattice calibration, `evidence/live_inversion.json`):

| Emitted px `N` | credit needed for 0.2600 | for 0.2701 | for **0.3195** |
|---:|---:|---:|---:|
| 40,199 (tertiary) | 4,633 | 4,813 | 5,694 |
| **44,090 (0.2600 file)** | 4,836 | 5,024 | **5,942** |
| 60,069 (0.2477 file) | 5,667 | 5,887 | 6,963 |

The best owner-anchored submission earns **4,791 px of credit (39.2 % of |G|)** at `N = 44,090`.

> **The gap to 0.3195 at the current budget is +1,151 px of credit — 24.0 % more credit than the
> whole 0.2600 submission captures, and 9.42 points of |G|.**

### Why budget reallocation cannot close it

Holding credit per dot fixed at the current average efficiency `e = 4,791/44,090 = 0.1087`, DTI tends
to `e/0.2 = 0.5433` as `N → ∞`, and 0.3195 would be reached at `N ≈ 69,800` px. That looks reachable —
but it uses the *average* efficiency, and the *marginal* efficiency is what governs whether the next
dot helps. The programme has one exactly-controlled live measurement of it: thinning the same ridge
from `d = 1.5` (60,069 px, 0.2477) to `d = 2.8` (44,090 px, 0.2600) removed **15,979 dots and lost
495.08 px of credit**, i.e. a marginal efficiency of **0.03098 credit/px** — below the break-even
`0.2·DTI/(1−0.2·DTI) = 0.05485` at 0.2600 (which is precisely why removing them raised the score).
A dot earning 0.03098 does not clear the 0.2·target charge at any target ≥ 0.155, so **no quantity of
dots at the current marginal efficiency can reach 0.3195.**

The actionable form — how many *new* dots are needed, by the credit each one earns
(`ΔN = (C_req − TP₀) / (e − 0.2·target)`, at `TP₀ = 4,791`, `N₀ = 44,090`):

| marginal credit per new dot `e` | new dots needed for 0.3195 |
|---:|---:|
| 0.10 (our current *average*) | 31,890 |
| 0.20 | 8,459 |
| 0.30 | 4,876 |
| **0.40** | **3,425** |
| 0.50 | 2,640 |
| 0.75 | 1,678 |

**Conclusion (recorded in `evidence/reachability_frontier.json.conclusions`): the gap is a detection
gap, not a budget gap.** Roughly **2,600–3,400 dots that land on genuinely unmapped fault traces**,
each earning ~0.4–0.5 credit, would reach 0.3195. Every arm this repository has run — including
H33-1 as preregistered — is a *pruning* arm worth ~0.001–0.010. Pruning arms should still be taken
(they are free and compose), but they are not the path.

---

## 2. The blocker that made addition arms unvalidatable, and its removal

`evidence/arm_habitat_decomposition.json` (Session 4) established that the standing holdout hides
catalogue components **interleaved** with the known catalogue, so **100 % of its hidden truth lies at
distance 0 from the full published catalogue** (`habitat_A` truth = 0 of 120,983 px). Since
`scripts/verify_downloads.py` requires zero pixels on catalogue cells, a shippable file can only
occupy habitat A — which contains no truth in that protocol. **The harness structurally cannot
validate an arm that proposes dots where nothing is catalogued**, i.e. exactly the class that §1 says
is required.

Session 10 added `src/gems27/losfo.py` and `scripts/run_losfo_harness.py` →
`evidence/losfo_farfield_diagnostic.json` (5 seeds × 4 folds, 20 paired cells, 757 s):

* 60,988 catalogue px are grouped into **758 fault systems** (8-connected components of the catalogue
  dilated 300 m, so en-echelon segments of one structure are held out together).
* **190 systems / 13,156 px** are held out per seed, quadrant-blocked.
* A **600 m buffer around every held-out system is erased from the training labels**, so the truth is
  **≥ 8 px (800 m) from every pixel the detector saw as positive** (measured: minimum 8.0 px, median
  33.6 px = 3.4 km). 90.0 % of emitted dots are ≥ 300 m from any known pixel.

**Result — the same held-out systems scored under a masked-label detector and an unmasked control:**

| arm | mean DTI | pooled DTI | credit TPw | recall_w | credit/dot |
|---|---:|---:|---:|---:|---:|
| `losfo` (600 m buffer erased) | 0.09974 | 0.10025 | 11,160.6 | 0.1439 | 0.0465 |
| `leaky` (unmasked control) | 0.10155 | 0.10060 | 11,291.3 | 0.1456 | 0.0462 |

Pooled ratio `losfo/leaky` = **0.9884** (credit), **0.9822** (DTI).

**Read this carefully, because the aggregate is not the whole story.** Per fold the ratio is
NW 0.892, NE 0.876, SW 1.204, SE 0.988 — a spread of −12 % to +20 %. So the honest statement is:

> **No large catalogue-interpolation inflation was detected** (the base arm keeps ~99 % of its
> far-field credit when 600 m of surrounding catalogue is hidden), **but with 5 seeds this harness
> cannot resolve effects smaller than roughly ±12 % per fold.** The aggregate 0.9884 is a bound, not
> a measurement of a small effect.

Two confounds are recorded rather than smoothed over: (i) the masked arm also has 21.6 % fewer
positive training pixels (47,832 vs 60,988), so class-balance differs as well as context; (ii)
held-out systems are still *mapped* faults, so their geophysical expression is detectable by
selection — this harness measures an **upper bound** on performance against genuinely unmapped
faults, not an estimate of it.

What is solidly gained: **the repository now has a far-field truth set on which addition arms can be
gated**, with a measured base-arm far-field operating point (recall_w 0.1439, credit/dot 0.0465, mean
12,001 dots/cell) to beat. `tests/test_losfo.py` guards the no-leakage invariant, including a
`scipy.ndimage.binary_dilation(iterations=0)` trap that returns an **all-True** array and would have
silently merged all 758 systems into one.

---

## 3. Re-ranked H33 series (supersedes the ranking in `knowledge/18`)

The ranking rule changed: **an arm that can only prune cannot reach the target, so addition arms are
ranked above pruning arms regardless of their individual expected ΔDTI.**

| Rank | ID | Class | Ceiling | Cost | Status |
|---:|---|---|---|---|---|
| 1 | **H33-3** heat-flow residual × 2 m probe thermal conjunction | **ADD** | can add credit | Medium (124 MB zip + probes already byte-verified) | Data gate OPEN (`sb_heat_flow_zip`, 130,154,244 B, `e7fd62c6…`); needs a derived clip like H33-1 |
| 2 | **H33-4** drainage-network neotectonics from 1 m DEMs | **ADD** | can add credit | High (GB-scale tiles + hydro toolchain) | Scope the tile footprint first; free official source (competition `dem_links.json` → USGS 3DEP) |
| 3 | **H33-5** Phase-2 discovery budget | **ADD** (bounded) | Phase-2 optionality, costs Phase-1 | Low | The only arm aimed at the Phase-2 rescoring rule; deliberately contrarian |
| 4 | **H33-1** kinematic reactivation favourability gate | PRUNE | +0.0005…+0.0030 | Medium | Preregistered (`knowledge/19`); data bridge landed this session, **data not yet held locally** |
| 5 | **H33-2** multi-depth MT conductance alignment | PRUNE/score | +0.0000…+0.0022 | Medium-high | Both probed GeoTIFFs now pin-verified; needs derived clips |

### The three things worth doing next, in order

1. **Land the derived clips.** One merge touching `scripts/fetch_external_layers.py` triggers the
   bridge; H33-1's clip is already specified. Add H33-3's heat-flow point layer the same way.
2. **Gate the first ADD arm on LOSFO, not on the interleaved holdout.** The interleaved protocol has
   no far-field truth (§2), so an addition arm scored on it is uninterpretable. A frozen LOSFO gate
   should require the added dots' credit/dot to beat the base arm's measured far-field **0.0465** and
   the inclusion threshold at the cell DTI, in ≥ 3/4 folds and ≥ 8/10 seeds.
3. **Keep taking free pruning gains** (H33-1, H32-1 stack) while the addition arms are built — they
   are worth ~0.001–0.010 each and compose with anything that lands.

---

## 4. Standing caveats that apply to every number above

* **|G| = 12,226 px rests on one anchor** (the 13GEMSDOE blind lattice at 0.0904). `g_sensitivity_for_leader_target`
  in `evidence/reachability_frontier.json` reports the required-credit gap at |G| × {0.75, 0.9, 1.0,
  1.1, 1.25}; the qualitative conclusion (a detection gap, unreachable by pruning) holds across that
  range because it depends on the sign of `e_marginal − 0.2·target`, not on |G|.
* **Scores are not receipts.** 0.2600 / 0.2477 / 0.2449 / 0.3195 are owner-reported or public
  leaderboard readings; a leaderboard row does not link a score to a specific TIFF or to the owner.
* **`drivendata.org` is never contacted** by any script in this repository (competition Terms of Use).
  All competition rasters come from hash-pinned public owner mirrors and are labelled as
  non-organizer-authenticated.
* **The sandbox cannot reach the science hosts** — `sciencebase.gov`, `doi.org`, `api.datacite.org`,
  `drivendata.org` all returned HTTP 000 (curl exit 35) when re-checked this session; `api.github.com`
  and `pypi.org` returned 200. Every external-byte claim in this repository is therefore
  runner-recorded, and is labelled as such.
