# Post-Mortem Metrics, Bridge & Lessons

## Profit, the bottom line

Both sides reconcile to profit the same way:

```
profit = sale
       − purchase − rehab − selling − holding − financing − buying − franchise_fee
```

Projected uses your underwritten ARV as "sale"; actual uses the real sale price.

## The profit bridge (the heart of the report)

The total profit variance is `actual_profit − projected_profit`. It decomposes
**exactly** into per-driver contributions:

- **Sale:** `actual_sale − projected_sale` (a higher sale *helps* profit, so the
  sign carries straight through).
- **Each cost line:** `−(actual − projected)` (spending more *hurts* profit, so
  the impact is the negative of the cost change).

Add up all eight contributions and you get the profit variance to the penny. The
script asserts this (`bridge_reconciles`); if it ever fails, something is wrong
with the inputs, not the lesson. Ranking the drivers by absolute impact is what
surfaces the single biggest reason the deal beat or missed plan.

## Derived cost lines (when the user doesn't supply them)

Same engine as the forVEX MAO tool, applied to each side independently:

| Line | Derivation | Default |
|---|---|---|
| Selling | % of that side's sale | 6% |
| Holding | 0.25%/mo of sale × hold months | — |
| Financing | hard money: interest + points on 90% of (purchase+rehab) | 10% + 2 pts |
| Buying | % of purchase | 2% |
| Transaction fee | user-entered % of sale, or flat $ per side | $0 if not set |
| Hold months | fallback when not given | 4 |

Cash deals carry zero financing. Always flag which lines were derived — a lesson
built on a derived cost is weaker than one built on a real invoice.

## Metrics, projected vs actual

- **Margin on sale** = profit ÷ sale price. The headline flip metric.
- **ROI on project cost** = profit ÷ (purchase + rehab). Quick and gross.
- **ROI on all-in** = profit ÷ (every cost line). The truest return on money spent.
- **Annualized ROI** = ROI on all-in × (12 ÷ hold months). Penalizes long holds —
  a 20% return in 3 months annualizes far better than the same 20% over 9 months,
  and this is where slow projects expose themselves.

## Verdict thresholds

Against projected profit:

- **LOST MONEY** — actual profit below zero.
- **BEAT PLAN** — actual ≥ 110% of projected.
- **MISSED PLAN** — actual ≤ 90% of projected (but still positive).
- **ON PLAN** — within ±10%.

If the deal was underwritten to break-even or worse (projected profit ≤ 0), the
verdict judges on absolute outcome instead of a ratio.

## Lessons logic

Each lesson fires off a threshold and is anchored to a dollar or percent:

- **Rehab accuracy** — over/under plan by more than 10%.
- **ARV accuracy** — sale over/under projected ARV by more than 5%.
- **Hold time** — a month or more long (with the extra carry cost) or a month or
  more short.
- **Purchase discipline** — paid more than underwritten.
- **Biggest single driver** — the top of the ranked bridge.
- **Calibration pattern** — if 3+ cost lines came in over plan, the franchisee
  underwrites optimistically and should buffer; if 3+ beat plan, they're
  conservative. This is the meta-lesson that compounds across deals.

The lessons are descriptive and decisive, never preachy. They tell the user what
the numbers say and what to do differently — nothing more.
