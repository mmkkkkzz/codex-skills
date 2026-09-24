#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

if is_connected; then
  print_status
  exit 0
fi

if ! explicit_password >/dev/null || ! explicit_secret >/dev/null; then
  print_shared_secret_guidance
  exit 1
fi

start_with_explicit_credentials
if wait_for_connection_state connected 8; then
  print_status
  exit 0
fi

print_status
print_shared_secret_guidance

exit 1
