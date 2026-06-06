#!/usr/bin/env python3
"""
Light rehab estimator — fast, condition-and-$/sf ballpark for a cosmetic-to-
moderate flip. A forVEX flip tool, standalone.

This is the LIGHT estimator on purpose. It rolls up a budget from square footage,
a condition level, and a finish level — good for a quick go/no-go number before
you've walked the house with a contractor. It is NOT a line-item takeoff. Where a
full estimate measures every room and prices real quantities, this one spreads
category rates over the floor area and adds flat costs for kitchens and baths.

Two independent axes drive cosmetic cost:
  - CONDITION (cosmetic | moderate) — how much work, i.e. quantity/scope
  - FINISH    (rental..luxury)      — how nice the replacements, i.e. unit cost
A house can need heavy work with cheap finishes (BRRRR) or light work with nice
ones (a lipstick luxury flip), so they scale separately.

BIG-TICKET SYSTEMS (roof, HVAC, rewire, repipe, windows, foundation) are handled
OUTSIDE the cosmetic engine — flagged in, priced as flat rough adders, and called
out. If any are present, the script says so plainly: this is past "light," and a
full line-item estimate is warranted. That cosmetic-vs-systems split is the main
lesson this prototype carries up to the full rehab tool.

Usage:
    python rehab_light.py '<json-input>'

Input (sqft required; everything else optional):
{
  "sqft": 1600,
  "condition": "moderate",       # cosmetic | moderate  (heavy/gut => use full tool)
  "finish_level": "mid",         # rental | entry | mid | moveup | luxury
  "kitchen_count": 1,
  "bath_count": 2,
  "cost_multiplier": 1.0,        # market labor/material scalar
  "contingency_pct": 0.12,       # reserve on top of the base estimate
  "big_ticket": {                # presence flags; true => add the rough adder
     "roof": false, "hvac": false, "electrical_panel": false,
     "repipe": false, "windows": false, "foundation": false, "water_heater": false
  },
  "big_ticket_overrides": {"roof": 14000}   # optional real numbers per item
}

Output: a JSON object — see build_result().
"""

import json
import sys

CALC_VERSION = "forvex-rehab-light-1.0.0"

CONDITIONS = {"cosmetic": 1.0, "moderate": 1.5}
FINISH_MULT = {"rental": 0.75, "entry": 0.90, "mid": 1.0, "moveup": 1.35, "luxury": 1.9}

# Per-floor-sqft rates at condition=cosmetic, finish=mid, multiplier=1.0.
# finish_sensitive => the finish level scales it (material-driven); otherwise the
# work is mostly labor and finish level barely moves it.
SF_RATES = {
    "paint":               {"rate": 2.50, "finish_sensitive": False, "label": "Interior paint"},
    "flooring":            {"rate": 4.50, "finish_sensitive": True,  "label": "Flooring"},
    "drywall_repair":      {"rate": 1.00, "finish_sensitive": False, "label": "Drywall repair/patch"},
    "electrical_fixtures": {"rate": 1.25, "finish_sensitive": True,  "label": "Lighting & fixtures"},
    "doors_trim":          {"rate": 1.50, "finish_sensitive": True,  "label": "Interior doors, trim, hardware"},
    "cleanout":            {"rate": 0.75, "finish_sensitive": False, "label": "Trash-out & cleaning"},
    "exterior_curb":       {"rate": 1.50, "finish_sensitive": True,  "label": "Exterior & curb appeal"},
}

# Flat, count-based items at finish=mid (condition + finish + market scale them).
COUNT_ITEMS = {
    "kitchen":  {"base": 8000, "label": "Kitchen (light refresh)"},
    "bathroom": {"base": 3500, "label": "Bathroom (light refresh, each)"},
}

# Rough flat adders for big-ticket systems, only when flagged present. National
# placeholders — wide variance, meant to be overridden. Scaled by cost_multiplier
# only (NOT condition/finish — a roof is a roof).
BIG_TICKET = {
    "roof":             {"cost": 9000,  "label": "Roof replacement"},
    "hvac":             {"cost": 8000,  "label": "HVAC replacement"},
    "electrical_panel": {"cost": 4000,  "label": "Electrical panel / partial rewire"},
    "repipe":           {"cost": 6000,  "label": "Repipe"},
    "windows":          {"cost": 9000,  "label": "Window replacement (whole house)"},
    "foundation":       {"cost": 12000, "label": "Foundation / structural"},
    "water_heater":     {"cost": 1500,  "label": "Water heater"},
}


def _round(x):
    return round(float(x), 2)


