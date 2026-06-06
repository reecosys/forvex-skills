---
name: forvex-deal-disposition
description: Move a forVEX deal through the pipeline lifecycle (LEAD → OFFER → UNDER_CONTRACT → INVENTORY → REHAB → LISTED → PENDING → SOLD, or LOST). Use when the franchisee says "we got it under contract", "made an offer on", "they accepted", "seller backed out", "killed the deal", "we closed on", "listed Maple today", "moved to inventory", or otherwise signals a pipeline status change. This skill ONLY moves status; for notes/touches that don't change status use forvex-activity-log.
---

# forVEX Deal Disposition

You move deals through the pipeline lifecycle on the user's behalf. Disposition writes are **not drafts** — they land immediately and surface to the whole team. Every write requires explicit echo-back confirmation.

## When to invoke

- "We got 113 Stevenson under contract at $130k"
- "Made an offer on Kim Dr — $95k"
- "Seller backed out of Dresden"
- "Listed Maple today"
- "Moved Cool Brook to inventory"
- "Killed the Goss School Rd deal — too much foundation"
- "Bring the Mel Smith lead back, the seller called"

**Not for** notes, touches, or color commentary that doesn't change status — use `forvex-activity-log`.

## Canonical authority

| Concern | Tool |
|---|---|
| Resolve property → deal_id | `forvex_resolve_property` + `forvex_list_deals` (see `references/resolve-context.md`) |
| Read current state | `forvex_get_deal` |
| Move status | `forvex_update_deal_disposition` |
| Verify | `forvex_get_deal_history` |

If MCP is offline, announce and stop. Never claim a status moved when it didn't.

## Workflow

### 1. Resolve the property

Follow `references/resolve-context.md`. Confirm `{ deal_id, property_id, address, current_status }`. Cache for the chat.

If the user names a deal that's already in the target status (e.g. "move Stevenson to LEAD" and it's already LEAD), that's a **same-status update** — needs `reason_code`, not a status move. See `references/transitions.md`.

### 2. Identify the transition

From the user's words, determine:

- `new_status` — one of the 9 enum values (uppercase)
- Whether the move is **forward sequential** (no override), **skip-forward / backward / terminal-reopen** (needs `override_reason`), or **same-status** (needs `reason_code`)
- Optional `notes` — captured verbatim from the user (price, seller words, who acted)
- Optional `follow_up_at` — resolve relative dates to absolute ISO

See `references/transitions.md` for phrase → move mapping and the override/reason rules.

### 3. Echo-back gate (required)

Before calling `forvex_update_deal_disposition`, echo every field:

> *"Moving **{address}** ({CURRENT_STATUS} → {NEW_STATUS}, deal `{deal_id_short}`).*
> *Notes: {notes or "—"}*
> *Override reason: {override_reason or "—"}*
> *Reason code: {reason_code or "—"}*
> *Follow-up: {follow_up_at or "—"}*
> *Confirm?"*

Wait for a clear yes. If the user adjusts anything, re-echo. **No silent writes.**

If the move requires `override_reason` and the user hasn't given one, propose one from the transitions guide and ask. Don't proceed without it — the server will reject.

### 4. Write

Call `forvex_update_deal_disposition` with:

- `deal_id`
- `new_status`
- `notes` if provided
- `override_reason` for skip/backwards/terminal-reopen moves
- `reason_code` for same-status updates
- `follow_up_at` if provided
- `source: "forvex-deal-disposition"`
- `workspace_id` only when multiple workspaces

### 5. Verify and confirm

Call `forvex_get_deal_history({ deal_id })`. The most recent entry should be a `lifecycle` transition matching the move. Report:

> *"✅ {address} is now {NEW_STATUS}. (Was {CURRENT_STATUS} at {ts}.)*
> *Anything else?"*

If verification fails or the new status doesn't match, flag the failure — don't claim success.

### 6. Suggest natural next steps (lightly)

After certain transitions, gently nudge the next-most-likely workflow without auto-invoking:

- → `UNDER_CONTRACT` → "Want to open or update the rehab estimate?" (hand to `forvex-rehab-estimator`)
- → `INVENTORY` → "Ready to start the project? I can open it in REbuild."
- → `SOLD` → "Want to run a post-mortem?" (hand to `forvex-postmortem`)
- → `LOST` → "Capture the reason for the buy-box / lead-source learning?"

These are **offers, not auto-runs**. One line each, then stop.

## Bundled activity + status changes

If the user packs both a note and a status move into one message ("called the seller, got Stevenson under contract at $130k"), split them:

- The note part → suggest `forvex-activity-log`
- The status part → handle here

Do not bundle both writes under one confirmation — let each skill own its own echo-back so the user can independently approve.

## Guardrails

- **Status moves are not drafts.** Land immediately and surface to the team. Echo every field, every time.
- **No invented details.** Don't guess prices, dates, or reasons. If the user said "under contract" without a price, leave `notes` blank — don't make one up.
- **No editorializing deal economics.** Same rule as activity-log: don't comment on margin, comp range, or whether the price is a good idea. If the user explicitly asks, hand to `forvex-underwriting`.
- **Override reasons are required and verifiable.** Use the transitions guide; don't invent codes the server won't accept.
- **No finalize-in-chat for sold deals beyond SOLD status.** Finalized accounting / commission lives in-app.
- **MCP offline = stop.** Never claim a transition landed when it didn't.

## References

- `references/resolve-context.md` — address → deal resolution (shared)
- `references/transitions.md` — lifecycle rules, override/reason mapping, phrase → move table

## Related skills

- **forvex-activity-log** — non-status touches and notes
- **forvex-rehab-estimator** — natural follow-up after `UNDER_CONTRACT`
- **forvex-postmortem** — natural follow-up after `SOLD`
- **forvex-underwriting** — for "is this a good price?" questions
