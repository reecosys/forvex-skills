# MCP Tools — Canonical Reference

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

When the **forVEX Control MCP** is connected, pull data from it before asking the user. Server: `https://control.forvex.app/api/mcp` (OAuth — configure once in Claude → Connectors).

> **Status (MCP 0.3.0 / `TOOL_SCHEMA_VERSION` 0.8.0):** Phase 1 read tools, Phase 4 write tools, and the learning-layer capture tools are **live**. `forvex_emit_event` (0.8.0, additive) accepts `entity_type: workspace` plus lanes `ops`/`net`. `forvex_render_presentation` (0.7.0, additive) renders operator HTML for six modes. Disconnect/reconnect the forVEX Control connector if tool names look stale. Every tool declares `outputSchema`; `forvex_get_comps` / `forvex_get_comp_detail` may include optional top-level `subject` and `search_params`. `forvex_get_property` may include optional `parcel` (decoded last-sale flags, physicals, winning debt). Market flip/rent scores may return `null` while tract resolution works — use MoM/YoY when scores are missing and default `market_risk` to 0.5. Auth failures read: *"Missing or invalid auth context. Re-authorize via /api/oauth/authorize (or refresh your Supabase session) and retry."*

---

## Operating principle

Don't ask the user for anything an MCP tool can provide. Each tool call should happen before prompting the user. If a tool returns nothing usable, fall back gracefully: ask the user or apply a default and flag it.

When MCP is connected, server state is authoritative. `my-buy-box.md` is only an offline/export fallback.

---

## Registered tools

| Tool | Phase | Purpose |
|------|-------|---------|
| `forvex_whoami` | 1 | Confirm auth + workspace (optional sanity check, not mandatory preflight) |
| `forvex_get_property` | 1 | Property fundamentals + ARV from comps. Returns `property_id`. Optional `parcel` (0.6.0). |
| `forvex_get_comps` | 1 | RealIE comps v3 — dual ARV/as-is, signals, pricing_hints (canonical 1mi/18mo cache) |
| `forvex_get_comp_detail` | 1 | Full comps roster via `trace_ref.id` from `forvex_get_comps` |
| `forvex_get_flood_data` | 1 | FEMA flood zone |
| `forvex_get_market_intelligence` | 2 | Sense tract + momentum (scores partial — see below) |
| `forvex_get_rent_estimate` | 1 | Rentometer rent band |
| `forvex_get_buy_box` | 1 | Franchisee prefs (legacy merge until `core.franchisee_prefs` migrates) |
| `forvex_underwrite` | Next | Canonical deterministic underwriting execution with server-resolved buy-box defaults |
| `forvex_save_buy_box` | 2.7 | Persist buy-box (used by `forvex-onboarding`) |
| `forvex_get_deal` | 1 | Single deal snapshot. Now surfaces `current_analysis_id`, `analysis`, `analysis_summary`. |
| `forvex_list_deals` | 1 | Pipeline list. Optional `property_id` filter. |
| `forvex_save_deal` | **4.1 (new)** | Persist an underwriting snapshot to `core.deals` + `core.deal_analyses`. Status never changes on re-analysis. |
| `forvex_update_deal_disposition` | **4.2 (new)** | Move a deal through the canonical lifecycle (`LEAD|OFFER|UNDER_CONTRACT|INVENTORY|REHAB|LISTED|PENDING|SOLD|LOST`). |
| `forvex_log_activity` | **4.3 (new)** | Append a Readvise property note + timeline event. Use for counters, calls, drive-bys, walkaway notes — anything that does not change status. |
| `forvex_get_deal_history` | **4 (new)** | Chronological merge of analyses, lifecycle transitions, and Readvise notes for a deal. |
| `forvex_capture_deal_brief` | **learning** | End-of-session retrospective: narrative brief + triaged corrections → shadow/candidate learned adjustments. |
| `forvex_record_deal_outcome` | **learning** | Ground-truth actuals at deal close (sale price, rehab, DOM) keyed to the analysis snapshot. |
| `forvex_attach_analysis` | 2 | Attach analysis blob to a deal (planning — not used in active skill flows) |
| `forvex_build_wholesale_sheet` | 0.6+ | Buyer-facing wholesale one-pager (`{ data, html }`). Suppresses operator economics. |
| `forvex_render_presentation` | **0.7.0 (new)** | Operator HTML for six modes: dashboard, deck, pdf, internal_sheet, appointment_debrief, rehab_scope. Returns `{ schema_version, mode, data, html }`. HTTP twin: `POST /api/operate/presentation`. |
| `forvex_emit_event` | **0.8.0** | Cross-lane ledger write. `entity_type`: `property` \| `deal` \| `workspace`. Lanes: `cmo` \| `cfo` \| `pm` \| `mkt` \| `ops` \| `net`. |

