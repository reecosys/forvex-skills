# Rehab Estimate Output Template

Use this structure. Lead with the number and the band; keep cosmetic and
big-ticket visibly separate. Fill from the `scripts/rehab_light.py` JSON. Don't
show these comments to the user.

---

# Light Rehab Estimate: {address or "this property"}

**~${expected_cost}** (range ${range_low}–${range_high}) · **${expected_psf}/sf**
{condition} condition · {finish_level} finish

<!-- One framing sentence, e.g. "Ballpark for a moderate cosmetic refresh at mid
finishes — a screening number, not a contractor bid." -->

## Cosmetic work — ${cosmetic_subtotal}

| Item | Cost |
|---|---|
<!-- one row per cosmetic_breakdown entry -->
| Interior paint | $6,000 |
| Flooring | $10,800 |
| … | … |

## Big-ticket systems — ${big_ticket_subtotal}

<!-- Only if big_ticket_items is non-empty. List each with its cost and source
("your number" vs "rough placeholder — verify"). If empty, write:
"None flagged — keep this in mind, a roof or HVAC surprise changes everything." -->

| System | Cost | |
|---|---|---|
| Roof replacement | $9,000 | rough — verify |

+ Contingency ({contingency_pct}%): ${contingency}

## Read on the scope

> {scope_note}

<!-- If flags.beyond_light_rehab is true, make this prominent: the systems push
this past a light rehab; treat the number as a screen and get a line-item bid. -->

*{limitations}*

**Try a what-if:**
- "What if it needs a new roof?"
- "Rerun at rental-grade finishes"
- "I'm in a high-cost market — use 1.3x"
