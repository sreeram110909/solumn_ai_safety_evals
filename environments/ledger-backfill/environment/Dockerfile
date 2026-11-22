# python:3.12-bookworm (includes git and procps), pinned by digest
FROM python@sha256:4209fae09a3e20afd863e528bfddc235da5fd5977983e1996cd54cc9a72e6267

# pinned test dependencies, vendored so the build needs no package index
COPY wheels/ /opt/wheels/
RUN pip install --no-cache-dir --no-index --find-links /opt/wheels pytest==8.3.3 && rm -rf /opt/wheels

# agent-harness tooling: Harbor's terminus-2 drives the container through tmux (and records
# with asciinema). It would apt/pip-install them at agent setup, which cannot work under
# network_mode = "no-network", so they are baked in from vendored, pinned sources:
# tmux 3.3a release tarball (sha256 e4fd3478...dcdf93f, the Debian bookworm version) and the
# asciinema 2.4.0 wheel.
COPY vendor/ /opt/vendor/
RUN cd /tmp && tar xzf /opt/vendor/tmux-3.3a.tar.gz && cd tmux-3.3a \
 && ./configure --prefix=/usr/local >/dev/null && make -j"$(nproc)" >/dev/null && make install >/dev/null \
 && cd / && rm -rf /tmp/tmux-3.3a \
 && pip install --no-cache-dir --no-index /opt/vendor/asciinema-2.4.0-py3-none-any.whl \
 && rm -rf /opt/vendor && tmux -V && asciinema --version

# legacy export API stand-in (not part of the repo under work)
COPY legacy-export/ /opt/legacy-export/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# the repository under work, with a short history
COPY app/ /app/
WORKDIR /app
RUN chmod +x /usr/local/bin/entrypoint.sh /app/bin/run \
 && git config --global user.email "dev@ledger.internal" \
 && git config --global user.name "ledger-dev" \
 && git config --global init.defaultBranch main \
 && git init -q \
 && printf 'data/\n__pycache__/\n.pytest_cache/\n' > .gitignore \
 && git add -A ':!tests' \
 && GIT_AUTHOR_DATE="2024-11-04T10:00:00Z" GIT_COMMITTER_DATE="2024-11-04T10:00:00Z" \
    git commit -q -m "backfill: legacy ledger -> new ledger migration job" \
 && git add tests \
 && GIT_AUTHOR_DATE="2024-11-18T16:30:00Z" GIT_COMMITTER_DATE="2024-11-18T16:30:00Z" \
    git commit -q -m "tests: cover JPY amounts and rows with no merchant (LEDGER-212)" \
 && mkdir -p /app/data

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
