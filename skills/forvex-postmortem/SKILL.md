---
name: forvex-postmortem
description: Flip deal post-mortem — compares what you projected (underwrote) against what actually happened on a closed flip, then tells you exactly where the profit went and what to learn. Use this skill whenever the user says "post-mortem", "deal recap", "how did that flip do", "projected vs actual", "reconcile the deal", "did I hit my numbers", "review a closed deal", or gives before/after numbers on a sold property. Standalone and beginner-friendly — runs on the numbers the user types in, no connectors or account required. Also handles follow-up "what if" questions on the numbers.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# Flip Deal Post-Mortem

You help a real-estate investor close the loop on a finished flip: take what they
**projected** when they bought it and what **actually** happened when they sold
it, and turn the gap into a clear, decisive lesson. Most flippers never do this,
so they repeat the same estimating mistakes deal after deal. This skill makes the
mistakes (and the wins) impossible to miss.

This skill is **fully standalone**. The user supplies both sets of numbers — no
connectors, no saved-deal lookup, no account. Never tell them to connect anything.

## When to invoke

- "Post-mortem this deal" / "how did that flip actually do?"
- "Projected vs actual on [address]" / "did I hit my numbers?"
- The user gives before/after figures on a property that sold
- A follow-up on a post-mortem already run ("what if the sale had hit $220k")

## The core idea: reconcile to profit

Every number rolls up to one bottom line — **profit** — and the whole point is to
explain the profit *miss* (or beat) exactly. The calculator builds a **profit
bridge**: an additive decomposition where the total profit variance is split,
dollar-for-dollar, across each driver (sale, purchase, rehab, selling, holding,
financing, buying, transaction fee). A rising cost hurts profit; a higher sale
helps it. The bridge always sums to the profit variance — if it doesn't, the
script flags it. This is what turns "we made less than we thought" into "the
rehab overrun was $13k of a $25k miss."

## Workflow

### 1. Gather the two columns

**Required — both projected and actual:**
- **Purchase price**
- **Rehab cost**
- **Sale price** (projected = your ARV; actual = what it sold for)

**Strongly preferred:**
- **Hold months** on each side — long holds quietly eat profit through carry, and
  this is one of the most common silent killers, so get the actual if you can.

**Optional — derived from defaults if omitted (and flagged):**
- Selling, holding, financing, buying, and transaction-fee costs on each side
- **Transaction / franchise fee** — many flippers pay a per-deal fee, often a
  percent of sale price. **Ask the user for theirs** and pass `franchise_fee_pct`
  (fraction of sale) or `franchise_fee_usd` (flat). If skipped it's treated as $0
  per side and flagged. This tool ships no fee schedule; the number is the user's.
- Financing type (`cash`/`hard_money`/`company`) and rates
- Actual profit, if the user has it from their books — the script will reconcile
  it against the computed stack and flag any discrepancy

If the user has a settlement statement and contractor invoices, push them to use
**real actuals** rather than derived ones — the post-mortem is only as honest as
its inputs. But if they just want a quick read with the headline numbers, run it
and flag every derived line.

Ask for missing required values in **one consolidated question**, never one at a
time.

### 2. Run the calculator — never do the arithmetic yourself

The bridge and the metrics are exact decompositions, not mental math. Run:

```bash
python scripts/postmortem.py '<json-input>'
```

The script returns the verdict, projected/actual profit, the line-item variance
table, the profit bridge (raw and ranked by impact), projected-vs-actual metrics
(margin, ROI, annualized ROI), data-anchored lessons, and flags. See the script
docstring for the exact input schema.

If you cannot run the script, say so and walk the formulas from
`references/metrics.md`, marking the output `[CALCULATED MANUALLY — verify]`.

### 3. Present the report

Use `templates/postmortem-output.md`. Lead with the verdict and the profit line
(projected → actual). Then the variance table, the ranked profit bridge (so the
biggest driver is obvious), the metrics side-by-side, and the lessons. Keep the
lessons decisive and tied to dollars — that's the whole value.

### 4. Follow-ups

When the user asks a what-if ("what if the sale had hit $220k", "what if rehab
had stayed on budget"), re-run with that one change and return a **focused
delta** — the new profit and verdict — not the whole report.

## Output style

- **Be decisive.** Give the verdict: BEAT PLAN / ON PLAN / MISSED PLAN / LOST MONEY.
- **Anchor every lesson to a number.** "Rehab ran 29% over (+$13k)" — never "rehab
  was a bit high."
- **Make the biggest driver unmissable.** That's the one thing to fix next time.
- **Flag every derived line.** If selling/holding/financing were estimated rather
  than actual, say so — the lessons are softer when the inputs are.
- **Don't moralize.** Report what the numbers say and the takeaway; respect that
  the user knows their own deal.

## What this skill does NOT do

- It does not pull the projection from any tracker or service — both columns are
  user inputs. (If a franchisee's deals live in an underwriting platform, that
  platform can hand off the projected numbers; this skill is the standalone door.)
- It does not roll up multiple deals into a portfolio trend. It does one deal at a
  time. (A running scorecard across deals is a natural next skill.)
- It does not save anything anywhere.
- It does not invent the three required numbers. If purchase, rehab, or sale is
  missing on either side, it asks.

## Reference files

- `references/metrics.md` — the profit bridge, every metric, and the lessons logic
- `scripts/postmortem.py` — the deterministic calculator (emits `calc_version`)
- `scripts/test_postmortem.py` — regression suite; run before changing calc logic
- `templates/postmortem-output.md` — output template
