#!/usr/bin/env python3
"""
Maximum Allowable Offer (MAO) calculator — a forVEX flip tool, standalone.

Solves for the highest price you can pay for a property and still hit your
profit target after rehab, selling, holding, financing, buying, and any
per-deal transaction/franchise fee. Runs on user inputs only — no external
data, no connectors. Any transaction fee is whatever the user enters; this
tool ships no fee schedule of its own.

Two numbers are always produced:
  1. detailed_mao  — the itemized, cost-by-cost answer (the real number)
  2. quick_mao     — the forVEX 65%-rule shorthand, as a cross-check

Usage:
    python mao.py '<json-input>'
    echo '<json-input>' | python mao.py

Input (only arv and rehab are required; everything else has a default):
{
  "arv": 220000,
  "rehab": 45000,
  "target_margin_pct": 0.15,      # profit target as a fraction of ARV
  "profit_floor_usd": 0,          # dollar floor; binds if higher than margin %
  "selling_cost_pct": 0.06,       # agent commission, as fraction of ARV
  "hold_months": 4,               # months from purchase to sale
  "monthly_holding_usd": null,    # taxes/ins/utils/misc per month; null => derived
  "financing": "hard_money",      # "cash" | "hard_money" | "company"
  "hm_rate": 0.10,                # annual interest (hard_money / company)
  "hm_points": 2.0,               # points (hard_money only)
  "ltv_cost": 0.90,               # fraction of (offer+rehab) the lender finances
  "buying_cost_pct": 0.02,        # purchase closing, as fraction of offer
  "franchise_fee_pct": null,      # per-deal transaction fee as a fraction of ARV
  "franchise_fee_usd": null,      # ...or as a flat dollar amount (wins if both set)
  "quick_factor": 0.65            # the forVEX "65% rule" multiplier
}

If no transaction/franchise fee is supplied, it is treated as $0 and flagged —
enter your own fee (many franchises charge a percent of the sale price).

Output: a JSON object — see build_result().
"""

import json
import sys

CALC_VERSION = "forvex-mao-1.0.0"

DEFAULTS = {
    "target_margin_pct": 0.15,
    "profit_floor_usd": 0.0,
    "selling_cost_pct": 0.06,
    "hold_months": 4.0,
    "monthly_holding_usd": None,   # derived from ARV when not supplied
    "financing": "hard_money",
    "hm_rate": 0.10,
    "hm_points": 2.0,
    "ltv_cost": 0.90,
    "company_rate": 0.08,
    "buying_cost_pct": 0.02,
    "franchise_fee_pct": None,      # user-entered transaction fee as fraction of ARV
    "franchise_fee_usd": None,      # ...or as a flat dollar (wins if both set)
    "quick_factor": 0.65,           # forVEX 65% rule cross-check
}

# Monthly soft holding (taxes/insurance/utilities/misc), as a fraction of ARV,
# used only when the caller doesn't supply a dollar figure. 0.25%/mo of ARV is
# a reasonable national placeholder (e.g. $500/mo on a $200k ARV).
HOLDING_PCT_OF_ARV_PER_MONTH = 0.0025


def _resolve_franchise_fee(arv, p):
    """Return (fee_usd, fee_pct_or_None, source_label). The fee is whatever the
    user enters — a flat dollar wins over a percent. If neither is supplied the
    fee is $0 and the caller flags it (many franchises charge a % of sale)."""
    if p.get("franchise_fee_usd") is not None:
        fee = float(p["franchise_fee_usd"])
        return fee, (fee / arv if arv else None), "user-entered (flat dollar)"
    if p.get("franchise_fee_pct") is not None:
        pct = float(p["franchise_fee_pct"])
        return pct * arv, pct, "user-entered (percent of ARV)"
    return 0.0, 0.0, "not set"


def _round(x):
    return round(float(x), 2)


def _financing_cost(offer, rehab, p):
    """Cost of capital over the hold, given a trial offer."""
    fin = p["financing"]
    months = p["hold_months"]
    if fin == "cash":
        return 0.0
    if fin == "company":
        loan = p["ltv_cost"] * (offer + rehab)
        interest = loan * p["company_rate"] * (months / 12.0)
        return interest  # company money: no points
    # hard money (default)
    loan = p["ltv_cost"] * (offer + rehab)
    interest = loan * p["hm_rate"] * (months / 12.0)
    points = (p["hm_points"] / 100.0) * loan
    return interest + points


