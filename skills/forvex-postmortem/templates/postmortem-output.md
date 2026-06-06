# Post-Mortem Output Template

Use this structure. Keep it tight and decisive. Fill from the
`scripts/postmortem.py` JSON. Don't show these comments to the user.

---

# Post-Mortem: {address or "this deal"}

**{verdict}** — projected **${projected_profit}** → actual **${actual_profit}**
({profit_variance} / {profit_variance_pct}%)

<!-- One sentence framing the headline: e.g. "You cleared $3.4k on a deal you
underwrote for $29k — an $25.5k miss, almost all of it rehab." -->

**Where the profit went** *(ranked by impact)*

| Driver | Projected | Actual | Profit impact |
|---|---|---|---|
<!-- Walk profit_bridge_ranked top to bottom. Show + for help, − for hurt.
Only list drivers with non-trivial impact; collapse the near-zero ones into a
single "everything else" row if it keeps it clean. -->
| Rehab | $45,000 | $58,000 | −$13,000 |
| Sale | $220,000 | $213,000 | −$7,000 |
| … | | | |

**The numbers, side by side**

| | Projected | Actual |
|---|---|---|
| Profit | ${proj.profit} | ${act.profit} |
| Margin on sale | {proj.margin}% | {act.margin}% |
| ROI (all-in) | {proj.roi}% | {act.roi}% |
| Annualized ROI | {proj.ann}% | {act.ann}% |
| Hold (months) | {proj.hold} | {act.hold} |

**What to take from it**

<!-- Render each item in `lessons` as a bullet. They're already dollar-anchored
and decisive — don't water them down. Put the biggest-driver and calibration
lessons last as the summary punch. -->

<!-- If any derived_lines were used, add one line: "Heads up — selling, holding,
and financing were estimated, not pulled from actuals. Plug in your real closing
and invoice numbers for a sharper read." -->

**Try a what-if:**
- "What if the sale had hit my ARV?"
- "What if rehab had stayed on budget?"
- "Recalc with my real carrying costs: $X"

<!-- If flags.lost_money is true, lead with empathy but stay factual — the point
is the lesson, not the wound. If a profit mismatch flag is true, surface it:
"Your booked profit (${...}) differs from what the line items add up to (${...})
— worth checking which costs aren't captured above." -->
