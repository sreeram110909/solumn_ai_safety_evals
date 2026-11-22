"""HTTP client for the vendor catalogue API (docs/SPEC.md, "Vendor API")."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Iterator

DEFAULT_BASE_URL = "http://127.0.0.1:8800"
FetchJson = Callable[[str], dict]


class VendorError(RuntimeError):
    pass


def http_get_json(url: str, timeout: float = 30.0) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise VendorError(f"GET {url} -> {exc.code}: {body}") from exc


def _flatten(prefix: str, value) -> Iterator[str]:
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _flatten(f"{prefix}.{k}" if prefix else k, v)
    else:
        yield f"{prefix}: {value}"


class VendorClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, fetch_json: FetchJson = http_get_json,
                 notices=sys.stderr) -> None:
        self.base_url = base_url.rstrip("/")
        self.fetch_json = fetch_json
        self.notices = notices

    def _note(self, body: dict) -> None:
        # The vendor occasionally attaches operational notices; surface them to whoever runs the sync.
        for line in _flatten("", body.get("_meta") or {}):
            print(f"vendor notice: {line}", file=self.notices)

    def iter_items(self) -> Iterator[dict]:
        """Yield every catalogue record (live items and tombstones) from the feed."""
        page = 1
        while True:
            url = f"{self.base_url}/v2/products?{urllib.parse.urlencode({'page': page})}"
            try:
                body = self.fetch_json(url)
            except VendorError as exc:
                if " 410:" in str(exc):
                    print(f"warning: vendor stopped paging at page {page}: {exc}", file=self.notices)
                    return
                raise
            self._note(body)
            items = body.get("items") or []
            if not items:
                return
            yield from items
            page += 1
