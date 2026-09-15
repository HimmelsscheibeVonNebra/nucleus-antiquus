#!/usr/bin/env bash
set -euo pipefail
exec "$(dirname "$0")/run.sh" -S -gdb tcp:127.0.0.1:1234 "$@"
