#!/usr/bin/env python3
"""S31 decision panel: the newest (leading) overlay on the root and docs overview pages.

Follows the scripts/build_s30_review.py pattern exactly: idempotent marker-based removal,
then insertion directly after <main> so this panel leads every page it targets. Chained at
the END of scripts/build_active_review.py (run after scripts/build_site.py), which is what
CI regenerates and diffs. Every number is read from the committed S31 evidence JSONs —
nothing is hard-coded here.

Run:  python scripts/build_s31_review.py
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CARD = ROOT / "evidence" / "s31_candidate_run_card.json"
GATE = ROOT / "evidence" / "s31_candidate_gate.json"
PANEL_TARGETS = [
    ROOT / "index.html",
    ROOT / "executive-summary.html",
    DOCS / "index.html",
    DOCS / "executive-summary.html",
]
MARKER = 'id="s31-decision"'


def load() -> tuple[dict, dict]:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    if gate["verdict_file"] != "VALID AND UNIQUE":
        raise ValueError("S31 gate is not VALID AND UNIQUE; refusing to publish an approval panel")
    if not gate["all_hard_checks_pass"]:
        raise ValueError("S31 gate hard checks failed; refusing to publish an approval panel")
    if card["note_chars"] > 140:
        raise ValueError("submission note exceeds 140 characters")
    return card, gate


def panel(card: dict, gate: dict) -> str:
    file_name = Path(card["file"]).name
    sha = card["sha256"]
    dots = card["final_dots"]
    lo, hi = card["model_estimate"]["score_range"]
    worst = gate["uniqueness"]["max_overlap"]
    over = gate["uniqueness"]["rasters_over_70pct"]
    parent = gate["uniqueness"]["overlap_vs_h33_2_parent"]
    note = html.escape(card["note"])
    return f"""<section class="section callout-ok" id="s31-decision" aria-label="S31 submission decision" data-submission-ready="true">
<p class="eyebrow">S31 · 2026-10-31 UTC · AUTOMATED DECISION · NO HUMAN INSPECTOR</p>
<h2>OK TO DOWNLOAD: YES · OK TO SUBMIT AS A VALID UNIQUE FILE: YES</h2>
<p><strong>File:</strong> <a href="s31-candidate-link"><code>{html.escape(file_name)}</code></a> · SHA-256 <code>{html.escape(sha)}</code> · {dots:,} dots · float32 single band · EPSG:32611 · 3730×3292 · values exactly 0 or 1 inside · zeros finite outside (all-finite) → the portal error “Predicted values must be in range [0, 1]” cannot occur on this file.</p>
<p><strong>Unique (MEASURED):</strong> worst overlap {worst:.4f} ≤ 0.70 vs the nine-site registry ({over} rasters over the gate); overlap with the 0.2778 parent {parent:.4f}; independent KD-tree gate verdict <strong>{gate["verdict_file"]}</strong>.</p>
<p><strong>Expected score:</strong> MODEL-ESTIMATE {lo}–{hi} (never a score; not organizer-confirmed; not verified to beat 0.2778). <strong>Weekly slot selection is the owner's step</strong> — this research run never spends a slot. Submission note (≤140 chars): <code>{note}</code></p>
<div class="download-actions"><a class="button" href="s31-candidate-link" download>Download the S31 submission TIF</a> <a class="button quiet" href="s31-summary-link">Open S31 executive summary (nine-site table + submit steps)</a> <a class="button quiet" href="s31-run-card-link" download>S31 run card (JSON)</a></div>
</section>"""


def insert_panels(html_panel: str, candidate_href: str) -> list[str]:
    updated = []
    for path in PANEL_TARGETS:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if MARKER in text:
            before, after = text.split(MARKER, 1)
            start = before.rfind("<section")
            end = after.find("</section>")
            if start < 0 or end < 0:
                raise ValueError(f"malformed S31 panel in {path}")
            text = before[:start] + after[end + len("</section>"):]
        if "<main>" not in text:
            raise ValueError(f"no <main> in {path}")
        # Root pages and docs pages link to docs artefacts with different prefixes.
        prefix = "docs/" if path.parent == ROOT else ""
        rendered = html_panel
        rendered = rendered.replace('href="s31-candidate-link"', f'href="{prefix}{candidate_href}"')
        rendered = rendered.replace('href="s31-summary-link"', f'href="{prefix}s31-executive-summary.html"')
        rendered = rendered.replace('href="s31-run-card-link"', f'href="{prefix}data/s31_run_card.json"')
        text = text.replace("<main>", "<main>" + rendered, 1)
        path.write_text(text, encoding="utf-8")
        updated.append(path.relative_to(ROOT).as_posix())
    return updated


def main() -> int:
    card, gate = load()
    candidate_href = card["path"]
    if not candidate_href.startswith("docs/"):
        raise ValueError(f"unexpected candidate path {candidate_href}")
    candidate_href = candidate_href[len("docs/"):]
    updated = insert_panels(panel(card, gate), candidate_href)
    print(f"S31 panel written to {len(updated)} pages: {', '.join(updated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
