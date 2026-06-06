#!/usr/bin/env python3
"""
Finish selection — tier, budget allocation, and over-/under-improvement guard.
A forVEX flip tool, standalone.

The whole game in flip finishes is matching the comps: put the finish level the
top of your comp set carries, and not a notch higher. Spend past the comp tier
and the market won't pay you back; spend under it and the house sits or trades
down. This script picks the target finish tier, splits a finish budget across
the categories that move a buyer, and — most importantly — flags when the plan
is over- or under-improving relative to what the comps support.

It does NOT pick specific materials. That judgment lives in the finish library
(references/finish-tiers.md), which the skill reads to fill in the actual
flooring / counters / fixtures per tier. This script handles the money and the
guardrails; the reference handles the taste.

Usage:
    python finish_select.py '<json-input>'
    echo '<json-input>' | python finish_select.py

Input (arv and sqft required; everything else optional):
{
  "arv": 250000,
  "sqft": 1600,
  "comp_tier": "mid",          # rental|entry|mid|moveup|luxury — the tier your COMPS sit at
  "local_median": 280000,      # local median/avg home price — sets tier by ARV-to-median ratio
  "buyer_profile": null,       # optional; defaults to align with the tier
  "rehab_budget": 40000,       # optional FINISH/cosmetic budget (not systems/structural)
  "tier_override": null,       # force a target tier
  "cost_multiplier": 1.0       # scale $/sf benchmarks to your market (>1 high-cost, <1 low-cost)
}

Tier vs. cost are two different axes: `local_median` sets the TIER (what finishes
the market expects, by where ARV sits relative to local prices), while
`cost_multiplier` sets the COST to install them (local labor/material). A $500k
home is luxury in a $280k-median market and merely mid in a $600k one — same
dollars, different tier.

Output: a JSON object — see build_result().
"""

import json
import sys

CALC_VERSION = "forvex-finish-1.0.0"

TIERS = ["rental", "entry", "mid", "moveup", "luxury"]
TIER_RANK = {t: i for i, t in enumerate(TIERS)}
TIER_LABEL = {
    "rental": "Rental / Investor-grade",
    "entry": "Entry / Starter",
    "mid": "Mid-market",
    "moveup": "Move-up / Premium",
    "luxury": "High-end / Luxury",
}

# Finish/cosmetic cost per square foot by tier (NATIONAL placeholders — scale with
# cost_multiplier). This is finish-out only: flooring, paint, kitchen, baths,
# fixtures, curb appeal. It is NOT total rehab (which adds roof/HVAC/systems).
TIER_PSF = {
    "rental": (8, 15),
    "entry": (12, 22),
    "mid": (20, 35),
    "moveup": (32, 50),
    "luxury": (50, 90),
}

# Default ARV -> tier inference. The RIGHT signal is where the ARV sits relative
# to the LOCAL median home price, not an absolute dollar figure: a $500k house is
# top-tier in a $280k-median market (Louisville) but mid/entry in a high-priced
# one (Miami). So we infer from the ratio arv / local_median when a median is
# given, and fall back to crude national dollar bands only when it isn't.
# Rental is never auto-inferred; it is a strategy choice the user states.

# Ratio of ARV to local median -> tier. Tuned so ~median = mid, well below =
# entry, well above = luxury.
def _tier_from_median_ratio(ratio):
    if ratio < 0.60:
        return "entry"
    if ratio < 1.10:
        return "mid"
    if ratio < 1.70:
        return "moveup"
    return "luxury"


# Crude absolute fallback when no local median is supplied (flagged hard).
def _tier_from_absolute_arv(arv):
    if arv < 150000:
        return "entry"
    if arv < 275000:
        return "mid"
    if arv < 450000:
        return "moveup"
    return "luxury"


def _infer_tier(arv, local_median):
    """Returns (tier, source_label). Prefer the local-median ratio; fall back to
    absolute national bands only when no median is given."""
    if local_median and local_median > 0:
        ratio = arv / local_median
        return _tier_from_median_ratio(ratio), "median_ratio"
    return _tier_from_absolute_arv(arv), "national_bands"


