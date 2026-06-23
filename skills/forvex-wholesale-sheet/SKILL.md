---
name: forvex-wholesale-sheet
description: Render an already-analyzed deal into a buyer-facing wholesale deal sheet — a print-ready HTML one-pager you can send a cash buyer, a wholesale desk, or a buyers list. Use when the user says "make a wholesale sheet / buyer flyer / deal sheet for [address]", "package this for a wholesale desk", "something I can send buyers", or "market this contract". Buyer-facing and audience-inverted — it suppresses every operator-internal number (acquisition price, assignment fee/spread, deal score, buy-box fit, verdict, MAO). Does NOT re-run the math; renders the saved analysis through the forvex_build_wholesale_sheet MCP tool.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# Wholesale Sheet — buyer-facing deal sheet

You turn an already-completed deal analysis into a **buyer-facing** wholesale
deal sheet: a single-page, print-ready HTML one-pager a franchisee shares with a
cash buyer, a co-wholesale desk, or a buyers list to market a contract. You do
not re-run the math and you do not change any numbers — the
`forvex_build_wholesale_sheet` MCP tool reads the saved analysis, assembles the
buyer-facing fact set, and renders the sheet.

This is the **inverse audience** of `forvex-presentation`. The presentation skill
renders the *operator's* view (verdict, deal score, buy-box fit, MAO, cost
basis, assignment spread). A wholesale sheet is for the *buyer* and must never
expose any of that. The data-suppression posture is the whole point of this being
a separate skill — see **Hard guardrails** below.

## When to invoke

- "Make a wholesale sheet / buyer flyer / deal sheet for [address]"
- "Package this for a wholesale desk" / "I want to wholesale this"
- "Give me something I can send buyers" / "market this contract"
- After a deal is under contract (or in inventory) and the user wants to dispose of it

Do **not** invoke for the operator's own analysis view — that's `forvex-presentation`.

## Required prerequisites

1. **A completed/saved analysis.** The tool reads it server-side. Preferred handles:
   - conversation context from `forvex-underwriting`
   - `forvex://deal/{deal_id}/analysis`
   - `forvex://property/{property_id}` for the property snapshot
   If there is no existing analysis, refuse: *"I package an existing analysis into a
   buyer sheet. Run `forvex-underwriting` on this property (or load a saved deal)
   first, then ask me for the wholesale sheet."*

2. **An operator-supplied asking price** — the wholesale **ask** (what the buyer
   pays for the contract). This is an operator input, never derived. Ask for it if
   the user hasn't given it. Do **not** prefill it from the offer or contract price.

3. *(Optional)* a **resale + carry** estimate. If the user doesn't give one, leave
   it out — the tool defaults to ~8% of the conservative ARV (agent + closing +
   holding + financing) and flags it as a default so the user can adjust.

## Workflow

### 1. Gather the operator inputs

Ask in one consolidated question if anything is missing:
- **Wholesale asking price** (required).
- *(Optional)* resale + carry estimate.
- *(Optional)* narrative the user wants to lead with — a one-line "the opportunity"
  lede, an "already modernized" list (systems the seller already did), and a
  "why this price" line. Only use **verified** features the user confirms; never
  invent specs or condition claims.

### 2. Call the tool — never assemble the numbers yourself

```
forvex_build_wholesale_sheet({
  deal_id | property_id | address,   // resolve the deal the usual way
  asking_price,                      // required, operator input
  resale_carry?,                     // optional; omit to default to ~8% of ARV
  lede?, already_done?, why_price?,  // optional verified narrative overrides
  brand_name?, brand_contact?        // defaults to the workspace brand
})
```

The tool returns `{ data, html }`:
- `data` — the whitelisted, buyer-safe fact set (subject specs, conservative ARV +
  comps, rounded rehab buckets, buyer economics, compliance flags). It is
  structurally incapable of carrying operator-internal numbers.
- `html` — the self-contained, print-ready one-pager. Present this as the artifact.

If the tool returns an error (e.g. no comp-derived ARV yet, or the deal can't be
resolved), relay it plainly and tell the user what to do (run/refresh comps, save
the deal, supply the address).

### 3. Present the result

- Render the `html` as the deliverable artifact. The user saves it and prints to
  PDF (browser print) to forward to a desk, or lifts the copy into Mailchimp /
  Facebook / an email.
- Give a one-line summary from `data` — conservative ARV, asking, projected buyer
  profit and margin/ROI — so the user can sanity-check before sending.
- If `data.compliance.bpo_pending` is set, tell the user the comp pool was thin and
  the sheet carries a BPO-pending caveat (recommend an independent BPO before
  committing to the ARV). If `data.subject.specs_low_confidence` is set, flag that
  specs are unverified.

## Hard guardrails (compliance)

- **Never surface or ask for** the operator's acquisition/tie-up price, assignment
  fee/spread, deal score, buy-box fit, engine verdict, or MAO. The tool suppresses
  these structurally — do not reintroduce them in your summary, your narrative
  overrides, or by editing the HTML. Rule of thumb: if a number would let the buyer
  back into the operator's margin, it does not go on the sheet.
- **ARV is always labeled "conservative"** and is comp-supported. The upside figure
  is a second scenario, never the headline.
- **Rehab is shown as rounded generic buckets**, never granular line items.
- The sheet carries the required **disclaimer block** (estimates-only, limited-comp
  caveat, verify SF/condition/title, "not an offer or guarantee of value"). Don't
  strip it.
- **Fair-housing-safe copy** — neighborhood/lifestyle language only; no
  protected-class or steering implications in any narrative you supply.

## What this skill does NOT do

- Does not re-run the underwriting math or change any numbers (render only).
- Does not produce actual PDF files — it produces HTML that prints/exports to PDF.
- Does not render the operator's analysis view — that's `forvex-presentation`.
- Does not invent property specs, features, or condition claims.

## MCP notes

- Requires MCP. `forvex_build_wholesale_sheet` owns the assembly, suppression, and
  render; this skill orchestrates inputs and presents the result.
- Prefer resolving the deal via `forvex://deal/{deal_id}/analysis` /
  `forvex://property/{property_id}` over asking the user to paste numbers.
- Output schema is `wholesale.v1`; the readvise "Dispo Kit" UI renders from the
  same tool, so a sheet generated here matches the one generated in-app.
