#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -f lab/Image ]] || { echo '먼저 ./scripts/build.sh를 실행하세요.' >&2; exit 1; }
exec qemu-system-i386 \
  -accel tcg -m 16M -boot a \
  -drive file=lab/Image,format=raw,if=floppy \
  -drive file=lab/hdc-0.11.img,format=raw,if=ide \
  -nic none -snapshot "$@"
