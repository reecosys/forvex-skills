# Condition Checklist (Rehab Estimator)

The zone-by-zone checklist the skill walks the franchisee through during a walkthrough. Each item maps a condition observation to a component the cost engine prices. This doubles as the **input contract** for the MCP `estimate_rehab_components` tool — every item here is a component the tool must accept.

Condition states are coarse on purpose (the franchisee is eyeballing, not inspecting): typically `ok` / `repair` / `replace`, or a tier (`cosmetic` / `full`) for rooms.

---

## Exterior & structure

| Item | Condition states | Params captured |
|---|---|---|
| Roof | ok / repair / replace | squares or sqft, age |
| Foundation | ok / monitor / repair | flag + rough $ (deal-killer if major) |
| Siding / exterior | ok / paint / replace | sqft |
| Windows | ok / partial / replace all | count |
| Gutters | ok / replace | linear ft (optional) |
| Grading / drainage | ok / issue | flag |

## Major systems

| Item | Condition states | Params captured |
|---|---|---|
| HVAC | ok / service / replace | systems, tons, age |
| Electrical | ok / panel only / rewire | panel age, sqft, code flags (knob-and-tube) |
| Plumbing | ok / fixtures only / repipe | pipe material, water heater age |
| Water / sewer | municipal / well / septic | flag (septic adds cost/risk) |

## Kitchen

| Item | Condition states | Params captured |
|---|---|---|
| Kitchen | ok / cosmetic / full | (cabinets, counters, appliances rolled into tier) |

## Bathrooms

| Item | Condition states | Params captured |
|---|---|---|
| Bath (per) | ok / cosmetic / full | count at each tier |

## Interior

| Item | Condition states | Params captured |
|---|---|---|
| Flooring | ok / replace | sqft, type (carpet / LVP / tile / hardwood) |
| Paint | ok / partial / full | sqft, interior/exterior |
| Drywall | ok / patch / replace | sqft (optional) |
| Doors / trim | ok / replace | flag |

## Safety / age flags (scope expanders & deal-killers)

| Item | What to flag |
|---|---|
| Mold / water intrusion | location + severity |
| Pest / termite | evidence |
| Asbestos / lead | pre-1978 build → likely present, adds abatement cost |
| Structural | sagging, cracks, additions without permit |

## Overall

| Item | Captured |
|---|---|
| Square footage | drives $/sqft and quantity math |
| Beds / baths | room counts |
| Year built | age flags (systems, lead/asbestos) |
| Stories | affects roof, exterior |
| Occupancy | occupied / vacant / tenant (affects access + cleanout) |
| Overall tier | light / medium / heavy / gut (for quick-mode cross-check) |

---

## Two modes the skill offers

**Quick mode** — capture only `sqft` + overall tier → `estimate_rehab_quick`. The walk-in / pre-offer number. Coarse, fast.

**Component mode** — walk the full checklist, capture condition per item → `estimate_rehab_components`. The post-walkthrough number that feeds the final offer. Detailed, defensible, and re-runnable in the appointment.

The skill should always offer to **cross-check**: if component mode produces a number wildly different from the quick-mode tier estimate, surface the gap ("component build is $48k but this looked like a 'medium' which would be ~$25k — worth a second look at the big-ticket items").
