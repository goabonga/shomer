#!/usr/bin/env bash

set -euo pipefail

echo "🔎 Fetching open PR branches..."

# branches utilisées par les PR ouvertes
PR_BRANCHES=$(gh pr list --state open --json headRefName -q '.[].headRefName')

# branches à garder
KEEP_BRANCHES="main"
KEEP_BRANCHES="$KEEP_BRANCHES $PR_BRANCHES"

echo "✅ Keeping:"
for b in $KEEP_BRANCHES; do
  echo " - $b"
done

echo ""
echo "🔎 Fetching local branches..."

# branches locales uniquement
ALL_BRANCHES=$(git for-each-ref --format='%(refname:short)' refs/heads)

echo ""
echo "🧹 Deleting local branches not in keep list..."

for branch in $ALL_BRANCHES; do
  KEEP=false

  for keep in $KEEP_BRANCHES; do
    if [[ "$branch" == "$keep" ]]; then
      KEEP=true
      break
    fi
  done

  if [[ "$KEEP" == false ]]; then
    echo "❌ Deleting: $branch"
    git branch -d "$branch" || git branch -D "$branch"
  else
    echo "✔ Keeping: $branch"
  fi
done

echo ""
echo "✅ Done"