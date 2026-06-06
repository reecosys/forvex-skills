# Comp Evaluation — RealIE via forVEX Control MCP (comps v2.1)

Documents how the underwriting skill (and `forvex-appointment-prep`) should use comp data from **RealIE** via the **forVEX Control MCP** (`forvex_get_comps`, `forvex_get_comp_detail`, `forvex_get_property`).

Source of truth in recontrol:
- `recontrol/lib/mcp/comps/` — comp intelligence engine, `CompTrace` persistence, deterministic signals, **`buildCompBrief`**
- `recontrol/supabase/functions/refresh-api-cache` — Realie fetch + param-scoped cache rows

The skill **never** calls Realie directly and **never** re-derives ARV from raw comps. It consumes the engine verdict, **`brief.recommended`**, and **signals**.

---

## RealIE API surface (server-side only)

```
https://app.realie.ai/api/public/premium/comparables/
```

| Param | Default | Notes |
|---|---|---|
| `radius` | **1 mile** | Expands to 1.5–2 mi when pool thin (`run-trace` only) |
| `timeFrame` | **18 months** | Expands to 24 mo when pool thin |
| `maxResults` | **50** | |
| `sqftMin`, `sqftMax` | subject ± 25% | |
| `bedsMin`, `bedsMax` | beds ± 1 if known | |

Response: raw `comparables[]`. Cached 3-day TTL per search window in `core.property_api_cache` (canonical row `comps_snapshot` = 1 mi / 18 mo; expanded pulls use separate keys such as `comps_snapshot__r2_t24`).

---

## MCP tool surface

### `forvex_get_comps(address | id, include_comps?)`

Runs the comps engine on the **canonical** cache (1 mi / 18 mo), persists a `CompTrace`, returns **`schema_version: "comps.v2.1"`**. Does **not** widen search — use `forvex_get_comps_expanded` or human verification when expansion is needed.

**Returns (v2.1 — dual numbers + brief + signals):**
```json
{
  "schema_version": "comps.v2.1",
  "arv": {
    "low": 180000,
    "median": 214000,
    "high": 224000,
    "confidence": "high",
    "confidence_score": 81,
    "source_band": "rehabbed",
    "reason_code": "reconciled_consensus",
    "basis": "from 4 arm's-length comps in the rehabbed band; comp-driven at $214,000",
    "agreement": "tight",
    "spread_pct": 0.061
  },
  "as_is_value": {
    "low": 145000,
    "median": 162000,
    "high": 178000,
    "confidence": "high",
    "confidence_score": 81,
    "source_band": "rehabbed",
    "reason_code": "reconciled_consensus",
    "basis": "…",
    "agreement": "moderate",
    "spread_pct": 0.11
  },
  "bands": {
    "as_is": { "price_low": 145000, "price_median": 162000, "price_high": 178000, "comp_count": 3 },
    "market": { "price_low": 188000, "price_median": 205000, "price_high": 222000, "comp_count": 6 },
    "rehabbed": { "price_low": 218000, "price_median": 230000, "price_high": 245000, "comp_count": 4 }
  },
  "bands_overlap": false,
  "pricing_hints": {
    "arv_retail": 230000,
    "wholetail_ceiling": 222000,
    "wholesale_anchor": 162000
  },
  "funnel": {
    "pulled": 48,
    "selected": 4,
    "distress_share": 0.12,
    "stages": []
  },
  "reconciliation": {
    "arv": {
      "reconciled_value": 214000,
      "agreement": "tight",
      "spread_pct": 0.061,
      "methods": [
        { "method": "sales_comp", "value": 215000, "weight": 1, "included": true,
          "note": "comp-driven ARV from selected band (not blended with as-is anchors)" }
      ]
    },
    "as_is": {
      "reconciled_value": 162000,
      "agreement": "moderate",
      "spread_pct": 0.11,
      "methods": [
        { "method": "provider_avm", "value": 158000, "weight": 0.4, "included": true }
      ]
    }
  },
  "signals": [
    { "key": "market_liquidity", "severity": "info", "message": "Deep comp pool (48 pulled, 4 in verdict band)." },
    { "key": "valuation_basis", "severity": "info", "message": "Value-add spread: as-is $162,000 vs ARV $214,000 (32% gap) — rehab play; use both numbers." }
  ],
  "narrative_flags": [
    { "headline": "Value-add spread: as-is $162,000 vs ARV $214,000 (32% gap) — rehab play; use both numbers.", "severity": "info" }
  ],
  "exhibits": [
    { "id": "…", "address": "2520 Duncan St", "band": "rehabbed", "match_score": 78,
      "sale_price": 92436, "adjusted_price": 95200, "likely_rehab": true }
  ],
  "investor_signals": { "rehab_spread": 68000, "market_tightness": "balanced" },
  "trace_ref": { "id": "…", "url": "https://control.forvex.app/comps/…", "schema_version": "comps.v2" },
  "expansion": null,
  "pulled_at": "2026-05-29T15:30:00Z",
  "from_cache": true,
  "brief": {
    "schema_version": "comps.brief.v1",
    "eligible": true,
    "recommended": {
      "anchor": "grid",
      "arv": 214000,
      "arv_low": 205000,
      "arv_high": 222000,
      "as_is": 162000,
      "confidence": "high",
      "confidence_score": 81,
      "basis": "Appraisal-style grid indication $214,000 after feature adjustments; engine cluster median $230,000 (7% gap). Conservative anchor per expansion/wide-gap policy."
    },
    "consensus": {
      "engine_median": 230000,
      "grid_indication": 214000,
      "realie_avm": 158000,
      "spread_pct": 0.12,
      "preferred_read": "grid",
      "engine_vs_grid_gap_pct": 0.07
    },
    "gates": {
      "low_confidence_mao": false,
      "directional_only": false,
      "block_offer": false,
      "reasons": []
    },
    "appraisal_grid_summary": {
      "indicated_low": 205000,
      "indicated_high": 222000,
      "reconciled": 214000,
      "top_adjustments": ["garage +$6,000 avg (3 comps)"]
    },
    "ai_guidance": {
      "posture": "trust",
      "summary": "Recommended ARV $214,000 (grid anchor). Comp pool looks usable for underwriting with standard MAO gates.",
      "on_site_questions": ["Does the subject have a garage? If so, how many spaces?"],
      "rerun_triggers": ["Re-run forvex_get_comps with subject_overrides when assumptions change."]
    },
    "trace_ref": { "id": "…", "url": "https://control.forvex.app/comps/…", "schema_version": "comps.v2" }
  }
}
```

