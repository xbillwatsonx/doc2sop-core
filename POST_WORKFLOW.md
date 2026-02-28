# X/Twitter Post Workflow

## Trigger
Significant improvement merged to main (not every PR)

## Process
1. Detect merge to main with meaningful changes
2. Generate post draft using VOICE.md guidelines
3. Run through humanizer skill
4. Queue for daily batch review
5. Present to Bill with:
   - Draft post
   - Reason for significance
   - Option: Approve / Edit / Skip / Delete+Consult

## Daily Batch Timing
- **Review window:** Bill's preferred time (morning check)
- **Queue location:** Discord DM or #doc2sop-lab thread
- **Expiry:** 24 hours, then auto-skip (can be recovered)

## Approval Interface
```
📬 Post Ready for Review

Draft:
[post text]

Significance: [why this matters]

[Approve] [Edit] [Skip] [Delete+Consult]
```

## If Deleted
- Pause posting
- Notify: "Post deleted — consultation needed before continuing"
- Resume only after explicit go-ahead

## X API Setup Needed
- OAuth app under @xbillwatsonx
- Post permissions (write, not DMs)
- Rate limiting: max 5 posts/day to start
