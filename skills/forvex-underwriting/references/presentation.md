# Presentation Rules

How to render the output. The template lives in `templates/deal-one-pager.md`. This file explains the rules behind it.

---

## Design constraints

- **Primary target: iPhone Claude chat.** Optimize for narrow screens. Tables with 2–4 columns work; 6+ columns break.
- **Markdown only.** No HTML widgets, no JS, no live recalculation. Use markdown tables, `<details>` blocks (which Claude renders), headers, and short bullets.
- **Scannable in 5 seconds.** A franchisee in a driveway should see the verdict and headline number without scrolling.
- **Auditable.** The math behind the verdict must be visible (or one tap away in a `<details>` block).

---

## Required sections, in order

1. **Headline block** — Address, verdict, best strategy, deal score
2. **Badge row** — Global badges as comma-separated tags
3. **Property block** — ARV, purchase, rehab, condition, confidence label
4. **Strategy comparison table** — All four strategies side by side
5. **Recommended strategy** — One paragraph plus a compact cost breakdown
6. **Other strategies** — Each in a `<details>` block, collapsed
7. **Risk + guardrails** — Risk score, label, any flags
8. **State nuances** — Governed per-state caveats (only when out-of-area / caveats present)
9. **MAO / sensitivity** — Compact "if you'd accept X, max offer is Y" line(s)
10. **Suggested follow-ups** — 3 prompts the user can tap-paste

---

## Headline block

```
**123 Main St, Dallas TX**
Verdict: **BUY** · Best strategy: **Wholetail** · Deal Score: **7.8 / 10**
```

- **BUY** in bold (uppercase).
- **NEGOTIATE** with a parenthetical target price: `NEGOTIATE (target ≤ $145,000)`.
- **PASS** with one-line reason: `PASS — wholesale margin too thin, no rental path`.

---

## Badge row

Inline, separated by `·` (middot):

```
🟢 Strong Spread · High Margin · Cash Flow Positive · DSCR > 1.2
```

If the user has indicated they prefer no emoji, drop the colored circle. Plain text works fine.

---

## Property block

```
| | |
|---|---|
| ARV | $215,000 |
| Purchase | $135,000 |
| Rehab (full) | $32,000 |
| Condition | Moderate |
| Confidence | full |
```

Two-column tables read well on iPhone.

When `server_context.property.parcel` (or `forvex_get_property.parcel`) is present, add rows rather than inventing a second property story:

```
| Last sale | Warranty Deed · Arm's-Length · yes |
| Winning debt | $218,000 (mortgages) |
| Physicals | attached · slab · none |
```

Match on `code`; speak `label` / `class`. Omit a row when that inner is null. Never treat null `recorded_lien_balance` as $0 owed.

---

## Strategy comparison table

```
| Strategy | Primary | Secondary | Score | Fit |
|---|---|---|---|---|
| Retail Flip | $42,800 profit | 18.4% margin | 7.8 | fit |
| Wholetail | $38,200 profit | 19.1% margin | 7.6 | fit |
| Wholesale | $14,600 profit | 8.7% margin | 5.2 | stretch |
| Rental | $3,840/yr cashflow | 11.2% CoC | 7.1 | fit |
```

- **Primary metric** is what the strategy is judged on (profit for flips, cashflow for rental).
- **Secondary metric** is the most useful supporting number (margin for flips, CoC for rental).
- **Score** with 1 decimal.
- **Fit** lowercase: `fit`, `stretch`, `fail`.

---

## Recommended strategy paragraph

Always one paragraph, 2–4 sentences. Cover:

- Why this strategy and not the others (1 sentence)
- The headline math: predicted sale, basis, profit, margin (1 sentence)
- The key risk or watchpoint (1 sentence)
- The recommended action: BUY at current price, or NEGOTIATE to a target (1 sentence)

Example:

> Wholetail edges out retail here because the discount realtor fee and shorter hold offset the lower sale price, and the buyer profile is wider. At a 87% ARV sale ($187,050) against a $164,800 total basis, you net $22,250 with an 11.9% margin. Watch the partial rehab scope creep — staying under $18k is what makes the math work. Recommend offer at $135,000 or below.

---

## Compact cost breakdown

Format varies by strategy. Use the right one for the recommended strategy.

### Flip strategies (Retail / Wholetail / Wholesale)

```
| | |
|---|---|
| Predicted sale | $187,050 |
| − Purchase | $135,000 |
| − Partial rehab | $18,000 |
| − Holding costs | $2,300 |
| − Realtor (4%) | $7,482 |
| − Title (0.4%) | $540 |
| − Financing | $0 (cash) |
| − Franchise fee (0.8%) | $1,496 |
| − Other sale fees | $375 |
| **= Net profit** | **$22,419** |
| ROI | 13.6% (54.4% annualized over 3mo) |
| Margin | 12.0% |
```

### Assignment

```
| | |
|---|---|
| Assignment fee | $15,000 |
| − Marketing / admin | $500 |
| **= Net profit** | **$14,500** |
| Earnest at risk | $1,000 |
| Spread-limited? | No (target fee feasible) |
```

### Rental

