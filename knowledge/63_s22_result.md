> **S22-AUDIT ERRATUM (2026-10-26):** The source run card's canary object is empty despite a true pass flag; no feature-alone coverage was established. Its stated 60,988 withheld positives conflicts with 36,596 summed over the 12 detail rows. The historic code uses a local quadrant-clipped proxy and unweighted cell means, not the shared pooled whole-segment holdout; no 95% CI is recorded. Independent final-dot checks pass only within 46 local non-self TIFFs plus nine named site rasters (maximum 53.56%); the complete registry and pre-placement surface are unavailable. The TIFF is research-only and **DO NOT SUBMIT**. See [corrected audit](../evidence/s22_sign_audit.json). Exact original runner bytes are snapshotted; its entry point is blocked.

# S22 Result — Signed Piedmont Break-in-Slope (H43-2-SIGN)

- Date: 2026-10-26/27 UTC
- Lane: H43-2-SIGN, preregistered in 62_s22_preregistration.md, seeds 360-362 (fresh)
- Experiments: 3/3 (surface + canary + pre-novelty; LOSFO holdout; emission + post-novelty + validation)
- Verdict: NEGATIVE, submission_ready false, 0 slots spent
- TIFF: gems28-s22-signed-piedmont-20261026-08703322d2af-{allfinite,nan,zip}, 37692 dots, SHA d9c2357...
- Holdout: `HOLDOUT-DTI` 0.0547 vs 0.1219 baseline (Δ -0.0673, 60,988 withheld positives; 12 cells), wholly negative. The source run card records no paired 95% confidence interval; do not infer one.
- Canary: ~0.54-0.58 all PASS
- Uniqueness: 22 prior rasters in this run's registry, max overlap 43.3%, max |r| 0.028 — PASS against that scoped set only; not proof against all historical or concurrent private rasters.
- Projection: ~0.18 [0.16, 0.20] is a model projection anchored to an unverified 0.2778 claim, not a score or confidence interval.
- Validator: exact grid, {0,1} in [0,1], no NaN inside — PASS
- Source/provenance: owner-mirrored DEM/LiDAR descriptors are not organizer-authenticated; no official receipt ties a score to this TIFF. This merge reconciliation did not independently refresh official competition/data pages or the public leaderboard; see the repository's [source ledger](../docs/sources.html) and retain its access limitations.
- Next: H43-3 Euler SI=0 is a historical proposal, not an assigned lane or permission to experiment. A new run still requires a fresh preflight and explicit lane authorization.

Full details in docs/session22-result.html and evidence/s22_run_card.json
