---
name: forvex-presentation
description: Render an already-analyzed forVEX deal, or a seller appointment that just happened, into a richer artifact — interactive HTML dashboard with charts, a 5-slide deal deck, a print-ready PDF one-pager, an internal deal sheet, an appointment debrief, or a rehab scope sheet. Use when the user asks "render this as a dashboard", "make this a slide deck", "give me a PDF", "show me this visually", "wrap up the appointment", "debrief that meeting", "what happened at the appointment", "appointment recap", "render the rehab scope", or "show me the estimate breakdown". Does NOT re-run the math — reads the existing analysis from conversation context or saved MCP analysis, and the appointment from the operator's own recount.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# forVEX Presentation — Rich Artifact Rendering

You take something that already happened — a completed deal analysis (from `forvex-underwriting` earlier in the conversation or from a saved MCP deal analysis), a seller appointment the operator just walked out of, or a saved REbuild rehab estimate — and render it as a richer artifact. You do not re-run the math. You do not change any numbers. You do not reconstruct events you weren't told about. You re-format what's already there into a more visual deliverable.

> **Status:** Phase 6 — **complete.** Built and production-ready: Mode 1 (Dashboard),
> Mode 2 (Slide deck), Mode 3 (Printable PDF), Mode 4 (Internal deal sheet —
> operator/confidential, strategy-aware), Mode 5 (Appointment debrief —
> operator/confidential, renders the conversation rather than the economics),
> and Mode 6 (Rehab scope — renders a REbuild estimate reconciled against the
> walkthrough). See `references/`.

## When to invoke

- "Render this as a dashboard"
- "Make a slide deck for this deal"
- "Give me a PDF I can share with [buyer / capital partner / spouse]"
- "Show me a chart of the sensitivity"
- "Wrap up the appointment" / "debrief that meeting" / "appointment recap"
- After a deal analysis, when the user wants something more than markdown
- After a seller appointment, when the user narrates how it went (Mode 5)
- "Render the rehab scope" / "show me the estimate breakdown" / "does this estimate match what we saw?" (Mode 6)

## Required input — per mode

**Modes 1–4 (economics artifacts)** need a completed underwriting analysis in the
conversation context or available from MCP. Preferred sources:

- conversation context from `forvex-underwriting`
- `forvex://deal/{deal_id}/analysis`
- `forvex://property/{property_id}` for property facts that accompany a saved analysis

If there isn't an existing analysis to read:
- Refuse: "I render existing analyses into rich formats. Run `forvex-underwriting` on a property first, or load a saved deal analysis, then ask me to render it."

**Mode 5 (appointment debrief)** is different: its input is the **operator's
recount of the appointment** — who was there, what was said, what was offered,
what happens next. An underwriting analysis is *optional* garnish that fills the
numbers strip; without one, drop that block and render the debrief anyway. A
franchisee can debrief a walk-through on a property they have not underwritten.

If the user asks for a debrief without telling you how the appointment went:
- Ask for it. Do not reconstruct an appointment from property data — the whole
  value of this artifact is that it records what actually happened in the room.

**Mode 6 (rehab scope)** needs a **saved REbuild estimate** — load it with
`forvex_get_estimate`. Walkthrough observations are optional but are what make
the artifact worth rendering: with them you get the reconciliation block, without
them you render the estimate and state plainly that it is unreconciled.

If there's no saved estimate:
- Refuse and route: "There's no saved estimate on this project yet. Run
  `forvex-rehab-estimator` to draft one, then ask me to render it."

## Render modes

### Mode 1 — Dashboard  *(built)*

An interactive HTML artifact (Chart.js from CDN) with: KPI tile row (Verdict,
Deal Score, Best Strategy, Risk), badge row, and four charts — net profit by
strategy (bar), cost basis → net profit (waterfall), profit drivers (tornado),
risk components (horizontal bar) — plus an action strip (MAO, suggested
offer, financing) and the confidence/defaults footer.

**Workflow:**

1. Read `references/style-guide.md`, `references/dashboard-template.html`, and
   `references/chart-recipes.md` (which chart for which data + the sensitivity
   derivation).
