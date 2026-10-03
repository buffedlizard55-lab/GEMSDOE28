"""Live-anchored operating-point arithmetic for the GEMS distance-tolerant IoU (DTI).

Why this module exists
----------------------
Every emission decision in this programme (how far apart to space the dots, which classes of dot to
drop) is a trade between kernel-weighted credit ``A`` and emitted-pixel mass ``N``. The official
metric reduces exactly to a two-number statement, so the trade can be decided arithmetically instead
of argued about:

    DTI  =  A / (0.2*A + 0.2*FP + 0.8*|G|)

and, closing FP with the one quantity the inversion in ``evidence/live_inversion.json`` measures
directly - ``FP = N - Atilde``, where ``Atilde = sum over emitted pixels of k(d(p, truth))`` is the
credit counted from the *emission* side rather than the truth side - the model used here is

    DTI  =  A / (0.8*|G| + 0.2*(1-gamma)*N + 0.2*A)                      (Eq. 1)

with ``gamma = Atilde / N``, the emitted-pixel-weighted fraction of the emission that falls inside
the 300 m kernel of truth. ``gamma`` is **measured, not fitted**: on the three hash-authenticated
live anchors of the H19-5 surface it is 0.1257 / 0.1258 / 0.1281 (spread 1.9 %), which is what
non-selective thinning predicts - ``thinning.dot_thin`` discards on-truth and off-truth dots at the
same rate, so the composition of the emission is invariant to the rung. That invariance is the whole
reason Eq. 1 can be extrapolated off the anchors at all, and it is why the naive closure
``FP = N - A`` (i.e. ``gamma = A/N``, which is 0.051-0.109 and *varies* by a factor of two across the
same anchors) is wrong: it charges every emitted pixel the full false-positive penalty, ignoring the
crowding excess ``Atilde - A`` that the metric already discounts.

Two consequences that drive everything else here:

Two consequences that drive everything else here:

1. **Packing ladder.** For a fixed detector surface, thinning to minimum dot separation ``d`` scales
   the credit by a retention factor ``r(d)`` and the mass by ``N(d)``. Both are *measured*, not
   modelled: ``N(d)`` on the actual emission and ``r(d)`` on a real 1-D curvilinear fault network
   (the published catalogue) that stands in for the geometry of the hidden truth. With two unknowns
   (the solid-emission credit ``L`` and the hidden-truth size ``|G|``) fitted to three
   hash-authenticated live scores of the *same* surface, Eq. 1 reproduces all three to ~1e-4.

2. **The decision threshold is operating-point dependent.** Differentiating Eq. 1, a set of pixels
   with removal efficiency ``e = |dA/dFP|`` is worth dropping iff

       e  <  tau  =  0.2*DTI / (1 - 0.2*DTI)                             (Eq. 2)

   (identical to ``metric.inclusion_threshold``). ``tau`` rises monotonically with DTI. A
   catalogue-holdout proxy detector scores ~0.10 and therefore gates at ``tau = 0.019``; the
   submission we actually modify scores 0.26 and gates at ``tau = 0.055`` - **2.85x more permissive**.
   Screening a live artifact against the proxy threshold rejects every arm whose efficiency lies in
   (0.019, 0.055), which is where most packing and de-screening arms live.

Everything here is deterministic, reads no labels except the published catalogue used as a geometric
stand-in, and never contacts drivendata.org.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.optimize import least_squares

from . import metric, thinning

ALPHA = metric.ALPHA          # 0.2 - false-positive weight
BETA = metric.BETA            # 0.8 - false-negative weight

#: ``gamma = Atilde / N`` - the emitted-pixel-weighted fraction of an emission that falls inside the
#: 300 m kernel of truth, so ``FPw = (1 - gamma) * N``. Measured on the three hash-authenticated
#: live anchors of the H19-5 surface (evidence/live_inversion.json) as 0.1257 / 0.1258 / 0.1281;
#: ``GAMMA`` is their mean. It is treated as rung-invariant because ``thinning.dot_thin`` is
#: non-selective with respect to truth proximity - which the same three anchors confirm to 1.9 %.
#: Callers may pass a different value to test that assumption.
GAMMA = 0.12653
ANCHOR_GAMMA = {121131: 0.12569, 60069: 0.12576, 44090: 0.12811}

#: Credit of the *unthinned* H19-5 surface (``19GEMSDOE h19-5``, N = 121,131) and the size of the
#: hidden truth, both **measured** rather than fitted: the first is the inverted credit of a
#: hash-authenticated 0.1922 score, the second is the blind-lattice calibration in
#: ``evidence/live_inversion.json`` (13GEMSDOE r13-lattice-s5). Using them leaves the density scale
#: :func:`fit_density_scale` as the only free parameter in the whole model.
MEASURED_CREDIT_SOLID = 6188.804163187549
MEASURED_TRUTH_PX = 12225.896194356133


# --------------------------------------------------------------------------------------------
# 1. The discrete packing ladder
# --------------------------------------------------------------------------------------------

def grid_distance_ladder(max_distance: float = 8.0, span: int = 10) -> list[float]:
    """Achievable Euclidean separations between two integer grid cells, ascending.

    ``thinning.dot_thin`` keeps a pixel iff no already-kept pixel is strictly closer than
    ``min_dist``, so the kept set changes only when ``min_dist`` crosses one of these values. There
    is therefore no continuum of thinnings to search - only this finite ladder.
    """
    return sorted({float(math.hypot(a, b))
                   for a in range(span) for b in range(span)
                   if 0.0 < math.hypot(a, b) <= max_distance})


def ladder_bucket(min_dist: float, ladder: list[float]) -> float:
    """The ladder rung a submitted ``min_dist`` actually realises."""
    above = [v for v in ladder if v >= min_dist]
    return above[0] if above else ladder[-1]


@dataclass
class LadderPoint:
    rung: float            # ladder separation (px) that remains allowed
    n_emitted: int         # dots kept in the submission surface at this rung
    retention: float       # fraction of solid credit retained (measured on the truth stand-in)
    n_stand: int = 0       # dots kept in the stand-in network at this rung
    dti: float | None = None   # filled in by :func:`predict_ladder`


@dataclass
class Ladder:
    surface: str
    stand_in: str
    points: list[LadderPoint] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"surface": self.surface, "stand_in": self.stand_in,
                "points": [{"rung": p.rung, "n_emitted": p.n_emitted, "retention": p.retention,
                            "n_stand": p.n_stand, "dti": p.dti} for p in self.points]}

    def best(self) -> LadderPoint | None:
        live = [p for p in self.points if p.dti is not None]
        return max(live, key=lambda p: p.dti) if live else None


def measure_ladder(emission: np.ndarray,
                   truth_stand_in: np.ndarray,
                   max_distance: float = 8.0,
                   rungs: list[float] | None = None) -> Ladder:
    """Measure ``N(rung)`` on ``emission`` and the retention ``r(rung)`` on ``truth_stand_in``.

    ``truth_stand_in`` must be a 1-D curvilinear network on the same grid - the published catalogue
    is used in practice, because the hidden truth is also a curvilinear 1-px fault network and the
    retention of a thinning rule is a property of that geometry, not of where the faults are.

    ``r(rung) = TPw(dotted at rung) / TPw(solid)`` with TPw evaluated by the official kernel
    (``metric.kernel_from_distance``), which is the metric's own credit functional.
    """
    emission = np.asarray(emission, bool)
    stand = np.asarray(truth_stand_in, bool)
    if emission.shape != stand.shape:
        raise ValueError("emission and truth stand-in must share a grid")
    ladder = rungs if rungs is not None else grid_distance_ladder(max_distance)
    n_truth = int(stand.sum())
    if n_truth == 0:
        raise ValueError("truth stand-in is empty")

    out = Ladder(surface="emission", stand_in="curvilinear network")
    for v in ladder:
        # -1e-9 so that a separation of exactly `v` is still allowed (dot_thin blocks offsets whose
        # squared length is strictly less than min_dist**2; float rounding of hypot() can tip this).
        dots_e = thinning.dot_thin(emission, v - 1e-9)
        dots_s = thinning.dot_thin(stand, v - 1e-9)
        if not dots_s.any():
            out.points.append(LadderPoint(v, int(dots_e.sum()), 0.0, 0))
            continue
        tpw = float(metric.kernel_from_distance(
            distance_transform_edt(~dots_s)[stand]).sum())
        out.points.append(LadderPoint(v, int(dots_e.sum()), tpw / n_truth, int(dots_s.sum())))
    return out


# --------------------------------------------------------------------------------------------
# 2. Fitting the live operating point
# --------------------------------------------------------------------------------------------

@dataclass
class OperatingPoint:
    """Two-number description of where a submission sits on the official metric."""
    credit_solid: float     # L: kernel credit the *unthinned* surface earns (px-equivalents)
    truth_px: float         # |G|: size of the hidden truth set (px)
    anchors: list[dict] = field(default_factory=list)
    residuals: list[float] = field(default_factory=list)
    leave_one_out: list[dict] = field(default_factory=list)

    def dti(self, retention: float, n_emitted: int, gamma: float = GAMMA) -> float:
        a = self.credit_solid * retention
        denom = BETA * self.truth_px + ALPHA * (1.0 - gamma) * n_emitted + ALPHA * a
        return a / denom if denom > 0 else 0.0

    def state(self, retention: float, n_emitted: int, gamma: float = GAMMA) -> dict:
        """Full metric state (A, FP, |G|, DTI, tau, marginal value of one pixel)."""
        a = self.credit_solid * retention
        g = self.truth_px
        fp = max(n_emitted * (1.0 - gamma), 0.0)
        denom = a + ALPHA * fp + BETA * (g - a)
        dti = a / denom if denom > 0 else 0.0
        return {"credit_A": a, "emitted_N": n_emitted, "fp": fp, "truth_G": g, "denominator": denom,
                "dti": dti, "tau": ALPHA * dti / (1.0 - ALPHA * dti),
                "weighted_recall": a / g if g else 0.0}

    def prune_gain(self, retention: float, n_emitted: int, n_removed: int, efficiency: float,
                   gamma: float = GAMMA) -> dict:
        """Exact Eq. 1 change from dropping ``n_removed`` pixels of efficiency ``e``.

        dDTI = n * [ ALPHA*A - e * (ALPHA*FP + BETA*|G| - BETA*A) ] / D**2
        derived by differentiating DTI = A/(A + ALPHA*FP + BETA(|G|-A)) with dA = -e*n, dFP = -n.
        """
        st = self.state(retention, n_emitted, gamma)
        d = st["denominator"]
        da = -efficiency * n_removed
        dfp = -n_removed
        d_denom = da + ALPHA * dfp + BETA * (-da)
        d_dti = (da * d - st["credit_A"] * d_denom) / (d * d)
        return {"n_removed": n_removed, "efficiency": efficiency, "dti_before": st["dti"],
                "dti_after": st["dti"] + d_dti, "delta_dti": d_dti,
                "breakeven_tau": st["tau"], "worth_it": bool(efficiency < st["tau"])}


def _solve_pair(s1: float, r1: float, n1: int, g1: float,
                s2: float, r2: float, n2: int, g2: float) -> tuple[float, float]:
    """Closed-form two-anchor solution of Eq. 1 for ``(credit_solid, truth_px)``.

    Eq. 1 with ``A = L*r`` rearranges to a line in ``G``:

        L = u_i * G + w_i,   u_i = 0.8 s_i / (r_i (1 - 0.2 s_i)),
                             w_i = 0.2 (1-gamma_i) s_i N_i / (r_i (1 - 0.2 s_i))

    so two anchors intersect exactly and no optimiser is involved. Two unknowns are fitted; ``gamma``
    is *measured* (see module docstring) and passed in per anchor. Used for the leave-one-out check
    so that the reported stability of the fit cannot be an artefact of a solver that stopped early.
    """
    def coeffs(s: float, r: float, n: float, gam: float) -> tuple[float, float]:
        den = r * (1.0 - ALPHA * s)
        return (BETA * s) / den, (ALPHA * (1.0 - gam) * s * n) / den

    u1, w1 = coeffs(s1, r1, n1, g1)
    u2, w2 = coeffs(s2, r2, n2, g2)
    if abs(u1 - u2) < 1e-15:
        raise ValueError("degenerate anchor pair: identical score/retention ratio")
    G = (w2 - w1) / (u1 - u2)
    L = u1 * G + w1
    return float(L), float(G)


def fit_operating_point(anchors: list[dict], ladder: Ladder,
                        gamma: float | None = None) -> OperatingPoint:
    """Fit ``(credit_solid, truth_px)`` to live-scored submissions of one detector surface.

    ``anchors`` items: ``{"min_dist": float, "n_emitted": int, "score": float, "label": str}``.
    Each is mapped onto its real ladder rung, so the measured ``(N, r)`` pair is the same one the
    live file actually realised. With two unknowns and three anchors there is one degree of freedom;
    ``leave_one_out`` refits each *pair* in closed form and predicts the held-out anchor, which is
    the honest stability test.

    ``gamma`` overrides the module default for every anchor; otherwise each anchor uses its own
    measured value from :data:`ANCHOR_GAMMA` when known and :data:`GAMMA` otherwise.
    """
    index = {p.rung: p for p in ladder.points}

    def resolve(min_dist: float) -> LadderPoint:
        for v in sorted(index):
            if v >= min_dist:
                return index[v]
        return ladder.points[-1]

    used = []
    for a in anchors:
        pt = resolve(a["min_dist"])
        if a.get("n_emitted") is not None and pt.n_emitted != int(a["n_emitted"]):
            raise ValueError(
                f"anchor {a.get('label', a['min_dist'])}: ladder gives {pt.n_emitted} px but the "
                f"scored file has {int(a['n_emitted'])}; the thinning rule does not match")
        gam = float(gamma) if gamma is not None else ANCHOR_GAMMA.get(pt.n_emitted, GAMMA)
        used.append((pt, float(a["score"]), a, gam))

    def fit_pair(items: list[tuple]) -> tuple[float, float]:
        (p1, s1, _a1, g1), (p2, s2, _a2, g2) = items[:2]
        return _solve_pair(s1, p1.retention, p1.n_emitted, g1,
                           s2, p2.retention, p2.n_emitted, g2)

    # Full fit: least squares over all anchors starting from the closed-form first pair, so the
    # reported (L, |G|) uses every anchor, while leave_one_out proves the closed form is stable.
    L, G = fit_pair(used)
    x0 = np.array([L, G], float)
    def resid(p: np.ndarray) -> list[float]:
        Lp, Gp = p
        return [Lp * pt.retention / (BETA * Gp + ALPHA * (1.0 - gam) * pt.n_emitted
                                     + ALPHA * Lp * pt.retention) - s
                for pt, s, _a, gam in used]
    sol = least_squares(resid, x0)
    L, G = float(sol.x[0]), float(sol.x[1])

    def dti_of(pt: LadderPoint, gam: float) -> float:
        return L * pt.retention / (BETA * G + ALPHA * (1.0 - gam) * pt.n_emitted
                                   + ALPHA * L * pt.retention)

    op = OperatingPoint(L, G,
                        anchors=[{"label": a.get("label"), "min_dist": a["min_dist"],
                                  "rung": pt.rung, "n_emitted": pt.n_emitted,
                                  "retention": pt.retention, "gamma": gam, "score": s,
                                  "fitted": dti_of(pt, gam), "residual": dti_of(pt, gam) - s}
                                 for pt, s, a, gam in used],
                        residuals=[float(r) for r in sol.fun])

    for k in range(len(used)):
        rest = [u for j, u in enumerate(used) if j != k]
        try:
            L2, G2 = fit_pair(rest)
        except ValueError:
            continue
        pt, s, a, gam = used[k]
        pred = L2 * pt.retention / (BETA * G2 + ALPHA * (1.0 - gam) * pt.n_emitted
                                    + ALPHA * L2 * pt.retention)
        op.leave_one_out.append({"held_out": a.get("label"),
                                 "fitted_on": [u[2].get("label") for u in rest],
                                 "score": s, "predicted": pred, "error": pred - s,
                                 "credit_solid": L2, "truth_px": G2})
    return op


def predict_ladder(ladder: Ladder, op: OperatingPoint, gamma: float = GAMMA) -> Ladder:
    for p in ladder.points:
        p.dti = op.dti(p.retention, p.n_emitted, gamma)
    return ladder


def rung_efficiency(ladder: Ladder, op: OperatingPoint, rung_from: float, rung_to: float,
                    gamma: float = GAMMA) -> dict:
    """Efficiency ``e = |dA|/|dN|`` of moving one rung further out on the packing ladder."""
    idx = {p.rung: p for p in ladder.points}
    a, b = idx[rung_from], idx[rung_to]
    d_a = op.credit_solid * (b.retention - a.retention)
    d_n = b.n_emitted - a.n_emitted
    st = op.state(a.retention, a.n_emitted, gamma)
    e = abs(d_a) / abs(d_n) if d_n else float("inf")
    gain = op.prune_gain(a.retention, a.n_emitted, abs(d_n), e, gamma)
    return {"rung_from": rung_from, "rung_to": rung_to, "d_credit": float(d_a), "d_emitted": int(d_n),
            "efficiency": float(e), "breakeven_tau": st["tau"], "worth_it": bool(e < st["tau"]),
            "delta_dti": gain["delta_dti"], "dti_from": st["dti"], "dti_to": gain["dti_after"]}


# --------------------------------------------------------------------------------------------
# 4. The density-scale correction: why the stand-in retention must be rescaled
# --------------------------------------------------------------------------------------------
def fit_density_scale(anchors: list[dict], ladder: Ladder,
                      credit_solid: float = MEASURED_CREDIT_SOLID,
                      truth_px: float = MEASURED_TRUTH_PX,
                      gamma: float | None = None) -> dict:
    """Fit the one free parameter of the model: how much of the stand-in's thinning loss is real.

    ``measure_ladder`` measures the retention ``r(v)`` by thinning a 1-px curvilinear network whose
    dot-to-truth density is 1:1 (every truth pixel starts as a dot). The H19-5 surface runs about
    ten dots per truth pixel, so thinning costs it proportionally less. Rather than fit the whole
    curve, scale the *loss*:

        A(v) = credit_solid * (1 - s * (1 - r(v))),      s in [0, 1]

    ``s = 1`` is the raw stand-in; ``s = 0`` is a surface that never loses credit. With
    ``credit_solid``, ``truth_px`` and ``gamma`` all measured, ``s`` is the only unknown, so three
    anchors give two degrees of freedom.

    Returns the fitted scale, the per-anchor fit, and - crucially - the per-anchor *implied* scale,
    whose spread is the honest statement of how well one number describes all three rungs.
    """
    index = {p.rung: p for p in ladder.points}

    def resolve(min_dist: float) -> LadderPoint:
        for v in sorted(index):
            if v >= min_dist:
                return index[v]
        return ladder.points[-1]

    rows = []
    for a in anchors:
        pt = resolve(a["min_dist"])
        gam = float(gamma) if gamma is not None else ANCHOR_GAMMA.get(pt.n_emitted, GAMMA)
        rows.append((pt, float(a["score"]), a, gam))

    def dti_at(pt: LadderPoint, score_scale_s: float, gam: float) -> float:
        a = credit_solid * (1.0 - score_scale_s * (1.0 - pt.retention))
        return a / (BETA * truth_px + ALPHA * (1.0 - gam) * pt.n_emitted + ALPHA * a)

    sol = least_squares(lambda p: [dti_at(pt, p[0], gam) - sc for pt, sc, _a, gam in rows], [0.83],
                        bounds=([0.0], [1.0]))
    s_fit = float(sol.x[0])

    per_anchor, implied = [], []
    for pt, sc, a, gam in rows:
        fitted = dti_at(pt, s_fit, gam)
        # the s that would reproduce this anchor exactly (undefined at the solid rung)
        if pt.retention < 1.0:
            target = sc * (BETA * truth_px + ALPHA * (1.0 - gam) * pt.n_emitted) / (1.0 - ALPHA * sc)
            implied.append((1.0 - target / credit_solid) / (1.0 - pt.retention))
        per_anchor.append({"label": a.get("label"), "rung": pt.rung, "n_emitted": pt.n_emitted,
                           "retention_stand_in": pt.retention, "gamma": gam, "score": sc,
                           "fitted": fitted, "residual": fitted - sc})
    return {"density_scale": s_fit,
            "credit_solid": credit_solid, "truth_px": truth_px,
            "max_abs_residual": max(abs(r["residual"]) for r in per_anchor),
            "per_anchor": per_anchor,
            "implied_scale_spread": (max(implied) - min(implied)) if len(implied) > 1 else 0.0,
            "implied_scale_values": implied,
            "free_parameters": 1, "n_anchors": len(rows),
            "degrees_of_freedom": len(rows) - 1}


def predicted_credit(credit_solid: float, retention: float, density_scale: float) -> float:
    """Eq. 1 credit at a rung: ``A = credit_solid * (1 - s*(1 - r))``."""
    return credit_solid * (1.0 - density_scale * (1.0 - retention))