# Share of the FINISH budget by category. Tuned slightly by tier: cheaper tiers
# lean on paint/flooring/curb; richer tiers shift weight into kitchen and baths.
ALLOCATION = {
    "rental":  {"kitchen": 0.22, "bathrooms": 0.15, "flooring": 0.22, "paint": 0.16,
                "lighting_fixtures": 0.07, "curb_appeal": 0.13, "hardware_misc": 0.05},
    "entry":   {"kitchen": 0.25, "bathrooms": 0.16, "flooring": 0.20, "paint": 0.14,
                "lighting_fixtures": 0.07, "curb_appeal": 0.13, "hardware_misc": 0.05},
    "mid":     {"kitchen": 0.28, "bathrooms": 0.18, "flooring": 0.18, "paint": 0.12,
                "lighting_fixtures": 0.07, "curb_appeal": 0.12, "hardware_misc": 0.05},
    "moveup":  {"kitchen": 0.30, "bathrooms": 0.20, "flooring": 0.17, "paint": 0.10,
                "lighting_fixtures": 0.08, "curb_appeal": 0.10, "hardware_misc": 0.05},
    "luxury":  {"kitchen": 0.32, "bathrooms": 0.22, "flooring": 0.16, "paint": 0.08,
                "lighting_fixtures": 0.09, "curb_appeal": 0.08, "hardware_misc": 0.05},
}

CATEGORY_LABEL = {
    "kitchen": "Kitchen", "bathrooms": "Bathrooms", "flooring": "Flooring",
    "paint": "Paint (interior + exterior)", "lighting_fixtures": "Lighting & fixtures",
    "curb_appeal": "Curb appeal", "hardware_misc": "Hardware & misc",
}


def _round(x):
    return round(float(x), 2)


def _validate_tier(t, field):
    if t not in TIERS:
        raise ValueError(f"{field} must be one of {TIERS}, got '{t}'.")


