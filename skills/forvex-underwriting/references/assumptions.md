# Assumptions & Default Values

These are the default values to apply when the user doesn't provide an override. Every default applied should be flagged in the output (e.g., `[defaulted]`) so the user knows what to confirm.

Source of truth: `redeal-mobile/app/services/calculator/assumptionsResolver.ts` and `normalizeInputs.ts`. Keep this file in sync if the redeal defaults change.

**Precedence order** (highest wins):

1. User input this turn
2. `my-buy-box.md` from project knowledge (per-franchisee overrides)
3. `forvex-frame.md` (HV-default targets and proprietary tables)
4. This file (calculation defaults)

---

## Rental strategy defaults

| Variable | Default | Notes |
|---|---|---|
| Vacancy rate | 5% | of gross monthly rent |
| Property management | 10% | of gross monthly rent |
| Maintenance | 5% | of gross monthly rent |
| CapEx reserve | 5% | of gross monthly rent |
| Property tax | 0.85% | of purchase price, annual |
| Insurance | 0.4% | of purchase price, annual |
| Down payment | 20% | of purchase price |
| Loan rate | 7.0% | annual, fixed |
| Loan term | 30 years | 360 months |
| Other income | $0 | parking, laundry, etc. |
| Utilities (owner-paid) | $0 | typical SFR; bump for multifamily |

### Fixed closing costs (rental)
| Item | Amount |
|---|---|
| Title fees | 0.4% of purchase price |
| Inspection | $500 |
| Appraisal | $600 |
| Lender fees | 2.0% of loan amount (points + origination) |
| Attorney | $800 |
| Recording | $200 |
| Other | $900 |

---

## Flip strategy defaults

### Holding periods
| Strategy | Months |
|---|---|
| Retail flip | 3 |
| Wholetail | 2 |
| Wholesale | 1 |
| Assignment | 0 |
| BRRRR stabilization | 6 (rehab + lease-up + seasoning) |

### Sale price targeting
| Strategy | Sale % | Notes |
|---|---|---|
| Retail flip | 99% of ARV | small discount for sale friction |
| Wholetail | 85% base + up to 4% uplift | uplift scales with `partial_rehab / full_rehab` |
| Wholesale | 80% of (ARV − full_rehab) | investor pays rehab themselves |
| Assignment | n/a — flat fee | bounded by wholesale spread (see `calculations.md`) |

### Realtor fees
| Strategy | Fee | Applied to |
|---|---|---|
| Retail flip | 6% (regular) | predicted sale price |
| Wholetail | 4% (discount) | predicted sale price |
| Wholesale | 4% (discount) | predicted sale price |
| Assignment | 0% | no closing |

### Holding costs (monthly during holding period)
- Tax: `(purchase_price × 0.85%) / 12`
- Insurance: `(purchase_price × 0.4%) / 12`
- Utilities: $0 default (adjust per market; common values $150–300/mo for vacant SFR)

Total holding cost = `(tax + insurance + utilities) × holding_months`

