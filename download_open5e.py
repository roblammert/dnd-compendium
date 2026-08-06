#!/usr/bin/env python3
"""Download the complete Open5e v2 API into a SQLite database.

Uses only the Python standard library.

Examples:
    python download_open5e.py
    python download_open5e.py --database ./data/open5e.sqlite3
    python download_open5e.py --replace
    python download_open5e.py --endpoint creatures --endpoint spells
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_API_ROOT = "https://api.open5e.com/v2/"
USER_AGENT = "open5e-sqlite-downloader/1.0"

# Used only if the API root cannot be enumerated. Unknown/unsupported routes are skipped.
FALLBACK_ENDPOINTS = (
    "backgrounds",
    "classes",
    "conditions",
    "creatures",
    "documents",
    "equipment",
    "feats",
    "magicitems",
    "magic-items",
    "rules",
    "sections",
    "species",
    "spells",
    "weapons",
    "armor",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_json(url: str, *, retries: int, timeout: int) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(response.read().decode(charset))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise
            if exc.code not in (429, 500, 502, 503, 504) or attempt >= retries:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else min(2**attempt, 30)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt >= retries:
                raise
            delay = min(2**attempt, 30)
        print(f"  Request failed; retrying in {delay:g}s: {url}", file=sys.stderr)
        time.sleep(delay)
    raise RuntimeError("unreachable")


def safe_identifier(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    if not value:
        raise ValueError("Endpoint produced an empty SQLite identifier")
    if value[0].isdigit():
        value = f"endpoint_{value}"
    return value


def endpoint_name_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1]


def discover_endpoints(api_root: str, retries: int, timeout: int) -> dict[str, str]:
    try:
        root = request_json(api_root, retries=retries, timeout=timeout)
    except Exception as exc:
        print(f"Could not enumerate {api_root}: {exc}", file=sys.stderr)
        return {
            name: urllib.parse.urljoin(api_root, f"{name}/")
            for name in FALLBACK_ENDPOINTS
        }

    endpoints: dict[str, str] = {}
    if isinstance(root, dict):
        for key, value in root.items():
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                name = endpoint_name_from_url(value) or str(key)
                # Search is a computed endpoint, not source content to mirror.
                if name != "search":
                    endpoints[name] = value

    if not endpoints:
        return {
            name: urllib.parse.urljoin(api_root, f"{name}/")
            for name in FALLBACK_ENDPOINTS
        }
    return dict(sorted(endpoints.items()))


def add_limit(url: str, limit: int) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    query["limit"] = str(limit)
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment)
    )


def iter_endpoint(url: str, *, limit: int, retries: int, timeout: int) -> Iterable[dict[str, Any]]:
    next_url: str | None = add_limit(url, limit)
    while next_url:
        payload = request_json(next_url, retries=retries, timeout=timeout)
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            results = payload["results"]
            next_value = payload.get("next")
            next_url = urllib.parse.urljoin(next_url, next_value) if next_value else None
        elif isinstance(payload, list):
            results = payload
            next_url = None
        else:
            raise ValueError(f"Unexpected response shape from {next_url}")

        for item in results:
            if isinstance(item, dict):
                yield item


def nested_value(record: dict[str, Any], *path: str) -> Any:
    value: Any = record
    for part in path:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def first_text(record: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, (str, int, float)):
            return str(value)
    return None


def record_identity(record: dict[str, Any]) -> str:
    document_key = nested_value(record, "document", "key") or nested_value(record, "document", "slug")
    key = first_text(record, "key", "slug", "id", "pk", "index")
    if key and document_key:
        return f"{document_key}:{key}"
    if key:
        return key

    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS _open5e_imports (
            endpoint       TEXT PRIMARY KEY,
            source_url     TEXT NOT NULL,
            row_count      INTEGER NOT NULL DEFAULT 0,
            imported_at    TEXT NOT NULL,
            completed      INTEGER NOT NULL DEFAULT 0,
            error          TEXT
        );

        CREATE TABLE IF NOT EXISTS _open5e_endpoints (
            endpoint       TEXT PRIMARY KEY,
            table_name     TEXT NOT NULL UNIQUE,
            source_url     TEXT NOT NULL
        );
        """
    )


