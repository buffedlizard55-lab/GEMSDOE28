"""Analysis for the preregistered H37-1 far-field test (knowledge/32).

Run once evidence/losfo_packing_farfield.json exists. Prints the F1-F5 verdicts, the paired
statistics with a t-based 95% interval on the paired mean, and the base-arm reproduction check
against the stored diagnostic.
"""
from __future__ import annotations

import json
import math

NEW = "evidence/losfo_packing_farfield.json"
OLD = "evidence/losfo_farfield_diagnostic.json"

new = json.load(open(NEW))
old = json.load(open(OLD))

cells = [c for c in new["cells"] if c.get("packing")]
print(f"cells with packing arms: {len(cells)}  seeds: {sorted({c['seed'] for c in cells})}")
print("runner sha256:", new["code_sha256"]["runner"][:16], " (stored run:", old["code_sha256"]["runner"][:16], ")")

# --- F5(a) reproduction -------------------------------------------------------------------------
print("\nF5(a) base-arm reproduction against the stored diagnostic")
for arm in ("losfo", "leaky"):
    for k in ("mean_dti", "sum_tp", "credit_per_dot", "mean_dots"):
        a, b = new["arms"][arm][k], old["arms"][arm][k]
        flag = "OK " if abs(a - b) < 1e-6 * max(1.0, abs(b)) else "DIFF"
        print(f"  {flag} {arm:5s} {k:14s} new {a:.8f}  stored {b:.8f}")


def paired(det: str, a: str, b: str) -> tuple[list[float], list[float]]:
    def val(c, name):
        return c["packing"][det][name]["dti"] if name != "base" else c[det]["dti"]
    d = [val(c, a) - val(c, b) for c in cells]
    return d, [c["seed"] for c in cells]


def stats(d: list[float]) -> dict:
    n = len(d)
    mean = sum(d) / n
    var = sum((x - mean) ** 2 for x in d) / (n - 1)
    sd = math.sqrt(var)
    se = sd / math.sqrt(n)
    tcrit = 2.093  # t(0.975, 19 df) for 20 cells; 2.776 for 5 seeds
    return {"mean": mean, "sd": sd, "se": se, "ci95": tcrit * se,
            "cells_up": sum(1 for x in d if x > 0), "n": n}


print("\nPaired deltas (per cell), t 95% interval with 20 cells")
for det in ("losfo", "leaky"):
    for a, b in (("max_coverage", "base"), ("max_coverage", "random_order"),
                 ("prob_order", "base"), ("random_order", "base")):
        d, _ = paired(det, a, b)
        s = stats(d)
        print(f"  {det:5s} {a:13s}-{b:13s} mean {s['mean']:+.6f}  se {s['se']:.6f}  "
              f"95% ±{s['ci95']:.6f}  cells up {s['cells_up']}/{s['n']}")

print("\nPer-seed means (losfo):")
for det in ("losfo", "leaky"):
    for a, b in (("max_coverage", "base"), ("max_coverage", "random_order")):
        d, seeds = paired(det, a, b)
        per = {}
        for x, s in zip(d, seeds):
            per.setdefault(s, []).append(x)
        line = "  ".join(f"{s}:{sum(v)/len(v):+.5f}" for s, v in sorted(per.items()))
        up = sum(1 for v in per.values() if sum(v) / len(v) > 0)
        print(f"  {det:5s} {a}-{b}: {up}/{len(per)} seeds up | {line}")

print("\nArm aggregates")
for det in ("losfo", "leaky"):
    for name in ("base", "prob_order", "random_order", "max_coverage"):
        arm = new["packing_variants"]["arms"][det][name]
        print(f"  {det:5s} {name:13s} dti {arm['mean_dti']:.6f} credit/dot {arm['credit_per_dot']:.6f} "
              f"dots {arm['mean_dots']:.0f}")
    print(f"  {det:5s} base coverage {new['packing_variants']['paired_vs_base'][det]['base_coverage']:.1f}")

# --- F1-F3 verdicts -----------------------------------------------------------------------------
print("\nFrozen verdicts")
d1, _ = paired("losfo", "max_coverage", "base")
d2, _ = paired("losfo", "max_coverage", "random_order")
s1, s2 = stats(d1), stats(d2)
f1 = s1["mean"] > 0
f2 = s2["mean"] >= 0.0005
seeds = sorted({c["seed"] for c in cells})
seed_means = {s: sum(x for x, ss in zip(d1, [c["seed"] for c in cells]) if ss == s) /
              sum(1 for ss in [c["seed"] for c in cells] if ss == s) for s in seeds}
f3 = (s1["cells_up"] >= 15) and (sum(1 for v in seed_means.values() if v > 0) >= 4)
print(f"  F1 max_coverage > base (losfo): mean {s1['mean']:+.6f} -> {'PASS' if f1 else 'FAIL'}")
print(f"  F2 max_coverage - random_order >= +0.0005: mean {s2['mean']:+.6f} -> {'PASS' if f2 else 'FAIL'}")
print(f"  F3 >=15/20 cells and >=4/5 seeds: {s1['cells_up']}/20 cells, "
      f"{sum(1 for v in seed_means.values() if v > 0)}/5 seeds -> {'PASS' if f3 else 'FAIL'}")
print(f"\nF1+F2 -> {'PASS (rule transfers far field)' if (f1 and f2) else 'the pre-committed demotion path applies'}")
print(f"seconds {new['seconds']:.1f}")