**When to call:** In parallel with `forvex_get_property` on every new address.

**Do not use:** Top-level `reconciliation.reconciled_value` (removed). Do not average `as_is_value` into ARV — they are separate on purpose.

### `forvex_get_comp_detail(trace_id, include_comps?)`

Full roster with `included`, `excluded_at_stage`, `exclude_reason`, real `band` / `match_score`. Use when the franchisee challenges the ARV.

---

## Field mapping for the skill

| Use case | Field |
|---|---|
| **Primary ARV for MAO / underwrite** | `brief.recommended.arv` when `brief.eligible && !brief.gates.block_offer` |
| **ARV band for brief / validation** | `[brief.recommended.arv_low, brief.recommended.arv_high]` |
| **Conservative anchor policy** | Prefer `brief.recommended` when `brief.consensus.preferred_read === "grid"` (gap >8% or expansion) |
| **Retail flip ARV (legacy)** | `arv.median` (engine cluster) or `pricing_hints.arv_retail` |
| **As-is / wholesale anchor** | `brief.recommended.as_is` or `as_is_value.median` or `pricing_hints.wholesale_anchor` |
| **Wholetail ceiling** | `pricing_hints.wholetail_ceiling` |
| Comp range for validation | `[arv.low, arv.high]` or brief band |
| Value-add narrative | `signals` (`valuation_basis`) or gap between as-is and recommended ARV |
| Confidence | `brief.recommended.confidence` / `brief.gates.*` |
| One-pager comp line | **`brief.recommended.basis`** (quote verbatim) |
| Caveats (≤3 headlines) | `narrative_flags[].headline` + `brief.gates.reasons` |
| On-site questions | `brief.ai_guidance.on_site_questions` |
| Rerun hints | `brief.ai_guidance.rerun_triggers` → `subject_overrides` on `forvex_get_comps` |
| Trust / liquidity | `signals` + `brief.ai_guidance.posture` |
| Usable comp count | `funnel.selected` |
| Deep link | `trace_ref.url` |
| **Do not use** | Raw `arv.median` when `brief.consensus.preferred_read === "grid"` unless user overrides |
| **Block offer ladder** | `brief.gates.block_offer` or `brief.ai_guidance.posture === "do_not_use"` |

