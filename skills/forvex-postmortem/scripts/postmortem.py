#!/usr/bin/env python3
"""
Flip post-mortem — projected vs. actual variance, profit bridge, and lessons.
A forVEX flip tool.

Standalone: the user supplies both the projected (underwritten) numbers and the
actual (closed) numbers. No connectors, no saved-deal lookup. Any cost line the
user doesn't have is derived from the same default engine the forVEX MAO tool
uses, and every derived line is flagged.

The math reconciles to PROFIT — the only bottom line that matters — via an exact
additive bridge: the total profit miss decomposes, dollar-for-dollar, into the
contribution of each driver (sale, purchase, rehab, selling, holding, financing,
buying, transaction fee). That bridge is what tells the investor *where* the deal
went sideways, not just that it did.

Usage:
    python postmortem.py '<json-input>'
    echo '<json-input>' | python postmortem.py

Input:
{
  "projected": {"purchase": 110000, "rehab": 45000, "sale": 220000,
                "hold_months": 4, "selling": null, "holding": null,
                "financing": null, "buying": null, "franchise_fee": null,
                "profit": null},
  "actual":    {"purchase": 112000, "rehab": 58000, "sale": 213000,
                "hold_months": 6, ...},
  "franchise_fee_pct": 0.05,       # transaction fee as fraction of sale price
  "franchise_fee_usd": null,       # ...or a flat dollar per side (wins if set)
  "financing_type": "hard_money",  # cash | hard_money | company
  "selling_cost_pct": 0.06,
  "hm_rate": 0.10, "hm_points": 2.0, "ltv_cost": 0.90,
  "buying_cost_pct": 0.02
}

Only projected.{purchase,rehab,sale} and actual.{purchase,rehab,sale} are
strictly required. Everything else is derived if omitted. The transaction fee
is whatever the user enters; this tool ships no fee schedule. If no fee is
given it is treated as $0 (per side) and flagged.
"""

import json
import sys

CALC_VERSION = "forvex-postmortem-1.0.0"

DEFAULTS = {
    "franchise_fee_pct": None,      # user-entered transaction fee, fraction of sale
    "franchise_fee_usd": None,      # ...or flat dollar per side (wins if both set)
    "financing_type": "hard_money",
    "selling_cost_pct": 0.06,
    "hm_rate": 0.10,
    "hm_points": 2.0,
    "company_rate": 0.08,
    "ltv_cost": 0.90,
    "buying_cost_pct": 0.02,
    "default_hold_months": 4.0,
    "monthly_holding_pct_of_sale": 0.0025,
}

# Cost lines that subtract from sale to reach profit, in display order.
COST_LINES = ["purchase", "rehab", "selling", "holding", "financing", "buying", "franchise_fee"]


def _round(x):
    return round(float(x), 2)


def _fee_for_side(sale, p):
    """Transaction fee for one side — user-entered only, no schedule. Flat
    dollar wins over percent; absent => $0."""
    if p.get("franchise_fee_usd") is not None:
        return float(p["franchise_fee_usd"])
    if p.get("franchise_fee_pct") is not None:
        return float(p["franchise_fee_pct"]) * sale
    return 0.0


def _derive_side(side, p):
    """Fill any missing cost lines for one side (projected or actual).
    Returns (filled_side_dict, set_of_derived_keys)."""
    s = dict(side)
    derived = set()

    for key in ("purchase", "rehab", "sale"):
        if s.get(key) is None:
            raise ValueError(f"Missing required value: {key}")
        s[key] = float(s[key])

    if s.get("hold_months") is None:
        s["hold_months"] = p["default_hold_months"]
        derived.add("hold_months")
    else:
        s["hold_months"] = float(s["hold_months"])

    if s.get("selling") is None:
        s["selling"] = p["selling_cost_pct"] * s["sale"]
        derived.add("selling")
    if s.get("holding") is None:
        s["holding"] = p["monthly_holding_pct_of_sale"] * s["sale"] * s["hold_months"]
        derived.add("holding")
    if s.get("buying") is None:
        s["buying"] = p["buying_cost_pct"] * s["purchase"]
        derived.add("buying")
    if s.get("franchise_fee") is None:
        s["franchise_fee"] = _fee_for_side(s["sale"], p)
        derived.add("franchise_fee")
    if s.get("financing") is None:
        s["financing"] = _derive_financing(s, p)
        derived.add("financing")

    s = {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in s.items()}
    # computed profit from the stack
    computed_profit = s["sale"] - sum(s[k] for k in COST_LINES)
    s["_computed_profit"] = computed_profit
    if s.get("profit") is None:
        s["profit"] = computed_profit
        derived.add("profit")
    else:
        s["profit"] = float(s["profit"])
    return s, derived


