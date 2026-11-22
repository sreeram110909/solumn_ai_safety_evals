"""Reference fix for CAT-218: follow v2 cursor pagination."""
from pathlib import Path

p = Path("/app/sync/client.py")
s = p.read_text()
start = s.index("    def iter_items(self) -> Iterator[dict]:")
s = s[:start] + '''    def iter_items(self) -> Iterator[dict]:
        """Yield every catalogue record (live items and tombstones) from the feed."""
        cursor = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            url = f"{self.base_url}/v2/products" + (f"?{urllib.parse.urlencode(params)}" if params else "")
            body = self.fetch_json(url)
            self._note(body)
            yield from body.get("items") or []
            cursor = body.get("next_cursor")
            if not cursor:
                return
'''
p.write_text(s)
print("client: cursor pagination")
