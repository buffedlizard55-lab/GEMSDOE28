# GEMSDOE28 — Fault Mapping for the Great Basin (`DrivenData #306`)

## Standing Prompt & Arena AI Core Values (Read First Every Session)

- **Core Value 1 — Maximize P(Win):** Prioritize the highest-leverage geological and mathematical actions that measurably increase expected Distance-Tolerant IoU (DTI) on the hidden test set; never spend a weekly submission slot on an idea that has not beaten the current holdout best on a spatially-blocked holdout set.
- **Core Value 2 — Own the Outcome:** Work autonomously end-to-end with zero manual input required, verify every claim line by line from official verified trusted sources with links for manual review, flag any irregularities in `registry/irregularities.json`, and run three full verification passes (Pass 1, Pass 2, Pass 3) before opening and merging a pull request onto `main`.

### Verbatim Task Prompt (Session 13, 2026-10-03 — read first every session)

> **Read this first, every session.** It is the owner's standing brief, reproduced word-for-word at the
> top of the repository so that every session starts from the same base instead of re-deriving it.
>
> **Euler deconvolution for depth, not just location.** Gradient and tilt-derivative features mark where
> a potential-field anomaly changes, but not how deep the source sits — and depth is exactly what a
> geologist uses to judge whether a lineament is a shallow dike, a buried contact, or a fault plane.
> Euler deconvolution (Reid, Allsop, Granser, Millett, and Somerton, *Geophysics*, 1990) solves Euler's
> homogeneity equation across a moving window of the field and its gradients to jointly estimate a
> source's location and depth, and the original paper validates it on real, structurally complex terrain,
> reporting that it yields "depth-labeled Euler trends which mark magnetic edges, notably faults, with
> good precision." Run it with the structural index appropriate to a fault contact, cluster the resulting
> depth-labeled solutions, and treat a cluster with shallow estimated depth aligned to a candidate
> lineament as corroboration distinct from a gradient peak alone — two unrelated methods agreeing there is
> both an edge and a shallow source at the same place is stronger evidence than either one, and it's a
> concrete detail a Phase 2 reviewer can actually evaluate.
>
> **Why and how did `dotted-h19-5-d2-8` (`GEMSDOE25`) get the highest score, and can we generate a
> submission that scores higher than `0.26`?** Answer with PhD-level experience, knowledge, and
> judgement. The official public leaderboard lists **`0.3195` at #1**, so design a strategy that can
> exceed `0.3195`.
>
> **Generate 3–5 candidate geological hypotheses we have not tried yet**, each naming the specific
> layer(s) involved, the physical signature being targeted, why it should catch a fault *missing* from
> the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already
> implemented in this repo. Rank them by expected DTI improvement and implementation cost. **Validate the
> top candidate on the spatially-blocked holdout set before touching a weekly submission slot** — do not
> spend a submission slot on an idea that has not beaten the current holdout best. If a candidate cannot
> be validated without new external data, name the specific free, official source needed and check that
> it is obtainable before proposing the idea as viable.
>
> **Deep research mandate.** Study, analyse and understand the science of geothermal-vent and fault
> discovery; store everything gathered from official verified sources as a starting point for other
> projects. Be contrarian but grounded; find sources of data and angles others are overlooking.
>
> **Submission mechanics, verbatim from the owner.** "There should be an easy to download submission tif
> file as described by the prompt… The site should be able to generate a TIF file that is required for
> submission. It should be as easy as download to click a File to submit into the competition. This needs
> to be in the executive summary or the very beginning of the site. It should be obvious when you visit
> the site." A past upload returned **"Predicted values must be in range [0, 1]"**; submissions need a
> unique name and a short note (≤ 200 characters). Create an executive-summary subpage that explains
> exactly how to make a submission into the contest. The project must also "solve the problem of having
> to manually check everything ourselves and having an up to date current feed."
>
> **Process (verbatim, unchanged).** Work line by line verifying from official verified trusted sources,
> provide links for manual review; there should be no manual input — work autonomously to complete tasks;
> flag any irregularities for review; no hallucinations; verify no hallucinations. Run three passes
> (Pass 1 implement and verify; Pass 2 review for bugs, missing requirements, wrong assumptions and edge
> cases, and fix; Pass 3 re-check the entire implementation against the original request and improve
> accuracy, reliability, completeness and code quality). Then create a pull request and merge it onto
> `main`, with suggestions for what still needs to be done and any limitations in the way of success.
>
> **Arena AI Core Values (focal points for every decision).** **Maximize P(Win)** — in every decision
> weigh tradeoffs, assess risk, and choose the path that maximises the probability of winning; set aside
> emotions. **Own the Outcome** — own results end to end, not just one slice; when problems arise and we
> have the means to act, act without waiting for permission; treat failure and success as signals.
>
> **Legacy verbatim prompt (Session 9, kept for the audit trail — the scorecard it carries is the
> owner's own list and is reproduced in §2).**
> **Euler deconvolution for depth, not just location.** Gradient and tilt-derivative features mark where a potential-field anomaly changes, but not how deep the source sits. Euler deconvolution (Reid, Allsop, Granser, Millett, and Somerton, *Geophysics*, 1990, DOI `10.1190/1.1442774`) solves Euler's homogeneity equation across a moving window of the field and its gradients to jointly estimate a source's location and depth. Run it with the structural index appropriate to a fault contact, cluster the depth-labeled solutions, and treat a cluster with shallow estimated depth aligned to a candidate lineament as corroboration distinct from a gradient peak alone — two unrelated methods agreeing is stronger evidence than either one.
>
> **Scorecard (owner sites → reported live scores).** GEMSDOE `0.1563` · 6GEMSDOE `0.0286` · GEMSDOE3 nodes `0.1193` / discovery `0.0830` / ridge `0.1152` · GEMSDOE2 `0.1560` · GEMSDOE4 `0.0343` · 5GEMSDOE `0.1563` · 7GEMSDOE `0.1461` · 8GEMSDOE `0.1563` · GEMSDOE9 `0.0107` · 11GEMSDOE `0.0202` · 12GEMSDOE `0.1294` · 15GEMSDOE `0.0782` · 14GEMSDOE `0.0020` · 17GEMSDOE `0.0187` · 18GEMSDOE `0.0297` · 19GEMSDOE `0.1894`/`0.1922` · GEMSDOE10 `0.0461`/`0.0921`/`0.1280`/`0.1839` · 13GEMSDOE `0.0904` · 16GEMSDOE `0.1855`/`0.0976`/`0.0360` · GEMSDOE21 `0.1894` · 20GEMSDOE `0.1890`/`0.1859` · GEMSDOE22 `0.1002`/`0.0748` · GEMSDOE23 `0.1352` · GEMSDOE24 `0.2477` · **GEMSDOE25 `dotted-h19-5-d2-8` = `0.2600` (our best)** · GEMSDOE26 `0.1223` · GEMSDOE27 `0.2449` · 28–33GEMSDOE: no score yet.
>
> **Study the highest score.** Site `https://buffedlizard55-lab.github.io/GEMSDOE25/`, submission `dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600`. Why and how did it get the highest score, and can we generate a submission scoring higher than `0.26`? Answer with PhD-level experience, knowledge, and judgement. Official public leaderboard: `https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/` — `0.3195` is the current #1, so design a new strategy that can score higher than `0.3195`.
>
> **Generate 3–5 candidate geological hypotheses we haven't tried yet**, each naming: the specific layer(s) involved, the physical signature targeted, why it catches a fault missing from the USGS/INGENIOUS catalogue, and how it differs from anything already implemented here. Rank by expected DTI improvement and implementation cost. **Validate the top candidate on the spatially-blocked holdout set before touching a weekly submission slot** — never spend a slot on an idea that hasn't beaten the current holdout best. If a candidate needs new external data, name the specific free official source and check it's obtainable first.
>
> **Deep research mandate.** Research the science of geothermal-vent/fault discovery heavily; store all knowledge from official verified sources as a starting point for future projects. Be contrarian but grounded; find overlooked data sources and angles. Official anchors: competition `https://www.drivendata.org/competitions/306/competition-doe-gems/` · problem `…/page/967/` · about `…/page/968/` · data tab (login-walled) · reference solution `https://github.com/drivendataorg/gems-prize-reference-solution` · official rules `https://docs.nlr.gov/docs/fy26osti/96647.pdf` · GDR `https://gdr.openei.org/submissions/1391`.
>
> **Submission mechanics.** The site must make it easy to download the submission `.tif` — one-click, in the executive summary / very beginning of the site, obvious on arrival. A past upload failed with `"Predicted values must be in range [0, 1]"` — address it. Give each submission a unique name and a short note (≤ 200 chars) to tell submissions apart. Provide an executive-summary subpage explaining exactly how to submit. Single-band GeoTIFF (or zip of one), matching the submission format's CRS, shape, and geotransform, values in `[0, 1]`.
>
> **Known limitation.** No DrivenData auth → cannot auto-download `training_features.tif`, `labels.tif`, `sample_submission.tif`, `1m_DEM_links.csv` (login-walled). Workaround in use: hash-pinned public owner mirrors restored by `scripts/restore_data.py` (never contacts DrivenData). Find free, public, official, verified sources for any external data.
>
> **Process.** Work line by line verifying from official verified trusted sources with links for manual review; no manual input; flag irregularities in `registry/irregularities.json`; no hallucinations; verify no hallucinations. Run three passes (Pass 1 implement & verify; Pass 2 review for bugs/missing requirements/wrong assumptions/edge cases and fix; Pass 3 re-check against the original request and improve). Then create a pull request and merge it onto `main`, with suggestions for remaining work and limitations.
>
> **Arena AI Core Values (focal points for all building, developing, researching, suggesting, and implementing).**
> - **Maximize P(Win):** in every decision, weigh tradeoffs, assess risk, and choose the path that maximizes the probability of winning; set aside emotions; prioritize the project's success above all else.
> - **Own the Outcome:** own results end to end, not just our slice; when problems arise and we can act, act without waiting for permission; treat failure and success as signals and improve; stay accountable to the final outcome.

---

## 1. Executive Summary & One-Click Verified Submission GeoTIFFs (`docs/downloads/`)

All submission artifacts in `docs/downloads/` are verified by `scripts/verify_downloads.py` (**`217/217` checks PASS, `0` failures**, `evidence/submission_file_audit.json`; this adds nine checks for registered submission-name presence, uniqueness, and content-ID linkage to the previous 208-check inventory; Session 13's conservative alternative remains audited): single-band `float32`, exact template grid (`EPSG:32611`, `3730 × 3292`, `100 m` pixels, `5,167,373` inside-footprint cells), values strictly in `{0.0, 1.0} ⊂ [0, 1]` inside the footprint, zero internal `NaN`s, `NaN` outside the footprint (`-nan.tif`, with an `-allfinite.tif` fallback having `0.0` outside and no `NaN` anywhere), zero overlap with the `60,988` known catalogue pixels, content-addressed 12-hex ID, single-member `.zip`, and a registered note $\le 200$ characters.

| Slot | Filename (`docs/downloads/`) | Content ID | Emitted px | 4-Fold Spatial-CV Holdout | Hybrid Model vs `0.2600` Anchor | Registered Note ($\le 200$ chars) |
|---|---|---|---:|---|---:|---|
| **Primary (One-Click) — RESTORED 2026-10-03 by the pre-committed far-field rule** | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | `b531dae0a36f` | `37,660` | **`+0.002599` (`10/10` seeds, `4/4` folds) on fresh seeds `240–249`, replicated `+0.002675` on the independent decade `250–259`**; matched-`N` random-drop control `−0.001657` | `0.2717–0.2727` (live-anchored dose ladder) | `28GEMSDOE H36-1 rung3.0+r1 | …` |
| **Secondary — far-field falsification FAILED (F1)** | `gems28-h37-1-coverprob-h19-5-r1-20261003-0bbddf41eb6d-nan.tif` | `0bbddf41eb6d` | `37,447` | **`+0.007289` interleaved (`10/10` seeds, `4/4` folds; control `−0.044684`) but `−0.000037 ± 0.000832` far field (LOSFO seeds `210–214`, 9/20 cells)** — the interleaved gain is catalogue adjacency; projection withdrawn | withdrawn (was `0.278–0.286`) | `28GEMSDOE H37-1 cover+h19 | … | UNSCORED, not slot-approved` |
| **Tertiary** | `gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif` | `8acb75e1f2cc` | `40,199` | +0.001766 (`10/10` seeds, `4/4` folds) — replicated `+0.001761` on fresh seeds 235–239 (`5/5` seeds, `4/4` folds) | `0.2686` | `28GEMSDOE H27-4 d2.8 solo | ΔDTI +0.00177 (10/10 seeds 180-189) replicated +0.00176 on fresh 235-239 (5/5 seeds, 4/4 folds) | 0.2600 d2.8 base, no T-v2 | id 8acb75e1f2cc` |
| **Quaternary** | `gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif` | `31e35eee884e` | `42,294` | +0.001399 (`10/10` seeds, `4/4` folds) | `0.2669` | `28GEMSDOE H32-1 d2.8 pre | OOF ΔDTI +0.00140 (10/10 seeds, 4/4 folds, seeds 180-189) pre-thinning d2.8; no T-v2 | id 31e35eee884e | UNSCORED, not slot-approved` |
| **Conservative alternative (kept audited)** | `gems28-h32-1-tip-euler-dejitter-d2-8-20261003-c3aeda1d31a3-nan.tif` | `c3aeda1d31a3` | `41,656` | +0.001272 (`10/10` seeds, `4/4` folds) — conservative alternative: protects fault tips and shallow Euler depth clusters | `0.2663` | `28GEMSDOE H32-1 d2.8 post | OOF ΔDTI +0.00127 (10/10 seeds, 4/4 folds, seeds 180-189) on 0.2600 d2.8 base; no T-v2 | id c3aeda1d31a3 | UNSCORED, not slot-approved` |
| **Reference** | `gems27-h27-4-r1-pruned-d1-5-20261003-450eb6859636-nan.tif` | `450eb6859636` | `54,714` | `+0.0022` on `d=1.5` (seeds `130–139`, `4/4` folds) | `0.2598` (on `0.2477` `d=1.5`) | `28GEMSDOE H27-4 r1 reference | OOF DTI gain +0.0022 solo (4/4 folds); UNSCORED, unconfirmed | id 450eb6859636 | research only` |

**One-click route that does not depend on GitHub Pages.** GitHub Pages for this repository reports
`status: errored` (legacy build; see `registry/irregularities.json` → `github-pages-legacy-build-errored`),
and the sandbox token cannot change the Pages source (`403 Resource not accessible by integration`).
The primary file is therefore also reachable directly from the repository, which is a normal one-click
download for a browser:

```
https://github.com/buffedlizard55-lab/GEMSDOE28/raw/main/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif
```

Verify the SHA-256 `5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641` after
downloading. The site carries the same fallback link under the main download button.

---

## 2. PhD-Level Analysis of the `0.2600`, `0.2449`, and `0.1223` Live Scores

**Evidence boundary — do not conflate these numbers.** The `0.2600` (and other GEMSDOE-series) values are owner-reported score/file associations preserved in the owner-controlled repository corpus. Local SHA-256 checks authenticate the bytes present here, not the organizer's receipt, scoring, or account attribution; the `0.2600` inversion is therefore conditional on that reported association. `0.3195` is the repository's prior observation of a row on DrivenData's organizer-hosted public leaderboard, but it was not re-fetched for Session 14 and this checkout has no verified link from that row to an identity or submission artifact. It is an external benchmark observation, not proof that our `0.2600` submission is directly comparable or that any local file earned either score. All reverse-engineered credit values below depend on the stated truth-size/metric assumptions; local blocked-holdout DTI is research evidence, not an organizer score.

We restored the missing inversion scripts (`scripts/fetch_scored_corpus.py`, `scripts/invert_live_scores.py`, `scripts/optimize_budget.py`) and inverted all **24 SHA-256-authenticated scored submissions** (`evidence/scored_corpus.json`, `evidence/live_inversion.json`, `evidence/budget_optimum.json`, plus `evidence/why_026_won.json`) at the blind-lattice-calibrated truth size $|G| = 12{,}226\text{ px}$:

$$\text{DTI} = \frac{\text{TP}_w}{0.2\,\text{TP}_w(1 - \rho) + 0.2\,N + 0.8\,|G|}, \qquad \rho = \frac{\text{MP}_w}{\text{TP}_w}$$

| Submission | Repo | Content ID | Off-catalogue `N` (px) | Live Score | Crowding `ρ` | Implied `credit_TPw` (px) | Credit / `|G|` |
|---|---|---|---:|---:|---:|---:|---:|
| **`dotted-h19-5-d2-8`** | `GEMSDOE25` | `e56ea318af89` | `44,090` | **`0.2600`** | `1.179` | `4,791.05` | `0.3919` |
| **`dotted-h19-5-d1-5`** | `GEMSDOE24` | `989f59505db1` | `60,069` | **`0.2477`** | `1.429` | `5,286.13` | `0.4324` |
| **`topo-gap-closure-t-v2-on-d1-5`** | `GEMSDOE27` | `5512495c6bd1` | `61,328` | **`0.2449`** | `1.425` | `5,288.78` | `0.4326` |
| **`H20-5` (blend parent)** | `GEMSDOE20` | `85ef8fb66294` | `102,434` | **`0.2072`** | `2.186` | `6,030.72` | `0.4933` |
| **`h19-5` (solid ridge parent)** | `GEMSDOE19` | `c85ac61b088b` | `121,131` | **`0.1922`** | `2.460` | `6,188.80` | `0.5062` |
| **`dilcond-oof-v1`** | `GEMSDOE26` | `47629f496133` | `58,670` | **`0.1223`** | `1.132` | `2,606.25` | `0.2132` |

### 2.1 Why and how `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` scored `0.2600`
1. **Exact construction**: `dotted-h19-5-d2-8` (`data/dotted_h19_5_d2_8_nan.tif`, SHA-256 `91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8`) takes the 1-px ridge skeleton of the 6-expert scarp/geophysics blend `H19-5` (`121,131` off-catalogue pixels, live `0.1922`), zeroes the `60,988` known catalogue pixels, and applies priority-ordered Poisson-disk thinning (`dot_thin(min_dist=2.8)`), emitting **`44,090` binary pixels** (`0.8532%` of footprint) with minimum Euclidean spacing $\ge \sqrt{8} \approx 2.828\text{ px}$ ($283\text{ m}$).
2. **Why `d=2.8` jumped `+0.0123` over `d=1.5` (`0.2477` $\to$ `0.2600`) AND beat the 2D geometric model (`0.2550` $\to$ `0.2600`)**:
   - Under the official linear distance-decay kernel $k(d) = \max(0, 1 - d/300\text{ m})$, two dots spaced at $s \in [2.828, 3.0]\text{ px}$ along a 1D fault trace have their midpoint at $d = s/2 \in [1.414, 1.50]\text{ px}$, where every intermediate truth pixel still receives $k(d) \in [0.50, 0.529]$ credit via the $\max_{x \in S} k(\|g - x\|)$ operator.
   - Meanwhile, the false-positive denominator penalty $0.2\,\text{FP}_w$ is **additive** over all emitted pixels: thinning from `60,069` px (`d=1.5`) to `44,090` px (`d=2.8`) removes `15,979` redundant dots (`-26.60%` budget), cutting $0.2\,\Delta N = 3{,}195.8$ denominator units and reducing kernel crowding $\rho$ from `1.429` to `1.179`.
   - Crucially, the 2D isotropic uniform-truth retention formula (`evidence/budget_optimum.json`) predicted $c(d=2.8)/c(d=1.5) = 0.8896$ (`0.2550`), whereas the **measured live credit retention is $4{,}791.05 / 5{,}286.13 = 0.9063$ (`+1.88%` higher than 2D isotropic retention)**! Because hidden truth $G$ is a **1D curvilinear fault network colinear with the `H19-5` ridge crest**, 1D crest thinning at $d=2.8\text{ px}$ loses much less credit than 2D area-coverage geometry predicts.

### 2.2 Why `topo-gap-closure-t-v2-on-d1-5` (`5512495c6bd1`) scored `0.2449` (`-0.0028` vs `0.2477`)
- `5512495c6bd1` added `1,259` non-redundant straight-line `T-v2` gap-closure dots across `345` links (`1–4 km` gaps between published Qfaults tips) onto `d=1.5` (`60,069` $\to$ `61,328` px).
- Inverting `0.2449` vs `0.2477` reveals that `credit_TPw` rose by only **`+2.65 px`** (`5,286.13` $\to$ `5,288.78` px), an empirical marginal efficiency of **`0.00210` credit/dot — `23.5x` below the `0.0495` live break-even threshold**!
- **Why catalogue holdouts overstated `T-v2` by `100x`**: Hiding pieces of already-compiled NBMG polylines artificially severs continuous mapped traces (`230/345` `T-v2` links were same-FID sub-parts) and rewards straight-line interpolation across those artificial cuts. In reality, the hidden organizer test set $G$ consists of **newly mapped faults omitted from the compilation**, not un-digitised straight lines between existing Qfaults tips. Every previously built candidate in `GEMSDOE27`/`GEMSDOE28` that bundled `T-v2` (`1113fba5f6cb`, `23ad46a4d7ba`, `3ebd51534bb1`, `d466b251f309`) was paying `-0.0028` to `-0.0033` of pure false-positive drag.

### 2.3 Can we generate a submission that scores higher than `0.2600`?
- **Yes — to `~0.2665–0.2701` directly on the `0.2600` (`d=2.8`) base by removing `100 m` catalogue-flank digitisation shadow (`c3aeda1d31a3`, `31e35eee884e`, `8acb75e1f2cc`) without `T-v2` drag**:
  - In `dotted-h19-5-d2-8` (`44,090` px, `0.2600`), **`3,891` dots (`8.83%` of all emitted pixels)** sit at $d_{\text{cat}} = 1.0\text{ px}$ ($100\text{ m}$) immediately adjacent to masked known catalogue faults (`2,434` along interior segments with $d_{\text{end}} > 300\text{ m}$, $\text{cat\_nbrs} \ge 2$, $d_{\text{Euler}} > 300\text{ m}$; and `1,457` within $300\text{ m}$ of a catalogue tip or shallow Euler $N=0$ depth cluster).
  - Because `labels.tif` masks only the 1-px rasterised USGS trace while the true 1 m LiDAR scarp expression is offset by `100–400 m` (Hermant et al., 2025, Fig. 2 & Fig. 9B), `H19-5` fires heavily on the $100\text{ m}$ flank of known faults — pixels that are almost pure false-positive mass (`0.0040` credit/FP on mid-segment flank shadow vs `0.0549` break-even at `0.2600`).
  - Removing those `2,434` mid-segment flank-shadow pixels on `d=2.8` (`c3aeda1d31a3`, `41,656` px) passes all 4-fold spatially-blocked holdout gates (`+0.001272` mean ΔDTI, `10/10` seeds, `4/4` folds on seeds `180–189`) and projects to **`0.2665`** (`+0.0065` over `0.2600`), while pre-thinning de-jittering (`31e35eee884e`, `42,294` px, `+0.001399` mean ΔDTI) projects to **`0.2685`** and solo `H27-4` `r=1` on `d=2.8` (`8acb75e1f2cc`, `40,199` px, `+0.001766` mean ΔDTI) projects to **`0.2701`**.

---

## 3. Session 10 — The Reachability Frontier and a Far-Field Harness

Two new results, both reproducible from a committed script and an evidence file named in the same
sentence. Full write-up: `knowledge/20_strategy_after_reachability_frontier.md`.

### 3.1 What beating `0.3195` costs, in pixels of credit

`scripts/reachability_frontier.py` → `evidence/reachability_frontier.json`. The closed form
$\text{DTI} = \text{TP}_w / (0.2\,\text{TP}_w(1-\rho) + 0.2N + 0.8|G|)$ is **checked numerically against
`metric.dti_binary` on 23 synthetic grids before use** — max absolute residual `2.22e-16`, and the
substitution $\text{FP}_w = N - \text{MP}_w$ holds in every case.

| Emitted px $N$ | credit for `0.2600` | credit for `0.2701` | credit for **`0.3195`** |
|---:|---:|---:|---:|
| 40,199 (tertiary) | 4,633 | 4,813 | 5,694 |
| **44,090 (the `0.2600` file)** | 4,836 | 5,024 | **5,942** |
| 60,069 (the `0.2477` file) | 5,667 | 5,887 | 6,963 |

The best owner-anchored submission earns **4,791 px of credit (`39.2%` of $|G| = 12{,}226$ px)** at
$N = 44{,}090$.

> **The gap to `0.3195` at that budget is `+1,151` px of credit — `24.0%` more credit than the entire
> `0.2600` submission captures, `9.42` points of $|G|$.**

**Why budget reallocation cannot close it.** Holding credit/dot at the current *average* efficiency
(`0.1087`), DTI tends to `0.5433` as $N \to \infty$ and `0.3195` would arrive at $N \approx 69{,}800$ —
but the *marginal* efficiency governs whether the next dot helps, and the programme has one
exactly-controlled live measurement of it: thinning the same ridge from `d=1.5` (`60,069` px,
`0.2477`) to `d=2.8` (`44,090` px, `0.2600`) removed **`15,979` dots and lost `495.08` px of credit**,
i.e. **`0.03098` credit/px**, below the break-even `0.05485` at `0.2600`. A dot earning that little
never clears the `0.2·target` charge, so **no quantity of dots at the current marginal efficiency
reaches `0.3195`.** The actionable form:

| marginal credit per new dot $e$ | new dots needed for `0.3195` |
|---:|---:|
| `0.20` | `8,459` |
| `0.30` | `4,876` |
| **`0.40`** | **`3,425`** |
| `0.50` | `2,640` |

**Conclusion: the gap is a detection gap, not a budget gap.** ~`2,600–3,400` dots that land on
genuinely unmapped fault traces would reach `0.3195`. Every arm this repository has run — including
`H33-1` as preregistered — is a *pruning* arm worth `~0.001–0.010`. Those are still worth taking
(free, and they compose), but they are not the path.

### 3.2 A far-field holdout that can finally gate *addition* arms

`evidence/arm_habitat_decomposition.json` (Session 4) showed the standing holdout hides catalogue
components **interleaved** with the known catalogue, so **`100%` of its hidden truth lies at distance
`0` from the published catalogue** (habitat-A truth `= 0` of `120,983` px). Since
`scripts/verify_downloads.py` requires zero pixels on catalogue cells, that protocol contains no
truth in the only habitat a submission can occupy — **it cannot validate any arm that proposes dots
where nothing is catalogued**, which §3.1 says is the only class that can reach `0.3195`.

Session 10 added `src/gems27/losfo.py` + `scripts/run_losfo_harness.py` →
`evidence/losfo_farfield_diagnostic.json` (5 seeds × 4 folds, 20 paired cells, 757 s):

- `60,988` catalogue px grouped into **`758` fault systems** (8-connected components of the catalogue
  dilated `300 m`, so en-echelon segments of one structure are held out together);
- **`190` systems / `13,156` px** held out per seed, quadrant-blocked;
- a **`600 m` buffer around every held-out system erased from the training labels**, so truth is
  **`>= 800 m`** from every pixel the detector saw as positive (median `3.4 km`), and `90.0%` of
  emitted dots are `>= 300 m` from any known pixel.

| Arm | Mean DTI | Credit TPw | recall_w | Credit/dot |
|---|---:|---:|---:|---:|
| `losfo` (600 m buffer erased) | `0.09974` | `11,160.6` | `0.1439` | `0.0465` |
| `leaky` (unmasked control, same truth) | `0.10155` | `11,291.3` | `0.1456` | `0.0462` |

Pooled ratio `losfo/leaky` = **`0.9884`** (credit). **Read with its uncertainty:** per-fold credit
ratios are NW `0.892`, NE `0.876`, SW `1.204`, SE `0.988` — a spread of roughly `-12%` to `+20%` — so
with 5 seeds this harness **cannot resolve effects smaller than about `±12%` per fold**. The honest
statement is *"no large catalogue-interpolation inflation was detected"*, not *"the inflation is
1.2%"*. Two confounds are recorded rather than smoothed over: the masked arm also has `21.6%` fewer
positive training pixels (`47,832` vs `60,988`), and held-out systems are still *mapped* faults, so
this measures an **upper bound** on performance against genuinely unmapped faults.

What is solidly gained: **a far-field truth set on which addition arms can be gated**, with a
measured base operating point (recall_w `0.1439`, credit/dot `0.0465`) to beat.
`tests/test_losfo.py` guards the no-leakage invariant, including a
`scipy.ndimage.binary_dilation(iterations=0)` trap that returns an **all-True** array and would have
silently merged all `758` systems into one.

### 3.3 Re-ranked H33 series (supersedes `knowledge/18`)

The ranking rule changed: **an arm that can only prune cannot reach the target, so addition arms rank
above pruning arms regardless of individual expected ΔDTI.**

| Rank | ID | Class | Ceiling | Data gate (2026-10-03) |
|---:|---|---|---|---|
| 1 | **H33-3** heat-flow residual × 2 m probe conjunction | **ADD** | can add credit | OPEN — `sb_heat_flow_zip` `130,154,244` B `e7fd62c6…` |
| 2 | **H33-4** drainage-network neotectonics from 1 m DEMs | **ADD** | can add credit | free official source; scope tile volume first |
| 3 | **H33-5** Phase-2 discovery budget | **ADD** (bounded) | Phase-2 optionality | none external |
| 4 | **H33-1** kinematic reactivation favourability gate | PRUNE | `+0.0005…+0.0030` | preregistered `knowledge/19`; bridge landed, **data not yet held locally** |
| 5 | **H33-2** multi-depth MT conductance alignment | PRUNE/score | `+0.0000…+0.0022` | both probed GeoTIFFs pin-verified |

### 3.4 The H33-1 data bridge (blocker removed this session)

The availability probe streams and discards bytes, so *"data gate OPEN"* never meant *"data
available"*. `scripts/fetch_external_layers.py --derived all` now keeps one pinned release,
re-verifies its SHA-256 against `registry/external_pins.json` (the four runner-recorded hashes),
opens the vector layer(s) inside, clips them to the competition footprint
(`src/gems27/external_clip.py`) and writes `docs/data/sb_slip_tendency_in_footprint.{csv,json}`.
The whole path — stream → hash → pin compare → archive → clip → write, plus pin-mismatch,
no-vector-layer and no-pin failure modes — is covered by `tests/test_external_bridge_derived.py`
(exercised on a `file://` pin because `sciencebase.gov` is unreachable from the sandbox) and
`tests/test_external_clip.py`. `knowledge/19_preregistration_H33-1.md` freezes a hard
precondition: **no seed is spent on H33-1 until that derived file exists and its schema lists
slip/dilation-tendency fields.**

**It landed, after three defects that each hid behind a green job.** Merging to `main` triggered the
runner three times. Each failure was a real bug, and two of them would have committed an unusable
table while reporting success:

| Run | Outcome | Root cause |
|---|---|---|
| `37145601551` | HTTP 200, `35,912,323` B, **`pin_match: true`** — but **`n_records: 0`** and job exit 0 | ScienceBase URLs carry no file suffix (`…?f=__disk__33%2Fb0%2F91%2F…`), so `fetch()` named the payload `.bin` and GDAL refused to open a zip wearing that extension. The per-layer error *was* recorded as `LAYER_UNREADABLE`, but the aggregate row still said `DERIVED_WRITTEN`. |
| `37145919044` | Failed loudly (**correct**) | `ImportError: geopandas is required to use pyogrio.read_dataframe()` — the workflow installed `pyogrio shapely pyproj pandas` but not `geopandas`. It ran locally only because `geopandas` was present in the sandbox; **the sandbox masked a runner-environment gap.** |
| `37146168753` | **`DERIVED_WRITTEN`, 84,484 records** | — |

Fixes now in place: `resolve_payload_format()` decides the archive type from **magic bytes first**
(`PK\x03\x04` → zip) and copies to a correctly-suffixed name *without mutating the hashed original*;
`build_sciencebase_derived` reports `LAYER_UNREADABLE` / `DERIVED_EMPTY` / `NO_VECTOR_LAYER` /
`ARCHIVE_UNREADABLE` as distinct non-success statuses; the workflow **fails the job** on any of them
plus `PIN_MISMATCH`, and asserts all five readers import *before* any fetch.

### 3.5 H33-1 was run on its reserved seeds — and refuted, `0` of `6` criteria

With the data in hand, H33-1 was executed before any new arm was designed, because it was the only
preregistered hypothesis that was actually runnable. Full record:
`knowledge/21_result_H33-1_refuted_2026-10-03.md`, `evidence/h33_1_holdout.json`.

The precondition was verified **from the bytes** first: **84,484 fault segments** (17,369 km of
trace, median segment 189 m) clipped from Siler (2022), DOI `10.5066/P9YL58W6`, carrying `TS`, `TD`,
`TS_norm`, `TD_TS`, `ShearStres`, `NormalStre` and stress-orientation fields, reprojected from NAD83
Albers Equal Area Conic to EPSG:32611. This **confirms from the data** the reading that
`knowledge/19` had to treat as unconfirmed (the sandbox cannot reach `api.datacite.org`). The source
`Strike` attribute was verified to be a geographic azimuth — median absolute difference `4.27°`
against the geometric azimuth of the clipped vertices on 4,000 segments.

| Variant | mean DTI | ΔDTI | seeds won | folds | Δdots/seed | credit per removed FP |
|---|---:|---:|---:|---:|---:|---:|
| `base_oof_d28` | 0.094633 | — | — | — | — | — |
| **`h33_1_prune_p10`** (primary) | 0.091618 | **−0.003014** | **0/10** | **0/4** | −582.4 | **0.12855** |
| `h33_1_prune_p05` (dose) | 0.093018 | −0.001615 | 0/10 | 0/4 | −290.0 | 0.14020 |
| `control_top_p10` (direction) | 0.092426 | −0.002207 | 0/10 | 0/4 | −582.4 | 0.10104 |

**All six frozen criteria failed** (`gate_passed: false`): ΔDTI `−0.003014` vs `+0.0010`; folds `0`
vs `3`; seeds `0` vs `8`; removed credit/FP `0.12855` vs break-even `0.019292`; direction control
`0.10104` — *better* than the primary, so the sign is inverted; `fav` coverage **`11.95%`** vs the
`60%` precondition.

Three things this teaches, in `knowledge/21` §2:

1. **A hard coverage ceiling of ~12%.** Only `11.95%` of emitted dots (worst fold `9.61%`) had a
   catalogued segment within 1 km whose strike agreed within 20°. The other 88% are neutral by
   construction. The cause is structural, not tunable: **candidate dots are emitted off-catalogue by
   design.** Any arm that transfers an attribute *from* mapped faults *to* off-catalogue candidates
   inherits that ceiling. This closes a *class*, not a parameterisation.
2. **The sign of the physics is inverted.** Dots the score called unfavourably oriented carried
   *more* credit (`0.12855`) than the ones it called favourable (`0.10104`).
3. **Pruning is exhausted as a family.** All three arms removed pixels at `0.101–0.140` credit per
   FP against a break-even of `0.019292` — the discarded pixels were worth **5–7× break-even**.
   With H31-1 and H32-2, that is three independent pruning arms failing the same way, reaching the
   §3.1 frontier conclusion from a completely different direction.

Per the preregistration: recorded, not retuned, not re-run on a fresh decade, no candidate TIFF,
**no slot spent**. Seeds `200–209` are spent; the next arm takes `220–229`. **Seed disclosure:**
seed `200` was invoked four times while fixing four implementation defects (metre/pixel unit
confusion in the borrow radius, `np.column_stack(np.flatnonzero(...))` returning shape `(1, 2)`, a
per-dot vector reshaped as a grid, float indices used to subscript an array). The harness is
deterministic and no frozen constant was ever changed, so those invocations returned the recorded
numbers; disclosed in `knowledge/21` §3 and `registry/irregularities.json`.

---

### 3.5 H34 — the packing ladder, and a threshold every arm was judged against

`scripts/analyze_operating_point_h34.py` → `evidence/h34_operating_point.json`;
`scripts/run_h34_holdout.py` → `evidence/h34_holdout.json` (seeds `220–229`, 40 cells).
Preregistration `knowledge/21_preregistration_H34.md`, result `knowledge/22_h34_result.md`.

**The ladder is finite.** `thinning.dot_thin` keeps a pixel iff no already-kept pixel is strictly
closer than `min_dist`, so its output changes only when `min_dist` crosses a distance two integer
cells can actually realise ($\sqrt{a^2+b^2}$). There is no continuum to search — only 29 rungs below
8 px. The current file sits at rung `2.828` ($N = 44{,}090$).

**The gate FAILED and the arm is closed.** Preregistered on four criteria; three passed, one did not:

| # | Criterion | Observed | Verdict |
|---|---|---:|---|
| 1 | `e(2.828→3.000) < tau_live` | **0.01914** (10/10 seeds, 4/4 folds) | PASS |
| 2 | direction control: `e(3.000→3.162) > tau_live` | **0.02814** | **FAIL** |
| 3 | seed/fold consistency | 10/10 and 4/4 | PASS |
| 4 | monotone emission, probabilities in `[0,1]`, grid pinned | 40/40 | PASS |

Criterion 2 says the proxy cannot locate a *stopping* rung — it rates both steps profitable, and it
would keep thinning forever. **Cause quantified:** removal efficiency scales with credit per dot, and
the proxy earns `0.0393` credit/dot against the surface's `0.1087` (`2.77×`), which flattens its
efficiency ladder by `1.4×`–`2.3×`. Per the preregistration: no confirmation run, no retuning on
`220–229`, **no candidate TIFF, no weekly slot, and rung 3.0 is not promoted.** The primary download
is unchanged.

**What did survive is bigger than the arm: the threshold was wrong.** Differentiating the metric, a
pixel class with removal efficiency $e = |d\text{TP}_w/d\text{FP}_w|$ is worth dropping iff
$e < \tau = 0.2\,\text{DTI}/(1-0.2\,\text{DTI})$, which **rises with DTI**. The catalogue-holdout
proxy scores `0.095` → $\tau = 0.0193$. The `0.2600` submission those harnesses inform scores `0.26`
→ $\tau = 0.0548$, i.e. **2.85× more permissive**. Every pruning arm in this repository has been
gated against the proxy's threshold, so **any arm whose efficiency lies in `(0.019, 0.055)` was
rejected by a threshold that does not apply to it.**

The rule itself is now confirmed empirically to ~1 %: on 40 independent holdout cells the proxy's
ΔDTI crosses zero at measured $e = 0.01914$ against a predicted $\tau_{\text{proxy}} = 0.019265$
(ΔDTI `−0.000031`), and the next step at $e = 0.0281 > \tau$ gives ΔDTI `−0.00227` — right sign, right
magnitude, on data the framework never saw.

**A modelling error found and fixed while building the test for this.** `src/gems27/operating_point.py`
closed the metric as $\text{FP} = N - A$, charging every emitted pixel full false-positive mass and
ignoring the crowding excess $\tilde{A} - A$ — which the inversion measures as `0.18×`, `0.43×` and
`1.46×` of $A$ on the three anchors, so no fitting can absorb it. Corrected to
$\text{FP} = (1-\gamma)N$ with $\gamma = \tilde{A}/N$ **measured** on the anchors as
`0.12569 / 0.12576 / 0.12811` — constant to `1.9 %`, exactly what non-selective thinning predicts (and
what H32-1's own evidence showed: `11.6 %` on-catalogue before thinning, `11.7 %` after). A second
error: the retention curve is measured on a network with `1:1` dot-to-truth density while the H19-5
surface runs `~10:1`, so a single fitted **density scale** $s$ rescales the loss. With $L$, $|G|$ and
$\gamma$ all measured, the model has **one** free parameter and reproduces three hash-authenticated
live scores to $\le 1.08\times10^{-3}$:

| anchor | $N$ | live score | model | residual |
|---|---:|---:|---:|---:|
| h19-5 solid | 121,131 | 0.1922 | 0.192201 | `+7.6e-07` |
| dotted-h19-5-d1-5 | 60,069 | 0.2477 | 0.246618 | `−1.08e-03` |
| dotted-h19-5-d2-8 | 44,090 | 0.2600 | 0.260627 | `+6.3e-04` |

The old two-parameter fit is **rejected**: it fits to `3.2e-04` but recovers $|G| = 9{,}698$,
**20.7 % below** the blind lattice, because two free parameters cannot separate the crowding term from
the density mismatch. The corrected model agrees that rung 3.0 is optimal (`+0.00303`, stable for
$s \in [0.79, 0.87]$) and *does* satisfy the direction control ($e(3.0\!\to\!3.162) = 0.0659 > \tau =
0.0556$) — but a model projection is not a validated result, so the arm stays closed.

> **Consistency note.** The corrected closure is algebraically identical to the one
> §3.1's reachability frontier already used, $\text{DTI}=\text{TP}_w/(0.2\,\text{TP}_w(1-\rho)+0.2N+0.8|G|)$:
> substituting $\rho = \gamma N/A$ makes the denominators equal term for term, and the frontier's own
> $\rho = 1.17909$ at this anchor reproduces $\gamma = 1.17909 \times 4791.05 / 44090 = 0.12811$. The
> two sessions' arithmetic agrees; only the new module had the bug.

**Cross-check against the H33-1 result merged from `main`.** The parallel session ran the
preregistered H33-1 prune on seeds `200–209` and refuted it — 0 of 6 criteria, mean ΔDTI `−0.003014`,
`0/10` seeds, `0/4` folds. Its measured removal efficiency is **`0.12855`**, which is not merely above
$\tau_{\text{proxy}} = 0.0193$ but **2.3× above $\tau_{\text{live}} = 0.0548$** — so the threshold
correction does **not** rescue it, and its refutation is stronger than it looked. Two of its criteria
are independently damning: the direction control went the *wrong* way (a naive top-10 % prune destroys
less credit per unit of mass, $e = 0.10104$, than the kinematically-targeted prune does), and kinematic
favourability covers only `11.95 %` of the emission against a required `60 %`.

> **The pruning family is now exhausted.** H32-2 (`e = 0.0344`), H33-1 (`e = 0.1286`) and H34
> (criterion 2 failed) have all been measured and all fail, and §3.1 shows the gap to `0.3195` is a
> detection gap no prune can close. Future effort belongs on **addition** arms (H33-3, H33-4, H33-5),
> gated against $\tau_{\text{live}}$ on the LOSFO far-field truth set.

**Two re-readings follow, recorded as re-readings and not promoted.** `H32-2` (archived $e = 0.0344$)
flips from FAIL to profitable at the live threshold, worth `+0.0047` modelled — it stays closed
because it needs its own fresh decade, not a re-reading. The `LOSFO` far-field **addition** gate
(`knowledge/20` §3) is the one that changes a plan: measured far-field credit/dot is `0.0465`, which
clears the cell threshold `0.0204` but **not** $\tau_{\text{live}} = 0.0548$, so base-quality
far-field dots would *lower* the live score. That gate must be restated against the live threshold.


### 3.7 Session 11 — five addition hypotheses, one refutation, and a slot decision made on fresh seeds

Session 10 ended with a hard constraint (§3.1): beating `0.3195` from the `0.2600` emission needs
`+1,151 px` of credit, more than the whole submission captures, and thinning efficiency (`0.03098`) is
below break-even (`0.05485`). That is a **detection gap**, so only new dots on uncovered structure can
close it. Session 11 therefore designed an addition series and measured the first member of it.

**The H35 ledger** (`knowledge/23_h35_hypotheses.md`, ranked by expected ΔDTI × cost, with the
obtainability check actually performed for each):

| Rank | ID | Class | Physical signature | Cost | Obtainable in-sandbox? |
|---:|---|---|---|---|---|
| 1 | `H35-1` hydrothermal-discharge conjunction | ADD | point process of thermal discharge — not a derivative field | low | **yes**, bytes in hand |
| 2 | `H35-4` bounded Phase-2 discovery budget | ADD (bounded) | a budget rule, not a transform | low | yes, nothing to fetch |
| 3 | `H35-2` heat-flow residual × 2 m probe | ADD | conductive residual from a genuinely different field | high | **no** — `sciencebase.gov` returns HTTP `000`; Actions bridge only |
| 4 | `H35-3` drainage-network neotectonics | ADD | channel offsets / knickpoints from 716 1 m DEM tiles | very high | **no** — `prd-tnm.s3.amazonaws.com` returns `000`; Actions only |
| 5 | `H35-5` vent-corridor control | CONFIRM | vent alignment — only `21` points, re-ranking only | low | yes, in hand |

#### 3.7.1 `H35-1` is refuted — 3 of 4 frozen criteria failed, arm closed

Preregistered in `knowledge/23_h35_hypotheses.md` §5 **before** the run; executed on its reserved seeds
`230–234` with the LOSFO far-field instrument (`450 s`, `evidence/h35_1_thermal_farfield.json`).

| # | Criterion | Required | Observed | Result |
|---|---|---|---|---|
| G1 | Profitability | `>= tau_live = 0.054852` credit/dot | `0.013195` | **FAIL** (4.2× short) |
| G2 | Differential vs matched-count control | thermal `>` control pooled and `>= 4/5` seeds | `0.013195` vs `0.023781`; `1/5` seeds | **FAIL** |
| G3 | Support | `>= 200` added dots/seed | `6,856.8` | PASS |
| G4 | End-to-end | pooled mean ΔDTI `> 0` | `-0.001805` (control `+0.000354`) | **FAIL** |

The dose-response is flat-to-wrong in every pre-declared variant, so **no tighter subset rescues it**:
`temp_c >= 50 C` `0.015812`, quartz geothermometry `>= 100 C` `0.011717`, radius `1 px` `0.020949`,
radius `6 px` `0.010640` — every one at or below the control and 2.6–5× below `tau_live`.

**Mechanism.** Great Basin hydrothermal discharge is overwhelmingly basin-margin and fault-controlled,
which is precisely why those faults are already catalogued and why the blended detector already fires
along those margins. The base emission has therefore already spent its budget on the structure the
springs mark; the candidate pool (`ridge AND active AND NOT base`) is left with redundant neighbouring
slop. The control draws candidates `> 6 px` from any thermal site and **beats** the arm — on this grid,
sitting beside a mapped-margin hot spring is a mild *negative* indicator for the credit a new dot can
still earn. Radius confirms it: the association is strongest at `1 px` and dissolves by `6 px`, the
opposite of a geological control.

**Scope, stated so the record is not over-read.** LOSFO truth is *mapped* geometry, so the stronger
claim (a concealed unmapped permeable structure is marked by a spring) is **untested, not refuted**.
But because LOSFO is an upper bound, failing it closes the arm as constructed. Per the frozen reading
rule: no candidate TIFF, no weekly slot, no confirmation, no retuning. `knowledge/24_h35_1_result.md`.

#### 3.7.2 The defect review found: the one-click file was dominated

Review of our own site found the advertised primary (`c3aeda1d31a3`) **strictly dominated on every
published statistic** by the file sitting in its own *tertiary* slot (`8acb75e1f2cc`) — mean gain
`+0.001272` vs `+0.001766`, worst-seed gain `+0.000907` vs `+0.001370`, all four folds lower, removed
credit per removed FP `0.00402` vs `0.00598`, hybrid projection `0.26650` vs `0.27013`. Registered as
`one-click-primary-dominated-by-tertiary` (severity **high**) in `registry/irregularities.json`.

The honest cause is a multiple-comparison error in the *other* direction: the primary came from a
**preregistered** gate, while the candidate that beat it is the maximum of **four correlated variants
scored on one holdout run**. Re-ranking on the same run that selected the winner is exactly the error
the preregistration discipline exists to prevent. So the tie was broken on **unused seeds** with the
frozen runner **unmodified**, under a rule frozen in
`knowledge/25_preregistration_H35-6_candidate_adjudication.md` before the run: largest mean gain, and
`>= 4/5` seeds, and `>= 3/4` folds, else no change.

| Variant (slot *before* the adjudication) | Seeds `180–189` | **Seeds `235–239` (fresh)** | Seeds won | Folds |
|---|---:|---:|---:|---:|
| H27-4 solo r=1 `8acb75e1f2cc` (tertiary) | `+0.001766` | **`+0.001761`** | `5/5` | `4/4` |
| H32-1 post-thinning `c3aeda1d31a3` (primary) | `+0.001272` | `+0.001251` | `5/5` | `4/4` |
| H32-1 pre-thinning `31e35eee884e` (secondary) | `+0.001399` | `+0.000944` | `5/5` | `4/4` |
| anti-selective control (prune the *protected* pixels) | `+0.000479` | `+0.000490` | `5/5` | `4/4` |

**The ranking replicated**: `8acb75e1f2cc` won again, in all four folds, at `+0.001761` against
`+0.001766` on the older decade — a difference of `5e-6`. The control stayed far below the winner
(`0.000490`), so this is a **selective** prune, not a generic prune-harder effect. The promotion rule is
met, and the **one-click primary is now `8acb75e1f2cc`** (`knowledge/25...`,
`evidence/h35_6_candidate_headtohead.json`). The demoted file is retained as the *conservative*
alternative because it protects fault tips and shallow SI-0 Euler depth clusters. Five seeds cannot
resolve a `+0.0005` gap: this is a decision under uncertainty, stated as one.

#### 3.7.3 What Session 11 changes about the plan

The ADD arm that could be measured **failed**, and it failed below its own random control. That is now
the second independent route to the same conclusion as the reachability frontier, reached from the
opposite direction: at this operating point **new dots are expensive** and a layer must be extremely
specific to clear `tau_live = 0.0548`. Meanwhile the H34 threshold study rates every archived *removal*
arm `PRUNE` (`e = 0.004`, `0.03435`, `0.008`, all `< 0.055`) and puts the optimal packing rung at `3.0`
rather than the shipped `2.828`. Calibration effort therefore belongs on the axis that measurably pays.
Ranked next: (1) a rung-`3.0` re-thin combined with the flank prune, validated on a fresh decade;
(2) `H35-2` heat-flow residual via the Actions bridge; (3) `H35-3` drainage neotectonics.

---

### 3.8 Session 12 — the data blocker is closed, and the packing rung was re-measured

**Blocker closed.** `bash scripts/download_competition_data.sh` now runs end to end in this sandbox:
`17/17` pins restored and hash-verified (`evidence/restore_audit.json`, `data/restore_receipt.json`),
`data/prepared/features.npy` rebuilt at shape `(5,167,373, 32)` `float32`
(`83ed2704…`), and `evidence/submission_file_audit.json` re-audited. The earlier
"cannot download the competition data" note was an environment artefact, not a repository one:
`.venv` + `pip install -r requirements.txt` plus `gh api` (which *is* reachable) is sufficient.
**Egress from the sandbox is GitHub-only** — `raw.githubusercontent.com`, `sciencebase.gov`,
`prd-tnm.s3.amazonaws.com`, `api.datacite.org`, `drivendata.org` and `doi.org` all fail at the TLS
handshake, so any external layer still has to arrive through the Actions bridge (§3.4).

**A measurement that changed the arm before it ran.** The rung ladder had been described as a
"re-thin". It is not a thinning. On the full footprint the shipped `0.2600` file is *exactly*
`thinning.dot_thin(h19_5_surface, 2.8)` (44,090 px, 0 px symmetric difference — an independent
confirmation that the published artifact's construction is what the repo says it is), but
`dot_thin(surface, 3.0)` shares only 30,666 px with it, **adds 10,667 px and drops 13,424 px**. Because
`dot_thin` is a greedy lowest-raster-index cascade, raising `min_dist` *re-seeds* the packing instead
of deleting dots; 24,091 px change hands. The ladder is therefore a **layout** choice, not a budget
cut, and that is falsifiable — which is what the new control is for.

**H36-1, gate frozen in `knowledge/26_preregistration_H36-1.md` (commit `aaa659c`) before seeds
`240–249` were touched** (`evidence/h36_1_holdout.json`, `knowledge/27_h36_1_result.md`):

| Variant (vs the same-run rung-2.828 control, OOF DTI 0.094132) | ΔDTI | seeds | folds |
|---|---:|---:|---:|
| `rung30_unpruned` — the H34 claim in isolation | +0.000956 | 10/10 | 4/4 |
| **`rung30_blind_r1` — re-pack + H27-4 blind flank prune** | **+0.002599** | **10/10** | **4/4** |
| `rung30_flank_mid` — re-pack + H32-1 mid-segment prune | +0.002188 | 10/10 | 4/4 |
| `h27_4_blind_r1_d280` — the Session-11 incumbent | +0.001715 | 10/10 | 4/4 |
| `control_random_drop_matched_n` — **delete the same 2,649 dots at random** | **−0.001657** | **0/10** | **0/4** |
| `control_rung30_protected_only` — anti-selective control | +0.001352 | 10/10 | 4/4 |

All five frozen criteria pass: the rung effect is positive in every seed and fold (G1); the re-pack
beats the matched-`N` random drop by **+0.002613**, so the effect is layout and not budget (G2); every
prune's removal efficiency (0.0096–0.0098) is far below `tau_live = 0.054852` (G3); the winner beats
the incumbent by +0.000884 ≥ the pre-declared +0.0005 margin (G4); and the anti-selective control sits
below the winner, so the prunes are still selective (G5).

**The anti-budget control is the load-bearing result.** A coin-flip deletion of exactly the 2,649 dots
the rung removes *loses* 0.001657 — in `0/10` seeds and `0/4` folds — while the re-pack at the same
count gains 0.000956. That also falsifies the natural reading of H34: under its `gamma`-invariance
assumption removal is non-selective and a random deletion to the same `N` should have matched. It does
not. `gamma`-invariance held to 1.9 % across the three live anchors of one surface and does not survive
this test, because `dot_thin` re-seeds.

**Promoted artifact.** `docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`
(content id `b531dae0a36f`, 37,660 px, SHA-256 `5556aa14…`). `scripts/verify_downloads.py` → **PASS,
179 checks, 0 failures**. Live-anchored hybrid projection **0.2717–0.2727** (H34's ladder for the
re-pack, +0.002834; the gate's measured prune efficiency for the flank prune, 3,673 px at 0.0098447).
The range, not a point value, is deliberate — `operating_point.prune_gain` is a first-order expansion
and over-states a 9 %-of-`N` prune by ~0.001, now registered as
`prune-gain-linearisation-overstates-large-prunes`. **No weekly slot is used by this arm; a gate is not
a submission.** Do not preregister further rung arms: `3.1623` removes a further 6,516 px for no
measured retention gain and H34 rates it worse, so the family is bounded on both sides.

**Also fixed this session (defect review, `registry/irregularities.json`).** The first H36-1 build
shipped a submission note reading `28GEMSDOE 28GEMSDOE H36-1 … re-pack beats matched-N random d | …` —
a duplicated family token (the caller passed it *and* `make_note` prepends it) and a mid-word
truncation (the summary exceeded the 200-character budget and `make_note` slices silently). The note is
the text a human pastes into the organiser's Note field, so it is human-facing even though every raster
check passed. Rebuilt at 192/200 with an assertion in the builder that fails the build rather than
truncating, and the builder is now idempotent (re-running it previously demoted its own output into the
secondary rank). The site's above-the-fold paragraph was also split — it had become a single run-on
`<p>` concatenating historical H31/H32-structural/H35-1 failures onto the current status.

### 3.9 Session 13 — the emission rule itself was the leak, and it is now measured

Session 12 closed with the emission step (`thinning.dot_thin`) unchanged: it keeps a pixel iff no
already-kept pixel is closer than `min_dist`, walking candidates in **ascending raster index**, so the
detector's evidence never influences the layout. H36-1 had already shown the *layout* is worth
`+0.0026`/`−0.0017` at fixed count (`knowledge/27` §2). Session 13 replaced the rule and gated it.

**Hypothesis H37-1.** Replace the raster-order cascade with a lazy-greedy **maximum expected coverage**
of the detector's probability field under the official triangular kernel
(`k(d) = max(1 − d/300 m, 0)`, `R = 3 px`), at a **matched dot count**, followed by the unchanged
`H27-4` blind 1-px catalogue-flank prune:

$$\text{gain}(x \mid S) = \sum_q p(q)\,\max\!\big(0,\; k(|x-q|) - C(q)\big), \qquad C(q) = \max_{y \in S} k(|y-q|)$$

That is the official metric's own true-positive term used as the packing objective, so the objective
and the score are the same object. `gain` is monotone and submodular, so the greedy order carries the
`1 − 1/e` guarantee and lazy evaluation selects the same set. Implementation: `src/gems27/packing.py`,
tests `tests/test_packing.py` (including a brute-force `(1 − 1/e)` bound check and a
determinism contract). Every design choice below was fixed by an exploratory pass on **spent** seeds
`181`/`185` (`evidence/_scratch/packing_h37_explore{,_v2,_v3}.json`) before the gate was frozen in
`knowledge/29_preregistration_H37-1.md`.

**Frozen gate, fresh seeds `250–259`, 40 cells (`evidence/h37_1_holdout.json`, 442.6 s).**

| Variant | mean OOF DTI | ΔDTI vs `d=2.8` | vs incumbent | seeds | folds |
|---|---:|---:|---:|---:|---:|
| `base_oof_d280` | 0.098186 | — | — | — | — |
| `rung30_blind_r1` (H36-1 incumbent) | 0.100860 | +0.002675 | — | — | 4/4 |
| **`cover_prob_r1` (PRIMARY)** | **0.105475** | **+0.007289** | **+0.004614** | **10/10** | **4/4** |
| `cover_prob_pool3x_r1` (pool probe, 2.45 % density) | 0.105522 | +0.007336 | +0.004661 | 10/10 | 4/4 |
| `cover_prob_1p5n_r1` (dose, not promotable) | 0.108626 | +0.010440 | +0.007765 | 10/10 | 3/4 |
| `control_random_matched_n` (content-blind) | 0.053502 | −0.044684 | −0.047359 | 0/10 | 0/4 |

All five frozen criteria passed (G1 direction, G2 margin `+0.004614 ≥ +0.0005`, G3 `10/10` seeds and
`4/4` folds, G4 content-control margin `+0.0520`, G5 integrity 0 violations in 40/40 cells). Two
findings matter as much as the headline:

* **The instrument reproduced.** The H36-1 incumbent returned `+0.002675` here against `+0.002599` on
  seeds `240–249` — a `7.6e-5` difference on an independent decade.
* **The pool probe is what makes the artifact transferable.** The gate's primary drew from *every*
  ridge pixel (≈16 % of the footprint); the shipped H19-5 surface is only **2.34 %**. The probe
  restricted to a 2.45 % pool measured the same effect (`+0.004661`, 10/10 seeds, 4/4 folds), so the
  artifact is a measured analogue, not an extrapolation.

**Artifact.** `docs/downloads/gems28-h37-1-coverprob-h19-5-r1-20261003-0bbddf41eb6d-nan.tif` —
**37,447 px** at the same 41,333-px pre-prune budget as the incumbent, SHA-256 `4557311baedb4e66…`,
`verify_downloads.py` → **PASS, 208 checks, 0 failures**. The weight field is the full-fit detector
probability (the emission-time analogue of the gate's out-of-fold field). A second, **not-promoted**
probe (`…-probe-union-pool-r1-…`, 38,545 px) records the union-pool emission (H19-5 + the detector's
own ridges) because the live record already punishes that content: 26GEMSDOE `dilcond-oof-v1`, a pure
detector-product emission, scored `0.1223`.

**Far-field falsification: F1 FAILED.** The test frozen in `knowledge/32` ran on its dedicated LOSFO
decade (seeds `210–214`, whole fault systems removed with a 600 m buffer) after freeze commit `7e637c9`.
The unmodified base arms reproduced the stored diagnostic to eight decimals, so the instrument is stable;
the new rule then earned `−0.000037` against the raster cascade (95 % interval `±0.000832`, 9/20 cells,
3/5 seeds) while the field coverage it achieved rose slightly (`15,570.2 → 15,670.8`). The interleaved
`+0.007289` therefore does not transfer off the catalogue: habitat decomposition
(`evidence/arm_habitat_decomposition.json`) had already shown that 100 % of interleaved truth is
catalogue pixels, and the LOSFO truth lies ≥ 8 px from anything the detector saw. F2's pass
(`+0.002091` vs a random order) is **not** cited as an ordering result — the two ordering arms are
capacity limited (10,975 / 10,992 dots against the requested 12,001), so the only exactly matched
comparison is F1, which failed. The artifact is demoted to secondary by the pre-committed rule, both
numbers are printed on its card, and `knowledge/33` withdraws the live projection. Registered as
`h37-1-farfield-effect-is-zero` and `ordering-packers-are-capacity-limited`.

#### 3.9b H37-3 Euler SI-0 depth-coherence licence — REFUTED as a promotable arm (mechanism positive)

Rank-2 of `knowledge/31` was preregistered at `knowledge/34` (freeze commit `0788eec`) and run on its own
LOSFO decade, seeds `260–264` (20 paired cells, exit 0, ≈13 min; `evidence/losfo_h37_3_licence.json`,
analysis `scripts/analyze_h37_3.py`, integrity `evidence/h37_3_licence_integrity.json`). The licence rule
was frozen in advance: the 1,435 of 6,309 SI-0 Euler clusters with `depth_mad_m ≤ 60` **and**
`median_depth_m ≤ 400` **and** `n_solutions ≥ 8`, mapped one dot per cluster, excluding catalogue and
already-emitted pixels, at the shipped 2.8 px spacing; 296 dots added per cell on average. Three arms
were scored on the identical far-field truth, cell by cell: `base`, `base+licence`, and
`base+same-count random control` drawn from the same off-catalogue eligible region.

| criterion | result | verdict |
|---|---|---|
| **C1** mean ΔDTI(licence − base) > 0, ≥15/20 cells, ≥4/5 seeds | **+0.000576** ±0.000451, 13/20 cells, 5/5 seeds | **FAIL** (spread) |
| **C2** pooled credit per added dot ≥ `τ_live` 0.0548 | **0.031157** (57 % of the bar) | **FAIL** |
| **C3** mean ΔDTI(licence − random control) > 0, ≥15/20 cells | **+0.000699** ±0.000452, 16/20 cells | **PASS** |
| **C4** integrity | same-seed base arms bit-identical to the pre-patch harness; fresh-decade base arms inside the documented LOSFO spread | **PASS** |

**Verdict by the pre-committed rule: refuted as a promotable arm**, with the mechanism recorded as real and
this session's second honest negative. The licence's dots earn **1.65×** what the same number of random
dots earn in the same region — the depth-dispersion statistic does carry off-catalogue information — but
0.0312 < 0.0548, so adding dots at this rate *lowers* the live score (296 dots: `0.260627 → 0.260294`;
the arm's full 5,916-dot scale: `→ 0.254356`). One of four folds is negative (`NE_LidarGapHeavy`
−0.000390 against `NW` +0.001186, `SE` +0.000893, `SW` +0.000617), which is why C1's spread rule exists.
**At the close of Session 13:** seeds 260–264 were spent and 265–269 were still recorded as free; the Session 13 ledger put **H37-2** (concealed-fault conjunction) next, with the H37-3 lesson attached: *a licence that clears 1.65× random can still lose if its rate is below the bar*. That ledger is historical: Session 14 subsequently reserved and ran 265–269 once, then burned them on analyzer failure; see §3.9c and [`knowledge/39_session14_closeout_2026-10-03.md`](knowledge/39_session14_closeout_2026-10-03.md). Registered as `h37-3-licence-real-but-below-the-live-rate` and `cross-seed-baseline-comparison-is-not-an-integrity-check` in `registry/irregularities.json`.

#### 3.9c Session 14 — five ranked hypotheses; H38-1 analyzer failure, no gate decision

Full scientific record: [`knowledge/37_ranked_hypotheses_session14_2026-10-03.md`](knowledge/37_ranked_hypotheses_session14_2026-10-03.md); frozen H38-1 protocol: [`knowledge/38_preregistration_H38-1.md`](knowledge/38_preregistration_H38-1.md); single-use run and three-pass close-out: [`knowledge/39_session14_closeout_2026-10-03.md`](knowledge/39_session14_closeout_2026-10-03.md). These are risk-adjusted planning intervals, all including zero—not observed holdout gains or leaderboard predictions. Generative-AI use is disclosed in [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md); include this in any final competition narrative.

| Rank | Hypothesis / layers | Planning-only ΔDTI | Cost / data gate |
|---:|---|---:|---|
| 1 | **H38-1:** SI-0 Euler depth-coherent cluster × independent gravity-gradient edge × low valid LiDAR relief | `0.0000…+0.0010` | Low–medium; local hash-pinned owner mirrors; no new official data required |
| 2 | **H38-2:** USGS heat-flow well residual × GDR #1391 2 m temperature probe anomaly × potential-field corridor | `0.0000…+0.0025` | Medium–high; USGS 124 MB archive is listed, but a local clip/schema/coverage audit is still required |
| 3 | **H38-3:** GDR paleogeothermal deposits (sinter/tufa/travertine) × subsurface contact corridor × low relief | `0.0000…+0.0015` | Low–medium; official resource is listed, but this checkout has no audited local clip |
| 4 | **H38-4:** USGS 3DEP 1 m drainage offsets/knickpoints/beheaded channels × potential-field lineaments | `0.0000…+0.0035` | Very high; product is official/public-domain, but 716 owner-mirrored tile URLs, footprint, bytes, CRS/datum and total volume are not verified |
| 5 | **H38-5:** five-depth USGS MT conductance boundary coherence (2–200 km) × gravity/magnetic edge | `0.0000…+0.0015` | Medium–high; ScienceBase lists five layers, but a five-layer local clip/schema audit is still required |

**H38-1 label-free sufficiency result, not validation.** The frozen conjunction retains SI-0 clusters with `depth_mad_m ≤ 60 m`, median depth `≤ 400 m`, and at least 8 solutions; requires band-18 `iso_grav_anom_hg` at/above its in-footprint P80 within 200 m; and requires valid LiDAR band-9 `relief` at/below its valid-footprint median. It selected 140 of 1,435 depth-eligible clusters (9.76%; thresholds `1.460558295249939` and `44.0`; candidate CSV SHA-256 `2e5c607affa635418c90a520ef843494a4fb00fb7e7d69f63fb317c73849d369`; support-audit SHA-256 `91d86b012fcbfa472ff79859623743e1292a077d591427e78bf8627a92250b60`). This count is a label-free feasibility screen only. Euler SI=0 is an idealized contact geometry, gravity edges may be lithologic/basin boundaries, and subdued relief is not evidence of faulting, activity, permeability, or geothermal favorability.

**Freeze and seed reservation.** The protocol freeze was committed as `cf1d03627ad3f863d10ff34e5195f126efad51f5` and pushed before seed inspection. The local audit returned `PASS_LOCAL_SCAN` over 61 `evidence/*.json` files, with zero target-range references, collisions, or unreadable JSON (audit SHA-256 `413cc522519a394e06d826eacccc11262c0653890659d9e94c550f5c0e91394e`). The exact-range claim was committed as `RESERVED` before execution; the local-only scan cannot establish use in other repositories, owner workspaces, or unpublished runs, and the Git checkout is shallow.

**Single-use attempt, seeds 265–269.** The wrapper was invoked once on `arena/01a10412-gemsdoe28`; the LOSFO runner completed all 20 cells and saved the [raw artifact](evidence/losfo_h38_1_raw.json) (SHA-256 `0375a9e58ed9dc43f6dddecb431644a18e10b39e42219ed491ede530dbf5a4ba`). The frozen analyzer then exited 1 while serializing its report: `TypeError: Object of type int64 is not JSON serializable`. No summary report or C1–C5 gate decision was written. The claim is now `FAILED`, seeds `265–269` are burned, and the [failure record](evidence/h38_1_holdout.started.json) has current SHA-256 `1bd9bd5e3e4c2c4861a34f4b1714e7b89e36f73b8dd6f3bb8e819768163a3791`. This is an execution/analysis failure—not evidence that the geological hypothesis passed or failed. Per the frozen rule, do not rerun, repair, or make a gate decision on this seed range. No H38-1 TIFF was built or promoted, no organizer upload occurred, and no weekly slot was used. Any future test needs a new preregistration, a distinct fresh seed range, and a corrected analyzer.

Frozen gates remain as preregistered: positive repeatable ΔDTI, at least `0.0548` credit per added dot, superiority to same-count random, ≥200 additions with clean integrity, and a mean gain above H37-3's `+0.0005763894914862378`; even a pass would have permitted only independent confirmation and exact-file review, **not** a weekly slot.

Official-source checks are links, not claims of local acquisition: [DrivenData problem statement](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) says public labels are incomplete and experts added faults; [USGS heat-flow ScienceBase record](https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28); [DOE GDR #1391 INGENIOUS listing](https://gdr.openei.org/submissions/1391); [USGS five-depth MT conductance release](https://www.sciencebase.gov/catalog/item/62979746d34ec53d276c113b); and [USGS 3DEP one-meter DEM catalog](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e). Listings and product-level availability do not establish local coverage, schema, byte integrity or suitability. No DrivenData login is assumed.

**Answer to the standing question.** Why did `0.2600` win, and can we beat it? `0.2600` won because
Poisson-disk thinning at `d = 2.8` cut 63 % of the H19-5 pixels while retaining 90.6 % of the `d=1.5`
credit (`knowledge/01`). Session 13 tested the cheapest remaining candidate — the **selection rule** rather than new
geology: `+0.0073` interleaved at a matched budget, and its far-field falsification test then
**failed** (`−0.000037 ± 0.000832` on the LOSFO decade; F1/F3 FAIL, F2 passes only against a
capacity-limited random control — `knowledge/33`). The honest conclusion is that the interleaved
gain is earned beside the published catalogue, the `0.278–0.286` projection is withdrawn, and the
one-click slot returned to H36-1's live-anchored `0.2717–0.2727`. Beating `0.3195` still needs
`+1,151 px` of credit (`knowledge/20` §3.1) and remains a **detection** problem; the ranked geological
candidates for that are in `knowledge/31_hypotheses_session13.md`.

**Stated plainly, in the same breath.** The standing holdout hides catalogue components interleaved
with the known catalogue, so 100 % of its truth lies at distance 0 from the published catalogue. A
coverage objective aimed at a field trained on that catalogue is *a priori* favoured by the protocol.
The gate is therefore necessary and passed with a devastating content-blind control, **but this session
did not run the LOSFO far-field instrument on it**, and that is the highest-value next measurement.

**Infrastructure irregularity found and reported this session.** GitHub Pages for this repository is
**not deploying**: the Pages API reports `status: errored`, the last successful legacy build was at
`2026-10-03T21:11Z`, and the runs after it (`e429135` → `"Page build failed."`; `a667805` → stuck
`building`) leave the published site stale. The repository's own Actions deployment
(`.github/workflows/pages.yml`, `actions/deploy-pages`) succeeds and the two paths are configured
against each other (`build_type: legacy`, source `main:/`). Registered in
`registry/irregularities.json: github-pages-legacy-build-errored`; whatever is published at
`https://buffedlizard55-lab.github.io/GEMSDOE28/` should be treated as possibly stale until the Pages
source is switched to **GitHub Actions**.

---

## 4. Euler Deconvolution for Depth (Reid et al., *Geophysics*, 1990) & Screen Ledger

Implemented in `src/gems27/euler.py` (`scripts/build_euler_features.py`, `evidence/h31_1_euler_feature_audit.json`, `evidence/h31_1_euler_clusters.csv`):
1. **Formulation (Reid, Allsop, Granser, Millett, & Somerton, 1990, [DOI:10.1190/1.1442774](https://doi.org/10.1190/1.1442774))**:
   $$(x - x_0)\frac{\partial T}{\partial x} + (y - y_0)\frac{\partial T}{\partial y} + (z - z_0)\frac{\partial T}{\partial z} = N(B - T)$$
   Solved via moving $10 \times 10$ ($1\text{ km} \times 1\text{ km}$) least-squares windows across `tmi` (band 14) with all three derivatives ($\partial_x T, \partial_y T, \partial_z T$) derived self-consistently from the same `tmi` field (`80.265%` valid vertical-derivative coverage).
2. **Primary Structural Index $N=0$ (Fault Contact) & Depth-Labeled Clustering**:
   - Retains `118,089` accepted $N=0$ source solutions (`depth_m` median `296.4 m`, P10 `155.3 m`, P90 `614.1 m`), of which `22,718` have *Euler-estimated source coordinates* $(x_0, y_0)$ aligned within `200 m` of an independent `tmi` horizontal-gradient ridge, forming **`6,309` depth-coherent clusters** (`evidence/h31_1_euler_clusters.csv`).
   - Descriptive sensitivity runs at $N=1$ (`5,665` clusters) and $N=2$ (`4,661` clusters) confirm substantial centroid shift (`41.0%` and `30.2%` match within `600 m` of $N=0$), documented in `evidence/h31_1_euler_feature_audit.json`.
3. **Why `H31-1` (GBDT feature injection) and `H32-1` (structural-step GBDT screen) failed while our `180–189` Euler depth-cluster structural protection gate succeeded**:
   - Feeding 3 rasterised Euler cluster channels into a 41-band `HistGradientBoostingClassifier` (`H31-1`, seeds `160–169`, `evidence/h31_1_euler_screen.json`) failed its frozen screen (`-0.001947` mean ΔDTI, `1/4` folds, `2/10` seeds), and feeding 6 structural-step derivative features (`src/gems27/structural_step.py`, seeds `170–179`, `evidence/h32_1_structural_step_holdout.json`) also failed its frozen screen (`-0.001570` mean ΔDTI, `3/4` folds, `3/10` seeds).
   - In contrast, using the `6,309` shallow $N=0$ Euler depth-coherent clusters (`evidence/h31_1_euler_clusters.csv`) as an **independent subsurface contact corroboration gate** during $100\text{ m}$ flank-shadow de-jittering on `d=2.8` on fresh seeds `180–189` (`evidence/h32_1_holdout.json`) shows that pixels protected by fault tips or shallow $N=0$ Euler depth clusters exhibit **`2.29x` higher hidden-fault credit density (`0.00919` vs `0.00402` credit/FP)** than mid-segment flank-shadow pixels, improving DTI in **`10/10` seeds and `4/4` spatial folds**.

---

## 5. Candidate Geological Hypotheses

**Current ledger: `knowledge/31_hypotheses_session13.md` (Session 13)** — five ranked arms, each naming
- **Session 13 close-out (deliverables, three passes, limitations, AI-use disclosure):** `knowledge/36_session13_closeout.md`.
its layers, physical signature, why it catches a fault *missing* from the catalogue rather than one
already in it, and how it differs from everything already implemented, plus a per-claim obtainability
ledger. It supersedes `knowledge/23_h35_hypotheses.md` (Session 11) for ranking; the H35 results
themselves remain the record. **Previous ledger: `knowledge/23_h35_hypotheses.md` (Session 11).** It adds the five-hypothesis H35
addition series on top of the H33 ranking below and is the file to read first; the H33 entries remain
live for the two arms that still have no run. Session 10's ledger,
`knowledge/20_strategy_after_reachability_frontier.md`, re-ranks
`knowledge/18_new_hypotheses_H33_series_2026-10-03.md`, which superseded the session-8 ranking in
`knowledge/13_current_ranked_hypotheses_2026-10-03.md`.

**Ranking rule changed in Session 10.** §3.1 shows the gap to `0.3195` is `+1,151` px of credit that
only an *addition* arm can supply, so **addition arms now rank above pruning arms regardless of
individual expected ΔDTI** — the ordering below differs from `knowledge/18` for that reason.

- **`H32-1-dejitter` — VALIDATED PASS (seeds `180–189`):** Tip- & Euler-Depth-Cluster-Protected Mid-Segment Flank-Shadow De-Jittering on `d=2.8` (`+0.001272` post-thinning / `+0.001399` pre-thinning, `10/10` seeds, `4/4` folds; `evidence/h32_1_holdout.json`). Remains the holdout best and the primary download.
- **`H32-2` — EXECUTED THIS SESSION, FROZEN GATE FAILED (seeds `190–199`, CLOSED):** shallow-over-deep magnetic de-screening scored `−0.003767` mean paired ΔDTI (`0/10` seeds, `0/4` folds; `evidence/h32_2_holdout.json`, `knowledge/17_h32_2_result.md`). Run-1 sentinel defect disclosed and repaired (`evidence/h32_2_holdout_run1_invalid_2026-10-03.json`). The direction control supported the physics (shallow dots carry more credit/FP: `0.0383` vs `0.0343`) but the deep class sits far above the OOF inclusion threshold (`0.0193`), so pruning it loses. No confirmation, no retuning, no slot.
- **Untried H33 series, re-ranked Session 10 (class now outranks expected ΔDTI):**
  1. **`H33-3` Heat-flow residual × 2 m probe conjunction — ADD arm.** DOI `10.5066/P9BZPVUC` (ScienceBase `6297d2fad34ec53d276c5b28`); runner byte-verified `sb_heat_flow_zip` = `130,154,244` B, SHA-256 `e7fd62c6…` (`registry/external_pins.json`) × already-verified GDR 2 m probes. The product carries a **residual** attribute (departure from de-convected background), which marks exactly the hydrothermal upflow the surface-rupture catalogue ignores.
  2. **`H33-4` Drainage-network neotectonics from 1 m DEMs — ADD arm.** Competition `dem_links.json` → USGS 3DEP/Theia tiles (free, official); channel offsets, beheaded streams, aligned knickpoints. Highest ceiling, highest cost; scope the in-footprint tile volume first.
  3. **`H33-5` Phase-2 discovery budget — bounded ADD arm.** ≤ ~600 px of multi-corroborated off-catalogue emission exploiting the official Phase-2 expert-expanded-label rescoring rule; Phase-1 cost capped at ≈ `0.2 × budget`. Contrarian by design: it buys Phase-2 optionality with a bounded Phase-1 cost.
  4. **`H33-2` Multi-depth MT conductance alignment — PRUNE/score arm.** DOI `10.5066/P9TWT2LU` (ScienceBase `62979746d34ec53d276c113b`); both probed GeoTIFFs runner byte-verified (`4,132,337` B `8cc1a224…`, `4,132,325` B `e8cfd731…`). Ranked last of the survivors because it is a pruning arm and pruning is now exhausted as a family (§3.5).
- **`H35-1` — EXECUTED Session 11, FROZEN GATE FAILED (seeds `230–234`, CLOSED).** Hydrothermal-discharge conjunction; credit/dot `0.013195` against `tau_live = 0.054852`, `1/5` seeds, mean ΔDTI `−0.001805`, and **below its own matched-count random control** (`0.023781`). Every pre-declared dose variant was at or below the control, so no tighter subset rescues it. Closed with no candidate TIFF and no weekly slot (§3.7.1, `knowledge/24_h35_1_result.md`, `evidence/h35_1_thermal_farfield.json`). **Do not re-run on a fresh decade and do not add another point-process layer without a new instrument.**
- **`H36-1` — EXECUTED Session 12, FROZEN GATE PASSED, PROMOTED (seeds `240–249`, CLOSED for screening).** Re-pack the H19-5 surface from packing rung `2.828` to rung `3.0` (41,333 px) and apply the `H27-4` blind 1-px catalogue-flank prune. `+0.002599` mean OOF ΔDTI, `10/10` seeds, `4/4` folds, promotion margin `+0.000884`; the matched-`N` random-drop control scored `−0.001657` (`0/10`, `0/4`), which is what makes this a *layout* result rather than a budget result. Live projection `0.2717–0.2727`. `knowledge/26_preregistration_H36-1.md`, `knowledge/27_h36_1_result.md`, `evidence/h36_1_holdout.json`, artifact `b531dae0a36f`. **Do not preregister further rung arms** — the family is bounded on both sides.
- **`H33-3` / `H35-2` — QUEUED, data gate now openable.** Heat-flow residual × 2 m temperature probe. The Actions bridge (`scripts/fetch_external_layers.py`, spec `sb_heat_flow_zip`) now enumerates mixed archives and Esri FileGDB layers and commits an in-footprint clip, because the release is a *mixed* raster/point archive rather than a shapefile. This is the top entry of `registry/next_hypotheses.json:session12_addendum.next_ranked` and the only queued arm that observes a field the surface-rupture catalogue cannot contain.
- **`H35-6` — ADJUDICATION, COMPLETED (seeds `235–239`).** Not a geological arm: a fresh-seed tie-break of the four candidate files under a frozen promotion rule. Promoted `8acb75e1f2cc` to the one-click slot (`+0.001761`, `5/5` seeds, `4/4` folds) after review found the previous primary dominated (§3.7.2, `knowledge/25_preregistration_H35-6_candidate_adjudication.md`, `evidence/h35_6_candidate_headtohead.json`).
- **`H33-1` — EXECUTED IN SESSION 10, FROZEN GATE FAILED (seeds `200–209`, CLOSED).** The only preregistered arm whose data had actually landed, so it was run first (§3.5). Mean paired ΔDTI `−0.003014`, `0/10` seeds, `0/4` folds, `fav` coverage `11.95%` against a `60%` precondition — **`0` of `6` criteria** (`evidence/h33_1_holdout.json`, `knowledge/21_result_H33-1_refuted_2026-10-03.md`). Do not re-run on a fresh decade, do not widen its radii, do not substitute another tendency field.
- **Standing consequence — pruning is closed as a family.** H31-1, H32-2 and H33-1 have now all failed the same way: the pixels they removed were worth `0.101–0.140` credit per FP against a `0.019292` break-even. **No further pruning arm should be preregistered.** The remaining budget goes to *addition* arms, validated on LOSFO (§3.2), never on the interleaved holdout.
- **Data-gate status (corrected this session).** `registry/irregularities.json` → `h33-external-byte-verify-pending` previously reported the two MT conductance probes as `FILE_NOT_LISTED` and `H33-2` as still gated; that text was **stale**. The facet-aware probe re-ran and the inventory committed at `2026-10-03T18:03:14Z` records **all four sources as `AVAILABILITY_FETCHED`**. All four hashes were promoted to `registry/external_pins.json`, so a later fetch is pin-checked rather than merely re-listed.
- **New this session — `interleaved-holdout-has-no-far-field-truth` (severity high).** The standing holdout cannot validate addition arms (§3.2). LOSFO is the instrument that fixes this; the first frozen addition-arm gate must run on LOSFO, requiring added dots to beat the measured base far-field credit/dot of `0.0465` and the inclusion threshold at the cell DTI, in `>= 3/4` folds and `>= 8/10` seeds.

---

## 6. Reproducibility & Verification Commands

```bash
# 1. Restore all 17 hash-pinned rasters/tables and build the 32-band prepared feature matrix
PYTHON=.venv/bin/python bash scripts/download_competition_data.sh

# 2. Fetch and invert the 24 SHA-256-authenticated live-scored submissions
.venv/bin/python scripts/fetch_scored_corpus.py
.venv/bin/python scripts/invert_live_scores.py --tomo
.venv/bin/python scripts/optimize_budget.py

# 3. Run the 4-fold spatially-blocked holdout validation on seeds 180-189 (H32-1 PASS)
.venv/bin/python scripts/run_h32_1_holdout.py --seeds 180-189

# 3a. Session 11: H35-1 hydrothermal-discharge ADDITION arm (seeds 230-234, ~8 min)
#     Executed: GATE FAILED 3/4 criteria -> arm CLOSED. Kept as the reproduction command.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h35_1_thermal_farfield.py \
    --seeds 230-234 --out evidence/h35_1_thermal_farfield.json

# 3a-bis. Session 11: fresh-seed adjudication of the candidate ladder (seeds 235-239, ~2 min)
#     Executed with the frozen runner UNMODIFIED so the result is comparable with seeds 180-189.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h32_1_holdout.py \
    --seeds 235-239 --out evidence/h35_6_candidate_headtohead.json

# 3b. H32-2 frozen screen on seeds 190-199 (executed session 9: GATE FAILED, arm closed)
.venv/bin/python scripts/run_h32_2_holdout.py --seeds 190-199

# 3c. Session 10: reachability frontier (identity-checked against metric.dti_binary)
.venv/bin/python scripts/reachability_frontier.py

# 3d. Session 10: leave-fault-system-out FAR-FIELD diagnostic (seeds 210-214, ~13 min)
#     Measurement instrument, NOT a promotion gate. Trains 2 detectors per seed (40 GBDT fits).
.venv/bin/python scripts/run_losfo_harness.py --seeds 210-214

# 3f. H34 live-anchored operating point (ladder, threshold, gamma closure) - ~35 s
.venv/bin/python scripts/analyze_operating_point_h34.py
# 3g. H34 preregistered holdout on seeds 220-229 - ~200 s. Result: GATE FAIL (direction
#     control). Arm closed; nothing is promoted from it.
.venv/bin/python scripts/run_h34_holdout.py --seeds 220-229
# 3e. Runner-bridge only: pin-verify and clip an official release to the footprint.
#     Cannot run in the agent sandbox (sciencebase.gov returns HTTP 000); runs on GitHub Actions.
python scripts/fetch_external_layers.py --derived all --external-pins registry/external_pins.json \
    --datasets paleo,probes,volcanics --out /tmp/gdr/out --pins /tmp/gdr/pins.json

# 3f. H33-1 frozen holdout (RUN 2026-10-03, seeds 200-209, REFUTED - do not re-run on a fresh
#     decade). Requires docs/data/sb_slip_tendency_in_footprint.json from 3e first; it aborts with
#     exit 2 if the clip schema lacks TS/TD. ~152 s for 10 seeds x 4 folds.
python scripts/run_h33_1_holdout.py --seeds 200-209 --out evidence/h33_1_holdout.json

# 3i. Session 13: exploratory packing passes (SPENT seeds only; they chose the variant, they do not gate it)
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/explore_packing_h37.py     --seeds 181,185
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/explore_packing_h37_v2.py  --seeds 181,185
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/explore_packing_h37_v3.py  --seeds 181,185

# 3j. Session 13: H37-1 frozen gate (seeds 250-259, ~7.5 min). Preregistration knowledge/29 was committed
#     (424401b) BEFORE the decade was touched; the runner is unmodified since.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h37_1_holdout.py --seeds 250-259
#     Executed: ALL FIVE CRITERIA PASSED -> cover_prob_r1 +0.007289 vs d=2.8 (+0.004614 over H36-1),
#     10/10 seeds, 4/4 folds, content-blind matched-N control -0.044684, integrity clean.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/build_h37_1_submissions.py

# 3k. Session 13b: H37-1 far-field falsification test (LOSFO decade 210-214, ~12.6 min). The preregistration
#     knowledge/32 is committed at the freeze commit 7e637c9 BEFORE the run; base arms reproduce the stored
#     diagnostic exactly. Result: F1 FAIL, F3 FAIL -> the interleaved gain does not transfer; the artifact
#     is demoted and the 0.278-0.286 projection withdrawn (knowledge/33).
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_losfo_harness.py --seeds 210-214 --packing-variants \
    --out evidence/losfo_packing_farfield.json

# 3l. Session 13c: H37-3 Euler SI-0 depth-coherence licence, far-field test (LOSFO decade 260-264, ~13 min).
#     Preregistration knowledge/34 froze the rule, the arm and the criteria at commit 0788eec BEFORE the run.
#     Result: C1 FAIL (13/20 cells), C2 FAIL (0.031157 credit/dot vs the 0.0548 live bar), C3 PASS (1.65x its
#     matched random control), C4 PASS -> refuted as promotable, mechanism real (knowledge/35).
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_losfo_harness.py --seeds 260-264 \
    --euler-licence evidence/h31_1_euler_clusters.csv --out evidence/losfo_h37_3_licence.json

# 3h. Session 12: H36-1 packing-rung re-pack + flank prune, frozen 10-seed gate (seeds 240-249, ~105 s)
#     Preregistration knowledge/26 was committed (aaa659c) BEFORE the run; runner frozen at that commit.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h36_1_holdout.py \
    --seeds 240-249 --out evidence/h36_1_holdout.json
#     Executed: GATE PASSED -> rung30_blind_r1 +0.002599 (10/10 seeds, 4/4 folds), PROMOTE.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/build_h36_1_submissions.py

# 4. Build and audit all submission GeoTIFFs, seed ledgers, and static GitHub Pages HTML
.venv/bin/python scripts/build_h32_1_submissions.py
.venv/bin/python scripts/build_h36_1_submissions.py
.venv/bin/python scripts/verify_downloads.py
.venv/bin/python scripts/audit_euler_seed_reuse.py
.venv/bin/python scripts/build_site.py
.venv/bin/python -m pytest -q
```
