# Current owner request — 2026-10-25 operational prompt

Read this and the current README notice before every session. This is a normalized requirements
record, not a claim to be a verbatim export of the chat. Historical verbatim prompts remain in
README. The original current chat is authoritative where wording differs.

## Highest urgency

> MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS
> SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF
> SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF
> SUBMISSION.

The goal is to compete for the top prize with scientifically distinct fault-prediction strategies,
not merely rename files or optimize a public-label proxy. Build a clean GitHub Pages site with the
current decision and one-click `.tif` download visible at the beginning, an executive-summary
submission guide, a unique submission name and a ≤140-character identifying note. Project inspection
must be automated, not deferred to a human inspector. A file-format pass is not a high-performance
validation or permission to spend a slot. Never promise that an untested file will beat a score.

## Parallel-run protocol

1. Stay in a single explicit method lane. If no paragraph is supplied, disclose that ambiguity;
   do not silently claim an external exclusive assignment. Check the surface BEFORE placement and
   final dots against the registry. Spearman >0.90 OR >70% of support/dots within 3 px of ANY one
   registry raster means duplicate: log and stop. Do not copy old submissions as new predictions.
2. Reuse the template cached feature stack, shared holdout evaluator and submission writer.
   Hide entire fault segments/systems with a buffer. Every catalogue feature must use only visible
   faults. Mask visible faults pixel-exactly. Pool DTI with α=0.2, β=0.8 and 300 m triangular kernel.
   Fix any shared-tool defect once in the template; report it, do not maintain a private fork.
3. Label computed performance HOLDOUT-DTI, with evaluator version, withheld-positive count and
   95% CI. ORGANIZER-CONFIRMED requires a submission-page receipt. Projections are not scores.
   Preserve user-supplied unverified claims as such; never fabricate receipts to force a label.
4. Test each feature alone before trusting results; AUC >0.90 is leakage until explained.
5. End with one JSON run card: hypothesis; mechanism; named non-fault mimic; holdout DTI + CI;
   registry correlation/overlap; raster SHA-256; validator output (no NaN inside footprint, values
   [0,1], matching CRS/shape/transform); submission name and short note; promote/negative verdict.
   Negative results are deliverables.
6. Stop after THREE experiments OR TWO hours. Do not pick/upload submissions. A separate selector
   controls promotion to a weekly slot within the authenticated page allowance.

## Research and implementation requirements

- Review repo and previous-session next steps first. Prioritize the highest reported artifacts in
  GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36. Study the GEMSDOE32 H33-2-B2 artifact associated
  in the user's lists with 0.2778; explain construction and possible metric mechanism without
  claiming hidden truth or score causation that cannot be verified.
- The prompt quotes conflicting leaderboard tops 0.4413 and 0.3195. Obtain a dated official
  observation when possible; distinguish public observation from a raster-linked receipt.
- Before implementing, rank 3–5 hypotheses not yet executed here by expected improvement and cost.
  For each: specific layers, physical transform/signature, why it might recover faults missing from
  USGS/INGENIOUS, differences from existing implementation, and named non-fault mimics. Scientific
  novelty is not established merely by different pixels. Any new data requirement needs a specific
  free official source and an actual availability check before it is called viable.
- Validate the top candidate on buffered spatial holdouts before a slot. It must beat the frozen
  current best with robust uncertainty/spread gates. Do not spend a slot on an unvalidated idea.
- Research physical mechanisms deeply and maintain an auditable source/knowledge table. Do not
  confuse faults, permeability, geothermal favorability and verified geothermal vents. Preserve
  official links for manual review without requiring manual geological inspection to determine
  the pipeline's disposition. Autonomous operation cannot confer legal eligibility or authenticate
  private data/receipts that it cannot access.
- Fix the observed portal range-error risk using independent exact-file checks, not a silent clamp
  or a claim of guaranteed portal acceptance. A valid submission is a single-band GeoTIFF (or ZIP
  containing one) with template CRS, shape and geotransform, and finite interior confidence [0,1].
- Restore actual available data rather than repeating a stale data-placement blocker. Use official
  external sources and disclosed, hash-pinned owner mirrors as distinct provenance classes. Keep
  large arrays and datasets out of Git. CPU/GPU requirements must reflect the actual method.
- Store the standing brief in README and read it every session. Maintain an up-to-date public-source
  feed where policy permits; never fabricate a refresh time or build a DrivenData scraper/login bot.
- Core values: **Maximize P(Win)** (choose evidence-backed tradeoffs, protect scarce slots) and
  **Own the Outcome** (own end-to-end file, UI, evidence and tests; act autonomously on defects).
- THREE passes: (1) implement and verify; (2) review for bugs, omissions, assumptions and edge cases,
  fix them; (3) check against the original request and improve accuracy/reliability/completeness.
  Flag irregularities explicitly, with no invented measurements or unsupported conclusions.
- Create a pull request and merge it to main after verification. Keep work on the Arena session
  branch. State limitations and prioritized next-session work. A code PR merge is not a competition
  submission or slot selection.

## Requested source starting points

- [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem, metric and file format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [About / cited literature](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official reference code](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS](https://gbcge.org/current-projects/ingenious/)
- [DOE GDR compilation 1391](https://gdr.openei.org/submissions/1391)
- [EPSG:32611](https://epsg.io/32611)
- [Tversky index background](https://en.wikipedia.org/wiki/Tversky_index)

The current request also includes historical result lists for GEMSDOE through GEMSDOE92,
Dropbox data links and a prior data-placement/training statement. Those are user-supplied context,
not verified current facts or proof that every historical artifact has been reviewed. S18's declared
nine-repository snapshot and actual input restoration are explicitly bounded in its run card.