---

## ARV derivation (v2.1)

```
brief.recommended.arv  = grid or engine anchor (see policy below)
brief.consensus.engine_median = raw comp cluster (trace.verdict.arv_median)
brief.consensus.grid_indication = mock appraisal grid reconciled value
arv.median             = engine cluster (audit / compare only when brief present)
as_is_value            = provider AVM + indexed last sale + assessment blend
pricing_hints:
  arv_retail         = rehabbed.price_median
  wholetail_ceiling  = market.price_high
  wholesale_anchor   = as_is.price_median
```

**Anchor policy (deterministic — do not override in prose):**
- Use **`brief.recommended.arv`** for MAO ladder and `forvex_underwrite` when eligible.
- **`grid` anchor** when engine vs grid gap **>8%** OR **`expansion.attempted`**.
- **`engine` anchor** when gap ≤8%, no expansion, and homogeneous cluster detected.
- **`eligible: false`** only when property type is unsupported (e.g. commercial `5000`, pipeline `FLIP`) or comps/sqft gates fail — **not** for duplex/MF.
- Duplex (`1101`/`1002`) and multifamily (`1112`) run **type-matched** comps (MF comps for MF subjects, etc.).

On value-add deals, cite **both** as-is and **recommended** ARV when `valuation_basis` or a wide gap is present.

---

## ARV validation — when to challenge user input

| Condition | Behavior |
|---|---|
| User ARV inside `[arv.low, arv.high]` | Accept silently |
| User ARV within 5% of band edges | Accept; show comp range |
| User ARV outside band by 5–15% | **Flag divergence**, ask to confirm |
| User ARV outside band by >15% | **Refuse to proceed** until explicit override |

---

## Confidence ripple

| `arv.confidence` | Effect on deal confidence |
|---|---|
| `high` | Deal confidence can be `full` |
| `medium` | Caps at `partial` |
| `low` | Caps at `partial`; warn to verify locally |
| `fail` | `limited`; directional only |

---

## Low-confidence MAO gate

**Trigger if any of:**
- `brief.gates.low_confidence_mao` or `brief.gates.directional_only`
- `brief.gates.block_offer`
- `brief.ai_guidance.posture === "do_not_use"`
- `brief.recommended.confidence_score < 50`
- `funnel.selected < 4`
- `bands_overlap == true` AND confidence not `high`
- Any `signals` entry with `severity: "warning"` on `search_effort` or `market_liquidity`
- `expansion` present AND `funnel.selected < 6`

**Behavior:** Mark offer ladder "directional only"; round MAOs to $5k; quote `narrative_flags` when present; cap verdict at `NEGOTIATE`.

---

## Signals (deterministic — do not re-derive)

| Key | Meaning |
|---|---|
| `market_liquidity` | Pool depth (raw pull + comps used) |
| `search_effort` | Expansion attempted; may include `axis`: `rural` or `recency` |
| `distress_share` | Share of raw pull with foreclosure / non-market deed / same-entity |
| `method_dispersion_arv` / `method_dispersion_as_is` | Agreement per valuation track |
| `valuation_basis` | Material as-is vs ARV gap — rehab play |
| `index_reliability` | Local index vs generic fallback |
| `comp_strength` | All-clear when pool is deep and tight |

Use `narrative_flags` (max 3, highest severity first) as punchy brief caveats.

---

## When MCP isn't connected

Accept user ARV with `confidence: partial`. Recommend connecting forVEX Control MCP.

**When connected:** `forvex_get_property` + `forvex_get_comps` in parallel on every address. User-stated ARV is confirmation when `arv.confidence` is `high`, not the primary source.

---

## Constants (recontrol engine)

| Name | Value |
|---|---|
| Default search | 1 mi / 18 mo (`comps_snapshot` cache row) |
| Expanded cache key example | `comps_snapshot__r2_t24` |
| `COMP_MAX_RESULTS` | 50 |
| `SQFT_BAND_PCT` | 0.25 |
| `COMPS_CACHE_TTL_DAYS` | 3 |
| `MIN_COMP_COUNT` | 4 |
| `COMP_THIN_USED_THRESHOLD` | 6 |
| `MATCH_STRONG_THRESHOLD` | 72 |
| `MATCH_WORKABLE_THRESHOLD` | 58 |
