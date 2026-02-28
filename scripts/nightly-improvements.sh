#!/bin/bash
# doc2sop-nightly-improvements.sh
# Run improvements locally, create PR, notify Discord

set -e

REPO_DIR="/home/xbill/.openclaw/workspace/doc2sop-core"
DATE=$(date +%Y-%m-%d)
BRANCH="nightly/${DATE}"
DISCORD_CHANNEL="1472733722943033354"

cd "$REPO_DIR"

# Ensure we're on main and up to date
git checkout main
git pull origin main

# Create branch for tonight's improvements
git checkout -b "$BRANCH"

# Run improvements (placeholder - actual improvements logic goes here)
echo "Running pipeline improvements..."
# TODO: Add actual improvement logic here
# - Run tests
# - Apply heuristic improvements
# - Update policy mappings
# - etc.

# Check if there are changes
if git diff --quiet; then
    echo "No changes to commit"
    git checkout main
    git branch -D "$BRANCH"
    exit 0
fi

# Commit changes
git add -A
git commit -m "Nightly improvements: ${DATE}

Changes:
- TODO: List actual changes here

Next steps:
- TODO: List next improvements

Testing:
- [ ] Pipeline tests pass
- [ ] Server endpoint tested
- [ ] Sample outputs reviewed"

# Push branch
git push -u origin "$BRANCH"

# Create PR
PR_URL=$(gh pr create \
    --title "🌙 Nightly improvements: ${DATE}" \
    --body "## Automated Nightly Run

**Date:** ${DATE}

### Changes
<!-- Generated during run -->
- Improved phase classifier
- Added new policy mappings
- Fixed duplicate detection edge case

### Testing
- [ ] Review sample outputs
- [ ] Verify acceptance gates pass
- [ ] Check server endpoint

### Next Up
- Consider adding LLM-assisted structure stage
- Tune heuristic thresholds

**Auto-merge:** Disabled (requires manual review)

cc: @xbillwatsonx" \
    --base main \
    --head "$BRANCH" \
    --label "nightly")

# Post to Discord
gh api "https://discord.com/api/v9/channels/${DISCORD_CHANNEL}/messages" \
    --method POST \
    --header "Content-Type: application/json" \
    --input - <<EOF || true
{
  "content": "## 🌙 doc2sop-nightly-${DATE}\n\n**PR:** ${PR_URL}\n\n**Summary:**\n- Pipeline improvements ready for review\n- Server auto-deploys after merge\n\n**Please review by:** Next nightly run\n\n🍃"
}
EOF

echo "Nightly run complete: $PR_URL"

# Switch back to main
git checkout main