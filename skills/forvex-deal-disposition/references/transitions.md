# Deal Disposition Transitions

The lifecycle (forward, no override needed):

```
LEAD → OFFER → UNDER_CONTRACT → INVENTORY → REHAB → LISTED → PENDING → SOLD
```

Plus terminal `LOST` (allowed from any non-terminal status, no override needed).

## When `override_reason` is REQUIRED

- **Skip-forward**: jumping stages (e.g. `LEAD → UNDER_CONTRACT` skips OFFER). Common in practice — wholesale assignments, direct-to-contract on existing LEADs.
- **Backwards**: e.g. `UNDER_CONTRACT → LEAD` if contract fell through and they want to keep pursuing.
- **Re-open terminal**: bringing a `SOLD` or `LOST` deal back to life.

Echo the override reason explicitly in confirmation. Examples:
- `buyer_under_contract` — skipped OFFER because the deal came together off-market
- `contract_terminated` — back to LEAD after the seller backed out
- `lead_revived` — re-opening a LOST deal because the seller called back

## When `reason_code` is REQUIRED

Same-status updates (e.g. user says "still on LEAD but flag follow-up scheduled") require a `reason_code`:
- `counter_pending`
- `follow_up_scheduled`
- `seller_backed_out` (often paired with going to LOST)
- `awaiting_inspection`
- `price_renegotiation`

## Same-status vs activity log

If the user is just adding color to a deal without a status change, that's an **activity log**, not a disposition write. Use `forvex_log_activity` instead. Disposition is for lifecycle moves or for marking same-status state flags that need to surface in pipeline filters.

## Common phrases → moves

| User says | Likely move | Notes |
|---|---|---|
| "We got it under contract" | → UNDER_CONTRACT | Usually skips OFFER, needs override |
| "Made an offer" | → OFFER | Forward, no override |
| "They accepted" | → UNDER_CONTRACT | Forward from OFFER, no override |
| "Seller backed out" | UNDER_CONTRACT → LEAD or LOST | Backwards = override; LOST = clean |
| "We closed" | → INVENTORY (if we own it) or SOLD (if we sold it) | Distinguish carefully |
| "Listed it" | → LISTED | After REHAB, no override |
| "Got an offer accepted on our listing" | → PENDING | From LISTED, no override |
| "We walked away" | → LOST | Override only if terminal-reopen |
| "Killed the deal" | → LOST | |
| "Not a fit, archiving" | → LOST | |

## Follow-up reminders

`follow_up_at` (ISO timestamp) is optional. Pair with same-status moves like `follow_up_scheduled`. If the user says "remind me to check back Tuesday," resolve Tuesday to absolute date in their timezone before passing.

## Notes field

Free-form, captured on the transition. Use it to record:
- Price (if it's a contract)
- Reason in the seller's words
- Who took the action

Don't recap math or analyze — same rule as activity log. Verbatim where possible.
