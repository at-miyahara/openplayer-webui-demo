#!/bin/sh
# 実機から /api/* の控えを取る。既定は USB NCM 接続時のアドレス。
#   ./tools/snapshot.sh [host]
set -e
HOST="${1:-10.67.210.1}"
DIR="$(dirname "$0")/fixtures"
mkdir -p "$DIR"
for e in status config triggers audiolist ntp network; do
  curl -sf -m 10 "http://$HOST/api/$e" -o "$DIR/$e.json"
  echo "$e: $(wc -c < "$DIR/$e.json" | tr -d ' ') bytes"
done
