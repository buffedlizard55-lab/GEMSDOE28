# Session 13 close-out — deliverables, three passes, limitations, AI-use disclosure

Written at the end of Session 13c, after PR #24 merged into `main` (`4d5c810`). Everything below is either
a file in this repository or a `gh`-verified remote state; nothing is inferred from an unreachable page.

## 1. What this session changed

| deliverable (standing task) | session state |
|---|---|
| Submission-ready single-band GeoTIFF, one click, at the top of the site, unique name, ≤200-char note | **Yes.** Primary `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`, 37,660 cells, note 192/200, SHA-256 + byte count printed above the fold on `index.html`; raw-repository mirror as a Pages-independent fallback; `verify_downloads.py` 208/208 checks PASS (format, grid, CRS, range, mask, hash). |
| Explain *why* 0.2600 won, PhD-level; is >0.26 reachable | `README` §3.9/§3.9b + `knowledge/33`/`35`. The interleaved-gain explanation is now **measured, not argued**: the interleaved hidden truth is 100 % catalogue pixels, and the two arms that were promoted on it earned −0.000037 (far field) and 0.0312 credit/dot (vs the 0.0548 live bar). Cracking 0.3195 still needs ≈ +1,151 px of credit ≈ 2,600–3,400 new dots, and this session narrowed the source: it must be **new detection**, not selection. |
| 3–5 new ranked hypotheses, validated before a slot | `knowledge/31` (five arms) + this session's tests: H37-1 → **demoted** (`knowledge/33`), H37-3 → **refuted as promotable** (`knowledge/35`). H37-2 is next. No submission slot was spent: the account shows no candidate of this repository with an organizer score, and no slot was used. |
| Deep literature/data research from official verified sources | Unchanged this session except the Euler basis already cited (Reid et al. 1990, DOI `10.1190/1.1442774`) and the H37-3 arm's use of it; the source feed (`docs/data/feed.json`) was last refreshed by the Source-feed workflow at 17:56:48Z on 2026-10-03 (10 sources, hashes recorded). |
| No manual input; flag irregularities | **77 items** in `registry/irregularities.json`, five added/changed this session: the proxy-artefact item resolved-as-confirmed, the H37-3 rate note, the cross-seed-integrity trap, the parallel-session naming collision, and the Pages build note (the 21:49Z failure is transient; the builds for `f91e3c2`, `8408037`, `4d5c810` are all *built* per `gh api .../pages/builds`). |
| Run three passes; PR → merge | PR **#22** (H37-1 far-field demotion) and PR **#24** (H37-3 + close-out) both MERGED into `main`; `origin/main` = `4d5c810`. |
| Core Values as focal points | Maximize P(Win): two promotion claims were killed by their own preregistered tests, which is the cheapest possible time to lose them. Own the Outcome: both negative results are published with their numbers, including the one that demoted the file this session had just promoted. |

## 2. The three passes

**Pass 1 — implement and verify.** Copied the far-field analysis into the repo as
`scripts/analyze_farfield.py`, wrote `knowledge/33`, applied the preregistered demotion through
`docs/downloads/manifest.json`, `scripts/build_site.py`, the README slot table, the answer paragraph, the
new §3.9b, `registry/next_hypotheses.json` and `registry/irregularities.json`; rebuilt the site and
confirmed `verify_downloads.py` 208/208. Then preregistered (`knowledge/34`), implemented
(`--euler-licence` + three helpers), tested (3 new tests) and ran H37-3 on its own LOSFO decade, and
wrote `knowledge/35` with `scripts/analyze_h37_3.py` and the integrity record.

**Pass 2 — review bugs and edge cases, and fix.** Four real defects were found and fixed, each with the
reason recorded:
1. **My own analyzer's C4 compared arms across different seed sets** (fresh 260–264 vs stored 210–214)
   and reported a spurious 3.5e-3 "integrity failure" that was pure LOSFO seed variation. Replaced with a
   same-seed reproduction (the patched harness re-ran the spent seed-181 panel and reproduces the
   pre-patch base arms to the last bit) plus a spread check. Registered.
2. **A unit-test edge case**: the licence-spacing test placed the blocking base dot 2 px from a candidate
   that was supposed to survive, so the test failed for the right reason and the test — not the code —
   was wrong. Fixed and documented in `tests/test_euler_licence.py`.
3. **`docs/downloads/manifest.json`'s `promotion_rule` did not carry the far-field requirement**, so a
   future arm could have cited the old rule and skipped it. Now states the rule explicitly with the
   H37-1 precedent.