---

### `forvex_get_property(address | id)`

Wraps Realie via `core.properties` + cache refresh.

**Returns (0.5.0 keys always; `parcel` optional in 0.6.0):**
```json
{
  "property_id": "3bc6012a-6576-43ae-b40b-1b38696b4315",
  "address": "8000 Kenhurst Dr, Louisville KY 40258",
  "lat": 38.1363, "lng": -85.8789,
  "bed": 3, "bath": 2, "sqft": 1230, "year_built": 1997,
  "lot_sqft": 10289,
  "estimated_arv": 225000,
  "arv_confidence": "high",
  "condition_estimate": "moderate",
  "last_sold_price": 148000, "last_sold_date": "2016-04-18",
  "comps_summary": "50 comps within 1mi, $70k–$715k range, median $225k",
  "sale_qualification": "TQ0002",
  "recorded_lien_balance": null,
  "current_lender": "Truist",
  "parcel": {
    "response_shape": "nested",
    "last_sale": {
      "date": "2024-10-21",
      "price": 231830,
      "deed": { "code": "TT0001", "label": "Warranty Deed" },
      "qualification": { "code": "TQ0002", "label": "Arm's-Length" },
      "arms_length": true,
      "distressed": false,
      "reo": false,
      "buyer_entity": { "code": "BE0001", "label": "Individual" }
    },
    "physical": {
      "garage": { "code": "PK0001", "label": "Attached Garage", "count": 2, "type": "attached" },
      "foundation": { "code": "FN0004", "label": "Concrete Slab Foundation", "class": "slab" },
      "basement": { "code": "BS0003", "label": "No Basement", "class": "none" },
      "construction": { "code": null, "label": null }
    },
    "debt": {
      "source": "mortgages",
      "archived": false,
      "balance": 218000,
      "lien_count": 1,
      "mortgages": []
    }
  }
}
```

**When to call:** First tool call as soon as the user mentions an address.

**Hold onto `property_id`.** Every Phase 4 write tool (`forvex_save_deal`, `forvex_log_activity`) and the existing pipeline reads (`forvex_list_deals({ property_id })`) accept it directly. Pass it through instead of re-resolving the address.

**Parcel facts (0.6.0) — read these, do not re-decode:**
- `parcel` is **null** when there is no Realie cache. Fall back to the 0.5.0 keys (`last_sold_*`, `condition_estimate`), then ask.
- Match on `code`; speak `label`. Never decode `TT####` / `TQ####` / `FN####` yourself.
- **Debt dual-read (do not mix these up):**
  - `recorded_lien_balance` is **liens-only**. Null when `liens[]` was omitted — that is *not* "$0 owed."
  - Winning debt is `parcel.debt.balance`. Use it when `parcel.debt.source` is `liens` or `mortgages`.
  - `archived_may_2026` is a frozen estimate — caveat it; do not treat it as a recorded payoff.
  - `none` means unknown, **not zero**.
- Last-sale flags (`arms_length`, `distressed`, `reo`, `buyer_entity`) are facts when present; null means the cache did not carry them (typical of flat v2 rows).
- Physicals: speak `foundation.class` / `basement.class` / `garage.type`, not the raw code.

**Behavior:**
- If `arv_confidence` is `low`, set deal confidence to `partial` and ask user to confirm ARV.
- If `condition_estimate` is `heavy` or `gut`, prompt user to confirm rehab scope before computing.
- Prefer `estimated_arv` from this tool when confidence is `medium` or `high`; call `forvex_get_comps` for detail.
- Prefer `parcel.debt.balance` over inventing payoff from `last_sold_price`.

