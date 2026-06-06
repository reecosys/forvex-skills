# Light Rehab — Assumptions, Rates & Prototype Notes

Every rate below is a national placeholder. Scale with `cost_multiplier` for the
local market, and flag every default you apply.

## The formula

```
cosmetic cost  = Σ (per-sqft category rate × sqft)  +  Σ (flat kitchen/bath × count)
                 each scaled by: condition × (finish, if finish-sensitive) × market

big-ticket     = Σ (flagged system adders × market)        # OUTSIDE the cosmetic engine

base           = cosmetic + big-ticket
expected       = base × (1 + contingency)
range          = [ base × 0.95 , expected × 1.15 ]          # rehabs surprise high
```

## Two scaling axes

| Axis | Values | What it scales |
|---|---|---|
| Condition | cosmetic ×1.0, moderate ×1.5 | quantity of work (all cosmetic categories) |
| Finish level | rental ×0.75, entry ×0.90, mid ×1.0, moveup ×1.35, luxury ×1.9 | unit cost (finish-sensitive categories only) |
| Cost multiplier | market scalar, default 1.0 | everything, including big-ticket |

`condition: heavy` / `gut` is rejected — beyond the light tool.

## Per-sqft category rates (cosmetic / mid / ×1.0)

| Category | $/sf | Finish-sensitive? |
|---|---|---|
| Interior paint | 2.50 | no |
| Flooring | 4.50 | yes |
| Drywall repair/patch | 1.00 | no |
| Lighting & fixtures | 1.25 | yes |
| Interior doors, trim, hardware | 1.50 | yes |
| Trash-out & cleaning | 0.75 | no |
| Exterior & curb appeal | 1.50 | yes |

"Finish-sensitive" means the finish level scales it (it's material-driven).
Paint, drywall, and cleanout are mostly labor, so finish level barely moves them
— a deliberate modeling choice the full tool will refine per line.

## Flat count items (mid finish)

| Item | Base each | Scaled by |
|---|---|---|
| Kitchen (light refresh) | $8,000 | condition × finish × market × count |
| Bathroom (light refresh) | $3,500 | condition × finish × market × count |

Light kitchen = paint/reface cabinets, new counters, appliances, fixtures — not a
full tear-out. Light bath = vanity, fixtures, reglaze or simple tile, toilet.

## Big-ticket adders (flat, present-only, rough)

| System | Placeholder | Note |
|---|---|---|
| Roof replacement | $9,000 | varies widely by pitch/material/size |
| HVAC replacement | $8,000 | system size and ducting drive it |
| Electrical panel / partial rewire | $4,000 | full rewire is much more |
| Repipe | $6,000 | material and access dependent |
| Windows (whole house) | $9,000 | count and quality dependent |
| Foundation / structural | $12,000 | HUGE variance — always get an engineer |
| Water heater | $1,500 | tank vs tankless |

These are screening placeholders, scaled by market only (a roof is a roof
regardless of finish level). Override any with a real bid. **If even one is
present, the scope is past "light."**

## Contingency

Default 12% of base. Cosmetic-only on a sound house can run 8–10%; older or
moderate scopes warrant 15%+. The band then widens the high side by another 15%
because overruns beat underruns in this business.

---

## Prototype notes: what the FULL rehab tool needs beyond this

This light estimator is a useful screen, but it makes simplifications that a
production line-item estimator must replace. Capturing them here so the bigger
build inherits the lessons rather than the shortcuts:

1. **Measured quantities, not floor-area spreads.** This tool multiplies one
   $/sf by total sqft. The full tool needs real takeoffs — wall area for paint
   (not floor area), actual flooring square footage by room, linear feet of trim,
   counts of doors/outlets/fixtures. Floor area is a proxy that breaks on odd
   layouts, high ceilings, and open plans.

2. **A unit-cost database, versioned.** Hardcoded rates go stale. The full tool
   needs a maintained cost catalog (material + labor split), ideally regional and
   date-stamped, so estimates are auditable and update without code changes.

3. **Real regional pricing, not a single multiplier.** One `cost_multiplier`
   can't capture that labor is tight in one trade and slack in another, or that
   material costs and labor costs diverge by metro. The full tool wants
   category-level regional factors.

4. **Per-line condition, not one global condition.** A house can have a gut
   kitchen and sound bedrooms. The full tool needs condition per room/system, not
   a single cosmetic/moderate switch.

5. **Big-ticket systems as first-class line items.** Here they're flat rough
   adders. The full tool needs them scoped properly (roof by squares and pitch,
   HVAC by tonnage, electrical by panel amperage and circuit count) — because
   they're where the real money and the real risk live.

6. **Contractor-bid reconciliation.** The full tool should ingest actual bids and
   diff them against the estimate (this pairs naturally with bid-leveling and the
   post-mortem skill), so estimates calibrate against reality over time.

7. **Outputs the trades can use.** A real SOW, a draw schedule tied to milestones,
   and an export a contractor can bid line by line — not just a total.

The most important architectural carry-over, already present here: **keep the
cosmetic engine and the big-ticket systems separate.** That separation is what
lets the full tool scope systems rigorously without polluting the fast cosmetic
path, and it's why this prototype draws the light/heavy line exactly there.
