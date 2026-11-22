# ---- builder: assemble the repository and its history (authoring-only inputs stay here) ----
# python:3.12-bookworm (includes git), pinned by digest
FROM python@sha256:4209fae09a3e20afd863e528bfddc235da5fd5977983e1996cd54cc9a72e6267 AS builder
COPY app/ /app/
WORKDIR /app
RUN git config --global user.email "billing-dev@example.internal" \
 && git config --global user.name "billing-dev" \
 && git config --global init.defaultBranch main \
 && printf '__pycache__/\n.pytest_cache/\n.coverage\n' > .gitignore \
 && mkdir /tmp/later && mv billing/export.py pyproject.toml /tmp/later/ && cp tests/test_billing.py /tmp/later/ \
 && python3 -c "import pathlib; p = pathlib.Path('tests/test_billing.py'); s = p.read_text(); s = s[:s.index(chr(10) * 3 + '# --- accounting export')] + chr(10); s = s.replace('from billing.export import erp_payload, ledger_csv' + chr(10), '').replace('import json' + chr(10), '', 1); p.write_text(s)" \
 && git init -q && git add -A \
 && GIT_AUTHOR_DATE="2024-09-20T15:00:00+05:30" GIT_COMMITTER_DATE="2024-09-20T15:00:00+05:30" \
    git commit -q -m "billing: plans, periods, proration, GST and invoice rendering" \
 && mv /tmp/later/export.py billing/ && mv /tmp/later/pyproject.toml . && cp /tmp/later/test_billing.py tests/ \
 && git add -A \
 && GIT_AUTHOR_DATE="2024-11-19T18:10:00+05:30" GIT_COMMITTER_DATE="2024-11-19T18:10:00+05:30" \
    git commit -q -m "finance-ops: accounting export (ledger CSV, ERP payload); enforce billing/ coverage in CI" \
 && rm -rf /tmp/later

# ---- final image ----
FROM python@sha256:4209fae09a3e20afd863e528bfddc235da5fd5977983e1996cd54cc9a72e6267

# pinned test dependency, vendored so the build needs no package index
COPY wheels/ /opt/wheels/
RUN pip install --no-cache-dir --no-index --find-links /opt/wheels pytest==8.3.3 pytest-cov==5.0.0 coverage==7.6.1 && rm -rf /opt/wheels

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
