"""Dependency-free integrity checks for the supplemental nine-site raster audit."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "docs/data/priority_site_review_2026-10-26.json"
PAGE_PATH = ROOT / "docs/cross-site-review.html"


class PrioritySiteReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        cls.page = PAGE_PATH.read_text(encoding="utf-8")

    def test_all_requested_sites_are_present_once(self):
        sites = [row["site"] for row in self.data["sites"]]
        self.assertEqual(
            sites,
            [
                "GEMSDOE24",
                "GEMSDOE25",
                "GEMSDOE27",
                "GEMSDOE28",
                "GEMSDOE30",
                "GEMSDOE31",
                "GEMSDOE32",
                "GEMSDOE33",
                "GEMSDOE36",
            ],
        )
        self.assertEqual(len(sites), len(set(sites)))

    def test_highest_supplied_score_and_evidence_class_are_explicit(self):
        self.assertIn("OWNER-REPORTED", self.data["score_evidence_class"])
        best = max(self.data["sites"], key=lambda row: row["reported_best_score"])
        self.assertEqual(best["site"], "GEMSDOE32")
        self.assertEqual(best["reported_best_score"], 0.2778)
        self.assertFalse(self.data["recommendation"]["new_tiff_this_review"])
        self.assertIn("USER-REPORTED / UNVERIFIED", self.page)

    def test_all_rows_have_auditable_artifact_metadata(self):
        for row in self.data["sites"]:
            with self.subTest(site=row["site"]):
                self.assertGreater(row["reported_best_score"], 0)
                self.assertGreater(row["measured_positive_pixels"], 0)
                self.assertRegex(row["source_commit"], re.compile(r"^[0-9a-f]{40}$"))
                self.assertTrue(row["source_path"].endswith(".tif"))
                self.assertTrue(row["construction_summary"])
                self.assertTrue(row["forensic_note"])

    def test_scorecard_exposes_download_estimate_and_uniqueness_status(self):
        self.assertIn("NINE-SITE HISTORICAL SCORECARD", self.page.upper())
        self.assertIn("MODEL PROJECTION", self.page)
        self.assertIn("NOT CERTIFIED", self.page)
        self.assertIn("NOT UNIQUE", self.page)
        self.assertIn("Download cited TIFF", self.page)
        self.assertIn("gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite.tif", self.page)
        self.assertIn("72.3%", self.page)
        self.assertIn("DO NOT SUBMIT", self.page)
        for site in ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]:
            self.assertIn(site, self.page)
        self.assertIn('href="session21-result.html">Latest result</a>', self.page)
        self.assertNotIn("h33-h33-2-b2</code> (0.2778) — learning reference only", self.page)

    def test_scorecard_download_links_are_commit_pinned_and_novelty_is_not_overclaimed(self):
        for row in self.data["sites"]:
            with self.subTest(site=row["site"]):
                self.assertRegex(row["raw_download_url"], r"/GEMSDOE\d+/[0-9a-f]{40}/docs/downloads/.+\.tif$")
                self.assertIn(row["uniqueness_audit"]["status"], {"NOT UNIQUE", "NOT CERTIFIED"})
                self.assertEqual(row["score_label"], "USER-REPORTED / UNVERIFIED; not an independent score estimate")
        self.assertFalse(self.data["candidate_review"]["submission_ready"])
        self.assertEqual(self.data["candidate_review"]["verdict"], "NEGATIVE — research download only; DO NOT SUBMIT")
        self.assertIn("MODEL PROJECTION", self.data["candidate_review"]["score_estimate_class"])

    def test_s22_preflight_blocks_science_until_required_inputs_exist(self):
        preflight = json.loads((ROOT / "evidence/s22_preflight.json").read_text())
        session = json.loads((ROOT / "registry/s22_session.json").read_text())
        self.assertEqual(session["branch"], "arena/7188b7b1-gemsdoe28")
        self.assertIsNone(session["lane"])
        self.assertEqual(preflight["status"], "BLOCKED")
        self.assertFalse(preflight["experiment_allowed"])
        self.assertFalse(preflight["submission_ready"])
        self.assertFalse(preflight["slot_selected"])
        self.assertTrue(preflight["shared_template"]["passed"])
        self.assertEqual(len(preflight["failures"]), 4)
        self.assertIn("Cached feature stack unavailable", preflight["failures"][-1])
        self.assertIn("S22 experiment preflight (blocked)", self.page)

    def test_session19_card_is_negative_and_does_not_claim_a_new_raster(self):
        card = json.loads((ROOT / "evidence/session19_run_card.json").read_text())
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["new_tiff_generated"])
        self.assertFalse(card["submission_ready"])
        self.assertEqual(card["experiments_run"], 0)
        self.assertIsNone(card["raster_sha256"])


if __name__ == "__main__":
    unittest.main()