def compute(raw):
    if "sqft" not in raw:
        raise ValueError("'sqft' is required.")
    sqft = float(raw["sqft"])
    if sqft <= 0:
        raise ValueError("sqft must be positive.")

    condition = str(raw.get("condition", "cosmetic")).lower()
    if condition in ("heavy", "gut"):
        raise ValueError(
            "condition '%s' is beyond a light rehab. Use the full line-item "
            "rehab estimator for heavy/gut scopes." % condition)
    if condition not in CONDITIONS:
        raise ValueError(f"condition must be one of {list(CONDITIONS)}.")
    cond_mult = CONDITIONS[condition]

    finish = str(raw.get("finish_level", "mid")).lower()
    if finish not in FINISH_MULT:
        raise ValueError(f"finish_level must be one of {list(FINISH_MULT)}.")
    fin_mult = FINISH_MULT[finish]

    mult = float(raw.get("cost_multiplier") or 1.0)
    kitchen_count = int(raw.get("kitchen_count", 1))
    bath_count = int(raw.get("bath_count", 2))
    contingency_pct = float(raw.get("contingency_pct", 0.12))

    # --- cosmetic engine: per-sqft categories ---
    cosmetic = []
    for key, c in SF_RATES.items():
        rate = c["rate"] * cond_mult * mult
        if c["finish_sensitive"]:
            rate *= fin_mult
        cost = rate * sqft
        cosmetic.append({"key": key, "label": c["label"], "cost": _round(cost)})

    # --- cosmetic engine: count items (kitchen/bath) ---
    for key, c in COUNT_ITEMS.items():
        n = kitchen_count if key == "kitchen" else bath_count
        each = c["base"] * cond_mult * fin_mult * mult
        cost = each * n
        cosmetic.append({"key": key, "label": f"{c['label']} ×{n}",
                         "cost": _round(cost), "count": n, "each": _round(each)})

    cosmetic_subtotal = sum(c["cost"] for c in cosmetic)

    # --- big-ticket systems (outside the cosmetic engine) ---
    flags = raw.get("big_ticket", {}) or {}
    overrides = raw.get("big_ticket_overrides", {}) or {}
    big = []
    for key, b in BIG_TICKET.items():
        if not flags.get(key):
            continue
        if key in overrides and overrides[key] is not None:
            cost = float(overrides[key])
            src = "your number"
        else:
            cost = b["cost"] * mult
            src = "rough placeholder — verify"
        big.append({"key": key, "label": b["label"], "cost": _round(cost), "source": src})
    big_subtotal = sum(b["cost"] for b in big)

    base = cosmetic_subtotal + big_subtotal
    contingency = contingency_pct * base
    expected = base + contingency
    # rehabs surprise high more than low — asymmetric band
    range_low = _round(base * 0.95)
    range_high = _round(expected * 1.15)

    # scope verdict
    has_big = len(big) > 0
    if has_big:
        scope_note = ("Big-ticket systems are present — this is past a 'light' "
                      "rehab. Treat this number as a rough screen and get a "
                      "line-item estimate before you commit.")
    elif condition == "moderate":
        scope_note = ("Moderate cosmetic scope — fine for a ballpark, but walk it "
                      "with a contractor before locking the budget.")
    else:
        scope_note = "Cosmetic scope — this ballpark should be reasonably close."

    return build_result(sqft, condition, finish, mult, kitchen_count, bath_count,
                        contingency_pct, cosmetic, cosmetic_subtotal, big,
                        big_subtotal, base, contingency, expected, range_low,
                        range_high, has_big, scope_note)


def build_result(sqft, condition, finish, mult, kitchen_count, bath_count,
                 contingency_pct, cosmetic, cosmetic_subtotal, big, big_subtotal,
                 base, contingency, expected, range_low, range_high, has_big,
                 scope_note):
    return {
        "calc_version": CALC_VERSION,
        "inputs": {
            "sqft": _round(sqft), "condition": condition, "finish_level": finish,
            "cost_multiplier": _round(mult), "kitchen_count": kitchen_count,
            "bath_count": bath_count, "contingency_pct": _round(contingency_pct),
        },
        "expected_cost": _round(expected),
        "range_low": range_low,
        "range_high": range_high,
        "expected_psf": _round(expected / sqft),
        "cosmetic_subtotal": _round(cosmetic_subtotal),
        "big_ticket_subtotal": _round(big_subtotal),
        "contingency": _round(contingency),
        "cosmetic_breakdown": cosmetic,
        "big_ticket_items": big,
        "scope_note": scope_note,
        "flags": {
            "big_ticket_present": has_big,
            "beyond_light_rehab": has_big,
            "moderate_condition": condition == "moderate",
        },
        "limitations": ("Ballpark only: category rates spread over floor area + flat "
                        "kitchen/bath costs, not a measured line-item takeoff. No room "
                        "dimensions, no real quantities, no live material/labor pricing. "
                        "Verify against a contractor walk-through before committing capital."),
    }


def main():
    raw = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.loads(sys.stdin.read())
    print(json.dumps(compute(raw), indent=2))


if __name__ == "__main__":
    main()
