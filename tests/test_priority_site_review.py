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
        self.assertIn("USER-REPORTED, UNVERIFIED", self.page)

    def test_all_rows_have_auditable_artifact_metadata(self):
        for row in self.data["sites"]:
            with self.subTest(site=row["site"]):
                self.assertGreater(row["reported_best_score"], 0)
                self.assertGreater(row["measured_positive_pixels"], 0)
                self.assertRegex(row["source_commit"], re.compile(r"^[0-9a-f]{40}$"))
                self.assertTrue(row["source_path"].endswith(".tif"))
                self.assertTrue(row["construction_summary"])
                self.assertTrue(row["forensic_note"])

    def test_cross_site_review_links_supplemental_artifact_audit(self):
        self.assertIn("Best reported result is not an approved submission", self.page)
        self.assertIn("USER-REPORTED, UNVERIFIED", self.page)
        self.assertIn("data/priority_site_review_2026-10-26.json", self.page)
        self.assertIn("https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/", self.page)
        self.assertIn("No new TIFF was generated", self.page)

    def test_session19_card_is_negative_and_does_not_claim_a_new_raster(self):
        card = json.loads((ROOT / "evidence/session19_run_card.json").read_text())
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["new_tiff_generated"])
        self.assertFalse(card["submission_ready"])
        self.assertEqual(card["experiments_run"], 0)
        self.assertIsNone(card["raster_sha256"])


if __name__ == "__main__":
    unittest.main()
