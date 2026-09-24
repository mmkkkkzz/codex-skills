#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

if is_disconnected; then
  print_status
  exit 0
fi

"$SCUTIL_BIN" --nc stop "$VPN_SERVICE"
if wait_for_connection_state disconnected 3; then
  print_status
  exit 0
fi

print_status
exit 1
