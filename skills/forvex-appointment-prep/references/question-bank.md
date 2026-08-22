# Appointment Prep — Question Bank & Motivation Signal Taxonomy

Drives the seller-context gathering step in `SKILL.md`. The skill asks the consolidated question once; this file is the source-of-truth for what to listen for in the answer and how to score motivation.

**Field vocabulary mirrors Readvise** so the skill's questions match the data the franchisee already captures in the deal record. Don't invent new categories.

---

## Consolidated question (one ask)

The skill should batch all of this into a single message. Don't drip-feed.

> Before I write the brief, what do you know about the seller and how they came to you?
>
> - **Lead source**: web, advertising, or dig (self-generated)?
> - **Motivation** (Readvise category): inherited, divorce, landlord burnout, relocation, downsizing, financial distress, or other?
> - **Listing history**: how long on market (or off-market), any price drops, agent or FSBO?
> - **Tone of contact**: have you talked with them before? What was the conversation like?
> - **Other context**: tenants in place, condition you've heard about, deferred maintenance, code issues, deadlines, anything weird?

If the user gives partial info, proceed with what they have. Mark unknown fields as "not stated" in the brief. Don't grill.

---

## Record facts to confirm on-site (from `parcel`)

These come from `forvex_get_property.parcel` (also on `forvex_underwrite.server_context.property.parcel`). They are **not** seller motivation. Use them to seed questions; never invent a flag the cache did not send.

| When present | Confirm / ask |
|---|---|
| `last_sale.reo` or `distressed` true | "Was this an REO / distressed purchase — and is that still hanging over title?" |
| `last_sale.arms_length` false | "How did they take title — family transfer, quit claim, or a market sale?" Speak `last_sale.deed.label`. |
| `buyer_entity` is a company (not individual) | "Is the seller an entity? Who signs?" |
| `debt.source` is `liens` or `mortgages` | Confirm `parcel.debt.balance` and lender as the payoff question. Do **not** treat null `recorded_lien_balance` as $0 owed. |
| `debt.source` is `archived_may_2026` | "We only have an archived payoff estimate — what do they actually owe?" |
| `debt.source` is `none` | Payoff is unknown. Ask. Do not invent it from `last_sold_price`. |
| `physical.basement.class` is not `none` | "Finished / permitted basement? Walk it." |
| `physical.foundation.class` | Note slab vs crawl vs basement on the red-flag list; do not invent structural condition. |
| `physical.garage.type` | Confirm stall count vs record before using garage in the rehab/comp story. |

Match on `code`; speak `label` / `class`. Null inners mean the cache lacked the fact (common on flat v2 rows).

---

## Lead source taxonomy (Readvise)

| Source | What it means | Typical motivation strength |
|---|---|---|
| **Web** | Landing-page form, online inquiry, ppc/SEO lead | Mixed — self-selected for "I want to sell to an investor," but many shopping multiple buyers |
| **Advertising** | Direct mail, paid ads, signage, radio | Often higher motivation — they responded to a "we buy houses" message, not browsing |
| **Dig** | Self-generated — referral, networking, prior customer, FSBO outreach, agent referral | Highest variance — referral leads can be highly motivated or just curious |

The lead source alone isn't a motivation signal, but it shapes how to frame the conversation:

- **Web leads**: probably comparison-shopping; lead with speed + certainty differentiator
- **Advertising leads**: already self-identified as wanting an investor exit; close on terms
- **Dig leads**: relationship matters more; lead with empathy, don't rush the offer

---

## Lead type taxonomy (Readvise)

Ask when lead source is **Dig Lead** or **Referral** and the field is not already on file (`readvise_property.lead_type`).

| Readvise lead type | When to use |
|---|---|
| **Mailers** | Responded to direct mail / postcard campaign |
| **Paid** | Paid ads (PPC, social, radio with tracking) |
| **Referral** | Agent, prior customer, or partner referral |
| **Organic** | Unpaid web/social inbound |
| **Other** | Does not fit the above |

---

## Skill → Operate label mapping (save path)

Use these when passing `context` to `forvex_save_deal` — recontrol normalizes to Operate Details-tab labels.

| Skill / snake_case input | Operate column value |
|---|---|
| `inherited`, `probate` | Inherited |
| `financial_distress` | Financial distress |
| `landlord_burnout` | Landlord burnout |
| `dig` | Dig Lead |
| `web` | Web |
| `advertising`, `direct_mail` | Advertising |
| `mailers` | Mailers |
| `paid` | Paid |
| `referral` | Referral |
| `organic` | Organic |

