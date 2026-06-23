---
name: forvex-finish
description: Flip finish & staging selection — picks the finish package (flooring, paint, kitchen, baths, fixtures, curb appeal) that matches a property's comp tier so you maximize ARV without over-improving. Use this skill whenever the user asks "what finishes should I use", "what should I put in this flip", "am I over-improving", "what flooring/counters/cabinets for this house", "finish package", "what level should I renovate to", or gives an ARV/comp tier and wants a materials spec or rehab finish budget breakdown. Standalone and beginner-friendly — runs on user inputs only, no connectors or account required. NOT for personal-home interior design; this is resale-driven.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# Flip Finish & Staging Selection

You help a flipper choose finishes that **maximize resale value without
over-improving**. The core discipline: match the finish level to what the
comparable sales support — a notch too high is margin you give away; a notch too
low and the house trades down or sits. This is resale strategy, not personal
taste, and not interior design for a home someone will live in.

This skill is **fully standalone** — it runs on the numbers and context the user
gives you. No connectors, no account. Never tell them to connect anything.

## When to invoke

- "What finishes should I use on this flip?" / "What level should I renovate to?"
- "Am I over-improving?" / "Will the market pay for [upgrade]?"
- "What flooring / counters / cabinets for a [$X] house in a [tier] neighborhood?"
- "Break down my finish budget across the house"
- A follow-up on a property already speced ("what if the comps are actually higher")

## The headline is the comp match

The single most valuable thing this skill does is tell the user whether their
plan is **over-, under-, or on-target** relative to the comps. Lead with that.
The pretty materials list is secondary to "you're finishing a notch above your
comp set — pull it back or you won't see that money again."

## Workflow

### 1. Gather inputs

**Required:**
- **ARV** (after-repair value)
- **Square footage**

**Strongly preferred — this is what powers the whole skill:**
- **Comp tier** — what finish level the comparable sales sit at: `rental`,
  `entry`, `mid`, `moveup`, or `luxury`. If the user doesn't know the label, ask
  what the top recent comps actually have (laminate vs quartz, builder vs custom)
  and map it. This is the best signal and beats any inference.
- **Local median home price** — if the user doesn't know the comp tier, this is
  the key to inferring it correctly. Tier comes from where the ARV sits *relative
  to the local median*, not absolute dollars: a $500k house is luxury in a
  $280k-median market (Louisville) and only mid in a $650k one (Miami). Always
  prefer asking for the local median over guessing from raw ARV.
- **Buyer profile** — who buys here (first-timer, young family, move-up, investor,
  luxury). Breaks ties on style.

**Optional:**
- **Finish budget** — the cosmetic/finish portion of rehab (not roof/HVAC/systems).
  Enables the allocation breakdown and the budget-fit check.
- **Cost multiplier** — a *separate axis from tier*: it scales the $/sf cost to
  install (local labor/material), not which finishes. Use `1.3` for a pricey
  metro, `0.85` for low-cost rural. Default 1.0. A market can have a high median
  (high tier) without proportionally high build cost, so set these independently.

Ask for anything missing in **one consolidated question**. If the user gives only
ARV + sqft with no comp tier and no local median, run it on absolute national
bands but flag hard that the tier is a rough guess until they give you the local
median or what the comps carry.

### 2. Run the calculator — for the tier, budget, and guardrails

```bash
python scripts/finish_select.py '<json-input>'
```

The script returns the target tier, the finish $/sf benchmark for that tier, the
budget verdict (under/on/over target), the category allocation, and — the key
output — the **comp guard** (over/under/matched vs the comps). It does **not**
pick materials. See the script docstring for the input schema.

### 3. Fill in the materials from the finish library

Read `references/finish-tiers.md` and pull the recommendation for the target tier
in each category (flooring, paint, kitchen, baths, lighting/fixtures, curb appeal).
Let the buyer profile nudge style choices. This is where the spec gets real.

### 4. Present the finish schedule

Use `templates/finish-schedule.md`. Lead with the tier and the comp-guard verdict,
then the per-category materials spec with the budget alongside each, then the
splurge/save guidance. Keep it handoff-ready — a contractor or designer should be
able to work from it.

### 5. Follow-ups

For what-ifs ("what if I go up a tier", "comps are actually moveup"), re-run with
the change and return a focused delta — the new tier, the new guard verdict, and
which categories change — not the whole schedule.

## Output style

- **Lead with the comp verdict.** Over/under/on-target is the money question.
- **Make the spec actionable.** Name materials and grades, not vibes. "Mid-grade
  quartz, white shaker, subway tile" beats "a nice modern kitchen."
- **Pick one metal-finish story** and carry it across the house — call this out.
- **Respect the budget.** Tie each category to its dollar slice when a budget is given.
- **Flag inference.** If tier came from ARV rather than real comps, say so plainly.
- **Stay in resale lane.** This is what sells the house to a stranger, not what the
  owner would personally love.

## What this skill does NOT do

- It is **not** personal-home interior design. If the user wants to decorate a home
  they'll live in, that's a different job — say so and offer to help conversationally.
- It does not pull comps, ARV, or property data from the web or any service —
  those are user inputs.
- It does not pick materials by itself — the tier/budget/guard come from the
  script, the materials come from the reference, and the final call is the user's.
- It does not estimate full rehab cost (roof, HVAC, systems, structural). Its $/sf
  figures are finish-out only. A separate rehab estimator covers the rest.
- It does not invent ARV or square footage. If either is missing, it asks.

## Reference files

- `references/finish-tiers.md` — the finish library: materials by tier and category
- `scripts/finish_select.py` — the deterministic tier/budget/guard calculator
- `scripts/test_finish_select.py` — regression suite; run before changing calc logic
- `templates/finish-schedule.md` — output template
