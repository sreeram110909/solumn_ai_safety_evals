#!/bin/bash
# Build the submission archive: environments/, results/, QUALITY_BAR.md, README.md — then key-grep it.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=${1:-submission}
mkdir -p "$OUT" && rm -f "$OUT/solumn_rle_submission.tar.gz"
mkdir -p results/_tools && cp agents/unsafe_oracle.py results/_tools/unsafe_oracle.py
tar --exclude='__pycache__' --exclude='node_modules' -czf "$OUT/solumn_rle_submission.tar.gz" environments results QUALITY_BAR.md README.md
D=$(mktemp -d); tar -xzf "$OUT/solumn_rle_submission.tar.gz" -C "$D"
echo "top-level entries: $(ls "$D" | tr '\n' ' ')"
K=$(grep OPENAI_API_KEY .env | cut -d= -f2 | cut -c9-30)
P="sk-""rlej-"  # the issued key prefix, built from parts
hits=$( { grep -r "$P" "$D" || true; grep -r "$K" "$D" || true; } | wc -l)
echo "key grep hits (issued key prefix + real key fragment): $hits"
rm -rf "$D"; ls -la "$OUT/solumn_rle_submission.tar.gz"
