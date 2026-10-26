from scripts.audit_priority_repositories import cache_display_path


def test_relative_and_external_cache_paths(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)
    assert cache_display_path(repo / "data" / "blob.tif", repo) == "data/blob.tif"
    from pathlib import Path

    assert cache_display_path(Path("data/blob.tif"), repo) == "data/blob.tif"
    outside = tmp_path / "outside" / "blob.tif"
    assert cache_display_path(outside, repo) == str(outside)