def compute(raw):
    if "arv" not in raw or "sqft" not in raw:
        raise ValueError("Both 'arv' and 'sqft' are required.")
    arv = float(raw["arv"])
    sqft = float(raw["sqft"])
    if arv <= 0 or sqft <= 0:
        raise ValueError("arv and sqft must be positive.")

    mult = float(raw.get("cost_multiplier") or 1.0)
    local_median = raw.get("local_median")
    local_median = float(local_median) if local_median else None
    comp_tier = raw.get("comp_tier")
    tier_override = raw.get("tier_override")
    if comp_tier:
        _validate_tier(comp_tier, "comp_tier")
    if tier_override:
        _validate_tier(tier_override, "tier_override")

    # Target tier precedence: override > comp_tier (match the comps) > inference.
    # Inference prefers ARV-relative-to-local-median; absolute bands are last resort.
    tier_inferred_from_arv = False
    inference_source = None
    if tier_override:
        target_tier = tier_override
        tier_source = "override"
    elif comp_tier:
        target_tier = comp_tier
        tier_source = "matched to comp tier"
    else:
        target_tier, inference_source = _infer_tier(arv, local_median)
        tier_inferred_from_arv = True
        if inference_source == "median_ratio":
            ratio = arv / local_median
            tier_source = (f"inferred from ARV at {ratio:.2f}x the local median "
                           f"(${local_median:,.0f})")
        else:
            tier_source = ("inferred from ARV on national dollar bands — give me "
                           "your local median home price for a market-accurate tier")

    lo, hi = TIER_PSF[target_tier]
    psf_lo, psf_hi = _round(lo * mult), _round(hi * mult)
    psf_mid = _round((psf_lo + psf_hi) / 2)

    # Benchmark finish spend for this tier on this house
    bench_lo = _round(psf_lo * sqft)
    bench_hi = _round(psf_hi * sqft)

    # Budget verdict (only if a budget was supplied)
    budget = raw.get("rehab_budget")
    budget_block = None
    if budget is not None:
        budget = float(budget)
        implied_psf = _round(budget / sqft)
        if implied_psf < psf_lo:
            verdict = "UNDER-IMPROVING for this tier"
        elif implied_psf > psf_hi:
            verdict = "OVER-IMPROVING for this tier"
        else:
            verdict = "ON TARGET for this tier"
        alloc = ALLOCATION[target_tier]
        categories = [
            {"category": CATEGORY_LABEL[k], "key": k, "pct": _round(v),
             "budget": _round(v * budget), "psf": _round(v * budget / sqft)}
            for k, v in alloc.items()
        ]
        budget_block = {
            "finish_budget": _round(budget),
            "implied_psf": implied_psf,
            "tier_psf_range": [psf_lo, psf_hi],
            "verdict": verdict,
            "allocation": categories,
        }

    # Over-/under-improvement guard vs the COMPS (the money question)
    guard = None
    if comp_tier:
        dt = TIER_RANK[target_tier] - TIER_RANK[comp_tier]
        if dt > 0:
            guard = (f"OVER-IMPROVING vs comps: you're finishing to "
                     f"{TIER_LABEL[target_tier]} in a {TIER_LABEL[comp_tier]} comp set. "
                     f"The market likely won't pay back the extra {dt} tier(s).")
        elif dt < 0:
            guard = (f"UNDER-IMPROVING vs comps: {TIER_LABEL[target_tier]} finishes in a "
                     f"{TIER_LABEL[comp_tier]} comp set will trade down or sit. "
                     f"Step up to match the comps.")
        else:
            guard = f"Matched: finishing to {TIER_LABEL[target_tier]}, same as the comp set. This is the target."

    return build_result(arv, sqft, mult, target_tier, tier_source,
                        tier_inferred_from_arv, psf_lo, psf_hi, psf_mid,
                        bench_lo, bench_hi, budget_block, guard, comp_tier,
                        raw.get("buyer_profile"), inference_source, local_median)


def build_result(arv, sqft, mult, target_tier, tier_source, inferred,
                 psf_lo, psf_hi, psf_mid, bench_lo, bench_hi, budget_block,
                 guard, comp_tier, buyer_profile, inference_source=None,
                 local_median=None):
    return {
        "calc_version": CALC_VERSION,
        "target_tier": target_tier,
        "target_tier_label": TIER_LABEL[target_tier],
        "tier_source": tier_source,
        "buyer_profile": buyer_profile or target_tier,
        "inputs": {"arv": _round(arv), "sqft": _round(sqft),
                   "cost_multiplier": _round(mult), "comp_tier": comp_tier,
                   "local_median": (_round(local_median) if local_median else None)},
        "finish_psf_range": [psf_lo, psf_hi],
        "finish_psf_midpoint": psf_mid,
        "benchmark_finish_spend": [bench_lo, bench_hi],
        "budget": budget_block,
        "comp_guard": guard,
        "flags": {
            "tier_inferred_from_arv": inferred,
            "tier_inferred_from_median_ratio": inference_source == "median_ratio",
            "tier_inferred_from_national_bands": inference_source == "national_bands",
            "no_comp_tier_given": comp_tier is None,
            "over_improving_vs_comps": bool(guard and guard.startswith("OVER")),
            "under_improving_vs_comps": bool(guard and guard.startswith("UNDER")),
            "budget_off_target": bool(budget_block and budget_block["verdict"] != "ON TARGET for this tier"),
        },
        "note": ("$/sf figures are FINISH-OUT only (flooring, paint, kitchen, baths, "
                 "fixtures, curb appeal) — not total rehab, which adds roof, HVAC, and "
                 "systems. Calibrate with cost_multiplier for your market."),
    }


def main():
    raw = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.loads(sys.stdin.read())
    print(json.dumps(compute(raw), indent=2))


if __name__ == "__main__":
    main()
