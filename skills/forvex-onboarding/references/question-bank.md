# Question Bank — Onboarding Interview

Every question the onboarding skill might ask, with rationale and acceptable answer formats. The `SKILL.md` orchestrates which to ask; this file is the canonical text.

When a user answers in an unexpected format, normalize it and confirm back ("got it — $35k minimum profit, yes?").

---

## Category 1: Identity & franchise

### Q1. Name
**Ask:** "First — what should I call you in deal outputs?"
**Captures:** `name` (string)

### Q2. Franchise / market name
**Ask:** "What's the franchise / business name? (e.g., 'HomeVestors of Dallas-Fort Worth')"
**Captures:** `franchise_name` (string)

### Q3. Franchise type
**Ask:** "Are you a Full Franchise or Associate Franchise?"
**Captures:** `franchise_type` (`full` | `associate`)
**Why:** Associate franchises pay an additional 2% on the transaction fee. Material to every deal's economics.

### Q4. Franchise level
**Ask:** "What's your franchise level? 1, 2, 3, 4, 5, or 6?"
**Captures:** `franchise_level` (int 1–6)
**Why:** Drives the transaction fee per HV schedule.

**Confirmation back:** After capturing Q3 + Q4, compute and confirm:
- Full Franchise: L1=3.0%, L2=2.0%, L3=1.5%, L4=1.25%, L5=1.0%, L6=0.8%
- Associate Franchise: add 2.0%

Example: "Got it — Level 4 Full Franchise = 1.25% transaction fee."

### Q5. Primary market(s)
**Ask:** "Which markets do you operate in? List up to 3 — metro and state."
**Captures:** `markets` (list of {city, state})
**Why:** Drives market-specific tax/insurance defaults and attorney-fee conventions.

### Q6. Years in business
**Ask:** "How many years have you been doing this?"
**Captures:** `years_experience` (int)

---

## Category 2: Market context

### Q7. Typical market type
**Ask:** "Are your typical properties urban, suburban, rural, or a mix?"
**Captures:** `typical_market_types` (list of `urban` / `suburban` / `rural`)
**Why:** Drives default market_risk per deal. Rural defaults to 0.65; urban/suburban to 0.5.

### Q8. Deal volume
**Ask:** "Roughly how many deals do you analyze per week, and how many close per month?"
**Captures:** `deals_analyzed_per_week`, `deals_closed_per_month` (ints)
**Why:** High-volume users want terser outputs.

### Q9. Markets to flag
**Ask:** "Any markets, neighborhoods, or zip codes you'd like to flag for special handling? (flood-prone areas, rapidly-appreciating zips, places to avoid)"
**Captures:** `market_flags` (free-text list)

---

## Category 3: Strategy mix

### Q10. Strategies run
**Ask:** "Which strategies do you actually run? Pick all that apply: assignment, wholesale, wholetail, retail flip, rental, brrrr."
**Captures:** `strategies_active` (list)
**Note:** BRRRR (Buy-Rehab-Rent-Refi-Repeat) is distinct from rental — different capital path. BRRRR enters all-cash/LOC, stabilizes 6 months, refis at 75% LTV.

### Q11. Primary strategy
**Ask:** "Of those, which is your bread and butter?"
**Captures:** `primary_strategy` (one of the above)
**Why:** Tie-breaker when two strategies score similarly.

### Q12. Strategies avoided
**Ask:** "Any strategies you flat-out won't do?"
**Captures:** `strategies_excluded` (list)
**Why:** Suppress those strategies entirely from outputs.

---

## Category 4: Buy-box targets — Flips

### Q13. Assignment fee target
**Ask:** "Assignment — target fee per deal?"
**Default:** $15,000
**Captures:** `target_assignment_fee` (int)

### Q14. Wholesale profit minimum
**Ask:** "Wholesale — minimum net profit per deal you'd accept?"
**Default:** $15,000
**Captures:** `target_profit_wholesale` (int)

### Q15. Wholetail profit + margin
**Ask:** "Wholetail — minimum net profit AND minimum margin? (defaults: $25k, 15%)"
**Default:** $25,000 / 15%
**Captures:** `target_profit_wholetail`, `target_margin_wholetail`

### Q16. Retail flip profit + margin
**Ask:** "Retail flip — minimum net profit AND minimum margin? (defaults: $40k, 18%)"
**Default:** $40,000 / 18%
**Captures:** `target_profit_retail`, `target_margin_retail`

### Q17. Flip ROI + entry %
**Ask:** "Across all flips: minimum ROI and max all-in cost as % of ARV?"
**Default:** 25%, 65%
**Captures:** `target_roi_flip`, `target_entry_pct_arv`

