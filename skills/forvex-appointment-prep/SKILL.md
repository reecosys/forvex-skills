---
name: forvex-appointment-prep
description: Pre-meeting brief for a seller appointment. Pulls property data + comps via RealIE MCP, gathers seller-situation context (motivation signals, listing history, distress indicators), runs the underwriting math, and produces a one-pager brief covering the property, the offer range, likely seller posture, talking points, and red flags. Use when the user says "prep me for the meeting at [address]", "I'm seeing [address] tomorrow", "what should I know about the seller at [address]", "appointment brief for [address]".
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# forVEX Appointment Prep

You are preparing a franchise operator for an in-person (or call) appointment with a seller. The goal: walk into that meeting with the property numbers in your head, a defensible offer range, an informed read on the seller's likely posture, and a short list of questions you need answered to lock the deal in or kill it.

You do not invent seller motivation. You synthesize signals from data + the franchisee's notes.

## When to invoke

- "Prep me for the meeting at 123 Main St tomorrow"
- "I'm seeing 456 Oak at 2pm, what do I need to know"
- "Appointment brief for [address]"
- "Walk-through with seller in 30 min — what should I be thinking?"

## Workflow

### 1. Identify the property

Get the address. If the user gave you one in a prior turn of the same conversation, use it. Otherwise ask.

### 2. Pull data — MCP first, no web fallback

**Step 2a — MCP usage discipline.** Do not force `forvex_whoami` as a mandatory first call. Use it only when:

- the user asks to verify the connector
- the session appears unauthenticated
- a forVEX tool fails and you need to distinguish auth failure from empty data

If forVEX tools error or do not resolve, treat MCP as down for this session and skip to step 3 — but announce it explicitly at the top of the brief:

> ⚠️ **forVEX Control MCP not connected this session.** Brief built from your inputs only — no property/comps/flood/market data pulled. Reconnect at Claude → Settings → Connectors → forVEX Control to auto-populate. Numbers below are directional until validated.

**Do not fall back to scraping Zillow / Redfin / Trulia / Spokeo / Realtor.com for property facts.** This skill is not a web scraper. If MCP is down, work from what the franchisee tells you and flag every defaulted value.

**Step 2b — Server-first data pull (MCP live).** Read `references/platform/mcp-tools.md` for the canonical tool list. For appointment prep specifically, the priority calls are:

- `forvex_get_property(address)` — resolve `property_id` and property fundamentals. Read optional `parcel` (last-sale flags, physicals, winning debt) per `references/platform/mcp-tools.md`. Do not decode Realie codes yourself.
- `forvex_list_deals({ property_id })` and `forvex_get_deal(id)` — only when an existing deal record exists for this address. When `forvex_get_deal` returns, read `readvise_property` (motivation, lead_source, lead_type, exit_strategy, financing) and `analysis.context` — these pre-fill seller context for step 3.
- `forvex_underwrite(address, purchase_price?)` — canonical underwriting workflow; treat this as the source of truth for verdict, MAOs, pre-offer, confidence, and strategy comparison
- `forvex_get_flood_data(address)` — flood zone status when you need explicit flood commentary
- `forvex_get_market_intelligence(address)` — composite tract + neighborhood intel when you need supporting narrative. **Consume the `briefing` text directly.**
- `forvex_get_comps(address)` — only when the franchisee wants to inspect the default comp set
- `forvex_get_comps_expanded(address)` — only when they explicitly ask for a broader comp search
- `forvex_get_comp_detail(trace_id)` — only if the franchisee challenges a specific comp; use `trace_ref.id` from `forvex_underwrite.server_context` or `forvex_get_comps`
- `forvex_get_rent_estimate(address)` — only if rental or BRRRR is in the strategy mix and rent still needs confirmation

**Market intel — how to consume the response:**

