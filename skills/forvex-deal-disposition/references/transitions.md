# Deal Disposition Transitions

The lifecycle (forward, no override needed):

```
LEAD → OFFER → UNDER_CONTRACT → INVENTORY → REHAB → LISTED → PENDING → SOLD
```

Plus two exits from any non-terminal status (no override needed):

- **FOLLOW_UP** — paused. Same deal. Required follow-up `reason_code`. Does **not** record `DEAD`.
- **LOST** — terminal. Required lost `reason_code`. Then `forvex_record_deal_outcome` with `outcome_kind: DEAD`.

## When `override_reason` is REQUIRED

- **Skip-forward**: jumping stages (e.g. `LEAD → UNDER_CONTRACT` skips OFFER). Common in practice — wholesale assignments, direct-to-contract on existing LEADs.
- **Backwards**: e.g. `UNDER_CONTRACT → LEAD` if contract fell through and they want to keep pursuing.
- **Re-open terminal**: bringing a `SOLD` or `LOST` deal back to life.
- **FOLLOW_UP to a stage other than `reentry_stage`**: `forvex_get_deal` returns `reentry_stage` when status is FOLLOW_UP. That target needs no override. Any other sequential target needs `override_reason`.

Echo the override reason explicitly in confirmation. Examples:
- `buyer_under_contract` — skipped OFFER because the deal came together off-market
- `contract_terminated` — back to LEAD after the seller backed out
- `lead_revived` — re-opening a LOST deal because the seller called back

`FOLLOW_UP` is **not** terminal. "Bring them back" uses `reentry_stage` (furthest sequential stage; a cancelled `UNDER_CONTRACT` floors to `OFFER`).

## Closed reason lists

### LOST — we will not work this again

`take_me_off_list` · `inaccurate_submission` · `out_of_area` · `sold_to_another_buyer` · `property_not_a_fit` · `pass_on_margin` · `pass_on_bandwidth`

### FOLLOW_UP — paused, same deal

`unable_to_contact` · `price_gap_wont` · `price_gap_cant` · `listed_with_agent` · `under_contract_elsewhere` · `timing_not_ready` · `title_or_legal` · `contract_cancelled_by_seller`

The server rejects any other code on those exits. Do not invent.

## When `reason_code` is REQUIRED

- Moving to `FOLLOW_UP` or `LOST` (closed lists above).
- Same-status updates (e.g. user says "still on LEAD but flag follow-up scheduled"):
  - `counter_pending`
  - `follow_up_scheduled`
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
| "Can't reach them" / "never answered" | → FOLLOW_UP `unable_to_contact` | Largest follow-up population |
| "Check back in the spring" / "not ready yet" | → FOLLOW_UP `timing_not_ready` | Optional `follow_up_at` if they named a date |
| "Price is the problem — they won't come down" | → FOLLOW_UP `price_gap_wont` | |
| "They can't take less" | → FOLLOW_UP `price_gap_cant` | |
| "Listed with an agent" | → FOLLOW_UP `listed_with_agent` | |
| "Under contract with someone else" | → FOLLOW_UP `under_contract_elsewhere` | Not sold yet |
| "Seller cancelled, keep the file" | → FOLLOW_UP `contract_cancelled_by_seller` | Re-entry floors to OFFER |
| "Title / legal mess, not dead" | → FOLLOW_UP `title_or_legal` | |
| "Bring them back" / "seller called" (from FOLLOW_UP) | → `reentry_stage` from `forvex_get_deal` | No override |
| "Seller backed out" (done for good) | → LOST `property_not_a_fit` or `sold_to_another_buyer` | Ask which |
| "Sold to someone else" / "deed recorded" | → LOST `sold_to_another_buyer` | Then record `DEAD` |
| "We closed" | → INVENTORY (if we own it) or SOLD (if we sold it) | Distinguish carefully |
| "Listed it" | → LISTED | After REHAB, no override |
| "Got an offer accepted on our listing" | → PENDING | From LISTED, no override |
| "We walked away" / "we passed on margin" | → LOST `pass_on_margin` or `pass_on_bandwidth` | Operator pass is LOST, not FOLLOW_UP |
| "Killed the deal" / "take it off the board" | → LOST | Pick the matching lost reason |
| "Not a fit, archiving" | → LOST `property_not_a_fit` | |
| "Take me off the list" / junk lead | → LOST `take_me_off_list` / `inaccurate_submission` / `out_of_area` | |

"Walked away" with no Follow Up / Lost choice stays an **activity log**.

## Follow-up reminders

`follow_up_at` (ISO timestamp) is optional on FOLLOW_UP. Pair it when the user names a date. If the user says "remind me to check back Tuesday," resolve Tuesday to absolute date in their timezone before passing.

## Notes field

Free-form, captured on the transition. Use it to record:
- Price (if it's a contract)
- Reason in the seller's words
- Who took the action

Don't recap math or analyze — same rule as activity log. Verbatim where possible.
