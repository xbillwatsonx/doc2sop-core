#!/usr/bin/env bash
# Helper to package doc2sop nightly changes into a branch + PR.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

RUN_DATE="${1:-$(date +%F)}"
BRANCH_NAME="nightly/${RUN_DATE}"
PR_BASE="${DOC2SOP_PR_BASE:-main}"
COMMIT_MSG="${DOC2SOP_COMMIT_MSG:-Nightly refinement ${RUN_DATE}}"
PR_TITLE="${DOC2SOP_PR_TITLE:-Nightly doc2sop refinement ${RUN_DATE}}"
PR_BODY=${DOC2SOP_PR_BODY:-$'Automated nightly doc2sop refinement.\n\n- Synced curated pipeline updates\n- Smoke + welding sample rerun\n- See nightly notes for validation evidence'}

if git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
  git checkout "$BRANCH_NAME"
else
  git checkout -b "$BRANCH_NAME"
fi

git add -A
if git diff --cached --quiet; then
  echo "No staged changes; nothing to commit."
  exit 0
fi

git commit -m "$COMMIT_MSG"
git push -u origin "$BRANCH_NAME"

if gh pr view "$BRANCH_NAME" >/dev/null 2>&1; then
  echo "PR already exists for $BRANCH_NAME"
else
  gh pr create --base "$PR_BASE" --head "$BRANCH_NAME" --title "$PR_TITLE" --body "$PR_BODY"
fi