**Failure modes:**
- Address not found → ask user for the basics (ARV, beds/baths, sqft)
- API down → fall back to user-provided values; mark confidence `limited`
- `parcel` null → proceed on 0.5.0 keys; do not invent last-sale flags or debt

---

### `forvex_get_comps(address | id)`

RealIE comparables via recontrol comps v3 engine (`schema_version: "comps.v2"`). **`forvex_get_comps` uses the canonical cache only (1 mi / 18 mo)** — it does not expand search. Wider pulls happen on verification / `run-trace` and land in separate cache rows (`comps_snapshot__r2_t24`, etc.). See `comp-evaluation.md`.

**Returns (v3 — dual valuation + signals):**
```json
{
  "schema_version": "comps.v2",
  "arv": { "low": 195000, "median": 214000, "high": 224000, "confidence": "high", "agreement": "tight", "basis": "…" },
  "as_is_value": { "low": 145000, "median": 162000, "high": 178000, "confidence": "high", "agreement": "moderate", "basis": "…" },
  "bands": { "as_is": { "…": "…" }, "market": { "…": "…" }, "rehabbed": { "…": "…" } },
  "pricing_hints": { "arv_retail": 230000, "wholetail_ceiling": 222000, "wholesale_anchor": 162000 },
  "funnel": { "pulled": 48, "selected": 4, "distress_share": 0.12, "stages": [] },
  "reconciliation": {
    "arv": { "reconciled_value": 214000, "agreement": "tight", "methods": [] },
    "as_is": { "reconciled_value": 162000, "agreement": "moderate", "methods": [] }
  },
  "signals": [{ "key": "market_liquidity", "severity": "info", "message": "…" }],
  "narrative_flags": [{ "headline": "…", "severity": "info" }],
  "trace_ref": { "id": "…", "url": "https://control.forvex.app/comps/…" }
}
```

Optional: `forvex_get_comp_detail({ trace_id, include_comps: true })` for the full roster + exclusion reasons.

**Exhibits / `comps[]` (0.6.0 additive — `comps.v2.1` unchanged):**
- Keep raw `doc_type` for matching. Speak `doc.label` (e.g. quit claim). Do not decode `TT####` yourself.
- `qualification` is a `{ code, label }` pair. `arms_length` is the engine's keep/drop read.
- `sale_flags` `{ distressed, reo, foreclosure, company_buyer }` explains distress share — quote them, do not invent a second distress story.
- `foundation` / `basement` carry `class` (slab, none, …). `garage_type` is already classified (`attached` / `detached` / …).
- `subject.physical` is the **subject** garage/foundation/basement block (same shape as `parcel.physical`). It is not an exhibit row.

**When to call:** In parallel with `forvex_get_property` on every new address.

**Behavior:**
- Retail ARV math: **`arv.median`** (comp-driven). Wholesale / as-is: **`as_is_value.median`** or `pricing_hints.wholesale_anchor`.
- Do **not** blend `as_is_value` into `arv` — read both on value-add deals.
- Surface **`narrative_flags`** (≤3) instead of inventing caveats; check **`signals`** for liquidity, distress, expansion.
- Quote **`arv.basis`** verbatim on the one-pager.
- If `funnel.selected < 4` or `arv.confidence == "fail"`, treat as `limited`.
- If user ARV diverges, compare `[arv.low, arv.high]` per `comp-evaluation.md`.

---

### `forvex_get_flood_data(address | id)`

FEMA NFHL via cached `core.property_api_cache`.

**Returns:**
```json
{
  "flood_zone": "X",
  "in_sfha": false,
  "bfe": null,
  "hazard_rating": "low",
  "fema_panel_id": "21111C",
  "data_age_days": 12
}
```

**When to call:** Always, in parallel with market intel, immediately after `forvex_get_property`.

**Behavior:**
- If `in_sfha == true`, increase insurance default by ~3x and add a `Flood Zone` warning.
- If `hazard_rating` is `high` or `very_high`, surface in risk section.
- Honor hard constraints from `my-buy-box.md` (e.g., never touch flood zones → PASS).

**Failure modes:**
- No data → flag confidence `partial`, note flood-status-unknown

---

### `forvex_get_rent_estimate(address, bedrooms?)`

Rentometer via server (direct API today; core cache planned).

