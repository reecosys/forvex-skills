# forVEX Presentation — Style Guide

The visual vocabulary for **operator-facing** rendered artifacts (dashboard,
deck, PDF one-pager, internal deal sheet, appointment debrief). Keep it consistent across all render modes and all
franchisees so a forVEX deal artifact is instantly recognizable.

> **Audience reminder.** These artifacts are the **operator's** view — they show
> verdict, deal score, MAO, cost basis, assignment spread, risk. That is the
> opposite posture from `forvex-wholesale-sheet` (buyer-facing, those numbers
> suppressed). Do not blur the two. This style guide is the internal/forVEX Edge
> identity; the buyer sheet has its own (editorial Cobb Resource Group) look.

## Brand identity

forVEX Edge — a **business-intelligence** feel: confident, numeric, clean. Not
a luxury editorial sheet (that's the buyer side). Think dashboard, not brochure.

## Palette (CSS variables — keep these names across templates)

```css
:root{
  --paper:#FFFFFF;        /* card / sheet background */
  --paper-2:#FAFAF9;      /* subtle panel fill */
  --ink:#1A1714;          /* primary text */
  --ink-soft:#6B6862;     /* secondary text, labels */
  --line:#E7E3DC;         /* hairlines, borders */
  --accent:#EA580C;       /* forVEX orange — primary accent */
  --accent-soft:#FFF1E8;  /* accent tint fill */
  /* verdict / status */
  --buy:#15803D;   --buy-bg:#E8F3EC;
  --negotiate:#B45309; --negotiate-bg:#FBF0DD;
  --pass:#B91C1C;  --pass-bg:#FBEAEA;
  /* charts (dashboard mode) — categorical, colorblind-safe */
  --c1:#EA580C; --c2:#0F766E; --c3:#4F46E5; --c4:#9333EA;
  /* stance (appointment debrief) — ALIASES, never new hex */
  --yes:var(--buy);         --yes-bg:var(--buy-bg);
  --maybe:var(--negotiate); --maybe-bg:var(--negotiate-bg);
  --unknown:#6B6862;        --unknown-bg:#F0EDE7;
}
```

**Stance colors alias the verdict palette — they never introduce new hex.** A
franchisee who overrides brand tokens must get one color system, not two. The
"swing vote" stance is the accent ring (`--accent`), deliberately distinct from
green/amber because it is a *person*, not a verdict.

Tokenize brand so a franchisee can override `--accent` / logo / contact without
touching layout. Default is forVEX orange.

## Verdict color mapping (always)

| Verdict | Text var | Bg var |
|---|---|---|
| BUY / STRONG_BUY / LEAN_BUY | `--buy` | `--buy-bg` |
| NEGOTIATE / CONDITIONAL / REVIEW | `--negotiate` | `--negotiate-bg` |
| PASS / LEAN_PASS / STRONG_PASS | `--pass` | `--pass-bg` |

## Typography

- **Display / headings:** `Fraunces` is the buyer sheet's serif — do NOT use it
  here. Operator artifacts use a grotesque sans for a BI feel: **`Archivo`**
  (Google Fonts), weights 400/500/600/700.
- **Numbers / metrics:** a monospace for tabular figures — **`IBM Plex Mono`**
  (Google Fonts), 500/600. Always `font-variant-numeric: tabular-nums`.
- Scale: section eyebrow 10px uppercase tracking-wide `--ink-soft`; section title
  13px 600; hero metric 34–40px mono 600; KPI number 18–20px mono 600; body 12px.
- Sentence case for labels. No ALL-CAPS sentences (eyebrows/labels only).

## Layout rules

- Max one printed page (two pages absolute max). Letter, 12mm margins.
- **Header bar:** address + location left; verdict pill + deal score + best
  strategy right; hairline under.
- **KPI strip:** 5 cells — ARV · Target offer · Rehab · Entry % · Net profit.
- **Two-column body:** left = property facts + recommended-strategy cost basis;
  right = strategy comparison table + risk + MAO/action.
- **Footer:** confidence label, defaults-flagged note, generation date, brand.
- 0.5px hairlines (`--line`). `rx` 4–8px. Flat — no gradients, no drop shadows in
  print.

## Print CSS (every template)

```css
html{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }
@media print{
  body{ background:#fff; padding:0; }
  .sheet{ box-shadow:none; border:0; max-width:100%; }
  @page{ size:letter; margin:12mm; }
}
@media(max-width:680px){ .grid{ grid-template-columns:1fr; } }
```

**Dark panels must be lightened for print.** `print-color-adjust:exact` is on, so
a dark header slab or economics card otherwise prints as a solid block of ink.
Invert it to white-on-ink-border in `@media print`, and put `break-inside:avoid`
on every repeated item (`.person`, `.obj`, `.act`, rows) — not just on cards.

## Hard rules

- Self-contained HTML. Only CDN allowed: Google Fonts (+ Chart.js for dashboard).
- Never re-run or alter numbers — render only what the analysis provides.
- Show `confidence` and flag any defaulted assumptions in the footer — operator
  artifacts must be honest about how firm the inputs are.
- Color is never the only signal — verdict/risk also carry a text label.
- **Confidentiality tiers.** Modes 1–3 are operator artifacts. Mode 4 adds a red
  `--confidential` tag and carries cost basis + fee. **Mode 5 (appointment
  debrief) is the most sensitive artifact in the set** — it carries named third
  parties, their family and financial situation, and our negotiation posture.
  Render it inline or save it locally; **never publish it as a shareable artifact
  URL**, and never hand it to a seller, heir, agent, or buyer.
- **Third-party PII (Mode 5).** First names and roles only. Never DOB, SSN,
  account numbers, or medical detail beyond what bears on the transaction.
- **Dates carry the year, one format throughout** ("Aug 25, 2026"). Mixed or
  bare-month dates on a record read weeks later are a real failure mode.
- **Internal deal sheet (Mode 4):** same forVEX Edge identity, plus a confidential
  red tag (`--confidential:#B91C1C`) in the kicker and a dark ink economics card.
  It is operator/confidential and shows cost basis + fee — keep the "Internal ·
  Confidential" kicker and internal disclaimer; never hand it to a buyer.