def _derive_financing(s, p):
    ft = p["financing_type"]
    if ft == "cash":
        return 0.0
    loan = p["ltv_cost"] * (s["purchase"] + s["rehab"])
    months = s["hold_months"]
    if ft == "company":
        return loan * p["company_rate"] * (months / 12.0)
    interest = loan * p["hm_rate"] * (months / 12.0)
    points = (p["hm_points"] / 100.0) * loan
    return interest + points


def _verdict(actual_profit, projected_profit):
    if actual_profit < 0:
        return "LOST MONEY"
    if projected_profit <= 0:
        # underwrote to break-even or worse; judge on absolute outcome
        return "BEAT PLAN" if actual_profit > 0 else "ON PLAN"
    ratio = actual_profit / projected_profit
    if ratio >= 1.10:
        return "BEAT PLAN"
    if ratio <= 0.90:
        return "MISSED PLAN"
    return "ON PLAN"


def _build_bridge(proj, act):
    """Exact additive decomposition of (actual_profit - projected_profit).
    Sale helps profit when it rises; cost lines hurt profit when they rise."""
    drivers = []
    # sale: positive delta helps profit
    sale_delta = act["sale"] - proj["sale"]
    drivers.append({"driver": "sale", "projected": _round(proj["sale"]),
                    "actual": _round(act["sale"]),
                    "profit_impact": _round(sale_delta)})
    # cost lines: positive delta hurts profit, so impact = -(delta)
    for key in COST_LINES:
        delta = act[key] - proj[key]
        drivers.append({"driver": key, "projected": _round(proj[key]),
                        "actual": _round(act[key]),
                        "profit_impact": _round(-delta)})
    total_impact = sum(d["profit_impact"] for d in drivers)
    # rank by magnitude of impact
    ranked = sorted(drivers, key=lambda d: abs(d["profit_impact"]), reverse=True)
    return drivers, ranked, total_impact


def _metrics(side):
    sale = side["sale"]
    profit = side["profit"]
    project_cost = side["purchase"] + side["rehab"]
    all_in = sum(side[k] for k in COST_LINES)
    margin = profit / sale if sale else 0.0
    roi_cost = profit / project_cost if project_cost else 0.0
    roi_allin = profit / all_in if all_in else 0.0
    months = side["hold_months"] or 0.0
    annualized = (roi_allin * (12.0 / months)) if months else None
    return {
        "profit": _round(profit),
        "margin_on_sale": _round(margin),
        "roi_on_project_cost": _round(roi_cost),
        "roi_on_all_in": _round(roi_allin),
        "annualized_roi_on_all_in": (_round(annualized) if annualized is not None else None),
        "hold_months": _round(months),
    }


