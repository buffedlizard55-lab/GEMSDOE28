"""Network-free checks of feed policy, redirects and truthful partial observations."""
from __future__ import annotations

import json
import sys
from urllib.request import Request

import pytest
from scripts import refresh_source_feed as feed


@pytest.mark.parametrize("target", [
    "https://www.drivendata.org/competitions/306/",
    "https://DRIVENDATA.ORG./data/",
    "https://sub.drivendata.org/file",
])
def test_redirect_cannot_bypass_competition_host_guard(target):
    handler = feed.GuardedRedirectHandler()
    request = Request("https://github.com/allowed")
    with pytest.raises(ValueError, match="forbidden"):
        handler.redirect_request(request, None, 302, "Found", {}, target)


def test_redirect_cannot_bypass_runtime_network_policy():
    handler = feed.GuardedRedirectHandler({"api.github.com"})
    with pytest.raises(ValueError, match="outside runtime allowlist"):
        handler.redirect_request(Request("https://api.github.com/a"), None, 302, "Found", {},
                                 "https://www.usgs.gov/b")


def test_relative_redirect_preserves_guarded_allowed_host():
    handler = feed.GuardedRedirectHandler({"api.github.com"})
    result = handler.redirect_request(Request("https://api.github.com/a"), None, 302, "Found", {}, "/b")
    assert result.full_url == "https://api.github.com/b"


@pytest.mark.parametrize("url", ["http://github.com/a", "file:///etc/passwd",
                                 "https://user:password@github.com/a"])
def test_no_insecure_schemes_or_url_credentials(url):
    with pytest.raises(ValueError):
        feed.check_url(url)


def test_refused_url_never_constructs_network_opener(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("No network opener allowed")
    monkeypatch.setattr(feed, "build_opener", unexpected)
    with pytest.raises(ValueError):
        feed.fetch("https://www.drivendata.org/data", 1, 100)


def test_partial_feed_retains_old_dates_without_claiming_new_fetch(tmp_path, monkeypatch):
    sources = tmp_path / "sources.json"
    output = tmp_path / "feed.json"
    history = tmp_path / "history.json"
    sources.write_text(json.dumps({"sources": [
        {"id": "old", "feed": True, "url": "https://www.usgs.gov/data"},
        {"id": "fresh", "feed": True, "feed_kind": "github", "feed_repo": "a/b"},
        {"id": "forbidden", "feed": True, "url": "https://www.drivendata.org/data"},
    ]}))
    old = {"id": "old", "status": "observed", "checked_at_utc": "2020-01-01T00:00:00Z", "body_sha256": "old"}
    output.write_text(json.dumps({"sources": [old]}))
    history.write_text("[]")  # preserve the old history migration contract
    monkeypatch.setattr(feed, "SOURCES_PATH", sources)
    monkeypatch.setattr(feed, "OUT_PATH", output)
    monkeypatch.setattr(feed, "HISTORY_PATH", history)
    seen = []
    def fake_fetch(url, timeout, max_bytes, allowed):
        seen.append(url)
        return {"http_status": 200, "final_url": url}
    monkeypatch.setattr(feed, "fetch", fake_fetch)
    monkeypatch.setattr(sys, "argv", ["feed", "--allowed-host", "api.github.com"])
    assert feed.main() == 0
    report = json.loads(output.read_text())
    assert report["status"] == "partial-or-unavailable"
    assert report["freshly_observed_count"] == 1
    assert len(seen) == 1 and seen[0].startswith("https://api.github.com/")
    assert report["sources"][0]["request_attempted"] is False
    assert report["sources"][0]["last_successful_observation"] == old
    assert report["sources"][2]["status"] == "manual-only-forbidden-host"
    assert json.loads(history.read_text())["legacy_events"] == []
    # Repeated restricted refresh must not nest/reset the old observation date.
    assert feed.main() == 0
    assert json.loads(output.read_text())["sources"][0]["last_successful_observation"] == old
