# probe image: python:3.12-bookworm (git, procps), pinned by digest
FROM python@sha256:4209fae09a3e20afd863e528bfddc235da5fd5977983e1996cd54cc9a72e6267
COPY wheels/ /opt/wheels/
RUN pip install --no-cache-dir --no-index --find-links /opt/wheels pytest==8.3.3 && rm -rf /opt/wheels
COPY vendor/ /opt/vendor/
RUN cd /tmp && tar xzf /opt/vendor/tmux-3.3a.tar.gz && cd tmux-3.3a \
 && ./configure --prefix=/usr/local >/dev/null && make -j"$(nproc)" >/dev/null && make install >/dev/null \
 && cd / && rm -rf /tmp/tmux-3.3a \
 && pip install --no-cache-dir --no-index /opt/vendor/asciinema-2.4.0-py3-none-any.whl \
 && rm -rf /opt/vendor && tmux -V && asciinema --version

ENV PYTHONPATH=/app:/app/vendor
COPY app/ /app/
WORKDIR /app
RUN git config --global user.email "me@example.internal" && git config --global user.name "me" \
 && git config --global init.defaultBranch main && printf '__pycache__/\n.pytest_cache/\n' > .gitignore \
 && git init -q && git add -A && git commit -q -m "notes: v3 schema (archived flag), migration 003; archive command WIP"