| Field | Lands in brief |
|---|---|
| `briefing.neighborhood` (preferred) or `briefing.tract` (fallback) | "Submarket context" paragraph under Seller posture read |
| `briefing.key_takeaways` (e.g., Price↑, Rent↑) | "Market read" tag row in Top of mind |
| `scores.posture_label` + `scores.posture_score` + `scores.vs_market` | "Market read" line; also shifts probability-of-close band |
| `movement.volatility` | Offer-ladder tightness (high → directional only, $5K rounding) |
| `movement.trend` (declining) | Walkaway haircut commentary |
| `structure.older_housing_stock_share` > 0.65 | Auto-include red flag for mechanicals/electrical/plumbing verification |
| `activity.logged_properties_count` + `memory_recurring` | Confidence multiplier line under submarket context |
| `cache.stale: true` or briefing > 60 days old | Surface "market data older than 60 days" warning |

### 3. Gather seller context from the franchisee

The data tells you about the property. The franchisee tells you about the *seller*.

**Read-before-ask:** If `forvex_get_deal` returned `readvise_property` or `analysis.context` with motivation / lead source / lead type already set, **do not re-ask** for those fields. Cite the existing values in the brief (e.g., "Seller motivation on file: Inherited"). Only ask for fields that are still missing.

When gaps remain, ask in **one consolidated question** using Readvise's vocabulary so the answers map cleanly to deal records:

> Before I write the brief, what do you know about the seller and how they came to you?
>
> - **Lead source**: web, advertising, or dig (self-generated)?
> - **Lead type** (when source is dig/referral): mailers, paid, referral, organic, or other?
> - **Motivation** (Readvise category): inherited, divorce, landlord burnout, relocation, downsizing, financial distress, or other?
> - **Listing history**: how long on market (or off-market), any price drops, agent or FSBO?
> - **Tone**: have you talked with them before? What was the conversation like?
> - **Other context**: tenants, condition, deadlines, anything weird?

Don't grill. Most franchisees give you what they have in 2–3 sentences and that's enough. See `references/question-bank.md` for the full taxonomy mapping each Readvise motivation to signal strength and talking points.

### 4. Run the underwriting

Prefer `forvex_underwrite` as the canonical execution path. Use it as the source of truth for the appointment brief, then layer seller posture and talking points on top. Only fall back to local calculator execution if the underwriting tool is unavailable.

You do not need to render the full one-pager here. You need the verdict, recommended strategy, MAOs, pre-offer, and payoff estimate when available.

### 5. Produce the appointment brief

Use `templates/appointment-prep.md`. Structure:

1. **Top of mind** — property + verdict + recommended strategy + **Pre-Offer Number** + MAO range + **math basis line** (posture, rate, hold, rehab, listing %, franchise fee). The math basis line is required per `references/platform/forvex-frame.md` — never omit it.
2. **Property snapshot** — beds/baths/sqft/year, condition signals, garage/foundation/basement **class** from `parcel.physical` (or `subject.physical` on comps) when present, comp-validated ARV range with confidence
3. **Seller posture read** — what we know, what we infer, motivation signal strength (low/medium/high), probability of accepting an offer at MAO (rough)
   - **Payoff estimate block** — prefer `parcel.debt` from `forvex_get_property` (same object on `forvex_underwrite.server_context.property.parcel`). Use `parcel.debt.balance` when `source` is `liens` or `mortgages`. Treat `archived_may_2026` as a weak estimate and say so. `none` or null `recorded_lien_balance` is **unknown, not $0 owed** — do not invent payoff from `last_sold_price` when winning debt exists. Still pass `last_sold_price` / `last_sold_year` into `forvex_underwrite` and render `payoff_estimate` when the engine returns it. Make payoff the #1 on-site question if estimated payoff > target offer.
   - **Last-sale flags** — when `parcel.last_sale` is present, cite `deed.label` and flags (`distressed`, `reo`, `arms_length`, company/entity buyer). Null flags (typical of flat v2 rows) mean unknown — do not invent REO/distress. Use them to seed questions, not to invent seller motivation.
   - **Seller's math (hold-cost comparison) block** — render for motivations `relocation`, `financial_distress`, `inherited`, `landlord_burnout`. Compares your offer (net now) vs. their probable retail path (net later). Use: their expected resale × 0.94 (6% commission) − ($1,800–2,200/mo × expected DOM months) − payoff = "hold net." Compare to "now net" = your target offer − payoff − ~$3K closing. Surface the gap as the calibrated question.
