#!/usr/bin/env bash

set -euo pipefail

echo "🔎 Fetching open PR branches..."

# branches des PR ouvertes
PR_BRANCHES=$(gh pr list --state open --json headRefName -q '.[].headRefName')

# branches à garder
KEEP_BRANCHES="main"
KEEP_BRANCHES="$KEEP_BRANCHES $PR_BRANCHES"

echo "✅ Keeping:"
for b in $KEEP_BRANCHES; do
  echo " - $b"
done

echo ""
echo "🔎 Fetching remote branches..."

# toutes les branches remote (sans origin/)
#ALL_BRANCHES=$(git for-each-ref --format='%(refname:short)' refs/remotes/origin | sed 's|origin/||')
ALL_BRANCHES=$(git for-each-ref --format='%(refname:lstrip=3)' refs/remotes/origin | grep -v '^HEAD$')

echo ""
echo "🧹 Deleting branches not in keep list..."

for branch in $ALL_BRANCHES; do
  # skip HEAD symbolic ref
  if [[ "$branch" == "HEAD" ]]; then
    continue
  fi

  KEEP=false
  for keep in $KEEP_BRANCHES; do
    if [[ "$branch" == "$keep" ]]; then
      KEEP=true
      break
    fi
  done

  if [[ "$KEEP" == false ]]; then
    echo "❌ Deleting: $branch"
    git push origin --delete "$branch" -v
  else
    echo "✔ Keeping: $branch"
  fi
done

echo ""
echo "✅ Done"