def _solve_mao(arv, rehab, target_profit, p):
    """
    Fixed-point solve for offer O where:
      O = ARV - selling - rehab - holding_soft - target_profit
          - buying_cost(O) - financing_cost(O)
    Both buying and financing depend on O, so iterate to convergence.
    """
    selling = p["selling_cost_pct"] * arv
    holding_soft = p["monthly_holding_usd"] * p["hold_months"]
    fixed = arv - selling - rehab - holding_soft - target_profit - p["franchise_fee_usd"]

    offer = max(fixed, 0.0)  # seed ignoring O-dependent terms
    for _ in range(50):
        buying = p["buying_cost_pct"] * offer
        financing = _financing_cost(offer, rehab, p)
        new_offer = fixed - buying - financing
        if abs(new_offer - offer) < 0.01:
            offer = new_offer
            break
        offer = new_offer

    buying = p["buying_cost_pct"] * offer
    financing = _financing_cost(offer, rehab, p)
    breakdown = {
        "arv": _round(arv),
        "less_selling_costs": _round(selling),
        "less_rehab": _round(rehab),
        "less_holding_soft": _round(holding_soft),
        "less_financing": _round(financing),
        "less_buying_costs": _round(buying),
        "less_franchise_fee": _round(p["franchise_fee_usd"]),
        "less_target_profit": _round(target_profit),
        "equals_mao": _round(offer),
    }
    return offer, breakdown


def compute(raw):
    if "arv" not in raw or "rehab" not in raw:
        raise ValueError("Both 'arv' and 'rehab' are required.")

    p = dict(DEFAULTS)
    p.update({k: v for k, v in raw.items() if v is not None})

    arv = float(raw["arv"])
    rehab = float(raw["rehab"])
    if arv <= 0:
        raise ValueError("ARV must be positive.")
    if rehab < 0:
        raise ValueError("Rehab cannot be negative.")

    if p["monthly_holding_usd"] is None:
        p["monthly_holding_usd"] = HOLDING_PCT_OF_ARV_PER_MONTH * arv
        holding_derived = True
    else:
        p["monthly_holding_usd"] = float(p["monthly_holding_usd"])
        holding_derived = False

    # franchise transaction fee — % of sale price (ARV proxy), by level/type
    fee_usd, fee_pct, fee_source = _resolve_franchise_fee(arv, p)
    p["franchise_fee_usd"] = fee_usd

    # target profit: greater of margin% of ARV and the dollar floor
    margin_profit = p["target_margin_pct"] * arv
    target_profit = max(margin_profit, p["profit_floor_usd"])
    profit_floor_binds = p["profit_floor_usd"] > margin_profit

    detailed_mao, breakdown = _solve_mao(arv, rehab, target_profit, p)

    # quick forVEX 65%-rule cross-check
    quick_mao = p["quick_factor"] * arv - rehab

    # offer ladder — most you can pay at three margin tolerances
    ladder = []
    for label, margin in (("thin (walk-away)", 0.10),
                          ("target", p["target_margin_pct"]),
                          ("strong (opening offer)", max(p["target_margin_pct"] + 0.05, 0.20))):
        tp = max(margin * arv, p["profit_floor_usd"])
        mao_at, _ = _solve_mao(arv, rehab, tp, p)
        ladder.append({
            "label": label,
            "margin_pct": _round(margin),
            "target_profit_usd": _round(tp),
            "mao_usd": _round(mao_at),
        })

    return build_result(
        arv, rehab, detailed_mao, quick_mao, target_profit, breakdown, ladder,
        p, holding_derived, profit_floor_binds, raw,
        fee_pct, fee_source,
    )


def build_result(arv, rehab, detailed_mao, quick_mao, target_profit,
                 breakdown, ladder, p, holding_derived, profit_floor_binds, raw,
                 fee_pct=None, fee_source=None):
    spread = detailed_mao - quick_mao
    # these are override-only (None by design) — reported via franchise_fee_source instead
    _hide = {"franchise_fee_usd", "franchise_fee_pct"}
    defaults_used = sorted(k for k in DEFAULTS
                           if k not in _hide and (k not in raw or raw.get(k) is None))
    if holding_derived and "monthly_holding_usd" not in defaults_used:
        defaults_used.append("monthly_holding_usd")

    return {
        "calc_version": CALC_VERSION,
        "inputs": {
            "arv": _round(arv),
            "rehab": _round(rehab),
            "target_margin_pct": _round(p["target_margin_pct"]),
            "target_profit_usd": _round(target_profit),
            "financing": p["financing"],
            "hold_months": _round(p["hold_months"]),
            "franchise_fee_pct": _round(fee_pct) if fee_pct is not None else None,
            "franchise_fee_source": fee_source,
        },
        "detailed_mao": _round(detailed_mao),
        "quick_mao_65_rule": _round(quick_mao),
        "quick_vs_detailed_spread": _round(spread),
        "cost_stack": breakdown,
        "offer_ladder": ladder,
        "flags": {
            "holding_derived_from_arv": holding_derived,
            "profit_floor_binds": profit_floor_binds,
            "detailed_below_zero": detailed_mao < 0,
            "wide_quick_detailed_gap": abs(spread) > 0.05 * arv,
            "franchise_fee_not_set": fee_source == "not set",
        },
        "defaults_used": defaults_used,
    }


def main():
    if len(sys.argv) > 1:
        raw = json.loads(sys.argv[1])
    else:
        raw = json.loads(sys.stdin.read())
    print(json.dumps(compute(raw), indent=2))


if __name__ == "__main__":
    main()
