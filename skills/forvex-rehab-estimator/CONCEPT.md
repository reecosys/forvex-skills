# Concept Doc — Rehab Estimator (Claude Skill + MCP Server)

**Audience:** DevOps / engineering team
**Status:** MCP tools live on forVEX Control; skill authored in `SKILL.md` (Phase 7)
**Author:** Underwriting skills workstream
**Related:** `forvex-underwriting`, `forvex-appointment-prep`, Readvise MCP (planned)

---

## 1. Purpose

We're extending the forVEX underwriting skill suite with a **rehab estimation** capability. We already have a full rehab-estimation app (analogous to redeal for underwriting). This concept proposes surfacing that engine through a **Claude skill** (the franchisee-facing workflow + judgment) backed by an **MCP server** (the deterministic cost engine, regional pricing, and estimate persistence — the part this team builds).

The pattern is the same one we've used successfully for underwriting:

- **Claude does the reasoning** — walks the franchisee through condition capture, interprets observations, handles ambiguity, narrates the estimate.
- **The server does the arithmetic** — unit costs, regional multipliers, line-item math, persistence. No LLM math on dollar figures.

The rehab number this produces flows directly into the existing underwriting skill (it's the `rehab` input that drives every strategy and the Pre-Offer number), and into the appointment-prep brief.

## 2. Why this matters

Rehab is the single biggest swing factor in an offer. The underwriting calculator is only as good as the rehab estimate fed into it. Today the franchisee either:

- Eyeballs a `$/sqft` tier (light/medium/heavy/gut — already supported in the Pre-Offer logic), or
- Carries the estimate in their head / a separate tool.

This skill closes the loop: structured condition capture → priced estimate → straight into underwriting → re-priced offer, live in the appointment. It's the missing link between "walk in with a Pre-Offer" and "land on a defensible final offer after seeing the house."

It also directly enables the objection-handling play already built into appointment-prep: *"show me the work's less than I think and I'll re-run it on the spot."*

## 3. Architecture

```
┌─────────────────────────────────────────────┐
│  Claude.ai chat (iPhone / web / desktop)     │  ← franchisee on-site
├─────────────────────────────────────────────┤
│  forvex-rehab-estimator skill                    │  ← condition capture + workflow
│   ├─ quick mode ($/sqft tier)                │
│   └─ component mode (line-item)              │
├─────────────────────────────────────────────┤
│  Rehab MCP tools (THIS TEAM BUILDS)          │  ← cost engine over the existing app
│   estimate_quick / estimate_components /     │
│   get_cost_catalog / save / get / templates  │
├─────────────────────────────────────────────┤
│  Existing Rehab App engine + DB              │  ← unit costs, regional pricing, history
└─────────────────────────────────────────────┘
         │
         └──→ rehab estimate feeds forvex-underwriting (rehab input)
              and forvex-appointment-prep (Pre-Offer adjustment)
```

**Recommendation: expose these as additional tools on the planned Readvise MCP server** rather than standing up a separate MCP. One auth surface, one connector for the franchisee to configure, shared deal-id namespace. The rehab tools call into the existing rehab app's engine the same way the comp tools call RealIE. (If the rehab app is a separate service with its own auth, a dedicated MCP is acceptable — but the franchisee then configures two connectors.)

## 4. What the skill does (Claude side — for context, not your build)

1. Pull property fundamentals (sqft, beds/baths, year, type) from the property MCP tools.
2. Ask the franchisee which mode: **quick** (walk-in estimate) or **component** (post-walkthrough detail).
3. **Quick mode:** confirm sqft, pick a condition tier → call `estimate_quick`.
4. **Component mode:** walk the property zone-by-zone (exterior, systems, kitchen, baths, interior, safety flags), capture condition per item → call `estimate_components`.
5. Return the priced estimate with a breakdown; flag big-ticket items and surprises.
6. Feed the number into underwriting / Pre-Offer and optionally `save_rehab_estimate` to the deal.

The condition checklist the skill walks (zones and items) is documented in `references/condition-checklist.md` (skill-side reference; informs what fields the component tool must accept).

## 5. What the MCP server provides (YOUR BUILD)

### 5.1 Tool surface

All tools are authenticated per-user (per-franchisee token), call into the existing rehab engine, and return JSON.

#### `estimate_rehab_quick`

```
Input:  { sqft, condition_tier, market_id?, property_type? }
        condition_tier ∈ { light, medium, heavy, gut }
Output: {
  estimate_total,
  per_sqft_rate,
  condition_tier,
  market_id,
  market_multiplier,        // regional adjustment applied
  confidence: "low",        // tier-based is coarse
  calc_version
}
```

Mirrors the `$/sqft` tier logic already in the underwriting Pre-Offer (light $15, medium $25, heavy $40, gut $60 — baseline national; **server applies the regional multiplier**). The franchise operates KY/Southern IN; baseline rates should reflect that market, or be multiplier-adjusted from a national base.

#### `estimate_rehab_components`

```
Input:  {
  market_id?,
  property: { sqft, beds, baths, year_built, stories },
  components: [
    { category: "roof",     condition: "replace", params: { squares: 18 } },
    { category: "hvac",      condition: "replace", params: { systems: 1, tons: 3 } },
    { category: "kitchen",   condition: "full",    params: { } },
    { category: "flooring",  condition: "replace", params: { sqft: 1200, type: "lvp" } },
    { category: "paint",     condition: "full",    params: { sqft: 1200, scope: "interior" } },
    ...
  ]
}
Output: {
  estimate_total,
  line_items: [ { category, condition, quantity, unit_cost, extended_cost }, ... ],
  contingency,              // % of subtotal (e.g., 10%)
  permits_dumpster_misc,
  market_id, market_multiplier,
  confidence: "high",
  calc_version
}
```

This is the core ask. The component catalog (categories, condition states, unit costs, regional multipliers) lives in the existing rehab app — this tool wraps it.

#### `get_rehab_cost_catalog`

```
Input:  { market_id? }
Output: {
  market_id, market_multiplier,
  categories: [
    { category: "roof", unit: "per_square", base_cost: 350,
      conditions: ["ok","repair","replace"] },
    { category: "kitchen", unit: "per_room", conditions: {...}, base_cost: 12000 },
    ...
  ],
  calc_version
}
```

Lets the skill show the franchisee what's in the model and adjust assumptions. Also lets us keep the skill in sync with the catalog without hardcoding costs in the skill.

#### `save_rehab_estimate` / `get_rehab_estimate`

```
save:  { deal_id, estimate_payload } → { estimate_id, saved_at }
get:   { deal_id } → { estimate_id, estimate_payload, saved_at, saved_by }
```

Persist an estimate to a deal record (shared deal-id with underwriting/Readvise). Enables "pull up the estimate I did Tuesday."

#### `get_rehab_templates` (optional, phase 2)

```
Input:  { property_type?, era?, scope? }   // e.g., "1960s ranch cosmetic"
Output: { templates: [ { name, components_preset } ] }
```

Common scope presets so a franchisee can start from "1960s ranch, cosmetic" and adjust, rather than building every estimate from scratch.

### 5.2 Component categories (minimum set)

The component tool must accept at least these. Final list should match whatever the existing rehab app already models:

| Category | Unit | Notes |
|---|---|---|
| Roof | per square / sqft | age + condition → repair vs replace |
| HVAC | per system / per ton | age-driven |
| Electrical | panel + rewire (per sqft) | code/age flags |
| Plumbing | repipe (per sqft) + fixtures + water heater | pipe material matters |
| Kitchen | per room (tiered: cosmetic / full) | highest $/room |
| Bathrooms | per bath (tiered) | second highest |
| Flooring | per sqft by type (carpet/LVP/tile/hardwood) | |
| Paint | per sqft (interior / exterior) | |
| Drywall | per sqft | |
| Windows | per window | |
| Foundation | flag + estimate | deal-killer flag |
| Exterior/siding | per sqft | |
| Landscaping/cleanout | flat / tiered | |
| Permits / dumpster / misc | % of subtotal | |
| Contingency | % of subtotal | typically 10% |

### 5.3 Non-functional requirements

- **Auth:** per-franchisee token (same model as the rest of the Readvise MCP). Provider/engine credentials stay server-side — never in the skill.
- **Regional pricing:** every estimate carries a `market_id` and the `market_multiplier` applied. KY/Southern IN is the primary market; design for multi-market.
- **Versioning:** emit `calc_version` on every response (semver). Bump when the cost catalog or formula changes. Old estimates should record the version they were computed under.
- **Caching:** cost catalog is cacheable (changes infrequently); estimates are not (deal-specific).
- **Latency:** these are called interactively in an appointment. Target < 2s per call.
- **Idempotency:** `save_rehab_estimate` should upsert on `deal_id` (or version estimates per deal).
- **Audit:** log who computed/saved which estimate, when, under which catalog version.

## 6. What to extract from the existing rehab app

The existing app already has the hard part: the cost model. The work is to **expose it as the tool surface above** rather than rebuild it. Please confirm for us:

1. **Cost catalog data model** — categories, condition states, unit costs, units of measure. (Drives `estimate_rehab_components` and `get_rehab_cost_catalog`.)
2. **Regional multiplier model** — how does the app adjust for market? Per-line, or a flat market multiplier?
3. **Existing estimation API** — is there already a service endpoint that takes a component list and returns a priced estimate? If so, the MCP tool is a thin wrapper.
4. **Estimate persistence** — does the app store estimates today? Can they key to the shared `deal_id`?
5. **The $/sqft tier rates** — does the app have authoritative light/medium/heavy/gut rates per market? (We're using national baselines of $15/$25/$40/$60 in the underwriting Pre-Offer today; we'd prefer to source the real ones from this engine.)
6. **Photo/vision** — does the current app do any photo-based estimation? (Informs the phase-2 vision capability below.)

## 7. Integration points

- **forvex-underwriting** — the rehab estimate becomes the `rehab` input. A franchisee can say "estimate the rehab, then underwrite it" and the number flows through. Re-running with a revised estimate re-prices every strategy and the Pre-Offer live.
- **forvex-appointment-prep** — Pre-Offer's repair-adjusted number uses the estimate. The objection-handling play ("I'll re-run it") depends on this being fast.
- **Readvise** — `save_rehab_estimate` writes to the deal record; the estimate travels with the deal.

## 8. Phasing

| Phase | Scope |
|---|---|
| **1 — Quick + Component** | `estimate_rehab_quick`, `estimate_rehab_components`, `get_rehab_cost_catalog`. Read-only. Validates the skill workflow end-to-end. |
| **2 — Persistence + templates** | `save_rehab_estimate`, `get_rehab_estimate`, `get_rehab_templates`. Ties estimates to deals. |
| **3 — Vision-assisted** (stretch) | Skill accepts property photos; a vision step suggests condition tiers per component, franchisee confirms. Big UX win for on-site capture. Depends on whether the existing app has any photo model to lean on. |

## 9. Open questions for DevOps

1. Standalone rehab MCP, or extend the planned Readvise MCP? (We recommend extend.)
2. Does the existing rehab app expose a service API we can wrap, or do we need a new service layer over its DB?
3. What's the canonical `deal_id` that ties rehab estimates, comps, and underwriting together? Is it the Readvise deal id?
4. Regional coverage — KY/IN only at launch, or design multi-market from day one?
5. Who owns catalog updates (cost changes over time) and how do we version them?
6. Is there an existing photo/condition dataset we could use for the phase-3 vision capability?

## 10. Out of scope

- The skill itself (Claude-side workflow) — we build that once the tool surface is agreed.
- Rebuilding the cost model — we wrap the existing engine, not replace it.
- Contractor bid management, scheduling, draws — this is *estimation* for underwriting, not project management.

---

**Next step:** a 30-minute review with whoever owns the existing rehab app to answer §6 and §9, then we lock the tool contracts and you can build Phase 1 against a stub while we build the skill side in parallel.
