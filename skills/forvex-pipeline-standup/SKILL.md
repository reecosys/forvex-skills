---
name: forvex-pipeline-standup
description: Read-only morning briefing on the forVEX deal pipeline — what's stale, what's hot, where the user is stuck. Use when the franchisee asks "what's on my plate", "morning briefing", "what's hot today", "where am I stuck", "any stale deals", "pipeline standup", "what needs attention", "show me the pipeline", or wants a triage view before they start the day. Does NOT write anything — for follow-up actions, hands off to forvex-activity-log or forvex-deal-disposition.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# forVEX Pipeline Standup

You give the franchisee a fast triage view of their active pipeline. Read-only. The goal is one screen they can scan in 30 seconds and decide what to touch first.

## When to invoke

- "Morning briefing"
- "What's on my plate today"
- "Any stale deals?"
- "Where am I stuck?"
- "Pipeline standup"
- "What needs attention"
- "Show me the active deals" / "Show me what's hot"

**Not for** writes. If the user wants to act on what you surface, hand off:
- Note / touch → `forvex-activity-log`
- Status move → `forvex-deal-disposition`

## Canonical authority

| Concern | Tool |
|---|---|
| Active pipeline list | `forvex_list_deals` (paginated) |
| Last activity / transitions per deal | `forvex_get_deal_history` |
| Resolve specific deal if user drills in | `forvex_resolve_property` (see `references/platform/resolve-context.md`) |

If MCP is offline, announce and stop.

## Workflow

### 1. Fetch the pipeline

Call `forvex_list_deals({ limit: 100 })`. If `has_more`, paginate up to **200 active deals** total. Stop there — bigger pipelines need scoped filtering, not a full dump.

Normalize statuses to uppercase (`new` → `LEAD`, etc. — see `references/platform/resolve-context.md`).

Drop `SOLD` and `LOST` from standup output unless the user asked for terminal deals explicitly.

### 2. Score staleness

For each active deal, compute "days stale" using rules in `references/staleness.md`. Call `forvex_get_deal_history` for any deal that crosses the staleness threshold (cap at 25 history calls per standup) to pull the last activity excerpt.

### 3. Format the briefing

Group stale deals by status. Within each group, sort by staleness descending. One line per deal:

```
{address} — {STATUS}, {N} days stale — last: {one-line excerpt}
```

Lead the briefing with a **one-sentence headline**:

> *"4 stale: 2 LEADs, 1 OFFER waiting, 1 UNDER_CONTRACT past expected close. {N} active deals total."*

Then the grouped list. Then a **suggested-action line** per deal (from the staleness reference's status-keyed prompts).

End with a single offer:

> *"Want me to log a touch or move status on any of these?"*

Do not auto-call disposition or activity-log. Wait for the user.

### 4. Drill-in requests

If the user picks one ("tell me more about Stevenson" / "what's the history on Maple"), call `forvex_get_deal_history` for that deal and present the chronological events. Still read-only. Offer to hand off to `forvex-activity-log` or `forvex-deal-disposition` for any action.

If the user asks "what's a fair offer on this?" → hand to `forvex-underwriting`. Standup does not analyze price.

### 5. Filtered standup

If the user pre-scopes ("just my LEADs", "anything in Louisville", "REHAB status only"), apply the filter before fetching/listing:
- Status filter → `forvex_list_deals({ status: "LEAD" })` (pass-through)
- Geography filter → no server-side filter; fetch then filter client-side on `address`
- Owner filter → workspace is already user-scoped

## Common requests this skill handles

| User says | Behavior |
|---|---|
| "Morning briefing" | Default standup, all active statuses, stale-first |
| "What's hot" | Lead with most recently *active* deals (newest history events) |
| "What's stuck" | Same as stale — surface oldest-untouched first |
| "Just LEADs" | Filter to LEAD status only |
| "Show me REHAB projects" | Filter to REHAB; pair with rehab project context if asked |
| "What about Stevenson?" | Drill-in on that deal |

## Guardrails

- **Read-only.** No writes from this skill. Ever.
- **No editorializing.** Don't comment on whether a price is good, whether a lead matches the buy-box, or whether the user should act. Just surface state.
- **No invented summaries.** Last-activity excerpts come from `get_deal_history`, not paraphrase. If a deal has no history, say "no activity logged yet."
- **Cap calls.** Max 200 deals listed, max 25 history calls per standup. If more is needed, ask the user to narrow scope.
- **Status normalization.** Always uppercase in output.
- **MCP offline = stop.**

## References

- `references/platform/resolve-context.md` — address → deal resolution (shared, used on drill-in)
- `references/staleness.md` — staleness thresholds, output shape, action prompts per status

## Related skills

- **forvex-activity-log** — when the user picks a stale deal and wants to log a touch
- **forvex-deal-disposition** — when the user picks a stale deal and wants to move status
- **forvex-underwriting** — for "should I take this offer?" questions on a specific deal
- **readvise-capture** — if the user wants to capture personal action items from the standup
