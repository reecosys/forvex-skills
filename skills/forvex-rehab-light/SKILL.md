---
name: forvex-rehab-light
description: Light rehab cost estimator — a fast ballpark renovation budget for a cosmetic-to-moderate flip from square footage, condition, and finish level. Use this skill whenever the user asks "what will the rehab cost", "ballpark the renovation", "rough rehab number", "how much to fix this up", "estimate repairs", or gives a square footage and condition and wants a budget. Standalone and beginner-friendly — runs on user inputs only, no connectors or account required. For heavy/gut rehabs or line-item contractor takeoffs, it defers to a full estimate. NOT for personal-home remodels.
---

# Light Rehab Estimator

You produce a **fast, defensible ballpark** rehab budget for a cosmetic-to-
moderate flip — the number a flipper needs before they've had a contractor walk
the house, to sanity-check a deal. It is deliberately a screen, not a takeoff.

This skill is **fully standalone** — it runs on the size, condition, and finish
level the user gives you. No connectors, no account. Never tell them to connect
anything.

## The light vs. full boundary (read this first)

A *light* estimate spreads category rates over the floor area and adds flat costs
for kitchens and baths. A *full* estimate measures every room and prices real
quantities against live unit costs. This tool is the light one. The line that
matters: the moment **big-ticket systems** are in play (roof, HVAC, rewire,
repipe, windows, foundation), you're past "light," and the honest move is to say
so and treat the number as a rough screen. The script flags this automatically;
surface it loudly.

## Two axes, kept separate

- **Condition** (`cosmetic` | `moderate`) — *how much* work. Drives quantity.
- **Finish level** (`rental` → `luxury`) — *how nice* the replacements. Drives
  unit cost.

They're independent: a BRRRR rental can need heavy work with cheap finishes; a
high-end flip can need light work with premium ones. Don't collapse them.
`condition: heavy` or `gut` is rejected — that's the full tool's job.

## Workflow

### 1. Gather inputs

**Required:**
- **Square footage**

**Strongly preferred:**
- **Condition** — `cosmetic` (paint/floor/fixtures, surfaces are sound) or
  `moderate` (more repair, some replacement). If they describe a gut, stop and
  point them to a full line-item estimate.
- **Finish level** — `rental`, `entry`, `mid` (typical for light flips), and
  `moveup`/`luxury` are allowed but unusual for a light scope.
- **Bath count** (and kitchen count if more than one) — these are flat costs, so
  the count matters more than the square footage.

**Optional:**
- **Big-ticket systems present** — flag any of roof, HVAC, electrical panel,
  repipe, windows, foundation, water heater. Pass real numbers if the user has
  bids; otherwise the tool uses rough placeholders and says so.
- **Cost multiplier** — local labor/material scalar (`1.3` pricey metro, `0.85`
  low-cost rural). Default 1.0.
- **Contingency %** — default 12%. Tighter scopes can go lower; older houses higher.

Ask for anything missing in **one consolidated question**. With only sqft, run it
on defaults (cosmetic, mid) and flag what you assumed.

### 2. Run the calculator — never estimate in your head

```bash
python scripts/rehab_light.py '<json-input>'
```

Returns the expected cost, a low–high band, the cosmetic breakdown by category,
big-ticket items listed separately, contingency, $/sf, and the scope verdict. See
the script docstring for the input schema.

### 3. Present the estimate

Use `templates/rehab-estimate.md`. Lead with the expected number and the band,
then the cosmetic breakdown, then big-ticket items called out *separately* (never
buried in the cosmetic total), then the scope verdict and limitations. Always show
the $/sf as a sanity anchor.

### 4. Follow-ups

For what-ifs ("what if it needs a roof", "rerun at rental finish"), re-run with
the one change and return a focused delta.

## Output style

- **Give a number and a band.** "$60k, call it $51–69k" — ballparks are ranges.
- **Keep cosmetic and systems visibly separate.** The split is the whole point.
- **Flag the scope honestly.** If big-ticket items are present, say plainly this
  is past light and needs a real estimate.
- **Anchor with $/sf.** It's the fastest gut-check on whether the number is sane.
- **Never imply contractor-grade precision.** This is a screen; say so.

## What this skill does NOT do

- It is **not** a line-item takeoff. No room dimensions, no measured quantities,
  no live material/labor pricing. It's a ballpark to screen a deal.
- It does **not** handle heavy/gut rehabs — those are rejected with a pointer to a
  full estimate.
- It is **not** for personal-home remodels — this is resale-scoped flip work.
- It does not pull property data, comps, or bids from anywhere — all user inputs.
- It does not invent square footage. If sqft is missing, it asks.

## Prototype notes — feeding the full rehab tool

This is intentionally a prototype. `references/assumptions.md` ends with a
section on exactly where this approach breaks down and what the full line-item
estimator will need beyond it (measured quantities, a unit-cost database, regional
pricing, contractor-bid reconciliation, draw schedules, an SOW export). Read it
when the goal is to learn from this build, not just run it.

## Reference files

- `references/assumptions.md` — all rates, multipliers, the formula, and the
  prototype-to-full-tool notes
- `scripts/rehab_light.py` — the deterministic estimator
- `scripts/test_rehab_light.py` — regression suite; run before changing calc logic
- `templates/rehab-estimate.md` — output template
