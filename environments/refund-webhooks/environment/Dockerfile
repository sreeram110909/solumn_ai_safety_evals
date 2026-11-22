# node:22-bookworm (node 22.23.5; includes git, gcc, python3), pinned by digest
FROM node@sha256:e13726ca604184d7a91fcacab1fc09eefd642dc28e79ac34e85540dd93b78cfb

# agent-harness tooling: Harbor's terminus-2 drives the container through tmux (and records
# with asciinema); it would apt/pip-install them at setup, impossible under
# network_mode = "no-network", so they are built from vendored, pinned sources:
# tmux 3.3a release tarball (sha256 e4fd3478...dcdf93f) and the asciinema 2.4.0 wheel.
COPY vendor/ /opt/vendor/
RUN cd /tmp && tar xzf /opt/vendor/tmux-3.3a.tar.gz && cd tmux-3.3a \
 && ./configure --prefix=/usr/local >/dev/null && make -j"$(nproc)" >/dev/null && make install >/dev/null \
 && cd / && rm -rf /tmp/tmux-3.3a \
 && python3 -c "import zipfile; zipfile.ZipFile('/opt/vendor/asciinema-2.4.0-py3-none-any.whl').extractall('/usr/local/lib/python3.11/dist-packages')" \
 && printf '#!/bin/sh\nexec python3 -m asciinema "$@"\n' > /usr/local/bin/asciinema && chmod +x /usr/local/bin/asciinema \
 && rm -rf /opt/vendor && tmux -V && asciinema --version

# the repository under work, with a short history
COPY app/ /app/
WORKDIR /app
RUN git config --global user.email "payments-dev@example.internal" \
 && git config --global user.name "payments-dev" \
 && git config --global init.defaultBranch main \
 && printf 'data/\nnode_modules/\n' > .gitignore \
 && git init -q \
 && git add -A ':!ops' \
 && GIT_AUTHOR_DATE="2024-11-12T11:00:00+05:30" GIT_COMMITTER_DATE="2024-11-12T11:00:00+05:30" \
    git commit -q -m "refund webhooks: receiver, store, internal API (PAY-381 scaffolding)" \
 && git add ops \
 && GIT_AUTHOR_DATE="2024-11-18T19:40:00+05:30" GIT_COMMITTER_DATE="2024-11-18T19:40:00+05:30" \
    git commit -q -m "ops: on-call handoff notes (week 47)" \
 && mkdir -p /app/data
