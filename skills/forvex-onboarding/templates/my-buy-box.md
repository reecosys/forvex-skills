# My Buy-Box

> This file is an export snapshot of your server-side buy-box.
> If MCP is unavailable, you can save it to Claude Project knowledge as `my-buy-box.md` for offline fallback.
> Re-run the `forvex-onboarding` skill to update the canonical server state.

**Generated:** {DATE}
**Version:** 1

---

## Identity & franchise

- **Name:** {NAME}
- **Franchise:** {FRANCHISE_NAME}
- **Franchise type:** {FRANCHISE_TYPE}
- **Franchise level:** {FRANCHISE_LEVEL}
- **Transaction fee rate:** **{FRANCHISE_FEE_PCT}%** ({FRANCHISE_TYPE} Level {FRANCHISE_LEVEL})
- **Markets:** {MARKETS}
- **Experience:** {YEARS_EXPERIENCE} years
- **Volume:** ~{DEALS_PER_WEEK} deals analyzed/week, ~{DEALS_CLOSED_PER_MONTH} closed/month

## Market context

- **Typical property market types:** {TYPICAL_MARKET_TYPES}
- **Market flags / special handling:**
{MARKET_FLAGS_LIST}

## Strategy mix

- **Strategies I run:** {STRATEGIES_ACTIVE}
- **Primary focus:** {PRIMARY_STRATEGY}
- **Strategies I exclude:** {STRATEGIES_EXCLUDED}

## Buy-box targets

### Assignment
- Target fee: ${TARGET_ASSIGNMENT_FEE}

### Wholesale
- Min net profit: ${TARGET_PROFIT_WHOLESALE}

### Wholetail
- Min net profit: ${TARGET_PROFIT_WHOLETAIL}
- Min margin: {TARGET_MARGIN_WHOLETAIL}%

### Retail flip
- Min net profit: ${TARGET_PROFIT_RETAIL}
- Min margin: {TARGET_MARGIN_RETAIL}%

### All flips
- Min ROI: {TARGET_ROI_FLIP}%
- Max entry % of ARV (all-in): {TARGET_ENTRY_PCT_ARV}%

### Rental
- Min annual cashflow: ${TARGET_CASHFLOW_ANNUAL}
- Min DSCR: {TARGET_DSCR}
- Min cash-on-cash: {TARGET_COC}%

### BRRRR
- Max cash left in deal after refi: ${TARGET_BRRRR_CASH_LEFT}
- Typical refi LTV: {BRRRR_REFI_LTV}%
- Min annual cashflow (post-refi): ${TARGET_BRRRR_CASHFLOW_ANNUAL}

## Capital posture

- **Capital mix:** {CAPITAL_MIX_CASH}% cash / {CAPITAL_MIX_LOC}% LOC / {CAPITAL_MIX_COMPANY}% company / {CAPITAL_MIX_HM}% hard money
- **LOC internal cost of capital:** {LOC_INTERNAL_RATE}%
- **Max rehab:** ${MAX_REHAB}
- **Max holding (flip):** {MAX_HOLDING_MONTHS} months

### Hard money terms (if HM is in the mix)

- **HM interest rate:** {HM_RATE}%
- **HM points:** {HM_POINTS}
- **HM LTV cap (lender finances up to this fraction of ARV):** {LENDER_LTV_CAP}%

### Disposition costs

- **Retail listing fee:** {LISTING_FEE_PCT_RETAIL}%
- **Wholetail listing fee:** {LISTING_FEE_PCT_WHOLETAIL}%

### Dollar profit floor

- **Minimum dollar profit per deal (across strategies):** ${PROFIT_FLOOR_USD} *(optional — leave blank to let ROI thresholds govern alone)*

## Risk & verdict

- **Risk appetite:** {RISK_APPETITE}
- **BUY threshold:** deal score ≥ {BUY_THRESHOLD}
- **NEGOTIATE threshold:** deal score ≥ {NEGOTIATE_THRESHOLD}

## Voice & framing

- **Output style:** {OUTPUT_STYLE}
- **Emoji:** {USE_EMOJI}
- **Vocabulary rules:**
{VOCABULARY_RULES_LIST}

## Hard constraints

{HARD_CONSTRAINTS_LIST}

## Market-specific overrides

> The skill defaults assume national averages (property tax 0.85%, insurance 0.4%). Document any market-specific overrides here:

{MARKET_OVERRIDES}

---

## How the underwriting skill uses this file

When `forvex-underwriting` runs in a project containing this file:

1. **Franchise type + level resolve the transaction fee** applied to every sale-side calculation
2. **Targets override the forVEX defaults** in deal scoring and buy-box-fit
3. **Strategies excluded are suppressed** from outputs
4. **Voice preferences shape the output** — terse vs detailed, emoji on/off, vocabulary rules
5. **Risk appetite shifts the verdict thresholds** — conservative requires higher deal score for BUY
6. **Max rehab / max holding trigger warnings** when exceeded
7. **Hard constraints surface as guardrails** — the skill flags or forces PASS on violations
8. **Market-specific overrides** replace defaults for properties in those markets
9. **Capital mix biases the default posture** for first-pass analysis
10. **LOC internal rate** is used when posture = `loc` instead of forVEX default 7%
