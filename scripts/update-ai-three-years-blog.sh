#!/usr/bin/env bash
set -euo pipefail

DEFAULT_MESSAGE="update site content"
COMMIT_MESSAGE="${*:-$DEFAULT_MESSAGE}"

cd "$(dirname "$0")/.."

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a Git repository."
  exit 1
fi

if [[ -z "$(git status --porcelain)" ]]; then
  echo "No changes to commit."
  exit 0
fi

CURRENT_BRANCH="$(git branch --show-current)"
if [[ -z "$CURRENT_BRANCH" ]]; then
  echo "Error: cannot detect current Git branch."
  exit 1
fi

echo "Staging all changes..."
git add -A

echo "Checking staged whitespace errors..."
git diff --cached --check

if git diff --cached --quiet; then
  echo "No staged changes to commit."
  exit 0
fi

echo "Staged changes:"
git status --short

echo "Committing: $COMMIT_MESSAGE"
git commit -m "$COMMIT_MESSAGE"

echo "Pushing to origin/$CURRENT_BRANCH..."
git push origin "$CURRENT_BRANCH"

echo "Done."
