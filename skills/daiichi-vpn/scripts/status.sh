#!/bin/zsh

set -euo pipefail

VPN_SERVICE="${DAIICHI_VPN_SERVICE:-daiichi-ec}"

scutil --nc status "$VPN_SERVICE"
