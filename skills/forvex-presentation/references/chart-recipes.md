# forVEX Presentation — Chart Recipes

Chart.js (v4, UMD from cdnjs) configs for the **dashboard** mode. The working
implementations live in `references/dashboard-template.html` — this file explains
*which* chart for *which* data and the conventions to keep consistent. When in
doubt, copy the template's config and only swap the data.

## Conventions (all charts)

- **Library:** Chart.js 4.x via `cdnjs.cloudflare.com`. No plugins.
- **Fonts:** numbers/axes in `IBM Plex Mono`; legends/labels may use `Archivo`.
- **Palette** (from `style-guide.md`): accent `#EA580C`, then `#0F766E`, `#4F46E5`,
  `#9333EA`, neutral gray `#C8C3BA`. The **recommended** strategy / primary series
  is always accent; everything else is gray or the secondary ramp.
- `responsive:true, maintainAspectRatio:false` inside a fixed-height `.chart-box`
  (≈210px). Money ticks abbreviate to `$Nk`; tooltips show full `$N`.
- Color is never the only signal — tooltips and labels carry the number.

## 1. Net profit by strategy — vertical bar

- **Data:** `DATA.strategies = [{name, netProfit, best}]` from `all_strategies`
  (one bar per strategy; `best:true` on `best_strategy`).
- **Why bar:** discrete comparison across the 3–4 strategies.
- Recommended bar = accent, others = gray (`s.best ? accent : gray`). No legend.

## 2. Recommended cost basis — doughnut

- **Data:** `DATA.costBasis = [{label, amount}]` — the recommended strategy's cost
  components (Purchase, Rehab, Holding, Selling, Fees). Use the same component
  lines the PDF one-pager's cost-basis table uses.
- **Why doughnut:** part-to-whole of where the money goes. `cutout:'58%'`, legend
  right. Colors cycle accent → secondary ramp → gray.

## 3. Profit sensitivity to ARV — line

- **Data:** `DATA.sensitivity = [{label, profit}]` at ARV deltas
  `-15%, -10%, -5%, 0%, +5%, +10%, +15%`. Emphasize the `0%` point (radius 5).
- **Source:** use the analysis's sensitivity block if present. If it isn't,
  **derive** it from the recommended strategy: a $1 change in resale moves profit
  by roughly `(1 − selling_cost_pct)` dollars, so
  `profit(delta) ≈ base_net_profit + (ARV × delta) × (1 − selling_cost_pct)`.
  Use the analysis's `selling_cost_pct` (default 6% only if absent, and then add a
  defaults-flag note in the footer). Label the card "approx." if derived.
- **Why line:** continuous response of profit to a moving input.

## 4. Risk components — horizontal bar

- **Data:** `DATA.risk = {market, dealMath, execution}`, each `0–100` (higher =
  riskier) from the analysis risk breakdown. `indexAxis:'y'`, x-axis fixed `max:100`.
- **Why horizontal bar:** three labeled magnitudes on a common 0–100 scale; reads
  faster than a radar for 3 components.

## Honesty rules

- Never invent sensitivity points or risk components the analysis doesn't support —
  omit the card instead, or mark it "approx." when derived (sensitivity only).
- Keep the same 4 cards across franchisees; don't add bespoke chart types per deal
  (consistent visual vocabulary).
- Dashboard stays on the fixed forVEX Edge light palette (it's a shareable
  artifact, not a theme-reactive UI widget).
