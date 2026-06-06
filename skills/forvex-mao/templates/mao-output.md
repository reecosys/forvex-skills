# MAO Output Template

Use this structure. Keep it scannable — this is often read on a phone. Fill from
the `scripts/mao.py` JSON. Don't show this template's comments to the user.

---

**Max Allowable Offer: ${detailed_mao}**
*(at your {target_margin_pct}% target margin — ${target_profit_usd} profit)*

This is the most you can pay on {address-or-"this property"} and still clear
your target. Open lower, walk away higher.

**Your offer ladder**

| | Margin | Your profit | Pay up to |
|---|---|---|---|
| Open here | strong | ${ladder.strong.profit} | **${ladder.strong.mao}** |
| Target | {target}% | ${ladder.target.profit} | **${ladder.target.mao}** |
| Walk away above | thin | ${ladder.thin.profit} | **${ladder.thin.mao}** |

**Where the ARV goes** *(the detailed math)*

| | |
|---|---|
| ARV | ${arv} |
| − Selling costs | ${less_selling_costs} |
| − Rehab | ${less_rehab} |
| − Holding | ${less_holding_soft} |
| − Financing | ${less_financing} |
| − Buying costs | ${less_buying_costs} |
| − Transaction fee | ${less_franchise_fee} |
| − Your profit | ${less_target_profit} |
| **= Max offer** | **${equals_mao}** |

**forVEX 65%-rule cross-check:** ${quick_mao_65_rule}
<!-- If wide_quick_detailed_gap flag is true, add one line explaining why they
diverge — e.g. "Your detailed number is lower because the heavy rehab and hard-
money points cost more than the rule of thumb assumes." Otherwise: "Close to the
detailed number — the rule of thumb holds for this deal." -->

**Assumptions applied** *(change any of these and I'll re-run)*
<!-- List ONLY the defaults_used that materially affect the number, in plain
English: e.g. "4-month hold, hard money at 10% + 2 pts, 6% selling costs,
holding derived from ARV." Flag prominently if the transaction fee was $0 (franchise_fee_not_set). -->

**Try a what-if:**
- "What if I pay cash?"
- "Rehab's actually $X"
- "I want $X profit instead"

<!-- Mobile note: if rendering feels long, collapse the cost stack under a
<details> block and lead with the headline + ladder. -->
