---
name: forvex-presentation
description: Render an already-analyzed HV deal into a richer artifact format — interactive HTML dashboard with charts, a 5-slide deal deck, or a print-ready PDF one-pager. Use when the user asks "render this as a dashboard", "make this a slide deck", "give me a PDF", "show me this visually", or wants to share the analysis with a buyer/partner. Does NOT re-run the math — reads the existing analysis from conversation context or saved MCP analysis.
---

# HV Presentation — Rich Artifact Rendering

You take an already-completed deal analysis (from `forvex-underwriting` earlier in the conversation or from a saved MCP deal analysis) and render it as a richer artifact. You do not re-run the math. You do not change any numbers. You re-format what's already there into a more visual deliverable.

> **Status:** Phase 6 — sketch only. The render targets, chart libraries, and CSS/HTML scaffolding need to be built out before this skill is production-ready. The intent and structure are documented here so it slots cleanly into the architecture when its turn comes.

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

### Mode 1 — Dashboard

Produces an interactive HTML artifact with:

- **KPI tile row:** Verdict (BUY/NEGOTIATE/PASS), Deal Score, Best Strategy, Risk Score
- **Strategy comparison bar chart:** Net profit per strategy (Chart.js bar)
- **Sensitivity curve:** Profit vs. ARV at ±15% range (line chart with markers at ±5%, ±10%, ±15%)
- **Cost-basis donut:** Breakdown of the recommended strategy's cost basis
- **Badge row:** Global badges from analysis
- **Risk component bars:** Market / deal-math / execution
- **Action row:** MAO at target metrics, suggested offer

Optional: a sliders panel that lets the user (in browser) tweak rent or ARV and see the dashboard recompute. Implementation TBD — may require shipping a small precomputed lookup table since the artifact can't shell out to Python.

### Mode 2 — Slide deck

5 HTML slides (use a minimal slide framework like Reveal.js or a custom CSS deck):

1. **Cover** — property address, verdict, headline number, photo placeholder
2. **Strategy comparison** — the 4-strategy table, score column highlighted
3. **Recommended strategy** — cost breakdown + 1-sentence reasoning
4. **Risk + guardrails** — risk score, flags, MAO at target
5. **Action** — recommended offer, financing posture, next step

Designed for screen-share or PDF export. Keep typography big (audience reads from a distance).

### Mode 3 — Printable PDF

Print-CSS HTML that renders cleanly as a single page (or two pages max):

- Header bar: address, verdict, score
- Two-column body: property block + recommended strategy on left, comparison table + risk + MAO on right
- Footer: confidence label, defaults flagged, generation date

User saves the artifact, then prints to PDF via browser.

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

## Reference files (to be built in Phase 6)

- `references/dashboard-template.html` — base HTML/CSS/JS for dashboard mode
- `references/deck-template.html` — base HTML for slide deck
- `references/pdf-template.html` — print-CSS one-pager
- `references/style-guide.md` — colors, typography, layout rules (matches HV brand)
- `references/chart-recipes.md` — which Chart.js config to use for which chart type
