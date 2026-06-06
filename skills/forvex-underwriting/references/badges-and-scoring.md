# Signals, Warnings & Scoring

Replaces the prior "badges-and-scoring" model. Two cleanly-separated concepts now:

- **Signals** — positive, sparse, high-information. Fire above thresholds the deal score doesn't already convey.
- **Warnings** — negative, decision-relevant, always shown when triggered. Fire below risk thresholds.

**Rule of thumb: a strategy never fires a Signal AND a Warning on the same dimension.** They're opposite sides of a threshold gap with a neutral middle zone where neither fires. If you see redundancy, it's a documentation bug — flag it.

Source of truth: `redeal-mobile/app/services/calculator/{dealScore,badges,riskScore}.ts`.

---

## Deal Score (0–10)

Same formula as before, applies per strategy.

### Formula

```
base_score = (
    profit_score × w_profit +
    roi_score    × w_roi +
    third_score  × w_third
) × 10

final_score = clamp(base_score − (0.5 × num_warnings), 0, 10)
```

`final_score` is rounded to one decimal.

### Weights by strategy

| Strategy | profit | roi | third |
|---|---|---|---|
| **Assignment** | 1.0 | — | — (single dimension; just fee vs target) |
| Wholesale | 0.30 | 0.50 | 0.20 (rehab ratio) |
| Wholetail | 0.40 | 0.40 | 0.20 (rehab ratio) |
| Retail flip | 0.50 | 0.30 | 0.20 (rehab ratio) |
| Rental | 0.50 | 0.30 | 0.20 (DSCR) |

### Component scores (each 0–1)

- **profit_score** = clamp(net_profit / target_profit, 0, 1)
- **roi_score** = clamp(roi / target_roi, 0, 1) (flips) or clamp(coc / target_coc, 0, 1) (rental)
- **third_score (flip)** = if rehab_ratio ≤ 0.6 → 1.0, else clamp(0.6 / rehab_ratio, 0, 1)
- **third_score (rental)** = if dscr ≥ 1.25 → 1.0, else clamp(dscr / 1.25, 0, 1)

### Display tag

- **9.0–10.0:** "Strong"
- **7.0–8.9:** "Good"
- **5.0–6.9:** "Neutral"
- **3.0–4.9:** "Weak"
- **0.0–2.9:** "Pass"

### Global / headline deal score

The maximum of the five per-strategy deal scores. Tiebreaker: fit, then absolute profit. See `calculations.md`.

---

## Signals (positive)

These fire above their thresholds and add information the deal score alone doesn't convey. Kept intentionally small — over-badging clutters the output. Compute every applicable signal.

| Signal | Trigger | Why it's independently useful |
|---|---|---|
| **Strong Spread** | wholesale net_profit ≥ $15,000 | Highlights strategy-specific opportunity even when other strategies are weak |
| **High Margin** | retail margin ≥ 18% | Tolerance for ARV miss — different info than profit/score |
| **Cash Flow Positive** | rental monthly_cashflow > $0 | Fast mobile glance: "is the rental viable?" |
| **DSCR > 1.2** | rental dscr > 1.2 | Lender-qualifying read — relevant even if cashflow is thin |
| **Multi-Strategy Fit** | 2+ strategies score ≥ 7 | The rare deal that works multiple ways — strategic flexibility |
| **Buy-Box Match** | recommended strategy has `fit` on every buy-box check | Cleaner than per-check display |

### Removed (versus prior iteration)

These badges were dropped because they restated facts the deal score already encoded:

- ~~Rehab Light~~ (just "rehab is low")
- ~~Low Holding Risk~~ (just "holding cost is low")
- ~~Wholetail Friendly~~ (just "wholetail rehab is low")
- ~~Strong Buyer Spread~~ (tier-down of Strong Spread; redundant)
- ~~ARV Sensitive~~ (this is a confidence-label concern, not a signal)

### Display

Render inline on the deal one-pager:

```
🟢 Strong Spread · High Margin · Buy-Box Match
```

(Drop the emoji if user prefers no-emoji per buy-box.)

Order: positive strategy signals first, then rental signals, then meta signals (Multi-Strategy Fit, Buy-Box Match).

---

## Warnings (negative)

