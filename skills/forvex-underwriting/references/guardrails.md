# Guardrails — Rules of Thumb, Warnings, Buy-Box Fit

Source of truth: `redeal-mobile/app/services/calculator/buyBoxFit.ts` and risk-flag thresholds embedded in each strategy calculator.

This file defines the warnings and "don't let the user shoot themselves in the foot" checks. The skill should:

1. **Apply guardrails silently** during the math (they're computed in the script).
2. **Surface them prominently** in the output when triggered.
3. **Never override the math** to avoid an uncomfortable verdict.

---

## Precedence chain — buy-box drives guardrails

When `my-buy-box.md` is present in project knowledge, its values override forVEX defaults for **scoring AND guardrails**, not just scoring. Specifically:

| Buy-box field | Affects |
|---|---|
| `target_profit_*` | Deal score thresholds, MAO solver |
| `target_roi_*`, `target_margin_*` | Deal score, buy-box-fit checks |
| `target_dscr`, `target_coc`, `target_cashflow_annual` | Rental scoring + fit |
| `target_entry_pct_arv` | Buy-box-fit entry check |
| `max_rehab` | Triggers warning when exceeded |
| `max_holding_months` | Triggers warning when exceeded |
| `risk_appetite` | Shifts BUY/NEGOTIATE verdict thresholds |
| `hard_constraints` (flood, urban-only, etc.) | Automatic PASS on violation |
| `franchise_level`, `franchise_type` | Computes transaction fee for sale-fee math |
| `strategies_excluded` | Suppresses excluded strategies from the comparison table |
| `assignment_fee` (target) | Used as `target_fee` in assignment math |
| `loc_internal_rate` | Overrides default 7% for LOC posture |

---

## Buy-Box Fit

Each strategy is evaluated against a set of soft checks. Pass count determines fit:

| Pass rate | Label |
|---|---|
| ≥ 75% | **fit** |
| ≥ 40% (or some pass + near-miss) | **stretch** |
| < 40% | **fail** |

### Assignment buy-box check

- Assignment effective fee ≥ target_assignment_fee → `fit`
- Within 10% of target → `stretch`
- Otherwise `fail`

### Flip buy-box checks (retail, wholetail, wholesale)

| Check | Default threshold | Direction |
|---|---|---|
| Net profit ≥ target | varies by strategy | higher better |
| Entry % ≤ soft threshold | 65% (target), 70% (near-miss) | lower better |
| Margin ≥ 10% | | higher better |

### Rental buy-box checks

| Check | Default threshold | Direction |
|---|---|---|
| Annual cashflow ≥ target | $3,000 | higher better |
| DSCR ≥ 1.2 | | higher better |
| Cash-on-cash ≥ target | 10% | higher better |
| Monthly cashflow ≥ $100 | | higher better |

### "Near-miss" rule

A check that fails by ≤ 10% counts as a half-pass for the purpose of `stretch` classification.

---

## Hard constraints from buy-box

Captured during onboarding. The skill must enforce these — they take precedence over the math.

| Constraint type | Behavior when matched |
|---|---|
| `no_flood_zones` (or similar wording) | PASS verdict if `forvex_get_flood_data` returns `in_sfha = true` |
| `only_brick`, `only_2_story`, etc. | Prompt user to confirm before producing analysis |
| `max_rehab: $X` | Warning when proposed rehab > X; if rehab > 1.5× X, recommend PASS |
| `max_holding_months: N` | Warning on strategies with holding > N months |
| `strategies_excluded: [...]` | Drop those strategies from the comparison entirely |
| `markets_only: [Dallas, ...]` | Warning when address is outside listed markets |

When a hard constraint triggers a forced PASS, the output must explain *which constraint and why*.

---

## Verdict gating

| Condition | Verdict |
|---|---|
| Best score ≥ `risk_appetite.buy_threshold` AND no critical warnings AND `fit` | **BUY** |
| Best score ≥ `risk_appetite.negotiate_threshold` AND no critical warnings | **NEGOTIATE** (with target offer) |
| Any critical warning (negative_profit, negative_cashflow) on best strategy | **PASS** |
| Any matched hard constraint with PASS-level severity | **PASS** (with constraint cited) |
| Best score below NEGOTIATE threshold | **PASS** |

Risk appetite thresholds (from `assumptions.md`):

| | Conservative | Balanced | Aggressive |
|---|---|---|---|
| BUY | 8.0 | 7.0 | 6.0 |
| NEGOTIATE | 6.0 | 5.0 | 4.0 |

When **NEGOTIATE**, the skill must compute and show the MAO (Max Allowable Offer) that would shift the deal to BUY status.

---

## MAO (Max Allowable Offer)

For each strategy, MAO is the purchase price at which the deal hits the target profit.

### Retail flip MAO

```
target_profit = target_profit_retail
predicted_sale = ARV × 0.99
franchise = franchise_fee_pct(level, type)
sale_side_fees = predicted_sale × (0.06 + franchise + 0.002) + 500

MAO ≈ (predicted_sale − rehab − sale_side_fees − target_profit) / 1.0071
```

### Wholesale MAO

```
target_profit = target_profit_wholesale
predicted_sale = 0.80 × (ARV − rehab)
franchise = franchise_fee_pct(level, type)
sale_side_fees = predicted_sale × (0.04 + franchise + 0.002)

MAO ≈ (predicted_sale − sale_side_fees − target_profit) / 1.005
```

### Rental MAO

Binary search for the purchase price at which DSCR = 1.25 (or buy-box target).

### Assignment MAO

Not meaningful as a purchase-price input — assignment fee feasibility is the constraint. The skill should instead show the spread analysis (rough wholesale net minus investor buffer = max feasible fee).

---

## Out-of-area / remote underwriting posture

**Out-of-market is NOT a refusal condition. Underwrite it.** The marketplace lane is inherently remote — captured leads and out-of-state assignments are the point, not the exception. Do not gate, refuse, or hedge into a non-answer just because the property is outside a home market (e.g. Louisville). Every deal stands on its own comps + market read; do not anchor to a familiar market's numbers.

Underwrite out-of-area **with coverage caveats, not a refusal**:

- **Directional confidence.** Lean on the `confidence` label (limited / partial / full) to carry uncertainty — that is exactly what it is for. A thin out-of-area comp set means `partial`/`limited`, not "I can't tell you."
- **No boots on the ground.** Add a one-line "remote read — not seen in person; condition/rehab are estimates, verify before hard offer" note. State it once; don't apologize repeatedly.
- **Governed state law, not guesswork.** Render `server_context.state_rules.caveats` (the **State nuances** section — see `presentation.md`) for deed convention, disclosure regime, closing authority, and licensing. Do not freelance state specifics.
- **Debt dual-read.** Winning debt is `server_context.property.parcel.debt.balance` when `source` is `liens` or `mortgages`. Null `recorded_lien_balance` is not $0 owed. Do not recompute payoff from last sale when `parcel.debt` exists.
- **Coverage flags from the data.** Surface comp-thinness, rural exit-liquidity, and market-risk from `forvex_get_market_intelligence` / comp verdict — as flags that shape the read, not as reasons to decline.
- **Say what would sharpen it.** If a local inspection / BPO / agent walk-through would materially change confidence, name that as the next step — after giving the number, not instead of it.

The bar: a franchisee working a remote assignment gets a real verdict + offer with honest caveats, the same as a local deal.

---

## "Refuse to underwrite" conditions

The skill produces an explicit refusal-and-question instead of an analysis when:

1. **ARV missing AND no zip/market data** — too little to default.
2. **Rehab is more than 50% of ARV** — likely a teardown; recommend separate "land value" analysis.
3. **Purchase price > ARV** — almost certainly an input error. Confirm before proceeding.
4. **Rehab estimate < $5,000 on a SFR** — likely under-scoped.
5. **Rent estimate > 2% of purchase** — likely too optimistic.

In each case, ask one clarifying question, then proceed once answered. **Being out-of-area is not on this list** — it is a caveat posture (above), never a refusal.

---

## Sanity warnings (always check, don't change verdict)

- **High entry %** — All-in cost > 75% of ARV. "Aggressive entry."
- **Long holding period inflates carrying cost** — Show what each extra month costs.
- **Hard money on a thin deal** — If posture = hard_money and margin < 12%, show "rate sensitivity high."
- **Rent assumed at 1% rule** — Flag prominently if rent was defaulted.
- **Property tax / insurance defaulted** — Flag the state-specific risk (e.g., "TX tax may be 2.5%, not 0.85%").
- **Franchise fee defaulted** — Flag if no level/type supplied; suggest running `forvex-onboarding`.
- **Rural property** — Note exit-liquidity and comp-thinness; market_risk default is 0.65.

---

## Things to never do

- **Never recommend BUY on a deal that requires the user to "just be optimistic" about ARV or rent.** If the inputs are aggressive, say so.
- **Never hide a negative profit or cashflow** by averaging across strategies.
- **Never "find a way to make it work"** by stretching defaults beyond reasonable bounds.
- **Never override a buy-box hard constraint** even when the math is otherwise excellent.
- **Never invent values.** If something critical is missing, ask.
- **Never produce a verdict more confident than the data supports.** Use the confidence label honestly.
- **Never refuse (or hedge into a non-answer) just because a deal is outside a home market.** Out-of-area is a caveat posture, not a refusal — give the verdict + offer with honest coverage flags.
