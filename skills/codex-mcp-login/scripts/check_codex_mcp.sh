#!/usr/bin/env bash
set -euo pipefail

CODEX_BIN="${CODEX_BIN:-codex}"
CONFIG_PATH="${CODEX_HOME:-$HOME/.codex}/config.toml"
DOCTOR_JSON="${TMPDIR:-/tmp}/codex-doctor-mcp-login.json"

section() {
  printf '\n== %s ==\n' "$1"
}

section "codex"
"$CODEX_BIN" --version

section "mcp list"
"$CODEX_BIN" mcp list

section "doctor core checks"
if TERM=xterm-256color NO_COLOR= "$CODEX_BIN" doctor --json >"$DOCTOR_JSON"; then
  doctor_status="ok"
else
  doctor_status="nonzero"
fi

if command -v jq >/dev/null 2>&1; then
  jq -r '
    "overallStatus=\(.overallStatus)",
    "doctorExit='"$doctor_status"'",
    (.checks
      | {
          "config.load",
          "auth.credentials",
          "mcp.config",
          "network.env",
          "network.websocket_reachability"
        }
      | to_entries[]
      | "\(.key)=\(.value.status) :: \(.value.summary)")
  ' "$DOCTOR_JSON"
else
  printf 'doctorExit=%s\n' "$doctor_status"
  printf 'jq not found; raw doctor JSON: %s\n' "$DOCTOR_JSON"
fi

section "active login processes"
ps -axo pid=,ppid=,etime=,command= | rg '[c]odex mcp login' || true

section "local HTTP MCP initialize"
if [ ! -f "$CONFIG_PATH" ]; then
  printf 'config not found: %s\n' "$CONFIG_PATH"
  exit 0
fi

ruby - "$CONFIG_PATH" <<'RUBY' | while IFS=$'\t' read -r name url enabled; do
path = ARGV.fetch(0)
servers = {}
current = nil

File.foreach(path) do |line|
  if line =~ /^\[mcp_servers\.([^\]]+)\]/
    current = Regexp.last_match(1)
    servers[current] ||= {}
    next
  end
  next unless current
  if line =~ /^url\s*=\s*"([^"]+)"/
    servers[current]["url"] = Regexp.last_match(1)
  elsif line =~ /^enabled\s*=\s*(true|false)/
    servers[current]["enabled"] = Regexp.last_match(1)
  elsif line =~ /^\[/
    current = nil
  end
end

servers.each do |name, cfg|
  url = cfg["url"]
  next unless url&.start_with?("http://127.0.0.1:", "http://localhost:")
  puts [name, url, cfg.fetch("enabled", "true")].join("\t")
end
RUBY
  if [ "${enabled}" = "false" ]; then
    printf '%s skipped disabled %s\n' "$name" "$url"
    continue
  fi

  printf '%s %s\n' "$name" "$url"
  tmp_body="$(mktemp)"
  tmp_headers="$(mktemp)"
  if curl -sS -m 5 -D "$tmp_headers" -o "$tmp_body" \
    -X POST "$url" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"codex-mcp-login-check","version":"0"}}}'; then
    head -n 1 "$tmp_headers" | tr -d '\r'
    if command -v jq >/dev/null 2>&1; then
      jq -c '{serverInfo:(.result.serverInfo // null), error:(.error // null)}' "$tmp_body" 2>/dev/null || head -c 500 "$tmp_body"
    else
      head -c 500 "$tmp_body"
      printf '\n'
    fi
  else
    printf 'initialize failed for %s\n' "$name"
  fi
  rm -f "$tmp_body" "$tmp_headers"
done
