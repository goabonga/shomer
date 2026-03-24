#!/bin/bash
set -euo pipefail

REPO="${1:-goabonga/shomer}"

echo "=== Creating documentation labels for $REPO ==="

gh label create "type:docs" --repo "$REPO" --color "0075CA" --description "Documentation" --force

echo "=== Documentation labels created ($REPO) ==="