### Title fees
- Default 0.4% of purchase price
- Wholesale double-close variant pays both sides (× 2)
- Assignment: no title (assignor doesn't close)

### Sale fees
- **HV franchise transaction fee**: per franchise level + type schedule (see `forvex-frame.md`)
- Other sale fees: ~0.2% of sale price
- Marketing: $500 flat (retail flip only)

---

## HV franchise transaction fee schedule

Replaces the prior flat `transaction_fee_rate`. The fee is computed from the franchisee's level + type, captured in onboarding and stored in `my-buy-box.md`.

**Full franchise (% of sale price):**

| Level | Fee |
|---|---|
| 1 | 3.00% |
| 2 | 2.00% |
| 3 | 1.50% |
| 4 | 1.25% |
| 5 | 1.00% |
| 6 | 0.80% |

**Associate franchise:** add 2.00% to the level fee. (A Level 1 Associate pays 3.0% + 2.0% = 5.0%.)

**Default when buy-box absent:** Level 4 Full (1.25%) — mid-table fallback. Output flags this as defaulted.

This fee materially affects deal economics — a Level 1 Associate (5%) vs. Level 6 Full (0.8%) on a $200,000 sale price is the difference between $10,000 and $1,600 in fees per deal. Always resolve this from the buy-box.

---

## Capital posture

**Default for fresh analysis: `hard_money`** (HV bias — most franchisees lean on hard money for flips).

| Posture | Annual rate | Points | Notes |
|---|---|---|---|
| `cash` | 0% | 0% | no financing cost |
| `loc` (line of credit) | 7.0% | 0% | franchise's internal cost of capital — cash-equivalent timing, but reflects opportunity cost |
| `company` | 8.0% | 0% | internal HV / partner capital |
| `hard_money` | 12.0% | 2% of financed basis | one-time points + monthly interest |

Formula:
- Interest = `(financed_basis × annual_rate / 12) × holding_months`
- Points = `financed_basis × points_rate` (hard money only)
- Total financing cost = Interest + Points

**Per-franchisee overrides (opt-in inputs):**

- `hm_rate` — override hard-money interest rate (e.g., 0.10 for a senior franchisee at 10%). Default 0.12.
- `hm_points` — override hard-money points (e.g., 0.01 for 1 point). Default 0.02.
- `lender_ltv_cap` — fraction of ARV the HM lender will finance (e.g., 0.70). When set:
  - `financed_basis = min(purchase + rehab, arv × lender_ltv_cap)`
  - `cash_overlay = max(0, (purchase + rehab) − arv × lender_ltv_cap)` — out-of-pocket cash the franchisee must bring on top of the loan
  - Interest and points accrue on `financed_basis` only
  - When `lender_ltv_cap` is unset (default), full basis is financed (legacy behavior preserved for existing fixtures)

The calculator output surfaces `cash_overlay` per flip strategy and a top-level `cash_overlay` summary with `max_overlay` and `by_strategy` breakdown. The appointment-prep brief shows the cap line and the per-strategy overlay at the target offer so the franchisee sees their real cash exposure, not just the loan-side math.

For wholesale double-close variant: holding period for financing is 0 (simultaneous closing), so financing cost is just the points (hard money only).

For assignment: posture is irrelevant (no capital deployed).

---

## Assignment defaults

| Variable | Default | Notes |
|---|---|---|
| Target assignment fee | $15,000 | overridable per franchisee via buy-box |
| Earnest money | $1,000 | capital at risk |
| Marketing / admin | $500 | per-deal direct-mail + admin overhead |
| Investor buffer | $10,000 | minimum profit the investor expects to net |

**Spread-bounded fee:** the assignment fee can't exceed `(wholesale_predicted_sale − purchase × 1.02) − investor_buffer`. If the spread doesn't support the target fee, the calculator uses the smaller feasible fee and raises a `Spread Limits Fee` warning.

---

## BRRRR defaults

| Variable | Default | Notes |
|---|---|---|
| Refi LTV | 75% | of post-rehab ARV |
| Refi rate | 7.5% | DSCR loan, slightly above 30yr purchase rate |
| Refi term | 30 years | |
| Refi closing costs | 2.5% of new loan + $600 appraisal | title + lender + appraisal |
| Stabilization period | 6 months | rehab + lease-up + seasoning |
| Entry posture | cash | most BRRRRs entered all-cash or LOC during stabilization |
| Target cash left in deal | $5,000 | "successful BRRRR" — refi recovers nearly all of initial cash |

**Mechanics:** Phase 1 (buy + rehab + stabilize) is all-cash or LOC. Phase 2 (refi) places a new mortgage and pulls out cash. Phase 3 (hold) is long-term rental against the refi loan. The defining metric is `cash_left_in_deal = phase1_investment − cash_recovered_at_refi`. If `cash_left ≤ 0`, the calculator surfaces `infinite_return: true` and the `BRRRR Recoverable` signal fires.

DSCR is computed against the **post-refi** loan payment, not a hypothetical 80% LTV purchase loan. This is the lender's view at refi time.

---

## Time-adjusted metrics

All flip strategies now emit two derived values alongside ROI:

- **`annualized_roi`** = `roi × (12 / holding_months)` — lets you compare a 1-month wholesale at 30% ROI to a 3-month flip at 25% ROI on equal footing
- **`profit_per_month`** = `net_profit / holding_months` — useful for capital-velocity comparisons

These don't change the verdict; they're informational. Surface them when comparing strategies side-by-side or when the user asks "which is better?"

---

## Target metrics (HV defaults)

These are the targets used when the buy-box doesn't override them. Per-user overrides come from `my-buy-box.md`.

| Strategy | Metric | Target |
|---|---|---|
| Assignment | Net fee | $15,000 |
| Wholesale | Net profit | $15,000 |
| Wholesale | ROI | 25% |
| Wholetail | Net profit | $25,000 |
| Wholetail | Margin | 15% |
| Retail flip | Net profit | $40,000 |
| Retail flip | Margin | 18% |
| All flips | ROI | 25% |
| All flips | Entry % of ARV | ≤ 65% (all-in) |
| Rental | Cash-on-cash | 10% |
| Rental | DSCR | 1.25 |
| Rental | Annual cashflow | $3,000 |
| Rental | Monthly cashflow | $250 |

---

## Pre-Offer Number (HV walk-in number)

The Pre-Offer is the simple number a franchisee walks into an appointment with — distinct from the precise underwriting MAO.

```
Pre-Offer base = ARV × 65%        # purchase ceiling, repairs NOT subtracted
```

**Important distinction — two different "65% rules":**

| Rule | Formula | Used for |
|---|---|---|
| **Pre-Offer** (this) | `purchase / ARV ≤ 65%` | The walk-in number; purchase ceiling only |
| **Buy-box entry** (`target_entry_pct_arv`) | `(purchase + rehab + closing) / ARV ≤ 65%` | All-in guardrail in scoring/fit |

They share the 65% figure but apply it to different bases. The Pre-Offer is purchase-only and is therefore a *higher, simpler* number — the franchisee subtracts repairs in their head (or via the tier estimate below) during the appointment.

### Repair estimation for the Pre-Offer

The franchisee handles repairs one of two ways:

1. **On-site** (default) — walk in with the base number, subtract observed repairs mentally. No paper math.
2. **Pre-estimate by $/sqft tier** — before the appointment, pick a condition tier (`light` | `medium` | `heavy` | `gut`). Rates and pre-offer math are server-authoritative — see `recontrol/lib/mcp/underwrite/nativeEngine.ts` (`DEFAULTS.rehab_per_sqft`). When MCP is connected, pass `rehab_tier` + sqft into `forvex_underwrite` and use the returned `pre_offer` block; do not duplicate tier $/sqft figures here.

`Pre-Offer adjusted = (ARV × 65%) − repair estimate`

These tier rates are coarse walk-in estimates, not line-item rehab budgets. The detailed rehab input for underwriting strategies is separate.

The calculator emits a `pre_offer` block with `base`, `repairs_estimate`, `repair_source`, and `adjusted`. The skill shows the base as the primary walk-in number and the adjusted as "if repairs run ~$X."

---

## Verdict thresholds by risk appetite

Captured per franchisee in `my-buy-box.md` (`risk_appetite`). Default: `balanced`.

| Risk appetite | BUY threshold | NEGOTIATE threshold |
|---|---|---|
| Conservative | deal_score ≥ 8.0 | ≥ 6.0 |
| Balanced | deal_score ≥ 7.0 | ≥ 5.0 |
| Aggressive | deal_score ≥ 6.0 | ≥ 4.0 |

A BUY also requires `fit` on buy-box and no critical warnings (negative_profit, negative_cashflow).

---

## Market risk by property location type

Captured per deal or inferred from address. Drives the `market_risk` component of risk scoring.

| Location type | Market risk default |
|---|---|
| Urban | 0.5 (neutral) |
| Suburban | 0.5 (neutral) |
| Rural | 0.65 (elevated — exit-liquidity and comp-thinness concerns) |

State-specific tax/insurance overrides are still applied separately when known.

---

## State-specific overrides (apply when address known)

These override the national defaults above for accuracy:

- **Texas**: property tax often 2.0–2.5% (vs. 0.85% default)
- **Florida**: insurance often 0.8–1.2% (vs. 0.4% default), higher in coastal counties
- **New Jersey / Illinois**: property tax often 1.5–2.2%
- **California**: insurance often higher in fire zones; property tax capped at ~1.1% by Prop 13

When the address indicates one of these markets, override the rate and flag it. (These are factual corrections, not "market posture biases.")

---

## When to ask for an override vs. accept default

**Always ask** if missing:
- Address (or at least zip)
- Purchase price
- ARV
- Rehab estimate

**Default silently and flag** if missing:
- Rent (use 1% rule as placeholder, mark `[1% rule]`)
- Condition (default `moderate`)
- Property tax / insurance rates (use national defaults above)
- Financing posture (default `hard_money` per HV bias; offer to re-run with cash/loc)
- Franchise level/type (default L4 Full at 1.25%; prompt user to run `forvex-onboarding`)
- Location type (default `suburban` if uncertain)

**Never default** without flagging:
- Anything that meaningfully shifts the verdict by more than $5,000 in profit
- Anything that flips a strategy from "buy box fit" to "fail"

---

## Versioning

The calculator emits `calc_version` (semver) in every result. Bump rules:

- **Patch (0.2.x)** — bug fix, no behavior change for inputs that pass regression tests
- **Minor (0.x.0)** — new fields added, new strategy, new default values that may shift outputs
- **Major (1.0.0+)** — breaking change to JSON schema or removed fields

Snapshot baselines live in `scripts/test_underwrite.py`. Run before any calculator change:

```
python3 scripts/test_underwrite.py
```

All 10 fixtures must pass. When the math intentionally changes, bump `__version__` in `underwrite.py` and update fixture snapshots in the same commit.

---

## TODOs

- **Leveraged ROI** — current ROI uses total cost basis (faithful to redeal). When financed, this understates true cash-on-cash return. Future work: surface both "raw ROI" (current) and "leveraged ROI" (net profit / cash actually deployed) for flips, especially under hard money.
- **State-specific overrides as data** — currently documented in prose; ideally a lookup table the script reads.
- **Per-state attorney fees** — TX uses title companies (no attorney), NY/NJ/IL require attorneys ($1,500+).
- **Multi-period IRR** — `annualized_roi` is a flat extrapolation; true IRR for BRRRR (which has cashflows in periods 0, 6, and ongoing) would be more accurate.
