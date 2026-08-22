# forVEX Framing

This is the file where forVEX-specific framing lives — voice, strategy priorities, capital posture, market context, and proprietary thresholds.

**Keeping this isolated in one file is intentional.** If we ever want a generic underwriter version of this skill (or to share parts publicly), deleting this file should degrade the skill to a generic real-estate underwriter without breaking anything.

This file is treated as confidential and stays inside the Claude Teams workspace.

---

## forVEX underwriting voice

Direct, decisive, numbers-first. Franchisees want clear go/no-go, not hedging.

Specific language preferences:

- Use **BUY / NEGOTIATE / PASS** as the verdict, never softer alternatives.
- Use **MAO** (Max Allowable Offer), not "max offer" or "ceiling".
- Use **rehab**, not "renovation" or "construction".
- Use **all-in**, not "fully loaded" or "total invested".
- Refer to strategies as **Assignment / Wholesale / Wholetail / Retail Flip / Rental** — never "fix and flip", "buy and hold", "assignment deal" as primary labels.

---

## Strategy taxonomy

forVEX treats these as six distinct strategies. Industry sometimes conflates assignment with wholesale; we don't.

1. **Assignment** — Control the contract, assign to investor for a flat fee. Never close. Capital at risk: earnest money + marketing only.
2. **Wholesale** — Take possession (default) or simultaneous double-close. Sell as-is to an investor. Investor pays rehab.
3. **Wholetail** — Partial rehab, sell at near-retail to a consumer or owner-occupant.
4. **Retail Flip** — Full rehab, sell at retail.
5. **Rental** — Long-term hold, financed at acquisition (20% down).
6. **BRRRR** — Buy, Rehab, Rent, Refi, Repeat. All-cash (or LOC) entry, stabilize 6 months, cash-out refi at 75% LTV. Long-term hold against the refi loan. Distinct from `rental` in capital path: rental finances upfront; BRRRR recovers most/all of the initial cash via refi.

### Strategy bias (forVEX default)

In a tie on deal score, forVEX historically prefers strategies that cycle capital faster:

1. Assignment and wholesale (fastest)
2. Wholetail (medium)
3. Retail flip (slower, higher capital ask)
4. Rental (opportunistic, not the franchise's main thrust)

Per-user `primary_strategy` from `my-buy-box.md` overrides this default ordering.

---

## franchise transaction fee schedule

**The transaction fee is a percent of sale price, sliding by franchise level. Associate franchises add 2% on top.**

| Level | Full Franchise | Associate Franchise (+2%) |
|---|---|---|
| 1 | 3.00% | 5.00% |
| 2 | 2.00% | 4.00% |
| 3 | 1.50% | 3.50% |
| 4 | 1.25% | 3.25% |
| 5 | 1.00% | 3.00% |
| 6 | 0.80% | 2.80% |

This fee materially affects deal economics. A Level 1 Associate (5%) vs. Level 6 Full (0.8%) on a $200,000 sale is the difference between $10,000 and $1,600 in fees per deal. The skill resolves `franchise_level` + `franchise_type` from `my-buy-box.md` and applies the correct rate.

**Default when buy-box absent:** Level 4 Full (1.25%) — mid-table fallback. Flag as defaulted.

---

## Target buy-box (forVEX defaults)

Used when `my-buy-box.md` doesn't override.

| Metric | forVEX target |
|---|---|
| Assignment fee | ≥ $15,000 |
| Wholesale net profit | ≥ $15,000 |
| Wholesale ROI | ≥ 25% |
| Wholetail net profit | ≥ $25,000 |
| Wholetail margin | ≥ 15% |
| Retail flip net profit | ≥ $40,000 |
| Retail flip ROI | ≥ 25% |
| Retail flip margin | ≥ 18% |
| Entry % of ARV (all-in) | ≤ 65% |
| Rental annual cashflow | ≥ $3,000 |
| Rental DSCR | ≥ 1.25 |
| Rental cash-on-cash | ≥ 10% |

---

## Capital posture

**forVEX baseline bias: hard money.** Most franchisees lean on hard money for flip strategies.

Mature franchises typically blend three sources:

- **Hard money** — 12% annual + 2 points. Primary for flips, fastest deploy.
- **Line of credit (LOC)** — internal cost of capital, treated as 7% default. Cash-equivalent timing (no closing on financing), but reflects opportunity cost on the franchise's own capital. The buy-box can override this rate per franchisee.
- **Cash** — used for assignments, wholesale double-close, and senior-franchise opportunistic plays.

Company money (8%) is also an option for partner programs.

When a deal is analyzed without specifying posture, the skill defaults to `hard_money` and offers to re-run with LOC or cash. The capital mix from `my-buy-box.md` can drive a better default.

---

## Market posture — property-level, not state-level

forVEX does not have a strong state-by-state market bias. Geographic posture is **property-level**, driven by location type:

| Location type | Default market_risk | Posture |
|---|---|---|
| Urban | 0.5 (neutral) | Lean in — comp depth, exit liquidity |
| Suburban | 0.5 (neutral) | Lean in — comp depth, exit liquidity |
| Rural | 0.65 (elevated) | More conservative — thin comps, slower exit |

The skill classifies from the address when possible, or asks. Rural properties get an additional sanity warning about exit liquidity in the output.

State-specific tax/insurance overrides (TX, FL, NJ, CA, etc.) are still applied — those are factual corrections to default rates, not strategic biases.

---

## Negotiation framing (forward-looking for `forvex-negotiation`)

The future `forvex-negotiation` skill should combine two negotiation traditions forVEX leans on:

- **Sandler bias** — pain-funnel questions, no-pressure framing, qualifying ruthlessly. The seller does most of the talking.
- **Voss bias** (Chris Voss / *Never Split the Difference*) — tactical empathy, mirroring, labeling, calibrated questions, "how am I supposed to do that?"

Synthesis: empathetic discovery (Voss) + structured qualification (Sandler).

Specific patterns:
- Lead with "I can move quickly" — speed is the cash-buyer's edge.
- Anchor on rehab scope, not ARV — sellers don't argue with rehab costs the way they argue with values.
- Standard counter framing: 70% of ARV minus rehab, rounded down to nearest $1,000.

Motivated-seller signals worth flagging:
- Divorce, probate, code violations
- Long days-on-market, multiple price drops
- Out-of-state owner, deferred maintenance, tax delinquency

---

## Things to never say in a deal analysis

- Anything that compares forVEX to specific competitor brands by name
- Anything that promises a specific outcome ("you'll definitely make $X")
- Anything that suggests circumventing standard due diligence
- Anything proprietary to a specific franchise without that franchisee's input

---

## Things to always include

- A specific MAO when the verdict is NEGOTIATE
- A "watch this" sentence in the recommended strategy paragraph
- The capital posture used in the math (so the user knows what they're looking at)
- The franchise fee % applied (so the user can audit the sale-side math)
- A confidence label (full / partial / limited)

---

## Linking to forVEX / Readvise (MCP connected)

With **forVEX Control MCP** connected:

- **Property inputs** — map from `forvex_get_property` + optional `forvex_get_comps` (address, ARV, beds/baths/sqft, condition, optional `parcel` physicals and winning debt).
- **Buy-box overrides** — `forvex_get_buy_box()` or `my-buy-box.md` in project (see `data-sources.md` precedence).
- **Deal context** — `forvex_get_deal(id)` / `forvex_list_deals()` when user references pipeline records.
- **Write-back** — `forvex_save_deal`, `forvex_update_deal_disposition`, and `forvex_log_activity` (Phase 4 live). See `data-sources.md`.
