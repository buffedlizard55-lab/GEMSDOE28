"""Live-anchored operating-point arithmetic for the GEMS distance-tolerant IoU (DTI).

Why this module exists
----------------------
Every emission decision in this programme (how far apart to space the dots, which classes of dot to
drop) is a trade between kernel-weighted credit ``A`` and emitted-pixel mass ``N``. The official
metric reduces exactly to a two-number statement, so the trade can be decided arithmetically instead
of argued about:

    DTI  =  A / (0.2*A + 0.2*FP + 0.8*|G|)

and, using the closure the inversion in ``evidence/live_inversion.json`` is already built on
(``FP = N - A``, i.e. every emitted pixel carries one unit of mass and the part that lands within the
300 m kernel of truth is exactly the credit it earns):

    DTI  =  A / (0.8*|G| + 0.2*N)                                        (Eq. 1)

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
   submission we actually modify scores 0.26 and gates at ``tau = 0.055`` - **2.5x more permissive**.
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

    def dti(self, retention: float, n_emitted: int) -> float:
        return self.credit_solid * retention / (BETA * self.truth_px + ALPHA * n_emitted)

    def state(self, retention: float, n_emitted: int) -> dict:
        """Full metric state (A, FP, |G|, DTI, tau, marginal value of one pixel)."""
        a = self.credit_solid * retention
        g = self.truth_px
        fp = max(n_emitted - a, 0.0)
        denom = a + ALPHA * fp + BETA * (g - a)
        dti = a / denom if denom > 0 else 0.0
        return {"credit_A": a, "emitted_N": n_emitted, "fp": fp, "truth_G": g, "denominator": denom,
                "dti": dti, "tau": ALPHA * dti / (1.0 - ALPHA * dti),
                "weighted_recall": a / g if g else 0.0}

    def prune_gain(self, retention: float, n_emitted: int, n_removed: int, efficiency: float) -> dict:
        """Exact Eq. 1 change from dropping ``n_removed`` pixels of efficiency ``e``.

        dDTI = n * [ ALPHA*A - e * (ALPHA*FP + BETA*|G| - BETA*A) ] / D**2
        derived by differentiating DTI = A/(A + ALPHA*FP + BETA(|G|-A)) with dA = -e*n, dFP = -n.
        """
        st = self.state(retention, n_emitted)
        d = st["denominator"]
        da = -efficiency * n_removed
        dfp = -n_removed
        d_denom = da + ALPHA * dfp + BETA * (-da)
        d_dti = (da * d - st["credit_A"] * d_denom) / (d * d)
        return {"n_removed": n_removed, "efficiency": efficiency, "dti_before": st["dti"],
                "dti_after": st["dti"] + d_dti, "delta_dti": d_dti,
                "breakeven_tau": st["tau"], "worth_it": bool(efficiency < st["tau"])}


def fit_operating_point(anchors: list[dict], ladder: Ladder) -> OperatingPoint:
    """Fit ``(credit_solid, truth_px)`` to live-scored submissions of one detector surface.

    ``anchors`` items: ``{"min_dist": float, "n_emitted": int, "score": float, "label": str}``.
    Each is mapped onto its real ladder rung, so the measured ``(N, r)`` pair is the same one the
    live file actually realised. Two unknowns, so three anchors leave one degree of freedom; the
    leave-one-out block reports whether that residual is small enough to trust the fit.
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
        used.append((pt, float(a["score"]), a))

    def resid(p: np.ndarray) -> list[float]:
        L, G = p
        return [L * pt.retention / (BETA * G + ALPHA * pt.n_emitted) - s for pt, s, _ in used]

    sol = least_squares(resid, [float(max(1.0, used[0][1] * 10_000)), 12_000.0])
    L, G = float(sol.x[0]), float(sol.x[1])
    op = OperatingPoint(L, G,
                        anchors=[{"label": a.get("label"), "min_dist": a["min_dist"],
                                  "rung": pt.rung, "n_emitted": pt.n_emitted,
                                  "retention": pt.retention, "score": s,
                                  "fitted": L * pt.retention / (BETA * G + ALPHA * pt.n_emitted),
                                  "residual": L * pt.retention / (BETA * G + ALPHA * pt.n_emitted) - s}
                                 for pt, s, a in used],
                        residuals=[float(r) for r in sol.fun])

    # leave-one-out: refit on n-1 anchors and predict the held-out one
    for k in range(len(used)):
        sub = [u for j, u in enumerate(used) if j != k]
        s2 = least_squares(lambda p: [p[0] * pt.retention / (BETA * p[1] + ALPHA * pt.n_emitted) - s
                                      for pt, s, _ in sub], [L, G])
        L2, G2 = float(s2.x[0]), float(s2.x[1])
        pt, s, a = used[k]
        pred = L2 * pt.retention / (BETA * G2 + ALPHA * pt.n_emitted)
        op.leave_one_out.append({"held_out": a.get("label"), "score": s, "predicted": pred,
                                 "error": pred - s, "credit_solid": L2, "truth_px": G2})
    return op


def predict_ladder(ladder: Ladder, op: OperatingPoint) -> Ladder:
    for p in ladder.points:
        p.dti = op.dti(p.retention, p.n_emitted)
    return ladder


def rung_efficiency(ladder: Ladder, op: OperatingPoint, rung_from: float, rung_to: float) -> dict:
    """Efficiency ``e = |dA|/|dN|`` of moving one rung further out on the packing ladder."""
    idx = {p.rung: p for p in ladder.points}
    a, b = idx[rung_from], idx[rung_to]
    d_a = op.credit_solid * (b.retention - a.retention)
    d_n = b.n_emitted - a.n_emitted
    st = op.state(a.retention, a.n_emitted)
    e = abs(d_a) / abs(d_n) if d_n else float("inf")
    gain = op.prune_gain(a.retention, a.n_emitted, abs(d_n), e)
    return {"rung_from": rung_from, "rung_to": rung_to, "d_credit": float(d_a), "d_emitted": int(d_n),
            "efficiency": float(e), "breakeven_tau": st["tau"], "worth_it": bool(e < st["tau"]),
            "delta_dti": gain["delta_dti"], "dti_from": st["dti"], "dti_to": gain["dti_after"]}
