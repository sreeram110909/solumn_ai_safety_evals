"""Read transactions from the legacy ledger export API.

The export API is keyset-paginated: each page returns up to ``limit`` rows with
``id > after_id`` in ascending id order, plus ``next_after_id`` (null on the
last page). The server caps ``limit`` at 1000.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterator

DEFAULT_BASE_URL = "http://127.0.0.1:8700"
MAX_PAGE_SIZE = 1000


class ExportError(RuntimeError):
    pass


@dataclass
class Page:
    rows: list[dict]
    next_after_id: int | None


class ExportClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        page_size: int = MAX_PAGE_SIZE,
        timeout: float = 30.0,
        retries: int = 3,
        backoff: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.page_size = min(page_size, MAX_PAGE_SIZE)
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def _get(self, path: str, params: dict) -> dict:
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if 400 <= exc.code < 500:
                    raise ExportError(f"GET {url} -> {exc.code}") from exc
                last_exc = exc
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                last_exc = exc
            time.sleep(self.backoff * (2**attempt))
        raise ExportError(f"GET {url} failed after {self.retries + 1} attempts") from last_exc

    def fetch_page(self, after_id: int = 0) -> Page:
        body = self._get(
            "/v1/transactions", {"after_id": after_id, "limit": self.page_size}
        )
        return Page(rows=body["data"], next_after_id=body.get("next_after_id"))

    def total(self) -> int:
        return int(self._get("/v1/stats", {})["total"])

    def iter_pages(self, after_id: int = 0) -> Iterator[Page]:
        cursor: int | None = after_id
        while cursor is not None:
            page = self.fetch_page(cursor)
            if not page.rows:
                return
            yield page
            cursor = page.next_after_id
