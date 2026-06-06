**Appointment Brief — {ADDRESS}**
Meeting: {MEETING_TIME_OR_TBD} · Prepared: {DATE}

## Top of mind

- **Verdict: {VERDICT}** · Best strategy: **{BEST_STRATEGY}**
- **Pre-Offer (walk-in): ${PRE_OFFER_BASE}** (ARV × 65%) — subtract repairs on-site
- **Offer ladder: opening ${OPENING_OFFER} → target ${TARGET_OFFER} → walkaway ${WALKAWAY}**
- **Probability of close: {PROBABILITY_BAND}** ({SUPPORTING_SIGNALS})

## Property snapshot

| | |
|---|---|
| ARV (comp-validated) | ${ARV_LOW} – ${ARV_MEDIAN} – ${ARV_HIGH} ({COMP_CONFIDENCE}) |
| Asking | ${ASKING} |
| Rehab estimate | ${REHAB_LOW} – ${REHAB_HIGH} |
| Beds / baths / sqft / year | {BED} / {BATH} / {SQFT} / {YEAR} |
| Condition signals | {CONDITION_NOTES} |
| Location type | {LOCATION_TYPE} |
| Flood zone | {FLOOD_STATUS} |

## Seller posture read

**What we know:** {KNOWN_FACTS}

**Motivation signals present:** {SIGNALS_PRESENT}
**Motivation signals absent (worth asking about):** {SIGNALS_ABSENT}

**Read:** {POSTURE_NARRATIVE}

> Probability of close at MAO target: **{PROBABILITY_BAND}**. {PROBABILITY_REASONING}

## Offer ladder

| | Offer | Why |
|---|---|---|
| Pre-Offer base | ${PRE_OFFER_BASE} | ARV × 65%, before repairs — the walk-in ceiling |
| Pre-Offer (repairs ~${REPAIRS_EST}) | ${PRE_OFFER_ADJUSTED} | base − estimated repairs ({REPAIR_SOURCE}) |
| Opening | ${OPENING_OFFER} | {OPENING_RATIONALE} |
| Target | ${TARGET_OFFER} | {TARGET_RATIONALE} — meets buy-box on {STRATEGIES_THAT_FIT} |
| Walkaway | ${WALKAWAY} | {WALKAWAY_RATIONALE} — above this, no strategy clears buy-box |

## Questions to ask

1. {Q1}
2. {Q2}
3. {Q3}
4. {Q4}
5. {Q5}

## Talking points (lead with these)

- {TALKING_POINT_1}
- {TALKING_POINT_2}
- {TALKING_POINT_3}

## Likely objections

**"{OBJECTION_1}"**
{OBJECTION_1_RESPONSE}

**"{OBJECTION_2}"**
{OBJECTION_2_RESPONSE}

**"{OBJECTION_3}"**
{OBJECTION_3_RESPONSE}

## Red flags / due diligence on-site

- {RED_FLAG_1}
- {RED_FLAG_2}
- {RED_FLAG_3}

## Negotiation framing

{NEGOTIATION_NOTES — Sandler + Voss tailored to this seller's posture}

---

**After the meeting, ask me:**

Pick the prompts that match what you learned. Include the actual number / fact in the message so the rerun is targeted. Each prompt routes to the right MCP write tool — see `SKILL.md` step 7 for the full mapping.

*Re-runs (no pipeline state change):*

- "Seller countered at $X — re-run the ladder" *(also logs a `counter` activity)*
- "Saw the property — rehab is actually closer to $Y, redo"
- "Prior appraisal came in at $X — anchor target there"
- "Confirmed addition/basement is permitted, redo with sqft Y"

*Notes / touches (`forvex_log_activity`, status unchanged):*

- "Drove by — vacant, left card on the door"
- "Talked with the seller, still mulling — log the call"
- "Not my deal — refer this out as a wholesale assignment"
- "Walked away from this one — log it" *(walkaway note; status stays put)*

*Pipeline moves (`forvex_update_deal_disposition` — say the new stage out loud):*

- "We made an offer of $X" → **OFFER**
- "Got it under contract at $X" → **UNDER_CONTRACT**
- "Closed the purchase" → **INVENTORY**
- "Listed it on the MLS" → **LISTED**
- "Got an accepted offer on the listing" → **PENDING**
- "We closed the sale" → **SOLD**
- "Lost this one — take it off the active board" → **LOST** *(only when you mean it; "walked away" alone defaults to a note, not LOST)*

*Defaults applied: {DEFAULTS_NOTE}*
