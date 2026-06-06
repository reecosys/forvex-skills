# Data Sources — Rehab Estimator MCP Tools

> Server: `https://control.forvex.app/api/mcp` (OAuth — Claude → Settings → Connectors → forVEX Control)

When MCP is connected, use these tools **before** asking the user for data the server already has.

---

## Call order (happy path)

| Step | Tool | Notes |
|------|------|--------|
| 1 | `forvex_get_workspace_context` | Categories, profiles, price books, library summary, embedded builder prefs |
| 2 | `forvex_get_builder_prefs` | Defaults + `missing_fields` |
| 3 | `forvex_resolve_property` | One of: `address`, `property_id`, `core_deal_id` |
| 4 | `forvex_open_or_create_project` | `core_deal_id` or `core_property_id` + optional sqft/beds/baths |
| 5 | `forvex_get_missing_inputs` | After you draft `category_conditions` |
| 6 | `forvex_preview_estimate` | **Read-only** engine run |
| 7 | `forvex_save_draft_estimate` | After explicit user confirmation |
| 8 | `forvex_get_estimate` | Verify save |

Optional:

- `forvex_map_observations_to_skus` — narrative → catalog SKUs (validated server-side)
- `forvex_update_estimate` — replace line items on draft/derived estimate (blocked if status locked)

Supporting property context (underwriting path): `forvex_get_property` still works for ARV/comps; prefer `forvex_resolve_property` for REbuild linkage.

---

## Tool reference

### `forvex_get_workspace_context`

Returns workspace rehab taxonomy: profile list, price books, per-category library item counts, and `builder_preferences` object.

### `forvex_get_builder_prefs` / `forvex_save_builder_prefs`

Per-user rehab defaults in `rebuild.builder_preferences`:

- `default_profile_by_deal_type` (rental / flip / wholesale)
- `default_price_book_id`, `contingency_rate`, `severity_default`
- `rehab_rates_per_sqft` (light/medium/heavy/gut sanity bands)
- `finish_defaults`, `risk_posture`, `markets`

Save uses shallow merge; confirm with user before `forvex_save_builder_prefs`.

### `forvex_resolve_property`

**Input:** exactly one of `address`, `property_id`, `core_deal_id`.

**Output:** `core_property_id`, optional `core_deal_id`, `attrs`, `source`, `eligible_deals[]`.

Deal-first: matching address against `v_eligible_deals_for_new_project` before pure address upsert.

### `forvex_open_or_create_project`

**Input:** `core_deal_id` OR `core_property_id`; optional `sqft`, `beds`, `baths`.

**Output:** `project` row + `deep_link` (when `REBUILD_APP_URL` configured on server).

RPCs: `rpc_create_project_from_core_deal`, `rpc_create_project_from_core_property`.

### `forvex_get_missing_inputs`

**Input:** optional `project` stats + `category_conditions` map (`None`/`Light`/`Medium`/`Heavy` per category).

**Output:** `missing_categories`, `follow_up_questions`, `completeness` (confidence band).

Pure deterministic — no LLM.

### `forvex_preview_estimate`

**Input:**

```json
{
  "project": { "sqft": 1450, "beds": 3, "baths": 2, "year_built": 1972, "contingency_rate": 0.1 },
  "category_conditions": { "Kitchen": "Heavy", "Systems": "Medium", "Exterior": "Light" },
  "profile_id": "uuid-optional",
  "price_book_id": "uuid-optional"
}
```

**Output:** `contract_version`, `engine_output` (summary + lineItems), resolved profile/price book ids.

Does **not** write to the database.

### `forvex_map_observations_to_skus`

**Input:** `observations` (free text).

**Output:** `items[]` (valid SKUs), `rejected[]`, `degraded` flag.

Uses AI gateway + `validateSkusAgainstCatalog`. Grounding only — preview still drives pricing.

### `forvex_save_draft_estimate`

**Input:** `project_id`, `engine_output` (from last preview), optional `profile_id`, `price_book_id`, `idempotency_key`, `source`.

**Output:** `estimate_id`, `status` (`derived`), `rehab_summary`, `deep_link`, `idempotent_replay`.

RPC: `rpc_save_draft_estimate`.

### `forvex_get_estimate` / `forvex_update_estimate`

Get: `estimate_id` or `project_id` → estimate + line items + `status_locked`.

Update: requires draft-like status; re-saves line items from new `engine_output`.

---

## Preferences precedence

1. `forvex_get_builder_prefs` (connected MCP)
2. Project knowledge markdown (offline fallback only)
3. Defaults stated in `references/category-severity.md`

---

## Failure modes

| Symptom | Action |
|---------|--------|
| Auth error | Re-authorize OAuth connector |
| No library items / profile rules | User must configure REbuild workspace catalog |
| RPC not found | Migrations not applied on Supabase — escalate |
| Preview total = 0 | Check category severities are not all `None` without rules |
| `status_locked` on update | User finalizes in REbuild app |
