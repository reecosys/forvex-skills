# CFO lane — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

Writes: **`readvise_upsert_rental_debt`** (Holdings capital map) and **`forvex_emit_event`**
(review ledger). Reads below cross-check the deal spine against books in Drive / QuickBooks,
except the rental capital map which is the collateral source of truth.

## readvise_list_rental_debt

**Read.** Every Stock Yards facility in the workspace: lender, loan number, rate, terms,
dates, latest payoff snapshot, and pledged properties (`allocation_pct` 0–1 or null =
equal / value share). Filter with `loan_number` or `property_id`. Double-pledged rentals
return on both facilities.

**Not** occupancy, PM fees, or QuickBooks. **Not** the Track flip-runway planner.

## readvise_resolve_property

**Read.** Address → `readvise_properties.id` before attaching collateral.

## readvise_upsert_rental_debt

**Write.** Match by `debt_account_id` or `loan_number`; otherwise insert. Passing
`collateral` **replaces** the pledged set for that note. `snapshot` upserts on
`workspace_id + debt_account_id + as_of_date`. Echo and confirm before calling; verify
with `readvise_list_rental_debt`.

**Output:** `{ mode, debt_account_id, lender, loan_number, interest_rate, terms, start_date, maturity_date, collateral_replaced, collateral_count, snapshot_written }`

## forvex_list_deal_outcomes

**Read.** SOLD and LOST deals with closing outcome if one exists. Archived included by
default. Use `missing_only` to find closings with no `SOLD`/`RENTED`/`WHOLESALED`/`DEAD` row
— flag those as questions for the operator, do not write the outcome from this lane.

## forvex_list_deals

**Read.** Pipeline slice for capital tied up. Prefer `status` `INVENTORY`, `REHAB`,
`PENDING`. Paginated (default 25).

## forvex_get_deal

**Read.** Saved analysis snapshot. Use when a books line needs a job to attach to. Quote
fields; do not recompute MAO/ARV.

## forvex_get_deal_history

**Read.** Chronological analyses, lifecycle, and notes for one `deal_id`.

## forvex_emit_event

**Write.** `lane` is always `cfo`. Default `entity_type: workspace` with
`source_uri: "routine://cfo/<verb>/<YYYY-Www>"`.

Deal-scoped review: `entity_type: "deal"` and a canonical `deal_id` from a read above.
Never pass a raw address as the join key.

**Output:** `{ event_id, idempotency_key, status, deduped, entity_type, property_id, deal_id }`