def create_endpoint_table(connection: sqlite3.Connection, table_name: str) -> None:
    quoted = '"' + table_name.replace('"', '""') + '"'
    connection.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS {quoted} (
            record_id      TEXT PRIMARY KEY,
            api_key        TEXT,
            name           TEXT,
            document_key   TEXT,
            document_name  TEXT,
            updated_at     TEXT,
            json           TEXT NOT NULL,
            imported_at    TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS "idx_{table_name}_name" ON {quoted}(name);
        CREATE INDEX IF NOT EXISTS "idx_{table_name}_api_key" ON {quoted}(api_key);
        CREATE INDEX IF NOT EXISTS "idx_{table_name}_document" ON {quoted}(document_key);
        """
    )


def import_endpoint(
    connection: sqlite3.Connection,
    endpoint: str,
    url: str,
    *,
    limit: int,
    retries: int,
    timeout: int,
    replace: bool,
    commit_every: int,
) -> int:
    table_name = safe_identifier(endpoint)
    quoted = '"' + table_name.replace('"', '""') + '"'
    create_endpoint_table(connection, table_name)

    connection.execute(
        "INSERT OR REPLACE INTO _open5e_endpoints(endpoint, table_name, source_url) VALUES (?, ?, ?)",
        (endpoint, table_name, url),
    )
    connection.execute(
        "INSERT OR REPLACE INTO _open5e_imports(endpoint, source_url, imported_at, completed, error) "
        "VALUES (?, ?, ?, 0, NULL)",
        (endpoint, url, utc_now()),
    )
    if replace:
        connection.execute(f"DELETE FROM {quoted}")
    connection.commit()

    sql = f"""
        INSERT INTO {quoted}(
            record_id, api_key, name, document_key, document_name,
            updated_at, json, imported_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(record_id) DO UPDATE SET
            api_key=excluded.api_key,
            name=excluded.name,
            document_key=excluded.document_key,
            document_name=excluded.document_name,
            updated_at=excluded.updated_at,
            json=excluded.json,
            imported_at=excluded.imported_at
    """

    count = 0
    imported_at = utc_now()
    for record in iter_endpoint(url, limit=limit, retries=retries, timeout=timeout):
        document = record.get("document") if isinstance(record.get("document"), dict) else {}
        row = (
            record_identity(record),
            first_text(record, "key", "slug", "id", "pk", "index"),
            first_text(record, "name", "title"),
            first_text(document, "key", "slug"),
            first_text(document, "name", "title"),
            first_text(record, "updated_at", "modified", "last_updated"),
            json.dumps(record, ensure_ascii=False, sort_keys=True),
            imported_at,
        )
        connection.execute(sql, row)
        count += 1
        if count % commit_every == 0:
            connection.commit()
            print(f"  {endpoint}: {count:,} records", flush=True)

    connection.execute(
        "UPDATE _open5e_imports SET row_count=?, imported_at=?, completed=1, error=NULL WHERE endpoint=?",
        (count, utc_now(), endpoint),
    )
    connection.commit()
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="open5e.sqlite3", help="Output SQLite filename")
    parser.add_argument("--api-root", default=DEFAULT_API_ROOT, help="Open5e API root")
    parser.add_argument(
        "--endpoint",
        action="append",
        dest="endpoints",
        help="Import only this endpoint; may be repeated",
    )
    parser.add_argument("--limit", type=int, default=100, help="Records requested per API page")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout in seconds")
    parser.add_argument("--retries", type=int, default=5, help="Retries for transient HTTP errors")
    parser.add_argument("--commit-every", type=int, default=500, help="Commit after this many rows")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Clear each selected endpoint table before importing",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 1 or args.commit_every < 1:
        print("--limit and --commit-every must be positive", file=sys.stderr)
        return 2

    database = Path(args.database).expanduser().resolve()
    database.parent.mkdir(parents=True, exist_ok=True)

    endpoints = discover_endpoints(args.api_root, args.retries, args.timeout)
    if args.endpoints:
        requested = set(args.endpoints)
        endpoints = {name: url for name, url in endpoints.items() if name in requested}
        missing = requested.difference(endpoints)
        # Explicit endpoint names are allowed even if root discovery omitted them.
        for name in missing:
            endpoints[name] = urllib.parse.urljoin(args.api_root, f"{name}/")

    if not endpoints:
        print("No endpoints found.", file=sys.stderr)
        return 1

    print(f"Database: {database}")
    print(f"API root: {args.api_root}")
    print(f"Endpoints: {', '.join(sorted(endpoints))}")

    failures = 0
    total = 0
    with sqlite3.connect(database) as connection:
        create_schema(connection)
        for endpoint, url in sorted(endpoints.items()):
            print(f"\nDownloading {endpoint} from {url}")
            try:
                count = import_endpoint(
                    connection,
                    endpoint,
                    url,
                    limit=args.limit,
                    retries=args.retries,
                    timeout=args.timeout,
                    replace=args.replace,
                    commit_every=args.commit_every,
                )
                total += count
                print(f"  Completed: {count:,} records")
            except urllib.error.HTTPError as exc:
                failures += 1
                message = f"HTTP {exc.code}: {exc.reason}"
                connection.execute(
                    "UPDATE _open5e_imports SET imported_at=?, completed=0, error=? WHERE endpoint=?",
                    (utc_now(), message, endpoint),
                )
                connection.commit()
                print(f"  Skipped/failed: {message}", file=sys.stderr)
            except Exception as exc:
                failures += 1
                message = f"{type(exc).__name__}: {exc}"
                connection.execute(
                    "UPDATE _open5e_imports SET imported_at=?, completed=0, error=? WHERE endpoint=?",
                    (utc_now(), message, endpoint),
                )
                connection.commit()
                print(f"  Failed: {message}", file=sys.stderr)

        connection.execute("PRAGMA optimize")

    print(f"\nFinished. Downloaded {total:,} records; {failures} endpoint(s) failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
