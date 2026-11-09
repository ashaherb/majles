#!/usr/bin/env bash
# Smoke check for an installed `majles`: usage `install_smoke.sh <path-to-majles>`.
# Prints the version, makes a throwaway project in a temp folder and checks the
# files every project must have. Used by CI's install job.
set -euo pipefail
bin="$1"
"$bin" --version
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cd "$tmp"
"$bin" new demo
for f in CLAUDE.md README.md .majles.json .claude/rules/majles.md .claude/agents; do
  test -e "demo/$f" || { echo "missing: demo/$f" >&2; exit 1; }
done
echo "smoke ok: $bin"
