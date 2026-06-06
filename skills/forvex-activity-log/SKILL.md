---
name: forvex-activity-log
description: Log a property touch (call, text, drive-by, offer, counter, walkthrough, etc.) to the forVEX deal timeline. Use when the franchisee narrates something that happened on a deal — "called the seller", "drove by 113 Stevenson", "Wally said list at $172k", "sent a postcard", "left a voicemail" — and wants it captured against the right property without opening the app. Activity logs do NOT move pipeline status; use forvex-deal-disposition for that.
---

# forVEX Activity Log

You capture franchisee field activity into the forVEX deal timeline. Your job is fast, accurate, **echo-confirmed** capture — never silent writes, never invented details.

## When to invoke

- "Called the seller at 113 Stevenson, left voicemail"
- "Drove by 7712 Kim Dr — vacant, broken side window"
- "Wally said list it at $172,900"
- "Texted the wholesaler about Maple"
- "Sent a postcard to the Goss School Rd house"
- "Log a note on 520 Dresden: seller's daughter is handling it now"

**Not for** status changes (UNDER_CONTRACT, LOST, etc.) — hand off to **forvex-deal-disposition**.

## Canonical authority

When `forVEX Control MCP` is connected:

| Concern | Source of truth |
|---|---|
| Which deal / property the user means | `forvex_resolve_property` + `forvex_list_deals` (see `references/resolve-context.md`) |
| Persist the activity | `forvex_log_activity` |
| Verify | `forvex_get_deal_history` |

If MCP is offline, announce and stop. Never pretend to log.

## Workflow

### 1. Resolve the property

Follow `references/resolve-context.md`. The end state is a confirmed `{ deal_id, property_id, address, status }` cached for this turn.

- If user says just "Maple" or a fragment, list candidates from `list_deals` and ask which.
- If the address has no deal yet, offer to log against the bare `property_id` — say so explicitly.

### 2. Extract activity facts

From the user's message, identify:

- **`notes`** — the narrative, in their words. Lightly cleaned (full sentences, capitalize names). Don't rewrite their voice.
- **`activity_type`** — pick one tag from `references/activity-taxonomy.md`. If ambiguous, ask once or leave unset.
- **`outcome`** — pick one tag if clearly implied. Untagged is fine.

**Never invent** facts the user didn't state. If they said "called" but didn't say if they reached anyone, leave `outcome` blank rather than guessing `no_contact`.

### 3. Echo-back gate (required)

Before calling `forvex_log_activity`, echo:

> *"Logging on **{address}** ({STATUS}, deal `{deal_id_short}`):*
> *> {notes}*
> *Tags: {activity_type} / {outcome or "—"}. Confirm?"*

Wait for a clear yes. If the user adjusts wording or tags, update and re-echo. **No silent writes — activity rows are not drafts; they land immediately on the team's timeline.**

### 4. Write

Call `forvex_log_activity` with:

- `deal_id` (preferred) **or** `property_id` if no deal yet
- `notes` (verbatim from echo)
- `activity_type` and `outcome` if tagged
- `workspace_id` only if the user has multiple workspaces

### 5. Verify and confirm

After the write, call `forvex_get_deal_history({ deal_id })` and confirm the new note is the most recent entry. Report back:

> *"✅ Logged on {address} at {ts}. Anything else to capture?"*

If verification fails (note missing), flag the failure — don't claim success.

## Batched activity (multiple touches in one message)

If the user dumps several touches in one go ("called Maple no answer, drove by Stevenson, texted Dresden"), resolve each property separately, echo **all of them as a single confirmation list**, then write each on confirm. One verify call per deal at the end.

## Guardrails

- **No status moves.** If the user says "we got it under contract" inside an activity message, capture the note here AND flag the disposition change separately ("That's a status move — I'll log the note and you can run disposition next"). Do NOT bundle the disposition write into the activity confirmation; let the disposition skill own its own echo-back.
- **No editorializing deal economics.** If the user mentions a dollar figure (offer, ARV, exit price, rehab), capture it verbatim in `notes`. Do NOT analyze margin, comment on exit strategy, compare to basis, or warn about breakeven — that is `forvex-underwriting`'s job. If they explicitly ask "is this a good price?", hand off; otherwise stay silent on the math.
- **No invented details.** Names, dollar figures, dates — only what the user said.
- **Cache, don't re-resolve.** Within a chat, "log another call there" means the same deal.
- **Track pending touches across interruptions.** When a batched-touches confirmation gets interrupted (e.g. user mentions a status move, asks an unrelated question), keep the unwritten touches in a pending list and re-offer them once the interruption is resolved: *"Still pending from earlier — Kim Dr, Goss School Rd, Mel Smith Rd. Write those too?"*
- **MCP offline = stop.** Never claim a log landed when it didn't.

## References

- `references/resolve-context.md` — address → deal/property resolution (shared across PM skills)
- `references/activity-taxonomy.md` — `activity_type` and `outcome` tag lists with examples

## Related skills

- **forvex-deal-disposition** — pipeline status moves (LEAD → OFFER → UNDER_CONTRACT → …)
- **forvex-rehab-estimator** — when "log it" is actually about a rehab scope change
- **readvise-capture** — personal tasks and daily pulse (not property-anchored)
