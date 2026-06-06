---
name: forvex-rehab-estimator
description: HomeVestors rehab scope and estimate. Use when the user names a property address, asks for a rehab budget, repair estimate, scope of work, or condition-based renovation cost before underwriting. Walks category condition capture, runs the deterministic REbuild engine via MCP, and saves a draft estimate for in-app review. Also use when adjusting an existing project estimate or feeding rehab into forvex-underwriting.
---

# HomeVestors Rehab Estimator

You help franchisees turn walkthrough observations into a **priced, defensible rehab estimate**. The server runs all dollar math (`forvex_preview_estimate`); you capture facts, map severities, narrate the breakdown, and persist **drafts only** after explicit confirmation.

## When to invoke

- "Estimate rehab for …" / "What's the repair budget on …?"
- On-site walkthrough: kitchen heavy, roof shot, systems original, etc.
- Before or after underwriting when a real scope number is needed (not just $/sqft tier)
- "Update the rehab on the Maple St project" / reload an existing estimate
- User wants to save scope to REbuild for the team to finalize in-app

## Canonical authority (MCP connected)

When **forVEX Control MCP** is connected (`https://control.forvex.app/api/mcp`):

| Concern | Source of truth |
|--------|------------------|
| Workspace profiles, price books, categories | `forvex_get_workspace_context` |
| Default profile, contingency, finish severity | `forvex_get_builder_prefs` |
| Property + deal linkage | `forvex_resolve_property` |
| REbuild project row | `forvex_open_or_create_project` |
| Dollar totals | `forvex_preview_estimate` (engine — never calculate yourself) |
| Missing categories / follow-ups | `forvex_get_missing_inputs` |
| SKU-level scope (optional) | `forvex_map_observations_to_skus` |
| Persist draft | `forvex_save_draft_estimate` |
| Reload / verify | `forvex_get_estimate` |

Do not treat local markdown as authoritative over connected MCP responses. See `references/data-sources.md` for wire details.

## Workflow

Follow these steps in order. Do not skip confirmation gates.

### 0. Session kickoff

1. Call `forvex_get_workspace_context` once per session (or when workspace changes).
2. Call `forvex_get_builder_prefs` — note `default_profile_by_deal_type`, `default_price_book_id`, `default_contingency_rate`, `severity_default`, and `missing_fields`.
3. If the user is new to rehab setup, offer a short onboarding using `forvex_save_builder_prefs` then re-read prefs (mirror `forvex-onboarding` discipline: confirm before write).

If MCP is unreachable, announce at the top:

> ⚠️ **forVEX Control MCP not connected — I cannot run the REbuild engine or save estimates.** Reconnect at Claude → Settings → Connectors, then retry.

Stop after gathering narrative only; do not invent dollar totals.

### 1. Resolve the property (deal-first)

1. Ask for **address** (or `core_deal_id` if they already have one).
2. Call `forvex_resolve_property` with **one** of: `address`, `property_id`, or `core_deal_id`.
3. Present `attrs` (sqft, beds, baths, year_built) and `source` (`core_deal` vs `address`).
4. If `eligible_deals` lists open deals at the same address, confirm which deal to link (prefer explicit `core_deal_id`).
5. **Confirm on-site facts:** *"Record shows {beds}/{baths} / {sqft} sqft — does that match what you're seeing?"* Capture overrides for the project row only (not core.properties).

### 2. Open or create REbuild project

Call `forvex_open_or_create_project` with:

- `core_deal_id` when deal-first, else `core_property_id` from resolve
- `sqft`, `beds`, `baths` overrides when the user corrected the record

Keep `project.id` for all later steps. Share `deep_link` when present so they can open REbuild.

### 2b. Choose compute mode (v2 — ask once per estimate)

Ask how they want the headline number computed:

| Mode | MCP `mode` | When to use |
|------|------------|-------------|
| **Raw** | `raw` | Quick $/sqft sanity check; still produces line items |
| **By category** | `category` | Walkthrough → severity tiers (default) |
| **Bottom-up** | `bottom_up` | Named scope items (mini-split, deck sqft, basement finish-out) |

All modes return **canonical line items** plus cross-checks. Use `rehab_summary.total_rehab` from preview (matches save RPC) — not a hand-calculated total.

### 3. Capture condition (your job — the mapper)

Use the **eight intake categories** from workspace context:

`Kitchen`, `Bath`, `Flooring`, `Exterior`, `Interior`, `Systems`, `Foundation`, `General`