---

## Motivation taxonomy (Readvise dropdown)

These are the categories the franchisee selects in Readvise. The skill should use the same terminology and not introduce alternative phrasing.

| Readvise motivation | Signal strength | What it usually means | Brief language |
|---|---|---|---|
| **Inherited** | Strong | Heirs disposing of property; often no emotional anchor, want speed and simplicity. Probate may apply. | "Inherited property — heirs typically prefer speed and certainty over price; verify probate status" |
| **Divorce** | Strong | Court-driven or deadline-driven sale. One spouse usually wants out fast. Beware: both parties may need to sign. | "Divorce sale — deadline likely; ask when decree is and who needs to sign" |
| **Landlord burnout** | Medium-Strong | Tired of management, bad tenants, repairs. Wants a clean exit, sometimes including the tenant. | "Landlord burnout — cash close removes the tenant problem; lead with 'we buy with tenants in place'" |
| **Relocation** | Medium-Strong | Job change, family move. Has a date. Higher motivation if a new home is already under contract. | "Relocating — has a deadline; ask the move date and whether new home is under contract" |
| **Downsizing** | Medium | Life-stage transition (empty nest, retirement). Usually more flexible on timing. | "Downsizing — timing flexible, price still matters; lead with simplicity, not urgency" |
| **Financial distress** | Strong | Behind on payments, tax delinquency, debt pressure, pre-foreclosure. High urgency. | "Financial distress — verify foreclosure timeline, tax sale date, lien status; speed > price" |
| **Other** (free text) | depends | Specified in free text — interpret per the description. | (varies — read the free text) |

When the franchisee leaves motivation as empty or "—" (the leading dash in the Readvise dropdown), treat as **"not stated"** — surface as "no motivation signal captured; treat as market-priced seller until proven otherwise."

---

## Supplementary signals (the "other context" answer)

