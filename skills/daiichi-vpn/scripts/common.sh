#!/bin/zsh

set -euo pipefail

VPN_SERVICE="${DAIICHI_VPN_SERVICE:-daiichi-ec}"
VPN_AUTH_USER="${DAIICHI_VPN_AUTH_USER:-daiichi}"
SCUTIL_BIN="/usr/sbin/scutil"

raw_status() {
  "$SCUTIL_BIN" --nc status "$VPN_SERVICE"
}

status_line() {
  raw_status | head -n 1
}

is_connected() {
  [[ "$(status_line)" == Connected* ]]
}

is_disconnected() {
  [[ "$(status_line)" == Disconnected* ]]
}

print_status() {
  raw_status
}

wait_for_connection_state() {
  local expected="$1"
  local timeout="${2:-10}"
  local elapsed=0

  while (( elapsed < timeout )); do
    case "$expected" in
      connected)
        is_connected && return 0
        ;;
      disconnected)
        is_disconnected && return 0
        ;;
      *)
        print -u2 -- "Unknown wait state: $expected"
        return 1
        ;;
    esac

    sleep 1
    (( elapsed += 1 ))
  done

  return 1
}

explicit_password() {
  if [[ -n "${DAIICHI_VPN_PASSWORD:-}" ]]; then
    print -rn -- "${DAIICHI_VPN_PASSWORD}"
    return 0
  fi

  if [[ -n "${DAIICHI_VPN_PASSWORD_FILE:-}" && -r "${DAIICHI_VPN_PASSWORD_FILE}" ]]; then
    head -n 1 "${DAIICHI_VPN_PASSWORD_FILE}" | tr -d '\r\n'
    return 0
  fi

  security find-generic-password -a "$USER" -s DAIICHI_VPN_PASSWORD -w 2>/dev/null
}

explicit_secret() {
  if [[ -n "${DAIICHI_VPN_SECRET:-}" ]]; then
    print -rn -- "${DAIICHI_VPN_SECRET}"
    return 0
  fi

  if [[ -n "${DAIICHI_VPN_SECRET_FILE:-}" && -r "${DAIICHI_VPN_SECRET_FILE}" ]]; then
    head -n 1 "${DAIICHI_VPN_SECRET_FILE}" | tr -d '\r\n'
    return 0
  fi

  security find-generic-password -a "$USER" -s DAIICHI_VPN_SECRET -w 2>/dev/null
}

start_with_explicit_credentials() {
  local password secret
  password="$(explicit_password)"
  secret="$(explicit_secret)"

  "$SCUTIL_BIN" --nc start "$VPN_SERVICE" \
    --user "$VPN_AUTH_USER" \
    --password "$password" \
    --secret "$secret"
}

print_shared_secret_guidance() {
  cat >&2 <<'EOF'
Store the VPN password and IPsec shared secret in macOS Keychain as generic
passwords with account `$USER` and services `DAIICHI_VPN_PASSWORD` and
`DAIICHI_VPN_SECRET`. Environment variables or `*_FILE` overrides also work.
EOF
}
