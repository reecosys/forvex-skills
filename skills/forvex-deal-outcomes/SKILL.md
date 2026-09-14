---
name: forvex-deal-outcomes
description: Find missing deal-close actuals and write them to core.deal_outcomes. Use when the franchisee says "record outcomes", "backfill sold actuals", "what closed without numbers", "update last sale on the lost deals", "weekly outcome review", or wants learning calibration to see evidence. Does NOT move pipeline status — use forvex-deal-disposition for that.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# forVEX Deal Outcomes

You keep `core.deal_outcomes` current so the learning-calibration cron has
ground truth. Disposition step 5b writes one deal at close. This skill is the
**missing / refresh loop** — weekly or on demand.

**Do not record an outcome on `FOLLOW_UP`.** That deal is paused, not closed.

## When to invoke

- "Which sold deals still need actuals?"
- "Record outcomes" / "weekly outcome review"
- "Update last-sale on the lost deals"
- After a post-mortem, once the user confirms the numbers

**Not for** moving status — hand off to `forvex-deal-disposition`.

## Canonical authority

| Concern | Tool |
|---|---|
| Missing / existing closes | `forvex_list_deal_outcomes` |
| Parcel last-sale | `forvex_get_property` → `parcel.last_sale` |
| Write new actuals | `forvex_record_deal_outcome` |
| Refresh actuals | `forvex_update_deal_outcome` |
| Books on a live deal | `forvex_get_deal` |

If MCP is offline, announce and stop. Never claim an outcome landed when it didn't.

## Workflow

### 1. List candidates

Call `forvex_list_deal_outcomes` with:

- `missing_only: true` for the first pass
- `include_archived: true` (default)
- `status: "SOLD"` or `"LOST"` when the user scoped one side; otherwise both

Paginate with `offset` until `has_more` is false.

### 2. Echo actuals

**SOLD (pipeline status)** — echo books, do not invent:

| Annotated `exit_strategy` | `outcome_kind` |
|---|---|
| Wholesale | `WHOLESALED` |
| Retail / Wholetail / Other / blank | `SOLD` |
| BRRRR | `RENTED` |

Use `sale_price`, `purchase_price`, `rehab_actual` only when > 0, `sale_date`,
and the stored exit label as `actual_exit_strategy`. Never substitute
`rehab_estimate` as actual.

**LOST** — call `forvex_get_property` and echo `parcel.last_sale` (date, price,
`arms_length`). Propose `DEAD` only when:

1. `last_sale.date` is **after** the LOST event (or `archived_at` if no event)
2. `arms_length` is not `false`
3. The lost reason is not walked / price-gap (`price_gap`, `we_walked`,
   `too_far_apart`, `seller_price_expectation`, …) unless the user confirms

Otherwise report it and skip. Do not auto-write walked / price-gap.

### 3. Echo-back gate (required)

Same gate as disposition. One deal at a time, or a short batch the user can
reject as a set:

> *"Write **{address}** as {outcome_kind}: sale {price or —}, rehab {rehab or —},
> closed {date or —}. Confirm?"*

Wait for a clear yes. Re-echo if they change a number. **No silent writes.**

### 4. Write

- New row → `forvex_record_deal_outcome` with `source: "forvex-deal-outcomes"`
  and a fresh `idempotency_key`
- Existing row, new actuals → `forvex_update_deal_outcome`
- `analysis_id` defaults to the deal's current snapshot — pass it only when the
  user names a different one

### 5. After a post-mortem

If `forvex-postmortem` just confirmed projected-vs-actual numbers, persist those
actuals here (do not leave them only in chat). Then stop — do not re-run the
post-mortem math.

## Guardrails

- **No invented numbers.** Omit blank fields.
- **Annotated exit wins.** Never overwrite Wholesale as `SOLD`.
- **FOLLOW_UP is not a close.** The list tool never returns it.
- **MCP offline = stop.**

## Related skills

- **forvex-deal-disposition** — status move + live close (step 5b)
- **forvex-postmortem** — standalone math; this skill writes the confirmed actuals