4. **Offer ladder** — Pre-Offer Number (walk-in), opening, target, walkaway, with rationale
   - **Cash overlay block** — render when `lender_ltv_cap` was passed and `cash_overlay.max_overlay > 0`. Show overlay by strategy at the target offer. Warn that the overlay above the cap line is franchisee cash, not financed.
5. **Questions to ask the seller** — 5–7 questions that move the deal forward or kill it cleanly
6. **Talking points** — 3–4 angles to lead with based on what we know about the seller
7. **Likely objections** — 2–3 objections most likely for this seller's posture, with framed responses (see `references/objection-handling.md`)
8. **Red flags / due diligence items** — things to verify on-site that could change the math
9. **Negotiation framing** — Sandler + Voss notes specific to this seller's likely posture (see `references/platform/forvex-frame.md`)

### 6. Suggested follow-ups at the end

Three prompts the user can paste after the meeting. The exact menu lives in `templates/appointment-prep.md`. Each maps cleanly to a Phase 4 write tool — see the next step.

### 7. Post-meeting write-back

When the franchisee comes back after the appointment, **route the update to the right MCP tool**. The wrong tool here corrupts the pipeline state (e.g., losing the deal vs. just noting a walkaway).

| What the franchisee says | Tool | Payload notes |
|---|---|---|
| "We made an offer of $X" / "submitted offer" | `forvex_update_deal_disposition` → `OFFER` **then** hand off to `forvex-underwriting` | After disposition, re-run `forvex_underwrite` with `purchase_price: $X` and call `forvex_save_deal` so Operate shows the offer (Readvise does not infer offer from status alone). |
| "Got it under contract at $X" / "they signed" | `forvex_update_deal_disposition` → `UNDER_CONTRACT` | If currently `LEAD`, this skips `OFFER` — pass `override_reason: "went straight to contract"`. |
| "Closed on it" / "we own it now" | `forvex_update_deal_disposition` → `INVENTORY` | Sequential forward. |
| "Listed it" / "on the MLS" | `forvex_update_deal_disposition` → `LISTED` | Sequential forward. |
| "Got a contract on the listing" | `forvex_update_deal_disposition` → `PENDING` | Sequential forward. |
| "Closed the sale" / "we sold" | `forvex_update_deal_disposition` → `SOLD` **then** `forvex_record_deal_outcome` | Terminal status. Ask for actuals (sale price, rehab, DOM, close date) and record `outcome_kind: SOLD` — ground truth for the learning-calibration loop. See `forvex-deal-disposition` step 5b. |
| "Walked away" / "no deal" / "passed" | `forvex_log_activity` (`activity_type: walkaway`) | **Default to logging, not LOST.** Status stays where it was; the brain dump goes into Readvise notes. |
| "Lost the deal — take it off the board" / "remove from active" / "they sold to someone else" | `forvex_update_deal_disposition` → `LOST` **then** `forvex_record_deal_outcome` | Use `LOST` only when the franchisee explicitly wants the deal removed from the active lifecycle. Record `outcome_kind: DEAD` with whatever actuals they have. See `forvex-deal-disposition` step 5b. |
| "Drove by, vacant, left card" | `forvex_log_activity` (`drive_by` / `no_contact`) | Status untouched. |
| "Talked to the seller — still negotiating" | `forvex_log_activity` (`call` / `contact_made`) | Status untouched; capture the substance in `notes`. |
| "Counter at $X — rerun the ladder" | `forvex_log_activity` (`counter`) **then** re-invoke `forvex-underwriting` | The disposition doesn't change just because there's a counter; the conversation event does. After the rerun, if the franchisee says "save the new ladder", `forvex-underwriting` will `forvex_save_deal` again. |
| "Saw the property — rehab is actually $Y, redo" | re-invoke `forvex-underwriting` with new rehab; offer to `forvex_save_deal` after | No disposition change. |
| "Confirmed addition/basement is permitted, redo" | re-invoke `forvex-underwriting`; offer to `forvex_save_deal` | No disposition change. |
| "Refer this out as a wholesale assignment" | `forvex_log_activity` (`referral`) + ask whether they also want `LOST` | Don't auto-`LOST` — they may keep tracking it. |

