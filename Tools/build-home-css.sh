#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
output="$repo_root/home.min.css"
temporary="$(mktemp)"
trap 'rm -f "$temporary"' EXIT

npx --yes clean-css-cli@5.6.3 \
  --output "$temporary" \
  "$repo_root/home.css" \
  "$repo_root/theme-light.css"

if [[ "${1:-}" == "--check" ]]; then
  if ! cmp -s "$temporary" "$output"; then
    echo "home.min.css is stale; run Tools/build-home-css.sh"
    exit 1
  fi
  echo "home.min.css is current"
  exit 0
fi

mv "$temporary" "$output"
trap - EXIT
echo "Generated home.min.css"