**Returns:**
```json
{
  "estimated_rent": 1785,
  "range_low": 1485, "range_high": 2030,
  "confidence": "medium",
  "comps_count": 24,
  "as_of": "2026-05-23",
  "from_cache": false
}
```

**When to call:** Only if user didn't provide rent **and** rental strategy isn't excluded in `my-buy-box.md`.

**Behavior:**
- User-provided rent wins — do NOT call if they gave a number.
- If `confidence` is `low`, flag rental analysis as `partial`.
- If `comps_count < 5`, prefer asking the user over using the estimate.
- Show `as_of` in the rental block if older than 60 days.

**Failure modes:**
- API down → 1% rule fallback, flag prominently
- Do not retry on Claude's side — each fresh call costs money

---

### `forvex_get_market_intelligence(address | id | zip)`

Sense tract resolution + price momentum. **Flip/rent scores and ACS medians may be `null`** even when tract resolves — known gap until core metrics path ships.

**Returns:**
```json
{
  "zip": "40258",
  "tract_id": "21111012407",
  "flip_score": null,
  "rent_score": null,
  "mom_price_delta": 0.0,
  "yoy_price_delta": 0.0003,
  "median_price": null,
  "median_rent": null,
  "median_household_income": null,
  "owner_occupied_pct": null,
  "trend": "stable"
}
```

**When to call:** After `forvex_get_property` — pass `address` (preferred) or zip from property.

**Behavior:**
- If `flip_score` is non-null, feed `market_risk` per thresholds below.
- If `flip_score` is **null** but `yoy_price_delta` / `mom_price_delta` exist, derive a lighter market read:
  - YoY > +2% or MoM > +0.5% → note appreciating pocket; `market_risk` 0.4
  - YoY < −2% or MoM < −0.5% → note soft pocket; `market_risk` 0.6
  - Else → `market_risk` 0.5 (neutral)
- If `flip_score` is non-null:
  - `flip_score >= 7` AND trend `appreciating`/`stable` → market_risk 0.3
  - `flip_score 5–7` → market_risk 0.5
  - `flip_score < 5` OR trend `declining` → market_risk 0.7
- Show one-line market context in footer (tract id + trend or scores when present).
- If `mom_price_delta < -0.02`, surface as warning.

**Failure modes:**
- Tract not resolved → default `market_risk` 0.5, note submarket unknown
- Scores null → proceed with property + rent + flood; do not block underwriting

---

### `forvex_get_buy_box()`

Franchisee targets and constraints. When MCP is connected, this is the canonical source for connected runs.

**When to call:** On connected underwriting runs unless you already have fresh buy-box state for the current turn.

**Precedence:**
1. `forvex_get_buy_box()` when MCP connected
2. `my-buy-box.md` in project knowledge only when MCP is unreachable
3. forVEX defaults from `forvex-frame.md` / `assumptions.md`

---

### `forvex_underwrite(...)`

Canonical deterministic underwriting execution.

**When to call:** Prefer this as the default connected underwriting path.

**Behavior:**
- Resolves property snapshot from `address` or `property_id`.
- Loads canonical comps, market intelligence, latest saved deal defaults, and buy-box server-side.
- Accepts overrides such as `purchase_price`, `arv_override`, `rehab_override`, `strategy_focus`, and `calc_version`, while still honoring legacy explicit inputs when provided.
- Returns verdict, best strategy, confidence, strategy matrix, MAOs, pre-offer, payoff estimate when available, plus `effective_input` and `server_context` metadata.
- `server_context.property.parcel` is the same optional `parcel` object as `forvex_get_property`. Apply the same debt dual-read: winning debt is `parcel.debt.balance`, not `recorded_lien_balance`. Ignore unknown keys.

**Important:** user-provided inputs still win over buy-box defaults.

---

### `forvex_get_comps_expanded(...)`

Explicit broader comp search.

**When to call:** Only when the franchisee or agent explicitly asks for a wider search radius / looser comp set than the default `forvex_get_comps` workflow uses.

**Behavior:**
- Uses the same comps pipeline family as `forvex_get_comps`.
- Pays the higher latency cost in a dedicated tool call instead of inside the default underwriting path.
- Best used as a follow-up when the default comp set looks too thin or too strict.

---

### `forvex_list_deals(filter)` and `forvex_get_deal(id)`

Pipeline review, session kickoff, and re-analysis of existing deals.