**Rules of the road:**

- **Status moves are for real lifecycle changes.** If you can't name the new pipeline stage out loud, it isn't a disposition — it's an activity.
- **`LOST` is opt-in, not a default.** "Walked away" ≠ "lost". Only use `LOST` when the user uses words like "lost", "killed it", "take it off the board", "remove from active".
- **Always anchor by `deal_id`** when you have it. `forvex_log_activity` accepts `property_id` or `address` only as a fallback.
- **Verify by re-read** after disposition changes — call `forvex_get_deal(deal_id)` and confirm `current_status` matches.
- **`forvex-appointment-prep` does not call `forvex_save_deal`.** Underwriting analyses are owned by `forvex-underwriting`. When the franchisee transitions to underwriting or says "save," **pass gathered seller context forward** in the handoff (`seller_motivation`, `lead_source`, `lead_type`, `notes`) so `forvex-underwriting` can include it in `forvex_save_deal` `context`.
- **Terminal closes feed the learning loop.** On `SOLD` or `LOST`, disposition alone is not enough — also call `forvex_record_deal_outcome` with actuals (or hand to `forvex-deal-disposition` if that skill is active). Without outcomes, corrections captured in underwriting step 8.5 never get confirmed.

## Probability of close — how to frame it

Map the Readvise motivation + supplementary signals to a band. Full details in `references/question-bank.md`.

| Motivation profile | Probability band |
|---|---|
| Strong Readvise motivation (Inherited / Divorce / Financial distress) + asking within 10% of MAO | **High** (60–80%) |
| Strong motivation alone, OR Medium motivation + supplementary positive signal | **Medium** (30–50%) |
| Medium motivation alone, OR weak signals; asking 20%+ above MAO | **Low** (10–25%) |
| Negative signals dominant, retail-priced, "just testing" | **Walk** (<10%) |
| Motivation not stated in Readvise | **Unknown** — flag that motivation needs probing during the meeting |

State the band, name the Readvise motivation and supplementary signals supporting it, and let the franchisee make the judgment call.

**Submarket posture modifier:** the market intel `posture_score` shifts the band by at most one tier:

- `posture_score ≥ 70` (Strong / Outperforming) → may move probability up one tier when motivation is at least Medium (the submarket supports the math, so a motivated seller has fewer alternative exits worth waiting for)
- `posture_score < 40` (Soft / Declining) → moves probability up one tier independent of motivation (sellers in soft submarkets face declining alternatives and capitulate faster); also adds a "soft market" line to "What moves this up"
- `movement.trend: declining` AND `volatility: high` → caps the band at Medium regardless of other signals (uncertainty cuts both ways — seller may also walk away from a counter)

**Always include two "what moves this" bullets up and two down** — concrete, situation-specific, derived from the actual unknowns in this deal (not generic platitudes). Examples of the right level of specificity:

- ↑ "Payoff confirmed ≤ $200K on-site" / "Prior appraisal came in at $310K+" / "Addition is permitted per PVA"
- ↓ "Payoff ends up > $230K" / "Sqft discrepancy resolves to unpermitted" / "Seller's job offer firms up and removes the deadline"

If you can't name a specific lever that would shift the probability, leave the bullet out — don't pad with "if motivation is higher than stated." The bullets exist to tell the franchisee which question moves the most weight in the meeting.

## Motivation strength by Readvise category

Quick reference; see `references/question-bank.md` for full mapping:

| Readvise category | Strength | Reads as |
|---|---|---|
| **Inherited** | Strong | Probate/heir disposition; speed > price |
| **Divorce** | Strong | Court/deadline driven; verify who must sign |
| **Landlord burnout** | Medium-Strong | Wants exit from management headache; tenant-friendly close is a hook |
| **Relocation** | Medium-Strong | Has a date; verify whether new home is contracted |
| **Downsizing** | Medium | Life-stage; flexible timing, price still matters |
| **Financial distress** | Strong | Foreclosure/tax/lien pressure; verify deadlines |
| **Other / Not stated** | Depends | Read the free text; if blank, surface as "needs probing" |

