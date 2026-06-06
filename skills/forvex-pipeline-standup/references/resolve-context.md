# Resolve Context — Address → Deal/Property

Every PM skill that touches a specific property must first answer: **which `core_deal_id` (or bare `core_property_id`) does the user mean?** This reference is copied into each PM skill so the resolution logic stays identical.

## When you already have an id

If the user supplied a UUID (deal_id or property_id), or you have one cached from earlier in the conversation, skip resolution. Use it directly.

## Standard resolution flow

Call these **in parallel** on the first mention of a property:

1. `forvex_resolve_property({ address })` — normalizes address, returns `core_property_id`, optional `core_deal_id`, and `attrs` (sqft/beds/baths/year_built).
2. `forvex_list_deals({ limit: 100 })` — full active pipeline. Paginate if `has_more` and the property isn't found yet.

Then run the **client-side match** below. Do NOT trust `resolve_property.core_deal_id` alone — in practice it returns `null` even when a matching deal exists, and `resolve_property.eligible_deals` is the workspace LEAD list, not address matches.

## Client-side match algorithm

Given `resolve_property.attrs.address_line1` and `attrs.zip`:

1. **Normalize**: uppercase, strip punctuation, collapse whitespace on both `attrs.address_line1` and each `list_deals.deals[*].address`.
2. **Match priority**:
   - Exact `address_line1 + zip` match → use that `deal_id`.
   - `address_line1` match only (zip missing on one side) → use it but confirm in echo-back.
   - Fuzzy (street number + first street word match) → present as "did you mean…" — never auto-pick.
3. **Result cases**:
   - **1 match** → cache `{ deal_id, property_id, address, status }` in conversation context. Proceed.
   - **0 matches** → property exists in core but no deal. Say so explicitly. Offer to create a deal (or just log the activity against the property via `property_id`).
   - **>1 match** → ask user to disambiguate by status or last-updated.

## Status normalization

The API returns mixed casing: `new`, `LEAD`, `under_contract`, `UNDER_CONTRACT`. Always uppercase for display and branching:

```
new          → LEAD
under_contract → UNDER_CONTRACT
```

The lifecycle enum (authoritative) is:
`LEAD → OFFER → UNDER_CONTRACT → INVENTORY → REHAB → LISTED → PENDING → SOLD`, plus terminal `LOST`.

## Echo-back

Before any write that names a property, echo what you resolved:

> *"Got it — **113 STEVENSON AVE, LOUISVILLE KY 40206** (LEAD, deal `76578a58…`). Logging this activity. Confirm?"*

If the user corrects the address or deal, re-resolve. Never write against an unconfirmed deal_id.

## Caching within a conversation

Once resolved, keep `{ deal_id, property_id, address, status }` in working memory for the rest of the chat. Follow-ups like "log another call there" or "move it to under contract" must reuse the cached id, not re-resolve.

If the user names a different property mid-chat, resolve that one fresh — don't assume continuity.

## When MCP is offline

If `forvex_list_deals` or `forvex_resolve_property` errors, announce:

> ⚠️ **forVEX Control MCP not connected — I can't look up deals or write activity.** Reconnect at Claude → Settings → Connectors.

Do not invent deal_ids. Do not "log" anything locally — the user expects writes to land.