**`forvex_list_deals` filters:** `workspace_id?`, `status?`, `property_id?`, `limit?` (1–100, default **25**), `offset?` (≥ 0, default 0). After `forvex_get_property`, always call `forvex_list_deals({ property_id })` so the kickoff flow can detect prior analyses on the same address (see `SKILL.md` step 1).

**Pagination envelope** (MCP 0.2.0):

```json
{
  "deals": [...],
  "total_count": 142,
  "has_more": true,
  "next_offset": 25,
  "limit": 25,
  "offset": 0
}
```

Pass `next_offset` back as `offset` on the next call. When `has_more` is `false`, you've reached the end (`next_offset` is null). For kickoff with `property_id`, pagination is rarely needed (one active deal per property). For full pipeline views, either pass `limit: 100` or loop on `next_offset`.

**`forvex_get_deal` returns** (Phase 4 additions):

- `current_analysis_id` — id of the latest `core.deal_analyses` row
- `analysis` — the full snapshot blob
- `analysis_summary` — `{ arv, offer, rehab, best_strategy, verdict, deal_score }`
- `underwriting` — retained bridge field; prefer `analysis` / `analysis_summary` going forward

**When to call:** User references an existing deal ("re-analyze the deal at 456 Oak", "show active wholesales"), and as part of the kickoff flow / verify-by-re-read after `forvex_save_deal`.

---

### `forvex_save_deal(payload)` — Phase 4.1 write

Persist an underwriting analysis to `core.deals` + `core.deal_analyses`.

**Payload (full contract in `2026-05-27-mcp-phase-4-write-back.md`):**

```json
{
  "property_id": "3bc6012a-6576-43ae-b40b-1b38696b4315",
  "analysis": {
    "calc_version": "0.4.0",
    "arv": 345000,
    "offer": 235000,
    "rehab": 20000,
    "best_strategy": "retail_flip",
    "verdict": "NEGOTIATE",
    "deal_score": 7.2,
    "risk_score": 38,
    "confidence": "full",
    "all_strategies": { },
    "posture": "hard_money",
    "lender_ltv_cap": 0.70,
    "cash_overlay": 23500
  },
  "context": {
    "seller_motivation": "relocation",
    "lead_source": "dig",
    "notes": "Former agent of mine; CA in 2 days; back-on-market after appraisal fail",
    "appointment_date": "2026-05-28"
  },
  "source": "forvex-underwriting",
  "status": "LEAD",
  "idempotency_key": "<fresh-uuid>"
}
```

**Behavior:**

- First save creates the deal at the supplied status (default `LEAD`).
- Subsequent saves on the same property **append** a new `core.deal_analyses` row and update the deal's "current analysis" pointer. Status is **never** changed by `forvex_save_deal` — that's `forvex_update_deal_disposition`'s job.
- `idempotency_key`-based dedupe: if a previous call with the same UUID already landed in the workspace, the original analysis is returned and `deduped: true` is set. Safe to retry.
- Returns `{ deal_id, analysis_id, property_id, deduped }`.

**Verify by re-read.** After `forvex_save_deal`, call `forvex_get_deal(deal_id)` and diff `analysis_summary` against what you sent. Only confirm "saved" to the user once the round-trip matches.

**When to call:** Only after the franchisee explicitly says "save this" (or paraphrase) following a presented one-pager. Never on the skill's own initiative.

---

### `forvex_update_deal_disposition(payload)` — Phase 4.2 write

Move a deal through the canonical lifecycle:

`LEAD → OFFER → UNDER_CONTRACT → INVENTORY → REHAB → LISTED → PENDING → SOLD`, plus `LOST` from any non-terminal status.

**Rules enforced by the server:**