## Negotiation framing — Sandler + Voss in practice

From `references/platform/forvex-frame.md`:

- **Lead with speed and certainty** — "I can close in 14 days, no contingencies, cash" is the cash-buyer's edge over retail offers.
- **Anchor on rehab scope, not ARV** — sellers argue values; they don't argue rehab costs.
- **Use calibrated questions (Voss)**: "How are you supposed to make this work at [their ask]?" "What's the situation behind selling?" "How did you arrive at [their number]?"
- **Mirror + label (Voss)**: "Sounds like [emotion]..." "It seems like timing matters most..."
- **Pain funnel (Sandler)**: "Tell me more about that." "What does that look like?" "How does that affect you?" "How long has that been going on?" "Have you tried anything to fix it?"
- **Bring up the hard stuff first** (Voss: "accusation audit"): "You probably think my offer's going to be way too low. The reason it has to be is that the rehab is real money…"
- **End every counter with "fair"**: "That's the fair number on the math. If your number's higher, what's it based on?"

Tailor 3–4 of these to the specific seller posture. Don't dump all of them in the brief — pick what fits.

## What this skill does NOT do

- Does not produce the full underwriting one-pager. The brief is a **summary** with the offer range and seller posture — for the math detail, the user can ask `forvex-underwriting` separately.
- Does not invent motivation signals. If the franchisee didn't surface anything, the brief reads "no known motivation signals — treat as market-priced seller."
- Does not promise outcomes. "High probability" caps at 80%.
- Does not call seller, schedule meeting, or interact with anyone other than the franchisee.

## The Pre-Offer Number — the walk-in number

The brief leads with the **Pre-Offer Number**, the simple number the franchisee walks in with. From the underwriting result's `pre_offer` block:

- **Base** = `ARV × 65%` (purchase ceiling, repairs NOT subtracted). This is the number to hold in your head — *purchase / ARV ≤ 65%*.
- **Repair-adjusted** = base − repair estimate. Use when you've pre-estimated repairs.

Two ways the repair estimate gets set:

1. **Compute on-site** (default) — walk in with the base number; subtract repairs you observe during the walkthrough, in your head, no math on paper.
2. **Pre-estimate by $/sqft tier** — before the appointment, pick a condition tier (`light` | `medium` | `heavy` | `gut`) and call `forvex_underwrite` with `rehab_tier` + sqft, or use the server pre-offer block from its output. Tier rates are authoritative in `recontrol/lib/mcp/underwrite/nativeEngine.ts` — do not hardcode $/sqft in skill prose when MCP is connected.

The Pre-Offer is purchase-only and intentionally simpler than the underwriting MAO (which accounts for all fees, financing, holding). Show **both**: the Pre-Offer as the napkin number the franchisee trusts, the MAO as the precise per-strategy ceiling. They should be in the same ballpark; if the Pre-Offer is far above the MAO, flag it.

## After the appointment — hand off to the debrief

This skill covers the **before**. When the franchisee comes back and narrates how
it went ("wrap up the appointment", "here's what happened at 8003 Candleglow",
"debrief that meeting"), route to **`forvex-presentation` Mode 5 — Appointment
debrief**. It renders the conversation: who has to say yes, what they objected
to, how the hour went, where the deal honestly stands, and the next actions.

Prep brief in, debrief out. Then:

- the touch itself → `forvex-activity-log`
- a pipeline move the appointment caused (LEAD → OFFER) → `forvex-deal-disposition`

## Reference files

- `references/question-bank.md` — seller-context questions and motivation signal taxonomy
- `references/objection-handling.md` — common objections with Sandler/Voss framed responses
- `templates/appointment-prep.md` — the brief output template
- `references/platform/mcp-tools.md` — MCP tool surface (shared)
- `references/platform/comp-evaluation.md` — comp interpretation (shared)
- `references/platform/forvex-frame.md` — Sandler + Voss negotiation framing (shared)
