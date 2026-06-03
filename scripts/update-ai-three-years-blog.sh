#!/usr/bin/env bash
set -euo pipefail

POST_FILE="blog/posts/2026-06-03-ai-three-years-nine-lessons/index.html"
DEFAULT_MESSAGE="update AI three years blog post"
COMMIT_MESSAGE="${*:-$DEFAULT_MESSAGE}"

cd "$(dirname "$0")/.."

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a Git repository."
  exit 1
fi

if [[ ! -f "$POST_FILE" ]]; then
  echo "Error: target blog file not found: $POST_FILE"
  exit 1
fi

if git diff --quiet -- "$POST_FILE" && git diff --cached --quiet -- "$POST_FILE"; then
  echo "No changes to commit for $POST_FILE"
  exit 0
fi

CURRENT_BRANCH="$(git branch --show-current)"
if [[ -z "$CURRENT_BRANCH" ]]; then
  echo "Error: cannot detect current Git branch."
  exit 1
fi

echo "Checking whitespace errors..."
git diff --check -- "$POST_FILE"

echo "Staging $POST_FILE..."
git add "$POST_FILE"

echo "Committing: $COMMIT_MESSAGE"
git commit -m "$COMMIT_MESSAGE" -- "$POST_FILE"

echo "Pushing to origin/$CURRENT_BRANCH..."
git push origin "$CURRENT_BRANCH"

echo "Done."
