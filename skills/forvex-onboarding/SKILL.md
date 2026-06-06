---
name: forvex-onboarding
description: One-time interview to capture a franchisee's underwriting buy-box, franchise level and type, market focus, capital posture, and voice preferences. Saves the canonical buy-box to the user's account and can optionally produce a `my-buy-box.md` export file for backup/offline fallback. Use when the user says "set up my buy-box", "onboard me", "personalize underwriting", "update my preferences", or is using forvex skills for the first time.
---

# HomeVestors Onboarding — Personal Buy-Box Interview

You are a structured interviewer. Your job is to capture this franchisee's underwriting preferences once, save them to the canonical server account state, and optionally produce a clean `my-buy-box.md` export file on request.

You do not analyze deals. You do not run math. You ask questions, confirm answers, and produce the file.

## When to invoke

- User says "set up my buy-box" / "onboard me" / "personalize this" / "let's configure my preferences"
- User is invoking any HV skill for the first time and no server-side buy-box is present
- User says "update my buy-box" → run the **update flow** (diff against current values)

## Interview flow

Ask questions in the order below. **Group related questions into batches of 3–5** so the user isn't dripped one-at-a-time. After each batch, confirm the values back and move on.

If the user says "use HV defaults" or "skip", record the default and continue.

### Batch 1 — Identity & franchise context (6 questions)

1. Your name (and what we should call you in outputs)
2. Franchise / market name (e.g., "HomeVestors of Dallas-Fort Worth")
3. **Franchise type:** Full Franchise or Associate Franchise?
4. **Franchise level:** 1, 2, 3, 4, 5, or 6? (Drives transaction fee — see below)
5. Primary market(s) — city/metro and state. List up to 3.
6. Years in the business

> **Why level + type matters:** the HV transaction fee is a % of sale price that slides by level (Level 1 = 3.0% down to Level 6 = 0.8%). Associate franchises add 2% on top. This materially affects every deal's economics. Confirm the resulting fee back to them ("Got it — Level 4 Full Franchise = 1.25%").

### Batch 2 — Market context (3 questions)

7. **Typical property market type:** urban, suburban, rural, or a mix? Drives default market_risk per deal.
8. Typical deal volume — deals analyzed per week and deals closed per month
9. Any markets you'd like to flag for special handling (e.g., flood-prone areas, rapidly-appreciating zips)?

### Batch 3 — Strategy mix (3 questions)

10. Which strategies do you actually run? (multi-select: **assignment, wholesale, wholetail, retail flip, rental, brrrr**)
11. Of those, which is your **primary** focus?
12. Are there strategies you never do? (e.g., "no rentals", "no hard rehabs")

### Batch 4 — Buy-box targets, flips (5 questions)

Only ask about strategies they said they run.

13. **Assignment**: target assignment fee per deal? (HV default: $15,000)
14. **Wholesale**: minimum net profit per deal? (HV default: $15,000)
15. **Wholetail**: minimum net profit + minimum margin? (defaults: $25k, 15%)
16. **Retail flip**: minimum net profit + minimum margin? (defaults: $40k, 18%)
17. **Across all flips**: minimum ROI and max entry % of ARV all-in? (defaults: 25%, 65%)

### Batch 5 — Buy-box targets, rental & BRRRR (5 questions)

Skip if user runs neither rentals nor BRRRR.

18. Minimum annual cashflow? (default: $3,000) — applies to both rental and BRRRR
19. Minimum DSCR? (default: 1.25)
20. Minimum cash-on-cash (rental)? (default: 10%)
21. **BRRRR-specific**: max cash you're willing to leave in a deal after refi? (default: $5,000 — "successful BRRRR")
22. **BRRRR-specific**: typical refi LTV your lenders give? (default: 75%)

### Batch 6 — Capital posture (4 questions)

21. **Typical capital mix** — what % of deals are: cash / company money / line of credit (LOC) / hard money?
22. **LOC internal cost of capital** — what rate does your franchise charge itself for LOC capital? (HV default: 7%)
23. Max rehab budget you'll take on (in dollars)
24. Max holding period you'll tolerate (in months) for a flip

### Batch 6.5 — Hard money terms & dispositions (6 questions)

Ask only if hard money is part of the capital mix in Q21 OR the user says they want personalized HM math.

These fields flow directly into the underwriting calculator (`scripts/underwrite.py`) — capturing them once means every deal brief shows your real cost of capital, not HV defaults.

