# COO / PM lane — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

Writes for this lane: **`forvex_emit_event`**, **`readvise_upsert_property_capex`**,
**`readvise_upsert_rental_ops`**. Never write rental debt or underwrite.

## Flips

### forvex_list_deals

**Read.** Pipeline slice. Prefer `status` `INVENTORY`, `REHAB`, `PENDING`,
`LISTED`. Paginated (default 25). This is the flip book — not the 21 rentals.

### forvex_get_deal

**Read.** Saved analysis snapshot. Quote fields; do not recompute MAO/ARV.

### forvex_get_deal_history

**Read.** Chronological analyses, lifecycle, and notes for one `deal_id`.

### forvex_get_estimate

**Read.** Rehab estimate / scope on a named flip. Do not call
`forvex_save_draft_estimate` or `forvex_update_estimate`.

### forvex_get_property

**Read.** Parcel facts when the deal row is thin, or to resolve an address
before a property-scoped emit.

## Rentals

### readvise_list_rental_debt

**Read.** Holdings loan ↔ property map. Use to see which note a door pledges
and whether it sits in a blanket. Payoff is not rent. Writes belong to
`cfo-lane` (`readvise_upsert_rental_debt`).

### readvise_list_rental_ops

**Read.** Monthly statement snapshots (`rental_ops_snapshots`): rent, PM fee,
taxes, insurance, mx holdback, mortgage, other. Filter by `property_id`,
`as_of_month`, or recent `months`.

### readvise_upsert_rental_ops

**Write.** Log one statement month for one door. Unique on
`workspace + property_id + as_of_month` (first of month). Resolve address with
`readvise_resolve_property` first. Echo; confirm; re-read.

### readvise_list_property_capex

**Read.** CapEx watch (`property_capex_items`): system, property, rough timing,
cost range, status. Planning estimates only — not Track `capital_pool_*`.

### readvise_upsert_property_capex

**Write.** "Add to CapEx." Match by `capex_id` or `property_id + system`.
Label dollar ranges as planning estimates. Echo; confirm; re-read.

### readvise_resolve_property

**Read.** Address → `readvise_properties.id` before CapEx/ops write or a rental
follow-up emit.

## forvex_emit_event

**Write.** `lane` is always `pm`. Weekly rollup: `entity_type: workspace` with
`source_uri: "routine://pm/<verb>/<YYYY-Www>"`.

Flip follow-up: `entity_type: "deal"` and a canonical `deal_id` from a read
above. Rental follow-up: `entity_type: "property"` and `property_id` or
`address`. Never pass a raw address as a deal join key.

**Output:** `{ event_id, idempotency_key, status, deduped, entity_type, property_id, deal_id }`