2. Fill the static `{{TOKENS}}` (address, verdict, KPI tiles, action, footer) and
   the `DATA` object's arrays from the analysis — the token list and each field's
   source are in the template's top comment:
   - `DATA.strategies` from `all_strategies` (`best:true` on the recommended one).
   - `DATA.bridge` = ARV (`total`) → each cost (`down`: Purchase, Rehab, Holding,
     Selling, Fees) → Net profit (`total`); the downs must sum to ARV − net.
   - `DATA.drivers` + `DATA.baseProfit`: compute the profit swing for each lever
     (ARV, rehab, hold, offer) from the recommended strategy economics per
     `chart-recipes.md`; sort by swing desc and flag any defaulted input.
   - `DATA.risk` = market / deal-math / execution, each 0–100.
   - `DATA.badges` from the analysis global badges.
3. **Omit a card** if the analysis lacks its data rather than faking a chart.
4. Output the filled HTML as one self-contained artifact. On iPhone Claude, warn
   that charts may have reduced interactivity but remain viewable.

### Mode 2 — Slide deck  *(built)*

5 self-contained HTML slides (custom CSS deck — no framework): Cover · Strategy
comparison · Recommended strategy · Risk + guardrails · Action. Arrow-key/click
nav with dot indicators; prints to PDF one slide per landscape page. Big type for
screen-share.

**Workflow:**

1. Read `references/style-guide.md` and `references/deck-template.html` (token list
   in its top comment).
2. Fill the `{{TOKENS}}` from the analysis:
   - Slide 2: **repeat the `<tr>`** (see `STRATEGY_ROWS`) per strategy, `class="best"`
     on the recommended one.
   - Slide 3: recommended cost-basis lines + `{{REC_REASONING}}` (one sentence).
   - Slide 4: `{{RISK_FLAGS}}` is a set of `<li>` items (or a single "None" `<li>`);
     `{{MAO}}` / `{{WALK_ABOVE}}` from the offer stack.
   - Slide 5: `{{SUGGESTED_OFFER}}`, `{{FINANCING}}`, `{{NEXT_STEP}}` (the concrete
     next action).
3. **Drop a row/line** the analysis lacks rather than inventing it.
4. Output the filled HTML as one self-contained artifact. On iPhone Claude, note
   that nav still works by tapping the on-screen Prev/Next.

### Mode 3 — Printable PDF  *(built)*

A print-CSS HTML one-pager: header bar (address, verdict, deal score, best
strategy), KPI strip (ARV · target offer · rehab · entry % · net profit),
two-column body (property facts + recommended cost basis left; strategy
comparison + risk + MAO/action right), footer (confidence, defaults flagged,
date, brand). User saves the artifact and prints to PDF via browser.

**Workflow:**

1. Read `references/style-guide.md` (palette, fonts, verdict color mapping, layout
   rules) and `references/pdf-template.html` (the scaffold).
2. Map the saved analysis onto the template's `{{TOKENS}}` — the full token list
   and the analysis field each comes from is documented in the comment block at
   the top of `pdf-template.html`. Key mappings:
   - `{{VERDICT}}`/`{{VERDICT_CLASS}}` from `verdict` (class = `buy`/`negotiate`/`pass`).
   - `{{DEAL_SCORE}}`, `{{RISK_SCORE}}` from `deal_score` / `risk_score`.
   - KPI strip + cost basis from the recommended strategy's economics.
   - Strategy comparison: **repeat the `<tr>`** (see the `STRATEGY_ROWS` marker)
     once per strategy, `class="best"` on the recommended one.
   - Risk component bar widths are CSS percentages (e.g. `width:22%`).
3. **Omit a section** (drop the block) when the analysis lacks the data rather than
   printing `{{TOKENS}}` or inventing numbers.
4. Output the filled HTML as a single self-contained artifact. Default brand is
   forVEX Edge; override `--accent` / `{{BRAND}}` only if the workspace specifies.

Operator artifact — it shows verdict, score, MAO, cost basis. Never strip the
confidence/defaults footer.

### Mode 4 — Internal deal sheet  *(built)*

