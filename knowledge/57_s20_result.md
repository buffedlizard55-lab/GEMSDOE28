# Session 20 result — nine-site executive answer, H43-1 experiment, and the honest submission decision

**Date:** 2026-10-26 (UTC) · **Branch:** `arena/36be803a-gemsdoe28`
**Preregistration (frozen before experiments):** `knowledge/56_s20_preregistration_H43-1.md`
**Evidence:** `evidence/s20_exp1_forensic.json`, `evidence/s20_holdout.json`,
`evidence/s20_build.json`, `evidence/session20_run_card.json`
**Lane disclosure:** the prompt's "single method paragraph" assignment is absent (as Session 19
found); this session declared its own single lane (H43-1) in writing *before* any experiment and
stayed inside it. Three of three permitted experiments were used. Nothing was uploaded; no slot
was selected.

**Score labels:** site values from the owner prompt are **USER-REPORTED / UNVERIFIED** (no
submission-page receipt exists in this checkout for any of them). Local gate values are
**HOLDOUT-DTI** with evaluator, withheld positives and CI stated. Arithmetic extrapolations are
**MODEL**. Nothing here is ORGANIZER-CONFIRMED.

---

## 1. Executive summary per site — which single submission is best, site by site

"Best" = highest of the values supplied in the owner prompt for that site. The right-most column
is the decision-relevant reading: **all nine "best" files are emissions from one detection
family** (verified byte-by-byte for the GEMSDOE24/25/28/31/32 spine in Experiment 1), so there
are not nine competing strategies — there is one surface and a sequence of cleaner dot-emission
rules applied to it, plus two same-family variants whose bytes were not re-fetched this session
(GEMSDOE27/30/33/36; pinned links in Session 19's scorecard).

| Site | Best listed submission | Reported score | Executive reading |
|---|---|---:|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5` (60,069 dots, verified) | 0.2477 | First dotted emission (spacing 1.5 px). Superseded everywhere by the 2.8 px spacing. Benchmark only. |
| GEMSDOE25 | `dotted-h19-5-d2-8` (44,090 dots, verified) | 0.2600 | Same surface, kernel-matched spacing 2.8 px (+0.0123 over d1.5). Regenerated *exactly* this session from H19-5 via `dot_thin(·, 2.8)` (symmetric difference 0). |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5` (61,328 dots per repo record) | 0.2449 | Adding 1,259 gap-closure dots to d1.5 *lost* 0.0028 vs its own base — the family's cleanest live refutation of "new dots = new credit". Don't add dots without per-dot efficiency proof. |
| GEMSDOE28 | `h36-1-rung30-blind-r1` | 0.2710 | Highest listed for this repo; a rung-3.0 repack + ring-1 prune of the same family (local manifest calls the file unscored — association unverified). |
| GEMSDOE30 | `d28-poisson300m-offcat-44090` | 0.2600 | 44,090 in the name = the d2.8 dot count; treat as the same emission family unless byte-diffed. No independent strategy is evidenced. |
| GEMSDOE31 | `h27-4-solo-d28` (40,199-dot base, verified via local twin) | 0.2708 | d2.8 minus ring ≤1 px (verified *exactly* this session: symmetric difference 0). The champion's direct parent. |
| **GEMSDOE32** | **`h33-h33-2-b2-…-e5eb6e7e-zeros` (37,654 dots, fetched + verified)** | **0.2778** | **Best in the supplied list.** solo minus ring ≤2 px, nothing added (verified *exactly*). Its own audit JSON calls it UNSCORED with a MODEL projection of 0.2747 — see §2 for the conflict this creates. |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30` | 0.2632 | Name suggests tip/stepover logic on the same base; below blind B2, consistent with "rescued dots earn < break-even". |
| GEMSDOE36 | `anderson-geothermal-pinn-38854` | 0.2750 | Second-highest listed, 0.0028 below the champion. Dot count (38,854) is champion-scale; the PINN framing is not evidence of a different surface — byte-level family check still owed before any novelty claim. |

**Obvious bottom line the owner asked for:** if any single existing file deserves a submission
slot, it is the **GEMSDOE32 H33-2-B2 zeros TIFF**
(`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`, SHA-256 `c55bafc4…6fa9`,
37,654 dots, all-finite [0,1], EPSG:32611, 3730×3292) — **and only if it has not already been
submitted**. Every other site's best is a strictly earlier, dirtier emission of the same dots.
This session deliberately does **not** re-host that file as "ours" (that would be the exact
duplicate the prompt forbids); it is downloaded from GEMSDOE32 (pinned URL in §6). The new file
generated this session (§4) is **not** that file and is **not approved** — the automated gates
rejected it, without any human inspection.

Also from the prompt: competition-leaderboard maxima are stated as both **0.3195** and
**0.4413**. They conflict, neither was freshly retrieved from the authenticated leaderboard in
this session, and neither is bound to any raster above. Both are flagged, neither is adopted.

## 2. Why and how GEMSDOE32 H33-2-B2 got the highest listed score (PhD-level answer)

**How (construction — now byte-verified three independent ways).** This session restored the
SHA-256-pinned inputs and fetched the champion bytes from `GEMSDOE32@012e17b` (hash matches that
repo's own audit JSON). The full lineage is exact, zero symmetric difference at each step
(`evidence/s20_exp1_forensic.json`):

```
H19-5 solid ridge                121,131 dots   (owner-reported 0.1922)
  dot_thin(·, 1.5)                60,069 dots   (owner-reported 0.2477, GEMSDOE24 best)
  dot_thin(·, 2.8)                44,090 dots   (owner-reported 0.2600, GEMSDOE25/30 best)
  − dots at d(catalogue) ≤ 1 px   −3,891 → 40,199  "solo-r1" (owner-reported 0.2708, GEMSDOE31 best)
  − dots at d(catalogue) ≤ 2 px   −2,545 → 37,654  "H33-2-B2" (owner-reported 0.2778, GEMSDOE32 best)
```

The champion **adds zero dots and contains zero new geology** relative to a 0.1922 file. It is
the most aggressively *subtracted* emission of the family's one good surface.

**Why subtraction wins under this metric (the actual mechanism).** The official score is a
distance-tolerant Tversky index, DTI = TPw / (TPw + 0.2·FPw + 0.8·FNw), with triangular kernel
k(d)=max(1−d/300 m, 0) and catalogue pixels masked (`src/gems27/metric.py`, re-derived from the
official problem page; α=0.2, β=0.8). Two consequences dominate everything the 100+ sibling
submissions have measured:

1. **Credit saturates per dot; cost does not.** One dot already earns ≥0.5 credit for every truth
   pixel within 150 m and some credit out to 300 m, so a solid 1-px line pays ~3× the FP mass of
   a 2.8–3 px-spaced dotted line for only ~1.3× the on-line credit (exact table in
   `knowledge/01…md` §2). Spacing 1.5→2.8 px bought +0.0123 (0.2477→0.2600) with no new evidence.
2. **Catalogue-flank dots are near-pure FP.** Hidden truth consists of *new* expert traces, and
   known catalogue pixels are masked out of scoring. A dot 100–200 m beside a mapped fault is
   therefore H19-5's digitisation/scarp shadow of an already-known structure: it pays (almost)
   full FP cost and earns credit only if an unmapped fault happens to run within 300 m parallel
   to the mapped one. The inclusion rule makes the bar explicit — a dot set pays for itself iff
   ΔTP/ΔFP > 0.2·DTI/(1−0.2·DTI) ≈ **0.059** at DTI 0.2778. Rings 1 and 2 were below that bar:
   deleting them gained a remarkably constant **+2.76×10⁻⁶ DTI per dot** (3,891 dots → +0.0108;
   2,545 dots → +0.0070, owner-reported anchors), the signature of removing mass with ≈zero
   marginal credit. Meanwhile every *addition* experiment in the family's history (gap closure
   −0.0028 live; fresh ML/Euler/thermal surfaces 0.02–0.19 owner-reported) failed to clear the
   same bar. That asymmetry — subtraction has never lost, addition has never won — *is* the
   group's empirical law, and the champion is simply its furthest validated application.

**Two honesty caveats that must travel with the 0.2778.**

- The champion file's own audit JSON (fetched this session) embeds the note *"…projected
  live 0.2747; UNSCORED"* and `predicted_leaderboard_dti = 0.27467315976932155`. So at build
  time the file was unscored and 0.2747 was a MODEL. The prompt's 0.2778 may be a later real
  result (it is close to the projection, as a good model's outcome would be) — or the projection
  lineage may have been mis-copied somewhere. Without the submission-page receipt binding
  SHA-256 `c55bafc4…6fa9` to 0.2778, this report can verify the *construction and the
  mechanism*, not the score attribution. Logged in `registry/irregularities.json`
  (`s20-champion-unscored-audit-vs-02778`).
- The per-dot gains above use owner-reported anchors (0.2600/0.2708/0.2778). They are internally
  consistent to 3 significant figures across two independent ring deletions, which is why the
  mechanism is believed; they are still not organizer receipts.

## 3. Can we generate a unique submission above 0.2778? — what it would take

Under the corrected closure DTI = a/(0.8 + 0.2·N/|G|) (MODEL; |G| ≈ 12,226 px from a single
lattice calibration, unconfirmed; `knowledge/01…md` Addendum), at the champion's budget
N=37,654 the *only* route up is weighted-credit fraction a: ≈+24% more credit at the same dot
count reaches the 0.3195 figure quoted in the prompt, and proportionally more for 0.4413. There
are exactly three candidate sources, in descending credibility:

1. **Placement efficiency** — same pool, better dots (each dot covering more probable fault mass
   under the kernel). *Tested this session (H43-1): failed* — see §4. Greedy max-cover improved
   credit/dot by only +0.49% on holdout and *lost* packing capacity, net −0.0074 HOLDOUT-DTI.
2. **Ring-3 deletion** — the champion still carries **2,171 dots at 200–300 m** from the
   catalogue. Linear extrapolation of rings 1–2 predicts ≈**+0.0060 MODEL** (≈0.284) — but ring
   3 is the last ring inside the credit kernel, exactly where a genuine unmapped parallel splay
   would live, so the zero-credit assumption is weakest there; and as a pure subset of the
   champion it is 100% within-3px duplicate under the owner's protocol. Recorded as a labelled
   MODEL only; not built, not submitted.
3. **Genuinely new credit** — structure absent from H19-5's surface (Session 19's ranked slate:
   displaced potential-field piercing markers first). This is the only route to a *large* jump
   and the only route that is protocol-unique by construction (a new surface is not within 3 px
   of the family's dots everywhere). It is also the route that has failed every live test so
   far, because new detectors in this terrain keep earning < 0.059 credit/FP. It needs the
   419 MB training stack (hash-pinned owner mirror, obtainable — sparse git clone worked this
   session while `gh api` was rate-limited) and a fresh preregistered lane with fresh seeds.

**Answer:** above 0.2778 is possible in principle via route 3 (and marginally via a
packing-aware version of route 1, §5), but **no file in existence today is shown to do it**, and
this session's gated attempt made things measurably worse on the only honest local proxy.
Claiming otherwise would be exactly the hallucination the prompt forbids.

## 4. Session 20 experiments (all three, line-verified)

**Experiment 1 — forensics + leakage canary → PASS to proceed.**
Lineage exact (§2). Single-feature AUCs vs seed-340 hidden components (assignment only):
−d_visible 0.72–0.80, ring≤2 0.49–0.50, tip indicator 0.51–0.53, eligibility 0.49, pool 0.49.
Max 0.802 ≤ 0.90 ⇒ no leakage stop. (`evidence/s20_exp1_forensic.json`)

**Experiment 2 — frozen holdout gate, seeds 340–344 → FAIL (decisive).**
HOLDOUT-DTI (`metric.dti_binary`, quadrant component hide-and-recover, visible-only catalogue
quantities, pixel-exact visible masking, 20 cells, **61,613 pooled / 40,739 unique withheld
positives**): champion-analogue C0 = **0.103241**; H43-1 C1 = **0.095807**; pooled gain
**−0.007434**; paired gain 95% CI **[−0.01081, −0.00496]** (4-fold geographic block bootstrap,
S18 method; 20-cell sensitivity [−0.00899, −0.00608]); **0/20 cells positive**. Gates: G1 ✗,
G2 ✗, G3 ✓ (credit/dot 0.047580 vs 0.047350, +0.49%), G4 ✓ (0 dots on visible catalogue),
G5 ✓. Diagnosis, stated as finding not excuse: greedy max-cover is a *maximal* not *maximum*
packing — high-density early picks block line positions, so C1 placed only **87.1%** of C0's
dots per cell; a +0.49% per-dot efficiency cannot repay a −12.9% dot deficit when each missing
dot forfeits its full kernel credit. `dot_thin`'s humble raster-order sweep is, on 1-px ridge
networks, the better packer. (`evidence/s20_holdout.json`)

**Experiment 3 — build + uniqueness + validator → generated, format-valid, NOT unique by
protocol, rejected.**
`gems28-h43-1-tpb2gkc-20261026-76737f19814e-allfinite.tif` (33,354 dots — packing exhausted at
88.6% of the 37,654 target; SHA-256 `960c3d49…f117`; note 104/140 chars). Exact-file validator:
**all hard checks pass** (single-band float32; EPSG:32611; 3730×3292; template transform; no
NaN anywhere in the primary zeros variant; whole-array min 0 / max 1 — the direct fix for the
owner's *"Predicted values must be in range [0, 1]"* error class). Uniqueness vs 22 distinct
local registry dot-sets (+champion education copy): **exact duplicate: NO** (new dot digest;
Jaccard vs champion 0.260); **protocol duplicate: YES** — 94.3% of its dots lie within 3 px of
the champion's (100% vs H19-5/d1.5/d2.8, whose dots tile the same ridges), and pre-placement
surface Spearman vs the H19-5 pool is 0.949 > 0.90. Per the owner's stop rule this is logged as
a duplicate lane and stops here. (`evidence/s20_build.json`)

**Verdict: `negative`.** 🔴 **DO NOT SUBMIT the S20 file.** It is downloadable for
reproducibility only, is banner-marked as such on the site's first screen, and its
holdout + uniqueness failures were computed entirely by the project pipeline — no human
inspection was needed or used, per the owner's requirement. Seeds 340–344 are spent for this
lane; no retuning was performed.

## 5. What to do next (ranked, concrete)

1. **Selector decision on the existing champion (owner action, account-side).** Check the
   DrivenData submissions page: if SHA-256 `c55bafc4…6fa9` (the zeros champion) has no receipt
   yet and the weekly allowance (September rules: 3/week — verify on the page) permits, that
   file — downloaded from GEMSDOE32, §6 — is the single highest-E[V] slot spend available.
   Preserve the receipt; it converts 0.2778 from USER-REPORTED to ORGANIZER-CONFIRMED and
   anchors every future MODEL.
2. **Next lane (new session, new preregistration, fresh seeds ≥350): displaced potential-field
   piercing markers** (Session 19 rank 1; also §2 rank 2 of the S20 preregistration). Restore
   `training_features.tif` via sparse git clone of the pinned mirror (gh-API rate limit
   workaround proven this session), canary each derived band alone, gate exactly as in the S20
   gate script (which is now a tested, reusable harness: `scripts/run_s20_gate.py` pattern +
   `src/gems27/greedy_cover.py` eligibility).
3. **If staying in-family is ever revisited:** packing-first placement — `dot_thin` phase over
   tip-protected eligibles (guarantees champion-scale packing), *then* 1-for-1 greedy swap
   improvement under the kernel, accepted only if pooled holdout Δ>0 with positive paired CI on
   fresh seeds. Expect ≤ +0.002 live (MODEL); it cannot reach 0.3195, and it remains >70%
   within-3px of the champion, so under current protocol it is a *selector-side refinement of
   the champion lane*, not a new parallel-run lane. Say so wherever it appears.
4. **Registry hygiene:** keep one synchronised cross-repo registry (this session's 22-dot-set
   local snapshot is in `evidence/s20_build.json`); GEMSDOE27/30/33/36 best-file bytes still owe
   a same-family byte-diff to close §1's last unverified cells.

**Limitations:** no DrivenData login, receipts, quota, or hidden labels were available or
attempted; inputs are hash-pinned owner mirrors, not organizer-authenticated; the holdout
hides catalogue-internal components and is directionally biased *against* flank deletion
(disclosed in the preregistration before the run); |G| and every MODEL number inherit the
single-lattice calibration uncertainty; `gh api` was rate-limited this session (git sparse
clone fallback used, all SHA-256s verified identically).

## 6. Manual-review links (official first, then pinned owner artifacts)

Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ ·
Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ ·
Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf · Reference solution:
https://github.com/drivendataorg/gems-prize-reference-solution · USGS GeoDAWN:
https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and ·
INGENIOUS: https://gbcge.org/current-projects/ingenious/ · GDR 1391:
https://gdr.openei.org/submissions/1391 · EPSG:32611: https://epsg.io/32611 · Tversky index:
https://en.wikipedia.org/wiki/Tversky_index ·
Champion TIFF (pinned): https://github.com/buffedlizard55-lab/GEMSDOE32/blob/012e17b2a115c3c0d5e7885bea625bf9657c99fc/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif
(SHA-256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`) · Champion audit
JSON (same tree, `…-audit.json`, contains the UNSCORED note) · Nine site scorecard with pinned
per-site TIFFs: `docs/cross-site-review.html`.

**How a submission is made (when a future file is ever approved):** DrivenData → competition
306 → *New submission → File to submit* → choose the single-band float32 `.tif` (or a `.zip`
containing exactly that one TIFF) whose CRS/shape/transform match the sample submission →
paste the file's registered ≤140-character note → submit → save the organizer receipt bound to
the file's SHA-256. The full gated procedure is on `docs/executive-summary.html`. **Do not
perform these steps with the S20 file.**
