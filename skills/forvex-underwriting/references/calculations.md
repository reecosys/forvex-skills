# Calculations — Per-Strategy Formulas

Source of truth: `redeal-mobile/app/services/calculator/{rental,retailFlip,wholetail,wholesale,costStack}.ts`. The script `scripts/underwrite.py` implements these formulas. This file is for reference and verification.

## Two engines, five strategies

Redeal historically had two calculation engines:

- **Flip engine** — used by Assignment, Wholesale, Wholetail, Retail Flip. Computes a single transaction outcome (predicted sale − total cost basis = net profit). The four flip strategies differ in holding period, sale % of ARV, what's included in the cost basis (rehab in/out), and the realtor + franchise fee posture.
- **Rental engine** — used by Rental only. Computes monthly cashflow, debt service coverage, and returns on cash invested. Different metric shape entirely (cashflow per month, CoC, DSCR, cap rate).

The script keeps four explicit flip functions (one per strategy) for auditability rather than a single config-driven function. They share helpers (`build_holding_costs`, `build_financing_costs`, `build_sale_fees`, `realtor_fee`, `title_fee`) which is where the engine reuse lives.

---

## Shared formulas

### Monthly mortgage payment (amortization)

```
P × (r × (1+r)^n) / ((1+r)^n − 1)

where:
  P = principal (loan amount)
  r = monthly rate = annual_rate / 12
  n = total payments = years × 12
```

### Holding cost (per month, during holding period)

```
monthly_tax        = (purchase_price × property_tax_rate) / 12
monthly_insurance  = (purchase_price × insurance_rate) / 12
monthly_utilities  = utilities_amount (default 0)

holding_cost_total = (monthly_tax + monthly_insurance + monthly_utilities) × holding_months
```

### Financing cost (during holding period)

```
if posture == "cash":
    financing_cost = 0

if posture == "loc":
    interest = ((purchase + rehab) × 0.07 / 12) × holding_months
    financing_cost = interest        # no points

if posture == "company":
    interest = ((purchase + rehab) × 0.08 / 12) × holding_months
    financing_cost = interest

if posture == "hard_money":
    interest = ((purchase + rehab) × 0.12 / 12) × holding_months
    points   = (purchase + rehab) × 0.02
    financing_cost = interest + points
```

For wholesale double-close: holding_months = 0 for financing (simultaneous close), so financing_cost = points only (hard money) or 0 (cash / loc / company).

### Sale fees

```
franchise_fee   = sale_price × franchise_fee_pct(level, type)
other_fee       = sale_price × 0.002   (0.2%)
marketing       = 500 if strategy == retail_flip else 0

sale_fees_total = franchise_fee + other_fee + marketing
```

Where `franchise_fee_pct(level, type)`:
- Level 1: 3.0% / Level 2: 2.0% / Level 3: 1.5% / Level 4: 1.25% / Level 5: 1.0% / Level 6: 0.8%
- Associate franchise adds 2.0%

### Realtor fee

```
if strategy == retail_flip:
    realtor_fee = sale_price × 0.06   (regular 6%)
elif strategy in {wholesale, wholetail}:
    realtor_fee = sale_price × 0.04   (discount 4%)
else:  # assignment
    realtor_fee = 0
```

### Title fee

```
title_fee = purchase_price × 0.004   (0.4%)
```

