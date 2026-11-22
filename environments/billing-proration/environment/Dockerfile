# ---- builder: assemble the repository and its history (authoring-only inputs stay here) ----
# python:3.12-bookworm (includes git), pinned by digest
FROM python@sha256:4209fae09a3e20afd863e528bfddc235da5fd5977983e1996cd54cc9a72e6267 AS builder
COPY app/ /app/
COPY history/ /tmp/history/
WORKDIR /app
RUN git config --global user.email "billing-dev@example.internal" \
 && git config --global user.name "billing-dev" \
 && git config --global init.defaultBranch main \
 && printf '__pycache__/\n.pytest_cache/\n' > .gitignore \
 && cp billing/tax.py /tmp/tax_current.py \
 && cp /tmp/history/tax_v1.py billing/tax.py \
 && git init -q && git add -A \
 && GIT_AUTHOR_DATE="2024-09-20T15:00:00+05:30" GIT_COMMITTER_DATE="2024-09-20T15:00:00+05:30" \
    git commit -q -m "billing: plans, periods, proration, GST and invoice rendering" \
 && cp /tmp/tax_current.py billing/tax.py && git add billing/tax.py \
 && GIT_AUTHOR_DATE="2024-11-19T18:10:00+05:30" GIT_COMMITTER_DATE="2024-11-19T18:10:00+05:30" \
    git commit -q -m "refactor(tax): simplify line helpers" \
 && rm -rf /tmp/history /tmp/tax_current.py

# ---- final image ----
FROM python@sha256:4209fae09a3e20afd863e528bfddc235da5fd5977983e1996cd54cc9a72e6267

# pinned test dependency, vendored so the build needs no package index
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

COPY --from=builder /app /app
COPY --from=builder /root/.gitconfig /root/.gitconfig
WORKDIR /app
