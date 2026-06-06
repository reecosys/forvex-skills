# Metrics — KPI Definitions

Every KPI used in the deal one-pager. When a user asks "what is DSCR?" or "how is rehab ratio computed?", answer from here.

---

## Flip metrics (retail, wholetail, wholesale)

### Net Profit
- **Definition:** Predicted sale price minus total cost basis.
- **Why it matters:** The dollar number that actually hits your pocket. The primary metric for flips.
- **Rule of thumb:** HV target is $40,000+. Below $20k, the deal rarely justifies the risk for retail; below $10k for wholesale, the spread is too thin.

### ROI (Return on Investment)
- **Definition:** Net profit / total cost basis × 100.
- **Why it matters:** Percentage return on capital deployed. Lets you compare deals of different sizes.
- **Rule of thumb:** Retail target 25%+, wholetail 15%+, wholesale 25%+.

### Margin
- **Definition:** Net profit / predicted sale price.
- **Why it matters:** Cushion against ARV miss. A 5% margin gets wiped out by a 5% ARV overestimate; an 18% margin tolerates real-world friction.
- **Rule of thumb:** 18%+ is a "high margin" badge. Below 10% is fragile.

### Rehab Ratio
- **Definition:** Rehab cost / net profit.
- **Why it matters:** How much execution risk per dollar of profit. High ratios mean a small rehab overrun erases the deal.
- **Rule of thumb:** Ideal ≤ 0.6 (rehab is less than 60% of profit). Above 1.0, rehab risk dominates.

### Total Cost Basis
- **Definition:** Purchase + rehab + holding + realtor + title + financing + sale fees.
- **Why it matters:** The number on the "money out" side of the ledger. ROI denominator.
- **For wholesale:** rehab is NOT in the basis — the investor-buyer pays for repairs.

### Predicted Sale Price
- **Retail:** ARV × 0.99
- **Wholetail:** ARV × (0.85 + rehab_progress × 0.04)
- **Wholesale:** (ARV − full_rehab) × 0.80
- **Why this matters:** Different strategies discount ARV differently because they trade off speed for net.

### Entry % of ARV
- **Definition:** All-in cost (purchase + rehab + closing) / ARV.
- **Why it matters:** The classic "70% rule" lives here. Below 65% is HV target; above 75% the math gets aggressive.

---

## Rental metrics

### Annual Cashflow
- **Definition:** (Effective income − operating expenses − debt service) × 12.
- **Why it matters:** The dollar number a rental actually produces. Primary rental metric.
- **Rule of thumb:** $3,000/yr ($250/mo) is the HV baseline. Below $100/mo is too thin for capex shocks.

### Cash-on-Cash Return (CoC)
- **Definition:** Annual cashflow / cash invested × 100.
- **Why it matters:** Annual return on the cash you actually put into the deal (down + closing + rehab).
- **Rule of thumb:** 10%+ target; 8% minimum acceptable.

### DSCR (Debt Service Coverage Ratio)
- **Definition:** (Effective income − operating expenses) / monthly debt service.
- **Why it matters:** Lender's view of risk. NOI / debt = how much margin over the mortgage.
- **Rule of thumb:** 1.25+ qualifies for most DSCR loans. Below 1.2, lenders balk. Below 1.0, the rent doesn't cover the loan.

### Cap Rate
- **Definition:** NOI / property value × 100.
- **Why it matters:** Unleveraged yield. Lets you compare against market caps and other asset classes.
- **Note:** redeal computes cap rate with a flexible basis: either down_payment+closing OR full purchase price. Default basis: `down_payment` (a "cash equivalent" cap rate).
- **Rule of thumb:** 6%+ in most markets; 8%+ in cashflow markets.

### NOI (Net Operating Income)
- **Definition:** (Effective income − operating expenses) × 12.
- **Why it matters:** Income before debt. Lender underwriting metric.

### Expense Ratio
- **Definition:** Total operating expenses / effective income.
- **Why it matters:** Quick read on whether operating costs are eating the deal.
- **Rule of thumb:** Below 50% is healthy. Above 50% triggers a `high_expense_ratio` flag.

### Effective Income
- **Definition:** Gross monthly rent − vacancy loss + other income.
- **Why it matters:** What you actually collect, not what you bill.

### Monthly Cashflow
- **Definition:** Effective income − operating expenses − monthly mortgage payment.
- **Why it matters:** Month-to-month cash in pocket.

### Cash Invested (entry capital)
- **Definition:** Down payment + closing costs + rehab.
- **Why it matters:** CoC denominator. The actual money out of pocket to acquire and stabilize.

---

## Cross-strategy / portfolio metrics

### Deal Score (0–10)
- **Definition:** Weighted blend of profit-to-target, ROI-to-target, and a third metric (rehab ratio for flips, DSCR for rentals), with risk and capital-friction penalties.
- **Why it matters:** One-number verdict for ranking deals at a glance.
- **See:** `badges-and-scoring.md` for full formula and weights.

### Risk Score (0–100)
- **Definition:** Composite of market risk (45%), deal-math risk (35%), and execution risk (20%). Higher = riskier.
- **Bands:**
  - 0–25: Low
  - 26–50: Moderate
  - 51–75: Elevated
  - 76–100: High
- **See:** `guardrails.md`.

### Confidence Label
- **`full`** — all critical inputs supplied
- **`partial`** — some inputs defaulted but verdict is reliable
- **`limited`** — significant defaults applied; verdict is directional only

### Buy-Box Fit
- **`fit`** — meets ≥75% of buy-box checks
- **`stretch`** — meets ≥40% or shows near-miss on key metrics
- **`fail`** — meets <40% of checks
- Computed per strategy. See `guardrails.md`.

---

## Metric availability matrix

| Metric | Retail | Wholetail | Wholesale | Rental |
|---|---|---|---|---|
| Net profit | ✓ (primary) | ✓ (primary) | ✓ (primary) | — |
| Annual cashflow | — | — | — | ✓ (primary) |
| ROI | ✓ | ✓ | ✓ | — |
| Cash-on-cash | — | — | — | ✓ |
| Margin | ✓ | ✓ | ✓ | — |
| DSCR | — | — | — | ✓ |
| Cap rate | — | — | — | ✓ |
| Rehab ratio | ✓ | ✓ | ✓ | — |
| Predicted sale | ✓ | ✓ | ✓ | — |
| Total cost basis | ✓ | ✓ | ✓ | ✓ (cash invested) |
| Deal score | ✓ | ✓ | ✓ | ✓ |
| Risk score | ✓ | ✓ | ✓ | ✓ |
| Buy-box fit | ✓ | ✓ | ✓ | ✓ |
