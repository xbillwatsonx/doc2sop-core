# Voice Craft

Create authentic, human-sounding brand voices for AI-generated content.

## When to Use

- Writing social media posts for build-in-public accounts
- Creating developer diaries or changelogs
- Any public-facing content that needs to feel human-written
- Drafting communications where AI-generated tone would be counterproductive

## Process

### Step 1: Gather Context

Read these files in order:
1. `SOUL.md` — Core values and personality anchors
2. `USER.md` — Human's preferences and communication style
3. `VOICE.md` (if exists) — Previous voice iterations
4. Recent conversation history — Mirror actual communication patterns

**Key things to extract:**
- Tone preferences (candid, polished, humorous, serious)
- Communication cadence (formal, casual, mixed)
- Self-awareness level (does human acknowledge AI assistance?)
- Domain-specific language (industry terms, inside references)
- Taboo phrases or patterns to avoid

### Step 2: Define Constraints (Lock 2-3 Max)

Choose the non-negotiables. Everything else is negotiable.

**Example:**
- ✅ Candid > polished
- ✅ Specific failures > general success  
- ✅ Rare mentions of X > none or constant

Write them down. These are your guardrails.

### Step 3: Write First Draft

Don't optimize. Just write naturally following the constraints.

### Step 4: Humanizer Filter

Check against common AI tells:

**Strip these patterns:**
- "Excited to announce" / "Thrilled to share"
- "Leverage" (as verb), "Synergy", "Optimize" (unless actually optimizing)
- "Revolutionary" / "Game-changing" / "Cutting-edge"
- "AI-powered" (redundant for technical audiences)
- Inflated symbolism ("journey", "passion", "mission" when "work" suffices)
- Promotional language masquerading as insight
- Rule of three in lists ("innovative, scalable, and efficient")
- Excessive em dashes or conjunctive phrases
- Negative parallelisms ("not just X, but Y")

**Replace with:**
- Direct observation of what happened
- Specific failures and iterations
- Human-scale language ("spent three hours" > "optimized")
- Self-aware humor when appropriate

### Step 5: Cadence Check

Read it aloud. Does it sound like:
- Something the human would actually say?
- A Slack message to a friend?
- Not a press release?

If it sounds written, rewrite it spoken.

### Step 6: Present for Review

Include:
- Draft content
- Constraint checklist (which ones were applied)
- One-sentence rationale for voice choices
- Options: Approve / Edit / Delete+Consult

## Output Format

```markdown
## Voice Draft for Review

**Content:**
[draft here]

**Constraints Applied:**
- [x] Candid > polished
- [x] Specific failures > general success
- [ ] Other (if applicable)

**Rationale:** One sentence why this voice fits the context.

**[Approve]** **[Edit]** **[Delete+Consult]**
```

## Iteration Rules

- **If approved:** Document what worked in VOICE.md for future reference
- **If edited:** Note which constraints were wrong, adjust for next time
- **If deleted:** Pause and consult before continuing — voice mismatch is serious

## Anti-Patterns

**Don't:**
- Try to sound "professional" (boring and forgettable)
- Strip all personality to avoid risk (creates generic sludge)
- Over-craft the first draft (iteration is cheaper than perfectionism)
- Ignore context files (voice without values is hollow)

**Do:**
- Start with the human's actual communication patterns
- Admit when something took multiple tries
- Use specific details over general claims
- Stop when constraints are met (don't keep polishing)

## Related Skills

- `humanizer` — Use after drafting to strip AI patterns
- `session-wrap-up` — For capturing voice learnings to memory

## Version

1.0.0