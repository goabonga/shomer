#!/bin/bash
set -euo pipefail

REPO=""
ISSUE=""
BRANCH_OVERRIDE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch) BRANCH_OVERRIDE="$2"; shift 2 ;;
        *) if [[ -z "$REPO" ]]; then REPO="$1"; elif [[ -z "$ISSUE" ]]; then ISSUE="$1"; fi; shift ;;
    esac
done

if [[ -z "$REPO" || -z "$ISSUE" ]]; then
    echo "Usage: $0 <owner/repo> <issue-number> [--branch <branch-name>]"
    echo ""
    echo "Examples:"
    echo "  $0 goabonga/shomer 33"
    echo "  $0 goabonga/shomer 142 --branch chore/142-ci-skip-draft-prs"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
BRANCHES_FILE="$ROOT_DIR/BRANCHES.md"
PRS_DIR="$SCRIPT_DIR/../prs"

# Resolve branch name: --branch flag > BRANCHES.md lookup
if [[ -n "$BRANCH_OVERRIDE" ]]; then
    BRANCH="$BRANCH_OVERRIDE"
else
    BRANCH=$(grep -P "^\| #${ISSUE} \|" "$BRANCHES_FILE" | grep -oP '`[^`]+`' | tail -1 | tr -d '`' || true)
    if [[ -z "$BRANCH" ]]; then
        echo "ERROR: no branch found for issue #${ISSUE} in BRANCHES.md"
        echo "Hint: use --branch <name> for issues outside milestones"
        exit 1
    fi
fi

# Find PR template file (try feat-, docs-, chore-)
PADDED=$(printf '%03d' "$ISSUE")
PR_FILE=$(ls "$PRS_DIR"/feat-${PADDED}-*.md 2>/dev/null || ls "$PRS_DIR"/docs-${PADDED}-*.md 2>/dev/null || ls "$PRS_DIR"/chore-${PADDED}-*.md 2>/dev/null || true)

if [[ -z "$PR_FILE" ]]; then
    echo "ERROR: no PR template found for issue #${ISSUE} in $PRS_DIR"
    exit 1
fi

# Extract PR title from template (first ## line)
PR_TITLE=$(head -1 "$PR_FILE" | sed 's/^## //')

# Generate PR body with correct issue number
PR_BODY=$(mktemp)
sed "s|Closes #[0-9]*|Closes #${ISSUE}|g" "$PR_FILE" > "$PR_BODY"
trap "rm -f $PR_BODY" EXIT

echo "=== Starting issue #${ISSUE} ==="
echo "Branch: $BRANCH"
echo "PR title: $PR_TITLE"
echo ""

# Check if branch already exists (locally or remotely)
LOCAL_EXISTS=$(git branch --list "$BRANCH" | wc -l)
REMOTE_EXISTS=$(git ls-remote --heads origin "$BRANCH" 2>/dev/null | wc -l)

# Check if a PR already exists for this branch
EXISTING_PR=$(gh pr list --repo "$REPO" --head "$BRANCH" --json number --jq '.[0].number' 2>/dev/null || true)

if [[ "$LOCAL_EXISTS" -gt 0 || "$REMOTE_EXISTS" -gt 0 ]]; then
    echo "Branch '$BRANCH' already exists — resuming."

    # Switch to the existing branch
    if [[ "$LOCAL_EXISTS" -gt 0 ]]; then
        git checkout "$BRANCH"
    else
        git checkout -b "$BRANCH" "origin/$BRANCH"
    fi

    # Pull latest changes if tracking remote
    git pull --ff-only 2>/dev/null || true

    # Create PR if it doesn't exist yet
    if [[ -z "$EXISTING_PR" ]]; then
        echo "No PR found — creating draft PR."
        gh pr create --repo "$REPO" \
            --title "$PR_TITLE" \
            --body-file "$PR_BODY" \
            --draft
    else
        echo "PR #${EXISTING_PR} already exists."
    fi

    echo ""
    echo "=== Resumed ==="
    echo "Branch '$BRANCH' checked out. PR is ready."
    echo "Continue coding, then push your changes."
else
    # Create branch from latest main
    git checkout main
    git pull --ff-only
    git checkout -b "$BRANCH"

    # Empty commit to initialize the branch
    git commit --allow-empty -m "chore: init branch for #${ISSUE}

ref #${ISSUE}"

    # Push branch
    git push -u origin "$BRANCH"

    # Create PR as draft using template
    gh pr create --repo "$REPO" \
        --title "$PR_TITLE" \
        --body-file "$PR_BODY" \
        --draft

    echo ""
    echo "=== Done ==="
    echo "Branch '$BRANCH' created with draft PR."
    echo "Start coding, then push your changes."
fi
