#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${OUT_DIR:-$ROOT/reports}"
DATE_UTC="$(date -u +%Y-%m-%d)"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUT_FILE="$OUT_DIR/guardian-review-$DATE_UTC.md"

HOST_AUDIT="$ROOT/scripts/audit_openclaw_host.py"
CFG_AUDIT="$ROOT/scripts/audit_openclaw_config.py"
SBX_AUDIT="$ROOT/scripts/audit_subagent_sandbox.py"
CONFIG_PATH="${1:-/home/hex/.openclaw/workspace/.openclaw/workspace-state.json}"

mkdir -p "$OUT_DIR"

host_json="$($HOST_AUDIT)"
cfg_json="$($CFG_AUDIT "$CONFIG_PATH" 2>/dev/null || echo '{"verdict":"FAIL","score":20,"error":"config audit failed"}')"
sbx_json="$($SBX_AUDIT "$CONFIG_PATH" 2>/dev/null || echo '{"verdict":"FAIL","score":20,"error":"sandbox audit failed"}')"

extract() {
  local key="$1"
  python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print(d.get(sys.argv[1], "n/a"))' "$key"
}

host_verdict="$(printf '%s' "$host_json" | extract verdict)"
host_score="$(printf '%s' "$host_json" | extract score)"
cfg_verdict="$(printf '%s' "$cfg_json" | extract verdict)"
cfg_score="$(printf '%s' "$cfg_json" | extract score)"
sbx_verdict="$(printf '%s' "$sbx_json" | extract verdict)"
sbx_score="$(printf '%s' "$sbx_json" | extract score)"

{
  echo "# Aether Guardian Daily Security Review"
  echo
  echo "Generated: $TS"
  echo
  echo "## Summary"
  echo "- Host audit: **$host_verdict** (score $host_score)"
  echo "- Config audit: **$cfg_verdict** (score $cfg_score)"
  echo "- Sandbox audit: **$sbx_verdict** (score $sbx_score)"
  echo
  echo "## Raw JSON Results"
  echo
  echo "### Host"
  echo '```json'
  printf '%s\n' "$host_json"
  echo '```'
  echo
  echo "### Config"
  echo '```json'
  printf '%s\n' "$cfg_json"
  echo '```'
  echo
  echo "### Sandbox"
  echo '```json'
  printf '%s\n' "$sbx_json"
  echo '```'
} > "$OUT_FILE"

echo "Report written: $OUT_FILE"