A richer, **strategy-aware**, operator/**confidential** one-pager — the internal
twin of `forvex-wholesale-sheet`. It deliberately shows what the buyer sheet
suppresses: CRG cost basis / spread / fee, deal id, buy-box fit, deal score.
**Never give it to a buyer.** Sections: confidential kicker (stage · deal id ·
tag), verdict + one-line thesis, stats strip, **CRG economics** card, a **ladder**
(exit or offer), **buy-box fit** checklist, **what the asset supports** (strategy
matrix with margin + fit pills, CRG lane highlighted), **ARV & confidence** basis
table, and **risk flags + numbered next steps**.

**Workflow:**

1. Read `references/style-guide.md` and `references/internal-deal-sheet-template.html`
   (token list + the strategy-aware instructions in its top comment).
2. **Make the economics card + ladder match the recommended play:**
   - Flip / wholetail (self-execute): economics rows = Purchase, Rehab, Holding,
     Selling, Fees → net headline "Net profit"; ladder = offer ladder (or omit);
     show MAO among the guardrails.
   - Wholesale / paper: economics rows = Contract/tie-up (in), Resell (out), Gross
     spread, Less double-close costs → net headline "Net to CRG"; ladder = exit
     ladder (Resell at · Flipper net · Margin · Your fee), star the sweet spot.
3. Fill the repeatable blocks (buy-box flags, strategy matrix with the CRG lane,
   ARV basis rows, risk flags, next steps). **Drop a row/block** the analysis
   can't support rather than inventing it.
4. Output one self-contained artifact. Keep the "Internal · Confidential" kicker
   and the internal disclaimer footer — this sheet carries cost basis and fee.

### Mode 5 — Appointment debrief  *(built)*

The **after** bookend to `forvex-appointment-prep`. Modes 1–4 render the deal's
**economics**; this renders the **conversation** — who has to say yes, what they
pushed back on, how the hour went, what we learned on site, where the deal
honestly stands, and what happens next. Mobile-first (it gets read in a truck),
prints clean, operator/**confidential**.

Sections: header slab (address · attendees · who ran it · offer made · where it
stands · **next touch**) · The read (two paragraphs) · **Who has to say yes**
(the decision-map spine with stance dots) · Objections (each with an
open/partly/handled chip) · How the hour went (timeline) · What we learned ·
Where this actually stands · Next actions (checkbox, owner, when) · optional
numbers strip with a **mandatory** confidence line.

**Workflow:**

1. Read `references/style-guide.md` and `references/appointment-debrief-template.html`
   (token list, repeatable blocks, and the voice note in its top comment).
2. Fill from the operator's recount, not from property data:
   - `PEOPLE_ROWS` — one `.person` per decision-maker, stance
     `yes|maybe|swing|unknown`. Mark the **swing vote** (the person who decides
     on paper without having met you) — naming it is the point of the block.
     **One person is a valid decision map**; never invent a spine to fill it.
   - `OBJECTIONS` — what they actually said, how it was met, and an honest
     status chip. "Defused, not closed" is a real answer; prefer it to a
     flattering one. Drop the whole block if nothing was raised.
   - `TIMELINE`, `LEARNED` — condition facts, cost surprises, and any **play
     change** (e.g. retail flip → wholetail).
   - `NEXT_ACTIONS` — each one closes a named unknown, with an owner and a date.
     If an action doesn't close an unknown, it is a chore; leave it out.
   - Numbers strip + confidence line: **both or neither.** Only when a saved
     analysis exists, and never re-derived here.
3. **Do not write to the deal.** Render, then offer the handoff (below).
4. Output one self-contained artifact. Keep the "Internal · Confidential" tag
   and the disclaimer footer.

**Confidentiality — stricter than Mode 4.** This artifact carries named third
parties, their family and financial situation, and our own negotiation posture
("don't counter unprompted", "let the expiry pass quietly"). Leaked to the
seller it does more damage than a cost basis would.

- Render it **inline**, or save it locally. **Never publish it as a shareable
  artifact URL.**
- First names and roles only. Never DOB, SSN, account numbers, or medical detail
  beyond what bears on the transaction.
- Never hand it to a seller, an heir, an agent, or a buyer.

**After rendering — hand off, don't write.** A debrief naturally produces writes,
and this skill does not write (see *What this skill does NOT do*). Offer them:

- the touch itself → **`forvex-activity-log`** (`forvex_log_activity`)
- a pipeline move the appointment caused, e.g. LEAD → OFFER →
  **`forvex-deal-disposition`** (`forvex_update_deal_disposition`)

Say what you'd log and let the user confirm; don't log silently.

### Mode 6 — Rehab scope  *(built)*

Renders a saved **REbuild estimate** and reconciles it against what the operator
actually saw on site. The engine never walked the house; the operator did. That
gap is the reason this mode exists — it is the only artifact in the system that
crosses a REbuild estimate with REdeal walkthrough facts.

Sections: header slab (property · estimate revision · **lock chip** · total ·
$/sf · contingency) · The read · **Where the money goes** (category weight bars)
· **Estimate vs. what we saw** (the reconciliation, the signature block) ·
operator-lane vs fallback scope cards · what survives in the operator lane ·
**Not in this scope** (exclusions) · full line-item table with SKUs · what to
verify before this becomes a build budget.

**Workflow:**

1. Read `references/style-guide.md` and `references/rehab-scope-template.html`
   (tokens, repeatable blocks, and the numbers-discipline note in its comment).
2. Load the estimate with `forvex_get_estimate`. Every dollar figure comes from
   it verbatim — see *The one rule* and *Numbers discipline* below.
3. Fill `CAT_ROWS`, `REC_ROWS`, `LANE_ITEMS`, `EXCLUSIONS`, `LI_SECTION` /
   `LI_ROW`, `NEXT_CHECKS`. Each `NEXT_CHECKS` item resolves a flagged or
   missing line from the reconciliation.
4. **Do not write to the estimate.** Render, then offer the handoff (below).
5. Output one self-contained artifact. Keep the "Internal · Confidential" tag
   and the provenance footer.

**The one rule — reconcile against observations, never against the price book.**

Every reconciliation row must cite a **stated observation** ("the family said
both AC units were already replaced"). You flag that a line may not be *needed*.
You never argue a line is priced *wrong* — unit costs, category rates and the
engine total are the engine's authority, full stop. No observation, no flag.

This is what keeps Mode 6 compatible with `forvex-project-status`, which is
forbidden from editorializing on an estimate at all. Status reports the numbers;
Mode 6 reports the numbers **against the visit**. If you have no walkthrough
observations, drop the reconciliation block and say the estimate is unreconciled
— do not invent what was seen.

**Numbers discipline** (the template's comment carries the full list):

- Never recompute, re-derive or round a total. `forvex_get_estimate` is the
  source; `forvex-project-status`'s "never recompute" rule applies here too.
- A figure shown twice must be **byte-identical** in both places. A scope card
  reading `~$10,000` above a detail block reading `$9,057` is a defect.
- Category **bar widths are share of subtotal** — the same denominator as the
  percentage label beside them, so bar and number agree.
- Any figure **not** from the engine (a roof range, a market quote) is marked
  `class="outside"` and named in `{{OUTSIDE_NOTE}}`. An operator's guess must
  never inherit price-book authority.
- When reconciliation rows carry flags, `{{CONTINGENCY_NOTE}}` **must** comment
  on whether the contingency covers the exposure. A 5% contingency against 30%
  of the budget in question is a finding, not a footnote.
- **No deal economics here.** Resale %, ARV, margin and hold belong to the deal
  one-pager. Reference it; don't restate it.

**After rendering — hand off, don't write.** Same rule as Mode 5:

- scope or dollar changes → **`forvex-change-order`** (refused on a locked
  estimate — the lock chip tells you before you try)
- progress notes with no scope change → **`forvex-project-update`**

## Output

The skill always produces a **single self-contained HTML artifact** (no external dependencies beyond CDN-loaded chart libraries). Claude renders it inline.

For mobile (iPhone Claude), warn the user that the artifact may have reduced interactivity but should still be viewable.

## Buyer-facing? Use forvex-wholesale-sheet instead

This skill renders the **operator's** view — verdict, deal score, buy-box fit,
MAO, cost basis, assignment spread. Never hand that to a buyer. When the user
wants something to send a **cash buyer, a wholesale desk, or a buyers list**
("make a wholesale sheet / buyer flyer", "package this for a desk", "something I
can send buyers"), route to **`forvex-wholesale-sheet`** — it renders an
audience-inverted sheet that structurally suppresses every operator-internal
number. Do not build a "buyer mode" of this skill.

The **internal deal sheet** (Mode 4) is the *operator* twin of that buyer sheet —
it deliberately shows the suppressed numbers (cost basis, spread, fee, buy-box,
score) for internal use. Keep the two straight: buyer → `forvex-wholesale-sheet`;
internal/desk/partner → Mode 4 here.

The **appointment debrief** (Mode 5) is stricter still — it is operator-eyes-only
and must never be published as a shareable link. See Mode 5's confidentiality
rules.

The **rehab scope** (Mode 6) is internal too: it carries cost basis, the operator
lane, and scope no seller has agreed to. It is **not a contractor bid** — don't
let it be handed to a trade as one.

## Before vs. after the appointment

Don't confuse the two ends of an appointment:

| The user wants | Skill |
|---|---|
| To walk into a meeting prepared — numbers, offer range, seller posture, questions | **`forvex-appointment-prep`** |
| To capture a meeting that already happened — decision map, objections, next actions | **Mode 5 here** |
| To log the touch on the deal timeline | **`forvex-activity-log`** |
| To move the deal's pipeline status | **`forvex-deal-disposition`** |

`forvex-appointment-prep` produces a *prep brief*; Mode 5 produces a *debrief*.
Same appointment, opposite ends.

## Rendering a REbuild estimate (Mode 6) vs. checking one

This skill lives in the REdeal lane but Mode 6 renders a REbuild artifact. Keep
the boundary clean:

| The user wants | Skill |
|---|---|
| A fast read on project state — total, variance, lock, recent activity | **`forvex-project-status`** (read-only, **never editorializes**) |
| The estimate rendered, and reconciled against what they saw on site | **Mode 6 here** |
| To change scope or dollars | **`forvex-change-order`** |
| To log progress with no scope change | **`forvex-project-update`** |
| To draft a new estimate | **`forvex-rehab-estimator`** |

`forvex-project-status` is explicitly barred from commenting on whether a rehab
is too high, too low, or misallocated. Mode 6 is not a way around that rule — it
earns its commentary by citing **observations from the visit**, never by
disagreeing with the price book. See *The one rule* under Mode 6.

## What this skill does NOT do

- Does not re-run the math
- Does not pull new data
- Does not write to the deal — no activity logs, no disposition moves, no saved
  analyses. It renders and then hands off (see Mode 5)
- Does not produce actual PDFs or PPTX files — it produces HTML that can be saved/printed/screen-captured into those formats
- Does not invent visualizations beyond the modes listed above (keep the visual vocabulary consistent across all franchisees' decks)

## MCP notes

- Prefer MCP resources when available instead of asking the user to paste numbers back into the conversation.
- `forvex://deal/{deal_id}/analysis` is the preferred saved-analysis handle.
- `forvex://property/{property_id}` can supply the property snapshot that travels with the presentation.
- `forvex://workspace/{workspace_id}/buy-box` is framing context only. It should never change the saved underwriting numbers you render.

## Reference files

- `references/pdf-template.html` — print-CSS one-pager ✅ **built**
- `references/internal-deal-sheet-template.html` — operator/confidential, strategy-aware ✅ **built**
- `references/style-guide.md` — palette, typography, layout, verdict colors ✅ **built**
- `references/dashboard-template.html` — interactive Chart.js dashboard ✅ **built**
- `references/chart-recipes.md` — which Chart.js config for which chart type ✅ **built**
- `references/deck-template.html` — 5-slide deck (nav + print) ✅ **built**
- `references/appointment-debrief-template.html` — appointment debrief, operator/confidential ✅ **built**
- `references/rehab-scope-template.html` — REbuild estimate + walkthrough reconciliation, operator/confidential ✅ **built**