- Sequential forward moves need no override.
- `LOST` is allowed from any non-terminal status without override (use it when the franchisee explicitly wants the deal off the active board).
- Backwards or skip transitions, and reopening a terminal deal, require `override_reason`.
- Same-status updates (status unchanged) require `reason_code` (use this for "documenting a non-progressing event" — counter pending, follow-up scheduled, etc., when you don't want to advance the deal).

**Verify by re-read.** Call `forvex_get_deal(deal_id)` afterwards and confirm `status` matches. If the server rejected the transition (bad rules combo), the tool returns `{ error: ... }` — surface it to the user verbatim.

**When to call:** This is `forvex-appointment-prep`'s primary write tool. `forvex-underwriting` does not call it.

---

### `forvex_log_activity(payload)` — Phase 4.3 write

Append a Readvise property note + timeline event. Lighter than disposition changes — captures touches, drive-bys, calls, offers/counters, notes that don't change pipeline state.

**Anchor (one required):** `deal_id` (preferred), `property_id`, or `address`.

**Payload:**

```json
{
  "deal_id": "...",
  "notes": "Drove by, vacant. Left card on door.",
  "activity_type": "drive_by",
  "outcome": "no_contact"
}
```

**Behavior:**

- Resolves to the linked Readvise property via `canonical_property_id`. Returns a clear error if no Readvise row exists yet — in that case run `forvex_save_deal` first (which will let Readvise's downstream sync create the row), then retry.
- Activity_type / outcome are free-form tags stored in timeline metadata. Suggested taxonomy: `activity_type` ∈ `drive_by | call | offer | counter | walkaway | referral | other`; `outcome` ∈ `no_contact | contact_made | accepted | declined | other`. Server doesn't enforce — skill picks the most descriptive tag.
- Returns `{ note_id, readvise_property_id, timeline_event_id, deal_id }`.

**When to call:** This is `forvex-appointment-prep`'s lightweight write tool. `forvex-underwriting` does not call it.

---

### `forvex_get_deal_history(deal_id)` — Phase 4 read

Unified chronological history for a deal, merging:

- `core.deal_analyses` snapshots → `type: "analysis"`
- `core.deal_status_events` transitions → `type: "disposition"`
- Readvise property notes for the same property → `type: "activity"`

Sorted oldest → newest.

**When to call:**

- Session kickoff in `forvex-underwriting` step 1 when the franchisee picks "pick up where I left off" — gives the skill a one-call view of everything that's happened.
- After `forvex_update_deal_disposition` / `forvex_log_activity` from `forvex-appointment-prep` if the franchisee asks "what's been logged so far?".

---

### `forvex_capture_deal_brief(payload)` — learning-layer write

End-of-underwriting-session retrospective. Persists a narrative brief plus per-correction learned signals, triaged server-side. This is the capture front-end of the self-learning loop — authoring is skill-side; recontrol owns schema, triage, and write path.

**Payload:**

```json
{
  "deal_id": "…",
  "analysis_id": "…",
  "decisions": ["Offered $150k; seller likely counters ~$140k"],
  "open_questions": ["Confirm roof age on site"],
  "next_steps": ["Send offer", "Order inspection"],
  "outcome_unknown": true,
  "corrections": [
    {
      "field": "beds",
      "observed": 2,
      "engine_value": 1,
      "triage_class": "DATA_BUG",
      "rationale": "public record shows 1, MLS + seller confirm 2"
    },
    {
      "field": "rehab",
      "observed": 31000,
      "engine_value": 25000,
      "triage_class": "CALIBRATION",
      "rationale": "engine under-scopes heavy rehab in this tract",
      "suggested_adjustment": {
        "target_field": "rehab",
        "op": "scale",
        "value": 1.2,
        "scope": "market",
        "scope_ref": "<tract_id>"
      }
    }
  ]
}
```

**Triage (per `corrections[]` item):**

| Class | Meaning | Adjustment? |
|---|---|---|
| `DATA_BUG` | Engine/pipeline had wrong input (bad comp, wrong beds, stale sale) | **Never.** Returned in `data_bugs[]` — surface to operator as upstream fix items. |
| `CALIBRATION` | Engine assumption systematically off | Optional `suggested_adjustment` → **shadow** adjustment (held until outcomes confirm). |
| `PREFERENCE` | Operator/buy-box fit, not correctness | Optional `suggested_adjustment` → **candidate** adjustment. |

**`suggested_adjustment`** (CALIBRATION/PREFERENCE only):

`{ target_field, op: 'scale'|'delta'|'set', value, scope?: 'deal'|'market'|'franchisee'|'global', scope_ref?, promotion_target?: 'runtime'|'source' }`

- `runtime` (default) — nudges an **injectable engine input**: `rehab`, `market_risk`, `hm_rate`, `hm_points`, `lender_ltv_cap`, `rent`.
- `source` — targets an engine-internal/skill knob that can't be injected (e.g. wholetail %, rehab/sqft tiers, verdict thresholds) → surfaces as a **tool-improvement proposal** at recontrol `/learning`, not a runtime nudge.

**When to call:** `forvex-underwriting` step 8.5 — in the same close-out after a successful `forvex_save_deal` the franchisee explicitly requested. Only capture real overrides/judgments from the run; do not invent corrections. Captured adjustments are inert until a super admin approves at `/learning`.

---

### `forvex_record_deal_outcome(payload)` — learning-layer write

Ground-truth actuals when a deal closes. Writes to `core.deal_outcomes` keyed to the **specific analysis snapshot** (`core.deal_analyses.id`) that produced the prediction. The `learning-calibration` cron uses this to advance shadow → candidate adjustments.

**Payload:**

```json
{
  "deal_id": "…",
  "analysis_id": "…",
  "outcome_kind": "SOLD",
  "actual_sale_price": 218000,
  "actual_rehab_cost": 28500,
  "actual_purchase_price": 165000,
  "days_on_market": 47,
  "actual_exit_strategy": "retail_flip",
  "closed_at": "2026-06-15T00:00:00Z",
  "notes": "Appraisal came in $3k under list; closed anyway.",
  "idempotency_key": "<fresh-uuid>"
}
```

**`outcome_kind`:** `SOLD` | `RENTED` | `WHOLESALED` | `DEAD` | `APPRAISAL`

- `analysis_id` defaults to the deal's `current_analysis_id` when omitted.
- Server returns `arv_error_pct` / `rehab_error_pct` against the snapshot's predicted values.
- Idempotent when `idempotency_key` (UUID) is supplied.

**When to call:** `forvex-deal-disposition` when a deal reaches a terminal close (`SOLD`, `LOST` → `DEAD`, etc.). Without outcomes, nothing in the learning loop gets confirmed.

---

### `forvex_render_presentation(mode, deal_id | property_id | address | readvise_property_id, …)`

Read-only. One tool, six modes. Returns `{ schema_version: "presentation.v1", mode, data, html }`. HTTP twin: `POST /api/operate/presentation`.

| `mode` | Needs | Notes |
|--------|-------|-------|
| `dashboard` `deck` `pdf` `internal_sheet` | Saved analysis | Deterministic HTML from the deal |
| `appointment_debrief` | `debrief` payload | Server stamps HTML only. Refuses an empty payload. **Never persist as a shareable URL.** |
| `rehab_scope` | `estimate_id` or `project_id` | Estimate dollars verbatim. Empty `observations` → unreconciled, no invented walkthrough. |

**When to call:** `forvex-presentation` after a saved analysis, after the operator recounts an appointment, or after `forvex_get_estimate` when they want the scope sheet.

---

## Order of operations (canonical flow)

When the user mentions an address:

```
1. forvex_get_property(address)              ← includes property_id
2. forvex_list_deals({ property_id })        ← detect prior analyses / existing deal state
3. forvex_underwrite(address, purchase_price?) ← canonical server-side workflow
4. forvex_get_flood_data(address)            ← only when explicit flood detail is needed
5. forvex_get_market_intelligence(address)   ← only when supporting narrative is needed
6. forvex_get_comps(address)                 ← only when the user wants direct comp inspection
7. forvex_get_comps_expanded(address)        ← only on wider-search request
8. forvex_get_rent_estimate(address)         ← only if rent still needs confirmation
9. forvex_render_presentation({ mode, deal_id })  ← operator artifact (optional)
```

The default underwriting path is now step 3. The other tools are supporting reads, not the primary execution chain.

---

## What if MCP isn't connected?

- Ask user for ARV, rent, condition, etc.
- Default `market_risk` to 0.5
- Skip flood check (mark `partial`, advise external verification)
- Apply forVEX defaults from `assumptions.md`
- Mention once: connect **forVEX Control** MCP in Claude settings to auto-populate property, flood, rent, and comps

---

## Privacy / token discipline

**Never put provider tokens in the skill zip.** Rentometer, FEMA, and Realie keys live server-side on forVEX Control. The MCP authenticates the franchisee (OAuth → Supabase JWT); upstream calls use server keys only.