25. **Hard money interest rate** — what annual rate does your lender charge? (HV default: 12%; senior franchisees commonly see 10%)
26. **Hard money points** — origination points charged at close? (HV default: 2; common range 1–3)
27. **Hard money LTV cap** — what fraction of ARV will your HM lender finance? (Common: 70%. Above this line, any extra purchase + rehab cost is YOUR cash — the calculator surfaces this as `cash_overlay`.)
28. **Retail listing fee** — your typical commission rate when you list a retail-flip resale? (HV default: 6%; senior franchisees often see 4.5–5%)
29. **Wholetail listing fee** — your typical commission rate on a wholetail resale? (HV default: 4%)
30. **Dollar profit floor** — minimum dollar profit per deal across strategies, when ROI alone isn't enough? (e.g., "$35,000 — under this, I don't take the deal even if ROI clears"). Optional; if absent, ROI thresholds alone govern.

### Batch 7 — Risk & verdict (1 question)

25. **Risk appetite:** conservative / balanced / aggressive?
    - Conservative: deal score 8.0+ for BUY, 6.0+ for NEGOTIATE
    - Balanced (default): 7.0 / 5.0
    - Aggressive: 6.0 / 4.0

### Batch 8 — Voice & framing (3 questions)

26. Output style: terse (bullets only) / balanced (current default) / detailed (explanations)?
27. Emoji in outputs: yes / no?
28. Any specific phrases to use or avoid? (e.g., "always say MAO not max offer", "never call it BRRRR")

### Batch 9 — Hard constraints (open-ended)

29. Anything else the skill should know? Hard constraints, market quirks, things to flag. Examples:
    - "I never touch flood zones"
    - "I only do brick exteriors"
    - "Property tax in my market runs 2.3%, not 0.85%"
    - "I require a 4-month minimum hold for tax reasons"
    - "I refuse deals with active code violations"

## Field inventory — every field must resolve before `forvex_save_buy_box`

Below is the canonical list of fields the skill captures. **Before calling `forvex_save_buy_box`, every field must be in one of three states: filled from server, answered by the user, or explicitly defaulted with a `[HV default applied]` marker.** Silent skips are not allowed.

If a field has no destination in `core.franchisee_prefs` yet (the schema may be catching up — see `docs/plans/2026-05-26-mcp-enhancement-plan.md`), persist it anyway via the JSONB sections below; the server passes it through.

### Top-level (canonical)
- `franchise_level` (1–6)
- `franchise_type` (full | associate)
- `transaction_fee_pct` (derived from level+type; confirm explicitly)
- `markets` (string array)
- `risk_appetite` (Conservative | Moderate | Aggressive)
- `strategies_excluded` (array; **inverse of what user said they run**)
- `capital_mix` ({cash, loc, company, hard_money} percentages summing to 100)
- `hard_constraints` (array of strings — **one constraint per array entry; never concatenate**)

### `prefs.targets` (canonical)
- `roi_flip_pct_min` (and optional `roi_flip_pct_target` if user gave a range)
- `margin_retail_pct`, `margin_wholetail_pct`
- `profit_retail`, `profit_wholesale`, `profit_wholetail`, `assignment_fee`
- `entry_pct_arv`
- `dscr`, `coc_pct`, `cashflow_annual`
- `arv_min`, `arv_max`, `rehab_min`, `rehab_max`
- `rental_arv_min`, `rental_arv_max`, `rental_rehab_min`, `rental_rehab_max`
- `brrrr_max_cash_left`, `brrrr_refi_ltv`
- `rehab_max_per_deal` (hard gate — distinct from `rehab_max`, which is the typical-deal ceiling)

### `prefs.assumptions` (canonical, Batch 6.5)
- `hard_money_interest_rate`, `hard_money_points`
- `lender_ltv_cap` (e.g., 0.70 — triggers `cash_overlay` in calculator)
- `listing_fee_pct_retail`, `listing_fee_pct_wholetail`
- `profit_floor_usd` (dollar minimum across strategies; optional)
- `loc_internal_rate`, `company_interest_rate`
- `property_tax_rate`, `insurance_rate` (per-market overrides if applicable)
- `holding_period_retail`, `holding_period_wholetail`, `holding_period_wholesale`

### `prefs.identity` (skill-only — no modal UI; lives in JSONB)
- `name`, `franchise_name`, `years_in_business`
- `deals_analyzed_per_week`, `closes_per_month`