For wholesale double-close: title is paid on both sides (× 2).
For assignment: no title (assignor doesn't close).

---

## Strategy: Assignment

The assignor controls the contract and assigns it to an investor for a flat fee. No closing, no holding, no rehab.

### Inputs
- `purchase_price`, `arv`, `full_rehab`
- `assignment_fee` (target, default $15,000)
- `earnest_money` (default $1,000)
- `assignment_marketing` (default $500)
- `assignment_investor_buffer` (default $10,000 — minimum profit the investor expects)

### Computation

```
# Estimate what an investor could net if they took the deal direct
wholesale_predicted   = 0.80 × max(0, arv − full_rehab)
investor_rough_costs  = purchase × 1.02
rough_wholesale_net   = wholesale_predicted − investor_rough_costs

# Cap the fee at what the investor will accept
max_feasible_fee      = max(0, rough_wholesale_net − investor_buffer)
effective_fee         = min(target_fee, max_feasible_fee)

cost_basis            = earnest_money + marketing
net_profit            = effective_fee − marketing
roi                   = (net_profit / cost_basis) × 100
```

### Warnings
- `negative_profit` if net_profit < 0
- `thin_assignment` if effective_fee < $5,000
- `spread_limited` if effective_fee < target_fee (the deal doesn't support the franchisee's target)

---

## Retail Flip

### Inputs
- `purchase_price`, `arv`, `full_rehab`
- `holding_months` (default 3)
- `posture` (default `hard_money`)
- `arv_realization_pct` (default 99%)
- `franchise_level`, `franchise_type` (drive transaction fee)

### Computation

```
predicted_sale = arv × 0.99

holding_costs   = build_holding_costs(purchase_price, 3 months)
realtor_fee     = predicted_sale × 0.06
title_fee       = purchase_price × 0.004
financing_costs = build_financing_costs(purchase + rehab, posture, 3 months)
sale_fees       = build_sale_fees(predicted_sale, marketing=500,
                                  franchise_level=level, franchise_type=type)

total_cost_basis = purchase + rehab + holding_costs + realtor_fee +
                   title_fee + financing_costs + sale_fees

net_profit       = predicted_sale − total_cost_basis
roi              = (net_profit / total_cost_basis) × 100
margin           = net_profit / predicted_sale
rehab_ratio      = rehab / max(net_profit, 1)
```

### Warnings
- `negative_profit` if net_profit < 0
- `low_roi` if roi < 10%
- `high_rehab` if rehab_ratio > 1
- `thin_margin` if 0 < margin < 10%

---

## Wholetail

### Inputs
- `purchase_price`, `arv`, `full_rehab`, `partial_rehab` (default 55% of full)
- `holding_months` (default 2)
- `posture`
- `franchise_level`, `franchise_type`

### Computation

```
rehab_progress = min(partial_rehab / full_rehab, 1)
sale_pct       = min(1.0, 0.85 + rehab_progress × 0.04)
predicted_sale = arv × sale_pct

holding_costs   = build_holding_costs(purchase, 2 months)
realtor_fee     = predicted_sale × 0.04   (discount)
title_fee       = purchase × 0.004
financing_costs = build_financing_costs(purchase + partial_rehab, posture, 2 months)
sale_fees       = build_sale_fees(predicted_sale, franchise_level=level, franchise_type=type)

total_cost_basis = purchase + partial_rehab + holding_costs + realtor_fee +
                   title_fee + financing_costs + sale_fees

net_profit       = predicted_sale − total_cost_basis
roi              = (net_profit / total_cost_basis) × 100
margin           = net_profit / predicted_sale
rehab_ratio      = partial_rehab / max(net_profit, 1)
```

### Warnings
- `negative_profit`, `low_roi` (< 15%), `high_rehab` (ratio > 1.2), `thin_margin` (< 10%)

---

## Wholesale (possession or double-close)

Take possession (default) or do a simultaneous double-close. Sell as-is to an investor — investor pays rehab.

> Note: previously this strategy carried an `assignment` variant. Assignment is now its own strategy because capital, holding, and risk profiles differ materially.

### Inputs
- `purchase_price`, `arv`, `full_rehab`
- `holding_months` (default 1; 0 for double-close)
- `posture`
- `wholesale_variant`: `possession` (default) or `double_close`
- `franchise_level`, `franchise_type`

### Computation (possession)

```
predicted_sale = 0.80 × (arv − full_rehab)

holding_costs   = build_holding_costs(purchase, 1 month)
realtor_fee     = predicted_sale × 0.04
title_fee       = purchase × 0.004
financing_costs = build_financing_costs(purchase, posture, 1 month)   # repairs not in basis
sale_fees       = build_sale_fees(predicted_sale, franchise_level, franchise_type)

total_cost_basis = purchase + holding_costs + realtor_fee +
                   title_fee + financing_costs + sale_fees
# NOTE: repairs NOT included — investor pays.

net_profit       = predicted_sale − total_cost_basis
roi              = (net_profit / total_cost_basis) × 100
margin           = net_profit / predicted_sale
rehab_ratio      = full_rehab / max(net_profit, 1)
```

### Computation (double_close)

Same as possession with:
- `holding_months = 0`
- `holding_costs = 0`
- `financing_costs = points only` if posture is hard_money (no monthly interest)
- `title_fee × 2` (both sides)

### Warnings
- `negative_profit`, `low_roi` (< 25%), `high_rehab` (ratio > 0.8)

---

## Rental (long-term hold)

### Inputs
- `purchase_price`, `monthly_rent`, `full_rehab` (optional)
- `partial_rehab` (rent-ready cost; default 55% of full_rehab — same rule as wholetail)
- `down_payment_pct` (default 20%), `loan_rate` (default 7%), `loan_term_years` (default 30)

### Rehab posture
Rentals only need **rent-ready** condition (working mechanicals, safe, clean, leasable) — not retail-grade finish. The engine uses `partial_rehab` as the entry rehab cost, not `full_rehab`. This is the Wiggle Room reveal: a deal that scores mediocre as a flip can score strong as a rental purely because the cost basis drops.

### Computation

```
# Loan
loan_amount     = purchase_price × (1 − down_pct)
monthly_payment = amortize(loan_amount, loan_rate, loan_term_years)

# Closing costs
title         = purchase_price × 0.004
inspection    = 500
appraisal     = 600
lender_fee    = loan_amount × 0.02     # 2% — points + origination
attorney      = 800
recording     = 200
other         = 900
closing_total = title + inspection + appraisal + lender_fee + attorney + recording + other

cash_invested = (purchase_price × down_pct) + closing_total + partial_rehab

# Income
gross_monthly_rent = monthly_rent
vacancy_loss       = gross_monthly_rent × 0.05
effective_income   = gross_monthly_rent − vacancy_loss + other_income

# Expenses (monthly)
monthly_tax        = (purchase_price × 0.0085) / 12
monthly_insurance  = (purchase_price × 0.004) / 12
maintenance        = gross_monthly_rent × 0.05
management         = gross_monthly_rent × 0.10
capex              = gross_monthly_rent × 0.05
utilities          = 0 (owner-paid, default)
total_expenses     = monthly_tax + monthly_insurance + maintenance + management + capex + utilities

# Cashflow
monthly_cashflow   = effective_income − total_expenses − monthly_payment
annual_cashflow    = monthly_cashflow × 12

# Returns
noi               = (effective_income − total_expenses) × 12
cap_rate_basis    = down_payment + closing_total  (cash-equivalent basis)
cap_rate          = (noi / cap_rate_basis) × 100
cash_on_cash      = (annual_cashflow / cash_invested) × 100
dscr              = (effective_income − total_expenses) / monthly_payment
expense_ratio     = total_expenses / effective_income
```

### Warnings
- `negative_cashflow`, `low_cashflow` (< $100), `low_coc` (< 8%), `low_dscr` (< 1.2), `high_expense_ratio` (> 50%)

---

## Cross-strategy sanity checks

After computing all five:

1. **Wholesale profit should be much smaller than retail profit** for any reasonable deal. If wholesale > retail, something is off (likely rehab estimate too high or ARV too low).
2. **Wholetail should sit between wholesale and retail** on most metrics.
3. **Assignment should be smaller than wholesale net profit** in absolute terms — assignment captures a slice of the wholesale spread, not the whole thing. If assignment > wholesale net, the `spread_limited` cap isn't working.
4. **Rental cashflow being deeply negative while flip profit is strong** = legitimate flip-only deal. Flag it explicitly.
5. **All five strategies losing money** = PASS. The skill recommends PASS and refuses to "find a way to make it work."

---

## Tiebreak when multiple strategies hit max deal score

Sort order:
1. Higher `deal_score`
2. Better `fit` (fit > stretch > fail)
3. Higher absolute net profit / annual cashflow

Last tiebreaker matters when deep-spread deals max out scores across multiple strategies — the highest-dollar option wins by default. Per-franchisee `primary_strategy` from buy-box can override this in the future (TODO).
