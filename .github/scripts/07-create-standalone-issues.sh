#!/bin/bash
set -euo pipefail

REPO="${1:-goabonga/shomer}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ISSUES_DIR="$(dirname "$SCRIPT_DIR")/issues"

echo "=== Creating standalone issues for $REPO ==="

create_issue() {
    local file="$1"
    local title="$2"
    local labels="$3"

    local filepath="$ISSUES_DIR/$file"
    if [[ ! -f "$filepath" ]]; then
        echo "ERROR: File not found: $filepath"
        return 1
    fi

    echo -n "Creating: $title ... "
    local url
    url=$(gh issue create --repo "$REPO" \
        --title "$title" \
        --body-file "$filepath" \
        --label "$labels")
    echo "$url"
    sleep 0.5
}

create_issue "142-ci-skip-draft-prs.md" \
    "chore(ci): skip CI workflows on draft pull requests" \
    "type:infra,size:S"

echo ""
echo "=== Standalone issues created for $REPO ==="
