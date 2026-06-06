# Scope-Delta Patterns

A change order is a **delta** to a saved estimate: a category severity shifts, a bottom-up line item is added/removed, or quantities change. The MCP path is the same as drafting from scratch — re-preview, then update — but framed as "what changed and why."

## Two kinds of deltas

### 1. Category severity shift (most common)

User says: *"Found knob-and-tube, bump Systems to Heavy."*

- Load current estimate via `forvex_get_estimate`.
- Take its `category_conditions` (or reconstruct from `lineItems` if not stored).
- Apply the user's shift.
- Re-preview with `forvex_preview_estimate({ mode: "category", category_conditions, project: {...} })`.
- Echo the **delta**: old total → new total, delta dollars, which line items changed.
- On confirm, `forvex_update_estimate({ estimate_id, engine_output })`.

### 2. Bottom-up line add / remove

User says: *"Add a mini-split for the addition, 12k BTU."*

- Load current estimate.
- Call `forvex_map_observations_to_skus({ text: "mini-split 12k BTU" })` to find the SKU.
- Add the SKU to `user_overrides` with quantity.
- Re-preview in `bottom_up` mode (same `category_conditions` as before).
- Echo delta. On confirm, update.

For removals: drop the SKU from `user_overrides` or set quantity to 0 (engine treats 0 as exclude).

## Loading current state

`forvex_get_estimate` returns the saved engine_output. From it:

- `summary.grand_total_cost` → previous total
- `lineItems[]` → for diffing
- `mode`, `profile_id`, `price_book_id` → preserve on re-preview
- `category_conditions` if stored on the row — else reconstruct from lineItem categories

Always preserve the original `mode`, `profile_id`, and `price_book_id` unless the user explicitly asks to change them. Change-orders should not silently swap pricebooks.

## Lock check

If `forvex_get_estimate.status_locked === true`:

> *"This estimate is locked (finalized in REbuild). I can't update it from chat. Open the project in REbuild to make the change."*

Stop. Do not run a preview. Do not propose workarounds.

## Echo-back shape (delta-focused)

```
Change order on {address} (estimate `{estimate_id_short}`):

  Change: {category} {old_severity} → {new_severity}
       OR Add: {SKU name} × {qty}
       OR Remove: {SKU name}

  Previous total: ${old_total}
  New total:      ${new_total}
  Delta:          {±$X} ({±X.X%})

  Line items affected:
    + {new line} — ${cost}
    - {removed line} — ${cost}
    ~ {changed line} — ${old} → ${new}

  Variance after change: {flagged? "⚠️ flagged" : "ok"} ({pct}%)

Save this update?
```

Wait for explicit yes. Re-echo on any adjustment.

## Allowances

If the user says "make this an allowance" on a line, set `exclude_from_contingency: true` on that `user_overrides` entry. Allowances are excluded from contingency math.

## Why the delta framing matters

A change order should feel like "we changed this much" — not "here's the whole estimate again." Lead with the delta, show the new total, and only expand to full line items if the user asks. The user already approved the baseline; you only need their sign-off on the change.

## What change-order does NOT do

- **No new estimates.** If the user is starting from scratch, hand to `forvex-rehab-estimator`.
- **No status moves.** Estimate status (draft → final → contract → locked) is REbuild-app only. From chat, change orders stay on the same status row.
- **No pricebook swaps unless asked.** Preserve original profile + pricebook by default.
- **No bundled writes.** If the user also wants to log a project update or move pipeline status, those are separate skills with separate echo-backs.