---

## Category 5: Buy-box targets — Rental

### Q18. Annual cashflow minimum
**Ask:** "Rental — minimum annual cashflow?"
**Default:** $3,000
**Captures:** `target_cashflow_annual` (int)

### Q19. DSCR minimum
**Ask:** "Minimum DSCR you'll accept? Most DSCR lenders want 1.25+."
**Default:** 1.25
**Captures:** `target_dscr` (float)

### Q20. Cash-on-cash minimum
**Ask:** "Minimum cash-on-cash return?"
**Default:** 10%
**Captures:** `target_coc` (%)

### Q21. BRRRR — max cash left in deal
**Ask:** "If you do BRRRR, what's the most cash you're willing to leave in a deal after refi? ($0 is ideal — 'infinite return'; $5k is comfortable; $20k means it didn't really work.)"
**Default:** $5,000
**Captures:** `target_brrrr_cash_left` (int)
**Why:** The defining BRRRR metric. If refi recovers nearly all capital, you can redeploy into the next deal. If $20k+ is stuck in the deal, it's effectively a slow rental, not a BRRRR.

### Q22. BRRRR — typical refi LTV
**Ask:** "What LTV do your lenders typically give on cash-out refi for stabilized investment properties?"
**Default:** 75%
**Captures:** `brrrr_refi_ltv` (%)
**Why:** Drives how much cash gets pulled back at refi. Most DSCR lenders cap at 75%; some go to 80% for strong-DSCR properties.

---

## Category 6: Capital posture

### Q21. Capital mix
**Ask:** "Capital mix — what % of your deals run on: cash, line of credit (LOC), company money, hard money?"
**Default:** 100% hard_money (HV bias)
**Captures:** `capital_mix` ({cash, loc, company, hard_money} as percentages summing to 100)
**Why:** Lets us pre-run analysis with the right financing posture without asking each time.

### Q22. LOC internal rate
**Ask:** "If you use line of credit, what's your internal cost of capital — the rate the franchise charges itself? (HV default: 7%)"
**Default:** 7%
**Captures:** `loc_internal_rate` (%)
**Why:** LOC is cash-equivalent for timing (no closing on financing) but carries an opportunity cost. Varies by franchise maturity.

### Q23. Max rehab budget
**Ask:** "What's the largest rehab you'd take on? Dollar amount."
**Default:** $80,000
**Captures:** `max_rehab` (int)

### Q24. Max holding period
**Ask:** "Max holding period you'd tolerate for a flip, in months?"
**Default:** 6 months
**Captures:** `max_holding_months` (int)

---

## Category 7: Risk & verdict

### Q25. Risk appetite
**Ask:** "Overall risk appetite: conservative, balanced, or aggressive? This adjusts the verdict thresholds — conservative requires a higher deal score for BUY."
**Default:** balanced
**Captures:** `risk_appetite` (enum)

Thresholds applied:
- Conservative: BUY 8.0+, NEGOTIATE 6.0+
- Balanced: BUY 7.0+, NEGOTIATE 5.0+
- Aggressive: BUY 6.0+, NEGOTIATE 4.0+

---

## Category 8: Voice & framing

### Q26. Output style
**Ask:** "Output style — terse (bullets only), balanced (current default), or detailed (full explanations)?"
**Default:** balanced
**Captures:** `output_style` (enum)

### Q27. Emoji
**Ask:** "Emoji in outputs — yes or no?"
**Default:** no
**Captures:** `use_emoji` (bool)

### Q28. Vocabulary preferences
**Ask:** "Any specific phrases to use or avoid? (e.g., 'always say MAO not max offer', 'never use BRRRR', 'call them flips not rehabs')"
**Captures:** `vocabulary_rules` (list of strings)

---

## Category 9: Hard constraints

### Q29. Anything else
**Ask:** "Anything else the skill should know? Hard constraints, market quirks, things to flag."

Examples to suggest:
- "I never touch flood zones"
- "I only buy brick exteriors"
- "Property tax in my market runs 2.3%, not 0.85%"
- "I require a 4-month minimum hold for tax reasons"
- "I refuse deals with active code violations"

**Captures:** `hard_constraints` (free-text list)

---

## Notes for interview pacing

- 29 questions sounds like a lot, but most batches are 3-question sets the user can answer in one message. Skip rental batch if not active. Realistic time: 15–20 minutes.
- If the user fatigues, offer to use HV defaults for remaining questions.
- **Always confirm the franchise fee rate after Q3+Q4.** That single number affects every deal.
