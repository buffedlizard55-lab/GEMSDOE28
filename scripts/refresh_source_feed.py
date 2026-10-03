#!/usr/bin/env python3
"""Manually refresh registered non-competition source metadata.

This is an explicitly invoked, allowlist-aware helper. It never visits, queries, uploads to or monitors
DrivenData; those competition pages are manual-review links only. The static Pages builder does not call
this script. External availability/schema/licence must still be verified from the source's own metadata.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "registry" / "sources.json"
OUT_PATH = ROOT / "docs" / "data" / "feed.json"
HISTORY_PATH = ROOT / "docs" / "data" / "feed_history.json"
FORBIDDEN = ("drivendata.org",)


def feed_url(source: dict) -> str | None:
    kind = source.get("feed_kind")
    if kind == "github" and source.get("feed_repo"):
        return f"https://api.github.com/repos/{source['feed_repo']}/commits?per_page=1"
    if kind == "arcgis":
        raw = source.get("feed_url") or source.get("url")
        if raw:
            return raw + ("&f=pjson" if "?" in raw else "?f=pjson")
    return source.get("feed_url") or source.get("url")


def forbidden_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    return any(host == domain or host.endswith("." + domain) for domain in FORBIDDEN)


def fetch(url: str, timeout: float, max_bytes: int) -> dict:
    host = (urlparse(url).hostname or "").lower()
    if forbidden_host(host):
        raise ValueError(f"refusing to request forbidden host {host}")
    request = Request(url, headers={"User-Agent": "GEMSDOE28-source-review/1.0", "Accept": "application/json,*/*"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise ValueError(f"response exceeds configured {max_bytes}-byte limit")
        return {
            "http_status": int(response.status),
            "final_url": response.geturl(),
            "content_type": response.headers.get("Content-Type"),
            "content_length_header": response.headers.get("Content-Length"),
            "body_bytes": len(body),
            "body_sha256": __import__("hashlib").sha256(body).hexdigest(),
            "preview": body[:512].decode("utf-8", errors="replace"),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--max-bytes", type=int, default=2_000_000)
    parser.add_argument("--no-write", action="store_true", help="print results without changing feed JSON")
    args = parser.parse_args()
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))["sources"]
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for source in sources:
        if not source.get("feed"):
            continue
        url = feed_url(source)
        if not url:
            continue
        host = (urlparse(url).hostname or "").lower()
        if forbidden_host(host):
            # Fail closed. We record the manual-only restriction, never try another URL.
            print(f"refusing to request forbidden host {host}: {source.get('id')}")
            rows.append({"id": source.get("id"), "url": url, "status": "manual-only-forbidden-host", "checked_at_utc": checked_at})
            continue
        try:
            observation = fetch(url, args.timeout, args.max_bytes)
            rows.append({"id": source.get("id"), "url": url, "status": "observed", "checked_at_utc": checked_at, **observation})
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            rows.append({"id": source.get("id"), "url": url, "status": "fetch-failed", "checked_at_utc": checked_at,
                         "error_type": type(exc).__name__, "error": str(exc)[:500]})
    report = {
        "checked_at_utc": checked_at,
        "policy": "explicit manual invocation; DrivenData is forbidden and never requested",
        "source_count": len(rows),
        "sources": rows,
    }
    if not args.no_write:
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8")) if HISTORY_PATH.exists() else {"runs": []}
        history.setdefault("runs", []).append({"checked_at_utc": checked_at, "source_count": len(rows), "status_counts": {
            status: sum(row.get("status") == status for row in rows) for status in sorted({row.get("status") for row in rows})
        }})
        HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