Always shown when triggered. Lower-cased phrasing. Per-strategy warnings appear in the strategy card; deal-level warnings (critical) appear in the headline.

### Critical (gate the verdict — never BUY when triggered on the recommended strategy)

| Warning | Trigger |
|---|---|
| `negative_profit` | net_profit < 0 |
| `negative_cashflow` | rental monthly_cashflow < 0 |

### Important (surface in the risk section)

| Warning | Trigger |
|---|---|
| `thin_margin` | 0 < flip margin < 10% |
| `thin_assignment` | assignment effective fee < $5,000 |
| `spread_limited` | assignment effective fee < target fee (deal doesn't support buy-box) |
| `low_dscr` | rental dscr < 1.2 |
| `high_rehab` | rehab_ratio exceeds strategy threshold (retail/wholetail >1.0/1.2, wholesale >0.8) |
| `high_expense_ratio` | rental expense_ratio > 50% |
| `arv_missing` | ARV not supplied — confidence will be `limited` |

### Informational (surface in details)

| Warning | Trigger |
|---|---|
| `low_roi` | strategy ROI below threshold |
| `low_coc` | rental cash_on_cash < 8% |
| `low_cashflow` | rental monthly_cashflow < $100 |

Display: lowercase, comma-separated. Example: `thin margin, low DSCR (1.18)`.

---

## Risk Score (0–100)

Separate axis from deal score. Deal score answers "how good is the math?" Risk score answers "how likely is reality to break it?"

### Formula

```
risk = 100 × clamp(
    0.45 × market_risk +
    0.35 × deal_math_risk +
    0.20 × execution_risk,
    0, 1
)
```

### Components

**Market risk (0–1)** — from `location_type` (urban/suburban/rural) and external market data when MCP is available. Defaults to 0.5 (neutral) for urban/suburban, 0.65 for rural. See `assumptions.md`.

**Deal math risk (0–1)** — combination of:
- Profit shortfall = 1 − clamp(net_profit / target_profit, 0, 1)
- ROI shortfall = 1 − clamp(roi / target_roi, 0, 1)
- Third-metric shortfall (rehab or DSCR gap)
- Entry aggressiveness = clamp((entry_pct_arv − 0.65) / 0.10, 0, 1)

**Execution risk (0–1)** — from warnings, weighted:
- `negative_profit` / `negative_cashflow`: 0.30
- `thin_margin`: 0.15
- `thin_assignment`: 0.20
- `low_dscr` / `low_coc`: 0.10–0.15
- `arv_missing`: 0.20
- `high_rehab`: 0.15

Sum, clamp to 1.0.

### Risk label

| Score | Label |
|---|---|
| 0–25 | Low |
| 26–50 | Moderate |
| 51–75 | Elevated |
| 76–100 | High |

### Confidence

- **`limited`** — missing ARV or purchase price; outputs are directional only
- **`partial`** — partial market posture or missing rehab estimate; rent defaulted via 1% rule
- **`full`** — all critical inputs supplied

---

## Verdict — driven by deal score + risk appetite

Verdict thresholds come from `risk_appetite` in the buy-box (default `balanced`). See `assumptions.md` for the table.

| Risk appetite | BUY ≥ | NEGOTIATE ≥ |
|---|---|---|
| Conservative | 8.0 | 6.0 |
| Balanced | 7.0 | 5.0 |
| Aggressive | 6.0 | 4.0 |

**BUY** also requires:
- Recommended strategy has `fit` (not stretch or fail)
- No critical warnings (negative_profit, negative_cashflow)

**NEGOTIATE** comes with a target offer price (computed MAOs at buy-box targets).

**PASS** when neither threshold is met OR critical warnings on the best strategy.

---

## Display rules

1. **One headline number** — global deal score. Don't show the per-strategy breakdown unless asked.
2. **Signals are independent of deal score** — show them all, but they shouldn't restate the score.
3. **Warnings always shown** — they're decisions, not vanity.
4. **No signal/warning overlap on the same dimension** — never show "High Margin" badge AND "Thin Margin" warning on the same strategy.
5. **Risk + deal score both shown** — a deal can have a high score AND high risk (aggressive but profitable). Both are decision-relevant.
