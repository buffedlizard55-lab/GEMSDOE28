#!/usr/bin/env python3
"""Render the existing 81-link H27-5b map-review subset as a connector-only schematic."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

plt.switch_backend("Agg")

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "data" / "topology_priority_h27_5b.geojson"
OUTPUT = ROOT / "docs" / "assets" / "fig_map_h27_5b_priority.png"
COLORS = {"end-to-end": "#1b746c", "abutting": "#df6844", "tip-to-tip oblique": "#6956a7"}


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    features = data.get("features", [])
    fig, ax = plt.subplots(figsize=(9.2, 6.6), layout="constrained")
    fig.patch.set_facecolor("#fbfaf5")
    ax.set_facecolor("#fbfaf5")
    for kind, color in COLORS.items():
        rows = [item for item in features if item.get("properties", {}).get("kind") == kind]
        for item in rows:
            coords = item["geometry"]["coordinates"]
            xs, ys = zip(*coords)
            ax.plot(xs, ys, color=color, linewidth=1.35, alpha=.74, zorder=2)
            ax.scatter(xs, ys, color=color, s=8, alpha=.55, zorder=3)
        ax.plot([], [], color=color, linewidth=2.4, label=f"{kind} ({len(rows)})")
    all_xy = [coord for item in features for coord in item["geometry"]["coordinates"]]
    xs, ys = zip(*all_xy)
    margin_x = max((max(xs) - min(xs)) * .035, .015)
    margin_y = max((max(ys) - min(ys)) * .035, .015)
    ax.set_xlim(min(xs) - margin_x, max(xs) + margin_x)
    ax.set_ylim(min(ys) - margin_y, max(ys) + margin_y)
    ax.set_xlabel("Longitude (degrees)")
    ax.set_ylabel("Latitude (degrees)")
    ax.grid(color="#b7c3bb", linewidth=.55, alpha=.48)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("H27-5b map-review connectors", loc="left", fontsize=17, weight="bold", color="#163b36", pad=17)
    ax.text(0, 1.025, f"{len(features)} of 345 existing T-v2 candidates · connector geometry only · not verified faults",
            transform=ax.transAxes, fontsize=9.5, color="#52615b", va="bottom")
    ax.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#d4d8cf", fontsize=8.5)
    fig.text(.01, .005, "WGS84 endpoints from the owner-mirror review GeoJSON. Catalogue fault traces are not plotted; inspect with the official NBMG Qfaults layer.",
             fontsize=8, color="#56635d")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"wrote {OUTPUT.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)} ({len(features)} connectors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
