from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from sportkalender.catalog_registry import CatalogRegistry


@dataclass(frozen=True, slots=True)
class SourceDefinition:
    id: str
    urls_by_year: dict[str, str]
    language: str
    format: str
    mode: str
    adapter: str
    competition_keys: tuple[str, ...]
    required_catalog_ids: tuple[str, ...]
    authority: str


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    source_id: str
    url: str
    content: bytes = b""
    fetched_at: str = ""
    etag: str = ""
    last_modified: str = ""
    error: str = ""

    @property
    def content_hash(self) -> str:
        return sha256(self.content).hexdigest() if self.content else ""


def load_sources(path: Path, registry: CatalogRegistry) -> dict[str, SourceDefinition]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or not isinstance(payload.get("sources"), list):
        raise ValueError(f"invalid source registry: {path}")
    sources = {}
    for item in payload["sources"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"] or item["id"] in sources:
            raise ValueError("source registry needs unique source IDs")
        urls = item.get("urls_by_year")
        keys, required = item.get("competition_keys"), item.get("required_catalog_ids")
        if not isinstance(urls, dict) or not urls or any(
            not isinstance(year, str) or not year.isdigit() or not isinstance(url, str)
            or urlparse(url).scheme not in {"https", "http"} or not urlparse(url).netloc
            for year, url in urls.items()
        ):
            raise ValueError(f"source {item['id']} needs explicit year URLs")
        if not isinstance(keys, list) or not keys or any(key not in registry.competitions for key in keys):
            raise ValueError(f"source {item['id']} has unknown competitions")
        if not isinstance(required, list) or any(str(year) not in urls for year in required):
            raise ValueError(f"source {item['id']} has invalid required catalog IDs")
        if item.get("format") not in {"html", "pdf"} or item.get("mode") not in {"parsed", "reviewed"}:
            raise ValueError(f"source {item['id']} has invalid format or mode")
        if item.get("authority") not in {"official", "secondary"} or not item.get("language"):
            raise ValueError(f"source {item['id']} needs authority and language")
        adapter = str(item.get("adapter", ""))
        if item["mode"] == "parsed" and adapter not in {"premier_league_highlights", "ligue_1_highlights", "wikipedia"}:
            raise ValueError(f"source {item['id']} has an unknown parsed adapter")
        sources[item["id"]] = SourceDefinition(
            item["id"], urls, item["language"], item["format"], item["mode"], adapter,
            tuple(keys), tuple(str(year) for year in required), item["authority"],
        )
    return sources


def fetch_snapshot(
    source: SourceDefinition, year: int, cache_dir: Path, *, offline: bool = False,
    save: bool = True, opener=urlopen, pause=time.sleep,
) -> SourceSnapshot:
    from datetime import datetime, timezone

    url = source.urls_by_year.get(str(year))
    if url is None:
        return SourceSnapshot(source.id, "", error=f"No source URL is configured for {year}.")
    key = sha256(url.encode("utf-8")).hexdigest()
    body_path, metadata_path = cache_dir / f"{key}.raw", cache_dir / f"{key}.json"
    metadata = {}
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return SourceSnapshot(source.id, url, error=f"Invalid saved source metadata: {error}")
        if not isinstance(metadata, dict) or metadata.get("url") != url:
            return SourceSnapshot(source.id, url, error="Saved source URL does not match.")
    cached = body_path.read_bytes() if body_path.exists() else b""
    if cached and sha256(cached).hexdigest() != metadata.get("content_hash"):
        return SourceSnapshot(source.id, url, error="Saved source hash does not match.")
    if offline:
        if not cached:
            return SourceSnapshot(source.id, url, error="No saved source is available for offline use.")
        return SourceSnapshot(source.id, url, cached, str(metadata.get("fetched_at", "")))
    headers = {"User-Agent": "Sportkalender/0.1 (local monthly catalog check)"}
    if cached:
        for field, header in (("etag", "If-None-Match"), ("last_modified", "If-Modified-Since")):
            if metadata.get(field):
                headers[header] = metadata[field]
    error_message = ""
    for attempt in range(3):
        fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        try:
            with opener(Request(url, headers=headers), timeout=30) as response:
                content = response.read()
                etag = response.headers.get("ETag", "")
                modified = response.headers.get("Last-Modified", "")
            if not content:
                return SourceSnapshot(source.id, url, error="The source response is empty.")
            snapshot = SourceSnapshot(source.id, url, content, fetched_at, etag, modified)
            break
        except HTTPError as error:
            error.close()
            if error.code == 304:
                if not cached:
                    return SourceSnapshot(source.id, url, error="HTTP 304 has no matching saved response.")
                snapshot = SourceSnapshot(source.id, url, cached, fetched_at, str(metadata.get("etag", "")), str(metadata.get("last_modified", "")))
                break
            error_message = f"HTTP {error.code}: {url}"
            if error.code not in {429, 500, 502, 503, 504}:
                return SourceSnapshot(source.id, url, error=error_message)
        except (URLError, OSError, TimeoutError) as error:
            error_message = str(error)
        if attempt < 2:
            pause(attempt + 1)
    else:
        return SourceSnapshot(source.id, url, error=error_message)
    if save:
        cache_dir.mkdir(parents=True, exist_ok=True)
        # Content-addressed bodies preserve every source version for offline review.
        archive = cache_dir / f"{snapshot.content_hash}.raw"
        if not archive.exists():
            archive.write_bytes(snapshot.content)
        body_path.write_bytes(snapshot.content)
        metadata_path.write_text(json.dumps({
            "url": url, "content_hash": snapshot.content_hash, "fetched_at": snapshot.fetched_at,
            "etag": snapshot.etag, "last_modified": snapshot.last_modified,
        }, sort_keys=True) + "\n", encoding="utf-8")
    return snapshot
