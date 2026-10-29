"""Dated decision must be safe, reproducible, and replace itself."""
from scripts import build_s28_review


def test_panel_is_idempotent_and_fails_closed(tmp_path, monkeypatch):
    page = tmp_path / "index.html"
    page.write_text("<html><main><p>Content</p></main></html>", encoding="utf-8")
    monkeypatch.setattr(build_s28_review, "PAGES", (page,))
    build_s28_review.main()
    first = page.read_text(encoding="utf-8")
    build_s28_review.main()
    assert page.read_text(encoding="utf-8") == first
    assert first.count('id="s28-current-decision"') == 1
    assert 'data-submission-ready="false"' in first
    assert "OK TO SUBMIT: NO" in first
