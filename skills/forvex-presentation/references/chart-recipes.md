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

## 3. Profit drivers — tornado (floating horizontal bar)

- **Data:** `DATA.drivers = [{name, low, high}]`, one per lever, **sorted by
  `(high − low)` descending** (biggest swing on top). `DATA.baseProfit` = the
  recommended strategy's net profit, shown as the card subtitle (the bars read
  against it). Each bar floats from `low` to `high` profit.
- **Standard moves** (keep consistent across deals):
  ARV ±10% · Rehab ±20% · Hold time ±2 months · Offer/purchase ±5%.
- **Derivation** from the recommended strategy economics (`base_net_profit`,
  `arv`, `rehab`, per-month holding, `offer`, `selling_cost_pct`):
  - ARV ±10%: `profit ± arv × 0.10 × (1 − selling_cost_pct)`
  - Rehab ±20%: `profit ∓ rehab × 0.20`  (more rehab → less profit)
  - Hold ±2 mo: `profit ∓ holding_per_month × 2`
  - Offer ±5%: `profit ∓ offer × 0.05`
  `low/high` = min/max of each pair. **Drop a lever** the analysis can't support
  (e.g. no per-month holding) rather than guessing; flag any defaulted input
  (e.g. `selling_cost_pct` fallback 6%) in the footer.
- **Why tornado, not an ARV curve:** a single-variable ARV line is nearly linear
  and low-insight. The tornado **ranks which input moves profit most** — surfacing
  rehab-overrun risk and showing hold-time as the small lever it usually is — so
  the operator sees what to underwrite tightly and negotiate hardest on.
- Single accent color; the bar's left end is the downside (lower profit). No
  base-line annotation (no plugins) — base profit lives in the card subtitle.

## 4. Risk components — horizontal bar

- **Data:** `DATA.risk = {market, dealMath, execution}`, each `0–100` (higher =
  riskier) from the analysis risk breakdown. `indexAxis:'y'`, x-axis fixed `max:100`.
- **Why horizontal bar:** three labeled magnitudes on a common 0–100 scale; reads
  faster than a radar for 3 components.

## Honesty rules

- Never invent driver swings or risk components the analysis doesn't support —
  drop the lever/card instead, and flag any defaulted input (selling %, holding)
  in the footer.
- Keep the same 4 cards across franchisees; don't add bespoke chart types per deal
  (consistent visual vocabulary).
- Dashboard stays on the fixed forVEX Edge light palette (it's a shareable
  artifact, not a theme-reactive UI widget).
