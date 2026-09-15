#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker build --platform linux/amd64 -t linux-011-builder .
docker run --rm --platform linux/amd64 \
  -v "$PWD/lab:/work" -w /work linux-011-builder \
  make 'CFLAGS=-g -m32 -fno-pie -fno-builtin -fno-stack-protector -fomit-frame-pointer -fcommon -I/work/include'
