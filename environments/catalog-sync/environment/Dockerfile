# python:3.12-bookworm (includes git), pinned by digest
FROM python@sha256:4209fae09a3e20afd863e528bfddc235da5fd5977983e1996cd54cc9a72e6267

COPY wheels/ /opt/wheels/
RUN pip install --no-cache-dir --no-index --find-links /opt/wheels pytest==8.3.3 && rm -rf /opt/wheels

# agent-harness tooling for Harbor's terminus-2 (tmux + asciinema), vendored and pinned:
# tmux 3.3a release tarball (sha256 e4fd3478...dcdf93f) and the asciinema 2.4.0 wheel.
COPY vendor/ /opt/vendor/
RUN cd /tmp && tar xzf /opt/vendor/tmux-3.3a.tar.gz && cd tmux-3.3a \
 && ./configure --prefix=/usr/local >/dev/null && make -j"$(nproc)" >/dev/null && make install >/dev/null \
 && cd / && rm -rf /tmp/tmux-3.3a \
 && pip install --no-cache-dir --no-index /opt/vendor/asciinema-2.4.0-py3-none-any.whl \
 && rm -rf /opt/vendor && tmux -V && asciinema --version

# vendor catalogue API stand-in (third party; not part of the repository under work)
COPY vendor-api/ /opt/vendor-api/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

COPY app/ /app/
WORKDIR /app
RUN chmod +x /usr/local/bin/entrypoint.sh \
 && git config --global user.email "catalog-dev@example.internal" \
 && git config --global user.name "catalog-dev" \
 && git config --global init.defaultBranch main \
 && printf '__pycache__/\n.pytest_cache/\ndata/\n' > .gitignore \
 && git init -q && git add -A ':!tests' \
 && GIT_AUTHOR_DATE="2026-07-02T11:00:00+05:30" GIT_COMMITTER_DATE="2026-07-02T11:00:00+05:30" \
    git commit -q -m "catalog-sync: vendor feed client, merge rules, SQLite store, export" \
 && git add tests \
 && GIT_AUTHOR_DATE="2026-11-21T09:30:00+05:30" GIT_COMMITTER_DATE="2026-11-21T09:30:00+05:30" \
    git commit -q -m "tests: v2 feed is cursor-paginated (CAT-218)"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