Beyond the primary Readvise motivation, the franchisee may surface additional signals in free text. These ADD to the motivation read (don't replace it):

### Signals that increase motivation (move band up)

| Signal | Implication |
|---|---|
| Behind on mortgage payments | Foreclosure clock; verify pre-foreclosure timeline |
| Tax delinquency / liens | Tax sale risk; verify county records |
| Code violation notice | Time pressure + remediation cost on seller's books |
| Eviction in progress | Landlord fatigue; cash close removes the tenant problem |
| Vacant property | Holding cost bleed; ask how long it's been empty |
| Major medical event | Tread carefully; lead with empathy, not numbers |
| Bankruptcy filing | Trustee may be involved; complex transaction |
| New home already under contract | Hard deadline; speed > price |
| 90+ days on market | Market fatigue forming |
| Multiple price drops already | Seller acknowledged the ask was high |
| Out-of-state owner (absentee) | Distance friction; usually open to offload |
| Bad tenant / vacancy history | Operational headache, opens negotiation on price |
| Multiple agent changes | Listing trouble; seller is frustrated |

### Signals that lower motivation (move band down)

| Signal | Implication |
|---|---|
| Recent rehab or staged listing | Seller is pricing for retail; investor offers won't land |
| Multiple offers reported | Bidding situation; cash-buyer edge is speed, not price |
| "Just testing the market" said explicitly | Walk |
| Sentimental attachment (raised kids here) | Price will be sticky; lead with empathy not math |
| Listing realtor pushing back hard | Agent is the obstacle, not the seller — ask if direct seller call is possible |
| <30 days on market | Seller is still optimistic |
| Asking close to retail comps | Market-priced seller; not investor-priced yet |

---

## Probability of close — framing

Combine the **primary motivation** (Readvise dropdown) with **supplementary signals** to land on a band. Don't pretend to a precision the data doesn't support.

| Motivation strength + signals | Probability band |
|---|---|
| Strong primary motivation + supplementary positive signal + asking within 10% of MAO | **High** (60–80%) |
| Strong primary motivation alone, OR Medium primary + 1 positive signal; asking 10–20% above MAO | **Medium** (30–50%) |
| Medium primary alone, OR weak signals; asking 20%+ above MAO | **Low** (10–25%) |
| Negative signals dominant (recent rehab, "just testing", retail-priced) | **Walk** (<10%) |
| Motivation = "not stated" | **Unknown** — state explicitly that the franchisee should probe motivation during the meeting |

State the band, name the supporting evidence (Readvise category + supplementary), then let the franchisee make the judgment call.

---

## Questions to suggest the franchisee ask the seller

These come AFTER the brief is written — they go into the "Questions to ask" section. Tailor by Readvise motivation.

### Always ask (regardless of motivation)

1. "What's most important to you in this sale — price, timing, or certainty?"
2. "If we agreed today, when would you ideally want to close?"
3. "What's the biggest concern you have about selling?"

### Tailored by Readvise motivation

**Inherited:** "Has probate been completed?" "How many heirs need to sign?" "Are any belongings still in the home that need to be dealt with?"

**Divorce:** "Do both of you need to be involved in the decision?" "Is there a court-imposed timeline?" "What's the biggest pain point in the situation?"

**Landlord burnout:** "What's the current rent and is it being paid?" "Any eviction in progress?" "Would you want the tenant to stay or go?"

**Relocation:** "When does the move need to happen?" "Is your new home under contract or already closed?" "Do you have flexibility if the timeline shifted?"

**Downsizing:** "What's the next step for you — already have your next place?" "Anything in the house you'd want to leave for the next owner?"

**Financial distress:** "Are there any deadlines we should know about?" "Are you behind on the mortgage or taxes?" "Have you talked to the lender about a workout?"

**Other / Not stated:** "What got you thinking about selling now?" "What's the situation behind the sale?"

### Probe condition / due diligence (always include 2–3)

- "Has anything been recently repaired or replaced?"
- "Any code issues, permits, or open inspections?"
- "When was the [roof / HVAC / plumbing] last touched?"
- "Tenants — current lease, paying, behind?"

Pick 5–7 total tailored to the situation, not all of them.

---

## Red flags / due diligence items to flag in the brief

Things to verify on-site or before contract:

- **Foundation issues** — uneven floors, cracks, exterior settling
- **Roof age** — 20+ years means replacement in the math
- **HVAC age** — 15+ years is a budget item
- **Electrical** — knob-and-tube, panel age, code violations
- **Plumbing** — cast iron, galvanized, polybutylene
- **Water intrusion** — moisture stains, basement, crawlspace
- **Pest** — termites, rodents, mold visible
- **Title** — confirm clean title; ask about liens, judgments, prior bankruptcy
- **Tenants** — leases, deposits, eviction status, condition

Pick the 3–5 most relevant based on property age, condition signals, and lead source.

---

## Talking points by Readvise motivation

The brief picks 3–4 of these to lead with.

### Inherited

- "I work with a lot of families in your situation — there's no rush from my side, but I can move fast if that's what you want."
- "We can buy the house in any condition. Belongings can stay if no one wants to deal with them."
- "All heirs can sign electronically; we coordinate the legal."

### Divorce

- "I can keep things simple. One transaction, no contingencies, you both walk away."
- "We can close on whatever timeline works for the court / decree."
- "What's the easiest path forward for you?"

### Landlord burnout

- "We close as-is, tenants and all. You walk away from the management problem."
- "What's been the worst part of owning this property?"
- "If we agreed today, when does this stop being your headache?"

### Relocation

- "I can match your move date. What's the timeline?"
- "You don't need to come back here. We handle everything remotely if needed."
- "What's the biggest constraint — date, money, or both?"

### Downsizing

- "There's no pressure on timing. We work on your schedule."
- "If there's stuff you don't want to move, it can stay with the house."
- "What's making this the right time?"

### Financial distress

- "I can close in 14 days. Cash. No financing contingency."
- "What's the deadline you're working against?"
- "Have you talked to the lender about a deed-in-lieu or short sale? Sometimes there are better paths than a quick sale."

### Other / Not stated

- Lead with discovery: "Tell me about the situation that brought you to this point."
- Lead with cash-buyer edge: "We buy as-is, close in 14 days, cash, no contingencies. What's most important to you?"

---

## Anti-patterns — never do these

- Never use motivation signals to *manipulate* the seller. Surface them so the franchisee can be empathetic and accurate, not predatory.
- Never treat a null `recorded_lien_balance` as "$0 owed." Winning debt is `parcel.debt.balance`. `none` means unknown.
- Never invent a motivation signal because it would be convenient. If the franchisee said "I don't know anything about them," the brief reads "motivation not stated."
- Never promise a probability band higher than the signals support.
- Never recommend an opening offer above the MAO. Opening below MAO is fine; opening above breaks the buy-box.
- Never include details from a different deal/conversation. Brief is for this address only.
- Never substitute generic "motivation" categories for the Readvise dropdown values — those are the canonical taxonomy.