4. **A cross-session naming collision**: `thinning.directional_dot_thin` (added by a parallel session)
   calls itself "the candidate H37-1" in its docstring while H37-1 is the metric-aware packing arm.
   Flagged in the registry; no measured result is affected because the function is additive and
   `dot_thin` is untouched. **Session 14 resolution:** H38-1 is now reserved for the shallow SI-0 Euler × gravity-gradient × low-relief test; the parallel directional experiment remains distinct and must use H39 or later if revived (`registry/irregularities.json`).

**Pass 3 — re-check against the original request and improve.** Re-verified every standing requirement
(slot order, note length, range/format audit, exec-summary subpage, feed freshness, sources table,
irregularities count, no-drivendata policy in code — the feed script's hard guard is unchanged), and
improved two things the original request implies but the repo did not yet state: the far-field rule now
sits in the promotion rule itself, and the executive summary's "state" paragraph leads with what was
falsified this session instead of the previous session's closure.

## 3. Limitations (stated plainly)

* **Both of this session's results are far-field *rule* tests on the detector's ridge pool**, not
  measurements of the shipped H19-5 artifact. They establish that the packing rule does not transfer and
  that the licence does not pay; they do not measure either file end-to-end on the live population.
* **The live break-even 0.0548 and the live projections are model quantities**, built from the
  owner-reported 0.2600 and the official metric constants (|G| 12,226; α 0.2; β 0.8). No candidate of
  this repository has an organizer score; the only verified live numbers remain the owner-reported
  leaderboard rows.
* **H36-1, the file that just returned to the one-click slot, has never been measured far field.** Its
  support is the live-anchored dose ladder, which is a different axis from the ordering rule that failed.
  This is the top queued measurement and it is one harness run.
* **Every geological ADD arm in the ledger is untested at the point of emission.** H37-2's expected value
  is a prior, not a measurement; the H37-3 result (real signal, 1.65× random, still below the bar) is the
  best available calibration of how hard that bar is.
* **External-data arms remain gated on the Actions bridge.** `gdr.openei.org`, `sciencebase.gov`,
  `doi.org`, `usgs.gov` and `docs.nlr.gov` are all unreachable from the build sandbox (HTTP 000 / TLS
  handshake failure); the bridge workflows are the only route and the last `fetch-gdr-external-layers`
  run succeeded (2 m 11 s, `gh run list`), but no paleo-geothermal clip is committed.
* **Seed discipline is a finite resource.** Spent: 100–214, 210–214, 220–259, 250–259, 260–264.
  Free: 215–219 and 265+. Two arms per two decades is the observed burn rate.
* **The site cannot be fetched from the build sandbox** (`buffedlizard55-lab.github.io` → curl exit 35),
  so the live Pages rendering is verified only through `gh api .../pages/builds` (status *built*) and
  the local byte-identical rebuild, never by opening the page.
* **`registry/live_scores.json` and the leaderboard snapshot are owner/sibling-quoted, not
  agent-verified**; the hard repository rule forbids this agent from requesting drivendata.org.

## 4. AI-use disclosure (required in the final-round narrative)

This work was produced by an AI agent (Arena.ai Agent Mode) operating autonomously on a defined brief
inside a git repository, with no manual input from the owner beyond the standing brief. Concretely:
the agent designed and ran every experiment, wrote every script, generated every number, and
self-reviewed through the three passes above; the owner supplied the competition frame, the
repository's prior sessions, the data mirrors and the live leaderboard rows. **All code and all
analysis in this repository are machine-generated**; the physics and the published sources it cites are
real and linked for manual review, and the repository's own rule is that no figure is asserted without
a file, a hash or a committed script behind it. Any final-round narrative must state this, and must
carry the same limitation set as §3 rather than the optimistic reading alone.

## 5. Next steps, in order

1. **LOSFO far-field test of the H36-1 dose change** (the file now holding the one-click slot) — one
   harness run on free seeds 265–269.
2. **H37-2 concealed-fault conjunction** — preregister with a licence rate sized to clear 0.0548, since
   H37-3 proved that a real 1.65× signal can still lose.
3. Keep the site's slot order and the note ≤200 characters in sync with the manifest on every change;
   the promotion rule now requires a far-field number for any future promotion that rests on the proxy.
4. Refresh the source feed (the daily workflow does it; the last manual check was 17:56Z today) and
   re-check `gh api .../pages/builds` after the next site change.