```
| | |
|---|---|
| Monthly rent | $1,650 |
| − Vacancy (5%) | −$82.50 |
| = Effective income | $1,567.50 |
| − Tax + insurance | −$140.62 |
| − Maint / mgmt / capex (20%) | −$330.00 |
| − Debt service (P&I) | −$718.53 |
| **= Monthly cash flow** | **$378.35** |
| Annual cash flow | $4,540 |
| NOI (annual) | $13,163 |
| DSCR | 1.53 |
| Cash-on-cash | 7.02% |
| Cash invested (down + closing + rehab) | $64,700 |
```

### BRRRR

Three-phase format reflecting the buy → refi → hold lifecycle.

```
**Phase 1 — Buy, Rehab, Stabilize (6 months)**
| | |
|---|---|
| Purchase | $80,000 |
| + Rehab | $30,000 |
| + Closing | $720 |
| + Holding (6mo) | $844 |
| + Financing during stabilization | $0 (cash) |
| **= Initial cash deployed** | **$111,564** |

**Phase 2 — Refi at 75% LTV of ARV**
| | |
|---|---|
| New loan amount | $135,000 |
| − Refi closing costs (2.5% + appraisal) | −$3,975 |
| **= Cash recovered** | **$131,025** |

**Phase 3 — Hold (long-term rental against refi loan)**
| | |
|---|---|
| Cash left in deal | −$19,461 (infinite return — recovered everything) |
| Monthly cashflow post-refi | $245 |
| Annual cashflow | $2,940 |
| DSCR | 1.34 |
```

Always end the breakdown with the bolded primary metric for that strategy.

---

## Other strategies in `<details>`

```html
<details>
<summary>Retail Flip — $42,800 profit, 7.8 score, fit</summary>

| | |
|---|---|
| Predicted sale | $212,850 |
| − Purchase | $135,000 |
| − Full rehab | $32,000 |
| − Holding (3mo) | $3,450 |
| − Realtor (6%) | $12,771 |
| − Title | $540 |
| − Financing | $0 |
| − Sale fees | $1,490 |
| **= Net profit** | **$27,599** |
| ROI | 15.0% |
| Margin | 13.0% |

</details>
```

One `<details>` block per non-recommended strategy. Summary line: `<strategy> — <primary metric>, <score>, <fit>`.

---

## Risk + guardrails

```
**Risk: 38 / 100 — Moderate** · Confidence: full

⚠️ thin margin · low DSCR (1.18)
```

- Risk score, label, confidence on one line.
- Flags as comma-separated items on the next line. Lowercase.
- Use ⚠️ only if user hasn't opted out of emoji.

If no flags: write `No risk flags raised.`

---

## State nuances

The engine's `server_context.state_rules` carries a **governed** per-state operational brief from the canonical `core.state_rules` table (severity, closing authority, disclosure regime, deed convention, license, assignment/double-close posture) plus a ready-to-render `caveats[]` array.

**This is the source of truth for state law. Do NOT freelance state-specific commentary** (special-warranty deed conventions, non-disclosure comp posture, attorney-close requirements, licensing) from your own knowledge — render the governed `caveats` instead. If `state_rules` is absent (MCP down, or no state resolved), say so plainly rather than inventing it.

**When to show this section:**
- The subject is **out-of-area** (not the franchisee's home market), OR
- `state_rules.caveats` is non-empty.

Skip it silently for in-market deals with no caveats (don't add noise to a routine local underwrite).

```
**State nuances — TX** (severity: GREEN)

- Non-disclosure state — public sale prices are unreliable; lean on MLS-sold / ChatARV / BPO for ARV and treat comp confidence as reduced.
- Special Warranty is a standard arm's-length resale deed here — SW comps are kept, not treated as distress.
```

- Header: `**State nuances — {state}**` with the `severity` in parentheses when present.
- List each string in `caveats[]` verbatim as a bullet — they are already plain-language and franchisee-facing.
- For **attorney-close** states, the caveat already flags the fee/timeline; when the recommended path is assignment, echo it once in the MAO line too ("attorney-close adds fee + days").
- Keep it tight — bullets only, no paragraph.

---

## MAO / Sensitivity

Always include for NEGOTIATE verdicts. Optional for BUY (helpful but not required).

```
**Max offers (at target metrics):**
- Retail at 25% ROI → $128,000
- Wholetail at 18% margin → $131,500
- Wholesale at $15k profit → $112,000
- Rental at 1.25 DSCR → $142,000
```

If the user asked a what-if, replace this section with the focused mini-output for the changed variable.

---

## Suggested follow-ups

End every deal with 3 prompts the user can tap-paste:

```
**Ask me:**
- "What if rent is $1,500 instead of $1,650?"
- "Show me hard money on the retail flip."
- "Draft a counter at $128,000."
```

Vary the prompts based on what's interesting about *this* deal. If the rental was the close call, lean rental what-ifs. If financing was a key driver, lean financing variants.

---

## Default flags

Any time a default was applied, flag it at the bottom in a small block:

```
*Defaults applied: rent ($1,500, 1% rule) · property tax (0.85%) · financing (cash). Confirm to refine.*
```

Italicized, small, easy to skim past, but present.

---

## What NOT to do

- **Don't repeat the inputs back in prose** — the property block already shows them.
- **Don't say "the deal looks good" without numbers.** Always anchor to specific values.
- **Don't show all four cost breakdowns expanded.** Recommended only; others collapsed.
- **Don't include the deal score formula in the output** unless asked.
- **Don't apologize for missing data.** State the confidence label and move on.
- **Don't suggest follow-ups the skill can't actually handle.** Match the prompts to capabilities.