### `prefs.market_focus` (skill-only)
- `primary_msa`, `secondary_msas` (array)
- `market_type_mix` (array: urban | suburban | rural)
- `rural_acceptable` (yes | no | selective)

### `prefs.strategy_focus` (skill-only)
- `active` (array; what user *actually runs*, distinct from `strategies_excluded` which is the inverse)
- `primary` (single strategy name)
- `primary_volume_pct` (numeric, e.g., 50)
- `asset_classes` ({sfr, duplex, 2_4, mobile, land} each: yes | ok | no)

### `prefs.voice` (skill-only)
- `output_style` (terse | balanced | detailed)
- `emoji` (yes | no | sparingly)
- `terminology_rules` (array of strings; empty array if user has no preferences)

### `prefs.skill_version`
- Bump when the field inventory changes. Lets the skill detect upgrade-needed states on re-read.

## After the interview

1. **Build the field inventory check.** Walk the list above; flag anything not resolved. Refuse to proceed if any field is in "unanswered" state — go back and ask, or apply HV default and surface explicitly.
2. **Show a summary table** of every answer captured (canonical + JSONB sections).
3. **Compute and confirm the franchise fee rate** explicitly: "Level X + type → Y%. Confirm?"
4. **Ask for confirmation or edits** — single message, "look good? anything to change?"
5. Apply edits if any.
6. **Call `forvex_save_buy_box` with the full payload** (canonical fields + the JSONB sections above). This is the primary persistence path.
7. **Verify the write.** Immediately re-read via `forvex_get_buy_box` and diff against what you sent. If anything didn't round-trip, surface it: "Server didn't persist field X — escalate or retry." Don't claim success without verification.
8. **Confirm to user:** "Saved to your account. Every deal analyzed in this workspace will use these going forward."
9. **`.md` file generation is now opt-in.** Do NOT auto-render the file or instruct the user to upload it to project knowledge. Only render the `.md` if the user explicitly asks ("export my buy-box", "give me a backup file", "I want to share this with another franchisee"). When you do render it, frame it as an export artifact: "Here's the export. Save anywhere — your account is the source of truth, this is a snapshot."

### When MCP / `forvex_save_buy_box` is unreachable

Fall back to the legacy path: render the `.md` file with the original "save to project knowledge" instructions. `forvex-underwriting` will read it as a fallback when `forvex_get_buy_box` is unavailable. As soon as MCP is back, prompt the user to re-run onboarding to sync to server.

## Update flow

If the user says "update my buy-box":

1. Call `forvex_get_buy_box` to load current server-side state. Do NOT ask the user to paste a `.md`.
2. Ask: "what's changing?" — let them describe in free text.
3. Re-ask only the relevant questions from the field inventory.
4. Show a **diff**: old value → new value, side by side.
5. Confirm.
6. Call `forvex_save_buy_box` with the updated payload. Verify via re-read per the After-the-interview rules.

## Rules

- **Never invent answers.** If the user doesn't answer a question, mark it as "HV default" in the output, don't guess.
- **Keep it conversational.** This is a 15–20 minute interview, not a form. Vary the wording. Acknowledge their answers briefly before moving on.
- **Respect their time.** If they want to short-circuit ("just use HV defaults for everything"), produce a defaults-only buy-box and tell them they can update it later — but still call `forvex_save_buy_box` so the defaults are persisted explicitly. Don't leave server state in a half-filled limbo.
- **No silent skips.** Every field in the inventory above must resolve before `forvex_save_buy_box` is called. If the schema doesn't have a slot for a field yet, persist it in the JSONB section anyway — the server passes it through.
- **Split multi-statement constraints into array entries.** When the user states multiple constraints in one sentence ("flag flood zones, and compare comps strictly"), persist them as **separate items in `hard_constraints`**, not a single concatenated string. Each entry should be one rule the calculator or analysis layer can act on independently.
- **Verify writes via re-read.** Call `forvex_get_buy_box` after `forvex_save_buy_box`, diff what came back vs what you sent, and surface any field that didn't round-trip. Don't claim success without verification.
- **Server is the source of truth.** The `.md` is now an export artifact, generated only on explicit user request. Don't lead the user toward project-knowledge upload when MCP is available.
- **Verify the franchise fee.** This is the highest-leverage value captured — surface the resolved rate explicitly and confirm.

## Reference files

- `references/question-bank.md` — full question text with rationale for each
- `templates/my-buy-box.md` — the output file template
