"""Analysis for the preregistered H37-3 far-field licence test (knowledge/34).

Reads evidence/losfo_h37_3_licence.json and prints the C1-C4 verdicts with the paired statistics
(t-based 95 % interval on the paired mean, tcrit 2.093 at 19 df) plus the two break-even bars.
"""
from __future__ import annotations

import json
import statistics

NEW = "evidence/losfo_h37_3_licence.json"
REF = "evidence/losfo_farfield_diagnostic.json"
TCRIT_19 = 2.093

d = json.load(open(NEW))
ref = json.load(open(REF))
cells = [c for c in d["cells"] if c.get("euler")]
n = len(cells)
print(f"cells: {n}  seeds: {sorted({c['seed'] for c in cells})}")
print(f"runner sha256: {d['code_sha256']['runner'][:16]}  (H37-1 far-field run: cbc0c8d8...)")

print("\nC4 integrity")
integ = json.load(open("evidence/h37_3_licence_integrity.json"))
rep = integ["same_seed_reproduction"]
ok = bool(rep["per_cell_dti_equal"] and all(rep["aggregate_stats_equal"].values()))
print(f"  same-seed (181) base-arm reproduction, pre-patch vs licence-patch harness: "
      f"{'IDENTICAL' if ok else 'DIFFERS'} (4/4 cells, both arms)")
spr = integ["fresh_decade_base_arms_within_documented_spread"]
worst = max(abs(v["relative"]) for v in spr["arms"].values())
print(f"  fresh-decade base arms vs the stored 210-214 diagnostic: max |relative| "
      f"{worst:.3f} (documented LOSFO spread -0.12..+0.20): "
      f"{'within' if spr['within_spread'] else 'OUTSIDE'}")
ok &= bool(spr["within_spread"])

e = d["euler_licence"]
d_lic = [c["euler"]["delta_dti_licence"] for c in cells]
d_ran = [c["euler"]["delta_dti_random"] for c in cells]
d_lr = [a - b for a, b in zip(d_lic, d_ran)]


def ci95(v):
    sd = statistics.stdev(v) if len(v) > 1 else 0.0
    return TCRIT_19 * sd / (len(v) ** 0.5)


seeds_up = len({c["seed"] for c in cells if c["euler"]["delta_dti_licence"] > 0})
cells_up = sum(1 for v in d_lic if v > 0)
cells_lr = sum(1 for v in d_lr if v > 0)
print(f"\nmean paired dDTI(licence - base)   {statistics.mean(d_lic):+.6f}  +/-{ci95(d_lic):.6f}"
      f"   cells {cells_up}/{n}  seeds {seeds_up}/{len({c['seed'] for c in cells})}")
print(f"mean paired dDTI(random  - base)   {statistics.mean(d_ran):+.6f}  +/-{ci95(d_ran):.6f}")
print(f"mean paired dDTI(licence - random) {statistics.mean(d_lr):+.6f}  +/-{ci95(d_lr):.6f}"
      f"   cells {cells_lr}/{n}")
print(f"added dots total {e['added_dots_total']}  ({e['mean_added_per_cell']:.1f}/cell)"
      f"  control {e['control_dots_total']}")
print(f"credit per added dot {e['credit_per_added_dot']:.6f}   vs tau_live {e['tau_live_bar']}"
      f"   vs tau_farfield {e['tau_farfield_bar']:.6f}")
print("per-seed dDTI(licence - base): "
      + "  ".join(f"{s}:{v:+.6f}" for s, v in e["per_seed_delta_licence"].items()))

c1 = statistics.mean(d_lic) > 0 and cells_up >= 15 and seeds_up >= 4
c2 = e["credit_per_added_dot"] >= e["tau_live_bar"]
c3 = statistics.mean(d_lr) > 0 and cells_lr >= 15
c4 = ok
print("\nCRITERIA")
print(f"  C1 transfer          {'PASS' if c1 else 'FAIL'}   (>{0}, >=15/{n} cells, >=4 seeds)")
print(f"  C2 pays at the live bar  {'PASS' if c2 else 'FAIL'}   (credit/dot >= {e['tau_live_bar']})")
print(f"  C3 content not dots  {'PASS' if c3 else 'FAIL'}   (licence > random, >=15/{n} cells)")
print(f"  C4 integrity         {'PASS' if c4 else 'FAIL'}")
if c1 and c2 and c3:
    print("  -> validated ADD arm per knowledge/34 section 5")
elif c1 and c3:
    print("  -> far-field positive, below the live break-even: no slot, research candidate")
elif not c1:
    print("  -> H37-3 REFUTED; rank-3 H37-2 becomes the next arm (knowledge/34 section 5)")
else:
    print("  -> mechanism refuted (C3) even though C1 may hold; not promoted")

print("\nper-fold mean dDTI(licence - base):")
folds = sorted({c["fold"] for c in cells})
for f in folds:
    v = [c["euler"]["delta_dti_licence"] for c in cells if c["fold"] == f]
    print(f"  {f:18s} {statistics.mean(v):+.6f}  (n={len(v)})")