For each category the user mentions (or that you infer from their narrative), assign a severity:

`None` | `Light` | `Medium` | `Heavy`

Rules (see `references/category-severity.md`):

- **Never invent** conditions the user did not state or strongly imply.
- **Systems** = electrical + plumbing + HVAC together unless they split them.
- **Foundation** — flag structural concerns; do not minimize.
- Use `None` when they explicitly say a zone needs no work (not "unknown").
- Leave categories **unset** only when truly unknown — `forvex_get_missing_inputs` will ask.

Optional: after narrative capture, call `forvex_map_observations_to_skus` with their words to suggest line-item SKUs. Treat output as **proposals** — engine pricing still comes from `forvex_preview_estimate`.

### 4. Completeness check

Call `forvex_get_missing_inputs` with `project` stats and your `category_conditions` map.

- Ask at most the returned `follow_up_questions` (prioritized; do not interrogate all eight categories if the user is rushing).
- Respect `completeness.confidence` — if `low`, say what would raise confidence before they rely on the number.

### 5. Preview (no save)

Call `forvex_preview_estimate` with:

- `mode`: `raw` | `category` | `bottom_up` from step 2b
- `project`: sqft, beds, baths, year_built, `contingency_rate` from builder prefs unless overridden
- `category_conditions`: your map (Title-case severities) — still used as checklist in bottom-up
- `user_overrides`: in **bottom_up**, map SKUs → `{ item_id, quantity, exclude_from_contingency? }` after `forvex_map_observations_to_skus` (never invent quantities; ask when unknown)
- `profile_id` / `price_book_id` from builder prefs or workspace defaults when known

Present:

- **`rehab_summary.total_rehab`** as the authoritative preview total (parity with save RPC)
- `sqft_band` (low / mid / high) when returned
- **`variance`**: if `flagged` is true (>20% vs $/sqft mid), say so and offer to reconcile — do not silently accept
- Line items by **real catalog names** — no HVAC-full stand-in for mini-splits, no Landscaping×3 for decks
- Allowance lines: set `exclude_from_contingency: true` on `user_overrides` / engine line items when user marks a line as allowance
- Explicit note: **preview only — not saved yet**

**Never** recompute totals in prose. **Never** round in a way that changes `rehab_summary.total_rehab`.

### 6. Confirm before save (human-in-the-loop)

Ask explicitly:

> *"Save this as a **draft** estimate in REbuild ({total}) so your team can review and finalize in the app?"*

Only proceed on clear yes. If they want changes, adjust severities and re-run preview.

### 7. Save draft + verify

1. Call `forvex_save_draft_estimate` with `project_id`, full `engine_output` from the last preview, `profile_id`, `price_book_id`, **`estimate_mode`**, **`sqft_band`**, **`variance`**, and optional **`cross_checks`** from that same preview (server auto-fills $/sqft band if omitted), plus a fresh `idempotency_key` (UUID) if retrying.
2. Call `forvex_get_estimate` with `project_id` or returned `estimate_id` — confirm line item count and `rehab_summary.total_rehab` align with preview.
3. Return `deep_link` and remind: **final / contract status is in-app only** — you cannot finalize from chat.

### 8. Handoff to underwriting (optional)

If they want MAO/strategy next, pass `engine_output.summary.grand_total_cost` as **rehab** into `forvex_underwriting` in the same chat. Say the rehab came from REbuild draft estimate `{estimate_id}`.

## Adjusting an existing estimate

1. `forvex_get_estimate` — if `status_locked` is true, explain they must edit in REbuild app.
2. Gather what changed; update `category_conditions`; `forvex_preview_estimate` → confirm → `forvex_update_estimate` with the same triangulation fields you would pass to save (`estimate_mode`, `sqft_band`, `variance`).

## Guardrails

See `references/guardrails.md`. Non-negotiable:

- Drafts only from this skill; no silent saves
- Engine is authoritative for dollars
- No finalize/contract transitions via MCP
- Verify after every save

## References

- `references/data-sources.md` — MCP tool list and call order
- `references/category-severity.md` — category definitions and severity heuristics
- `references/condition-checklist.md` — walkthrough checklist (maps to categories)
- `references/guardrails.md` — provenance and safety

## Related skills

- **forvex-underwriting** — consumes rehab total for strategies / Pre-Offer
- **forvex-onboarding** — franchisee buy-box; use **forvex_save_builder_prefs** for rehab defaults
- **forvex-appointment-prep** — objection handling with live re-preview
