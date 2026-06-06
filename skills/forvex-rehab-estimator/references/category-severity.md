# Category & Severity Heuristics

Maps franchisee language to REbuild **intake categories** and engine severities. The MCP engine uses lowercase internally (`light`/`medium`/`heavy`/`none`); skill inputs use Title case (`Light`, `Medium`, `Heavy`, `None`).

## Eight categories (authoritative list)

| Category | What it covers |
|----------|----------------|
| **Kitchen** | Cabinets, counters, appliances, layout — highest $/room risk |
| **Bath** | Each bath: vanity, tile, tub/shower, plumbing fixtures |
| **Flooring** | Carpet, LVP, tile, hardwood — whole-house or selective |
| **Exterior** | Roof, siding, paint exterior, gutters, curb appeal |
| **Interior** | Paint interior, drywall, trim, doors — "cosmetic shell" |
| **Systems** | **Electrical + plumbing + HVAC** (treat as one unless user splits) |
| **Foundation** | Structural: slab, crawl, basement, movement, waterproofing |
| **General** | Permits, dumpster, cleanout, misc catch-all — use sparingly |

## Systems = E / P / HVAC

When the user mentions any of:

- Panel, wiring, knob-and-tube, GFCI, service upgrade → **Systems**
- Galvanized/poly, repipe, fixtures, water heater → **Systems**
- Furnace, AC, condenser, ductwork, heat pump → **Systems**

Default **Medium** for "old but working" on pre-1980 homes unless they say recently updated.

Escalate to **Heavy** for: full rewire, full repipe, multiple HVAC replacements, knob-and-tube with cloth wiring.

## Severity scale

| Severity | Meaning | Typical scope |
|----------|---------|----------------|
| **None** | Confirmed no work in this category | Engine excludes category items |
| **Light** | Cosmetic / refresh | Paint-touch, minor repairs |
| **Medium** | Standard investor rehab | Partial updates, selective replacement |
| **Heavy** | Full replacement / major work | Gut-level for that category |

Do not assign **Heavy** without user evidence or strong implication (e.g., "gutted kitchen," "roof leaking," "foundation crack").

## Phrase → category hints

| User says | Category | Notes |
|-----------|----------|-------|
| roof, shingles, leak | Exterior | Often largest exterior line |
| kitchen cabinets, counters | Kitchen | |
| bathroom, vanity, tub | Bath | Per-bath severity can match |
| floors, carpet, LVP | Flooring | |
| paint, drywall, walls | Interior | |
| electrical, panel, HVAC, plumbing | Systems | |
| foundation, crawl, structural | Foundation | Deal-killer check |
| trash-out, permits, dumpster | General | |

## Action taxonomy (SKU mapping)

When using `forvex_map_observations_to_skus`, valid actions are:

`none` | `repair` | `replace` | `reface` | `paint` | `upgrade` | `refresh`

SKUs must exist in the workspace catalog — rejected SKUs are dropped server-side.

## Age-based nudges (ask, don't assume)

- Built **before 1970**: ask Systems and Foundation explicitly.
- Built **before 1978**: mention lead/asbestos possibility; do not auto-add dollars without user scope.
- **Vacant long-term**: bias toward Medium Flooring + Interior minimum.

## Cross-check

If user also gave an overall "light/medium/heavy/gut" gut feel, compare to preview total vs `rehab_rates_per_sqft` from builder prefs. Flag large gaps; do not override engine.
