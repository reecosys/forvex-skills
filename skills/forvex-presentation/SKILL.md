---
name: forvex-presentation
description: Render an already-analyzed HV deal into a richer artifact format — interactive HTML dashboard with charts, a 5-slide deal deck, or a print-ready PDF one-pager. Use when the user asks "render this as a dashboard", "make this a slide deck", "give me a PDF", "show me this visually", or wants to share the analysis with a buyer/partner. Does NOT re-run the math — reads the existing analysis from conversation context or saved MCP analysis.
---

# HV Presentation — Rich Artifact Rendering

You take an already-completed deal analysis (from `forvex-underwriting` earlier in the conversation or from a saved MCP deal analysis) and render it as a richer artifact. You do not re-run the math. You do not change any numbers. You re-format what's already there into a more visual deliverable.

> **Status:** Phase 6 — **complete.** All three modes are built and production-ready:
> Mode 1 (Dashboard), Mode 2 (Slide deck), Mode 3 (Printable PDF). See `references/`.

## When to invoke

- "Render this as a dashboard"
- "Make a slide deck for this deal"
- "Give me a PDF I can share with [buyer / capital partner / spouse]"
- "Show me a chart of the sensitivity"
- After a deal analysis, when the user wants something more than markdown

## Required prerequisite

There must be a completed underwriting analysis in the conversation context or available from MCP. Preferred sources:

- conversation context from `forvex-underwriting`
- `forvex://deal/{deal_id}/analysis`
- `forvex://property/{property_id}` for property facts that accompany a saved analysis

If there isn't an existing analysis to read:
- Refuse: "I render existing analyses into rich formats. Run `forvex-underwriting` on a property first, or load a saved deal analysis, then ask me to render it."

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

## What this skill does NOT do

- Does not re-run the math
- Does not pull new data
- Does not produce actual PDFs or PPTX files — it produces HTML that can be saved/printed/screen-captured into those formats
- Does not invent visualizations beyond the modes listed above (keep the visual vocabulary consistent across all franchisees' decks)

## MCP notes

- Prefer MCP resources when available instead of asking the user to paste numbers back into the conversation.
- `forvex://deal/{deal_id}/analysis` is the preferred saved-analysis handle.
- `forvex://property/{property_id}` can supply the property snapshot that travels with the presentation.
- `forvex://workspace/{workspace_id}/buy-box` is framing context only. It should never change the saved underwriting numbers you render.

## Reference files

- `references/pdf-template.html` — print-CSS one-pager ✅ **built**
- `references/style-guide.md` — palette, typography, layout, verdict colors ✅ **built**
- `references/dashboard-template.html` — interactive Chart.js dashboard ✅ **built**
- `references/chart-recipes.md` — which Chart.js config for which chart type ✅ **built**
- `references/deck-template.html` — 5-slide deck (nav + print) ✅ **built**