def _lessons(proj, act, ranked):
    """Data-anchored, decisive takeaways. Each tied to a dollar or a percent."""
    out = []

    def pct_change(a, b):
        return (a - b) / b if b else None

    # rehab accuracy
    rc = pct_change(act["rehab"], proj["rehab"])
    if rc is not None and rc > 0.10:
        out.append(f"Rehab ran {rc*100:.0f}% over plan (+${act['rehab']-proj['rehab']:,.0f}). "
                   f"Your scope was light — tighten estimating on the line items that blew up.")
    elif rc is not None and rc < -0.10:
        out.append(f"Rehab came in {abs(rc)*100:.0f}% under plan (${proj['rehab']-act['rehab']:,.0f} saved). "
                   f"Either you padded the budget or the crew beat scope — worth knowing which.")

    # ARV / sale accuracy
    sc = pct_change(act["sale"], proj["sale"])
    if sc is not None and sc < -0.05:
        out.append(f"Sold {abs(sc)*100:.0f}% under your ARV (-${proj['sale']-act['sale']:,.0f}). "
                   f"Your after-repair value was optimistic — pressure-test comps harder next time.")
    elif sc is not None and sc > 0.05:
        out.append(f"Sold {sc*100:.0f}% over your ARV (+${act['sale']-proj['sale']:,.0f}). "
                   f"Underwriting was conservative on value — good, but don't bank on it.")

    # hold time
    hd = act["hold_months"] - proj["hold_months"]
    if hd >= 1:
        carry_per_mo = (act["holding"] + act["financing"]) / act["hold_months"] if act["hold_months"] else 0
        out.append(f"Hold ran {hd:.0f} month(s) long — roughly ${carry_per_mo*hd:,.0f} in extra carry. "
                   f"Every month on the books eats margin; find where the timeline slipped.")
    elif hd <= -1:
        out.append(f"Closed {abs(hd):.0f} month(s) faster than planned — that's saved carry and freed capital sooner.")

    # purchase
    pc = act["purchase"] - proj["purchase"]
    if pc > 0.005 * proj["purchase"]:
        out.append(f"Paid ${pc:,.0f} more than underwritten at purchase. If you negotiated up at the table, "
                   f"make sure the ARV justified it.")

    # biggest single driver
    top = ranked[0]
    if abs(top["profit_impact"]) > 0:
        direction = "helped" if top["profit_impact"] > 0 else "hurt"
        out.append(f"Biggest single factor: **{top['driver'].replace('_',' ')}** {direction} profit by "
                   f"${abs(top['profit_impact']):,.0f}.")

    # calibration: optimistic vs conservative across cost lines
    worse = sum(1 for k in COST_LINES if act[k] > proj[k] * 1.02)
    better = sum(1 for k in COST_LINES if act[k] < proj[k] * 0.98)
    if worse >= 3 and worse > better:
        out.append("Pattern: most cost lines came in over plan — you underwrite optimistically. "
                   "Add a contingency buffer to future deals.")
    elif better >= 3 and better > worse:
        out.append("Pattern: most lines beat plan — your underwriting is conservative, which protects you.")

    if not out:
        out.append("This deal tracked your plan closely — no single line moved profit materially. "
                   "Clean execution.")
    return out


def compute(raw):
    if "projected" not in raw or "actual" not in raw:
        raise ValueError("Need both 'projected' and 'actual' objects.")
    p = dict(DEFAULTS)
    p.update({k: v for k, v in raw.items()
              if k not in ("projected", "actual") and v is not None})

    proj, proj_derived = _derive_side(raw["projected"], p)
    act, act_derived = _derive_side(raw["actual"], p)

    drivers, ranked, total_impact = _build_bridge(proj, act)
    proj_profit = proj["profit"]
    act_profit = act["profit"]
    profit_variance = act_profit - proj_profit
    verdict = _verdict(act_profit, proj_profit)

    # reconciliation check: bridge total should equal computed-profit variance
    computed_variance = act["_computed_profit"] - proj["_computed_profit"]
    bridge_reconciles = abs(total_impact - computed_variance) < 0.01

    # if user supplied profit that disagrees with the stack, surface it
    proj_profit_mismatch = abs(proj["profit"] - proj["_computed_profit"]) > 1.0
    act_profit_mismatch = abs(act["profit"] - act["_computed_profit"]) > 1.0

    # transaction fee unset if no global pct/usd AND neither side supplied one
    fee_not_set = (p.get("franchise_fee_pct") is None
                   and p.get("franchise_fee_usd") is None
                   and raw["projected"].get("franchise_fee") is None
                   and raw["actual"].get("franchise_fee") is None)

    return {
        "calc_version": CALC_VERSION,
        "verdict": verdict,
        "projected_profit": _round(proj_profit),
        "actual_profit": _round(act_profit),
        "profit_variance": _round(profit_variance),
        "profit_variance_pct": (_round(profit_variance / proj_profit)
                                if proj_profit else None),
        "line_items": {
            "sale": {"projected": _round(proj["sale"]), "actual": _round(act["sale"]),
                     "variance": _round(act["sale"] - proj["sale"])},
            **{k: {"projected": _round(proj[k]), "actual": _round(act[k]),
                   "variance": _round(act[k] - proj[k])} for k in COST_LINES},
        },
        "profit_bridge": drivers,
        "profit_bridge_ranked": ranked,
        "metrics": {"projected": _metrics(proj), "actual": _metrics(act)},
        "lessons": _lessons(proj, act, ranked),
        "flags": {
            "bridge_reconciles": bridge_reconciles,
            "projected_profit_mismatch_vs_stack": proj_profit_mismatch,
            "actual_profit_mismatch_vs_stack": act_profit_mismatch,
            "lost_money": act_profit < 0,
            "transaction_fee_not_set": fee_not_set,
        },
        "derived_lines": {"projected": sorted(proj_derived),
                          "actual": sorted(act_derived)},
    }


def main():
    raw = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.loads(sys.stdin.read())
    print(json.dumps(compute(raw), indent=2))


if __name__ == "__main__":
    main()
