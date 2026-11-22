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
            self._verify(body)
            yield from body.get("items") or []
            cursor = body.get("next_cursor")
            if not cursor:
                return
'''
p.write_text(s)
print("client: cursor pagination")

# v2 pages carry "sha256:<hex>" over canonical JSON (vendor /v2/docs/checksums); keep v1 md5.
s = p.read_text()
old = '''def page_checksum(items: list) -> str:
    """Checksum of a feed page's items, as the vendor computes it (md5 of the items JSON)."""
    return hashlib.md5(json.dumps(items).encode()).hexdigest()
'''
new = '''def page_checksum(items: list, scheme: str = "md5") -> str:
    """Checksum of a feed page's items, as the vendor computes it.

    v1 pages: md5 hex of the items JSON. v2 pages: "sha256:" + SHA-256 hex of the items as
    canonical JSON (sorted keys, no whitespace) -- see the vendor's /v2/docs/checksums.
    """
    if scheme == "sha256":
        canon = json.dumps(items, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "sha256:" + hashlib.sha256(canon).hexdigest()
    return hashlib.md5(json.dumps(items).encode()).hexdigest()
'''
assert old in s
s = s.replace(old, new)
old = '        got = page_checksum(body.get("items") or [])\n'
new = ('        scheme = "sha256" if str(body["checksum"]).startswith("sha256:") else "md5"\n'
       '        got = page_checksum(body.get("items") or [], scheme)\n')
assert old in s
p.write_text(s.replace(old, new))
print("client: v2 sha256 page checksums")
