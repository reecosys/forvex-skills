#!/usr/bin/env python3
"""
forVEX underwriting calculator.

Ports the deterministic math from redeal-mobile/app/services/calculator/* into a
single Python module the skill can shell out to. Returns a JSON object with the
five strategies' financials, scores, signals/warnings, and risk.

Strategies: Assignment, Wholesale, Wholetail, Retail Flip, Rental.
Wholesale supports two variants (possession, double_close). Assignment is its
own strategy — distinct from wholesale because capital, holding, and risk
profiles differ materially.

Usage:
    echo '{"purchase":135000,"arv":215000,"rehab":32000,"rent":1650}' | python underwrite.py
    python underwrite.py --inputs '{"purchase":135000,"arv":215000,"rehab":32000}'

Source-of-truth references (mirror when redeal changes):
    rental.ts, retailFlip.ts, wholetail.ts, wholesale.ts, costStack.ts,
    dealScore.ts, badges.ts, riskScore.ts, buyBoxFit.ts
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any


__version__ = "0.4.0"  # Adds lender_ltv_cap / cash_overlay / payoff_estimate / per-franchisee hm_rate+hm_points.


# ---------- Defaults (mirror references/assumptions.md) ----------

DEFAULTS = {
    # Rental ops
    "vacancy_rate": 0.05,
    "management_rate": 0.10,
    "maintenance_rate": 0.05,
    "capex_rate": 0.05,
    "property_tax_rate": 0.0085,
    "insurance_rate": 0.004,
    "down_payment_pct": 0.20,
    "loan_rate": 0.07,
    "loan_term_years": 30,
    "other_income": 0,
    "utilities_monthly": 0,

    # Closing / sale
    "title_rate": 0.004,
    "other_sale_fee_rate": 0.002,
    "marketing_retail": 500,
    "realtor_regular": 0.06,
    "realtor_discount": 0.04,

    # Holding periods (months)
    "holding_retail": 3,
    "holding_wholetail": 2,
    "holding_wholesale": 1,
    "holding_assignment": 0,

    # Sale-price targeting
    "retail_sale_pct": 0.99,
    "wholetail_base_pct": 0.85,
    "wholetail_uplift": 0.04,
    "wholesale_sale_pct": 0.80,
    # Pure-assignment: disciplined end-buyer pays this % of ARV minus FULL repairs. A buy-box
    # preference (fallback 0.80), distinct from the 0.65 flip entry.
    "wholesale_entry_pct": 0.80,

    # Capital posture rates
    "company_rate": 0.08,
    "loc_rate": 0.07,           # Line of credit — internal cost of capital
    "hard_money_rate": 0.12,
    "hard_money_points": 0.02,
    # Lender LTV cap (hard money) — fraction of ARV the lender will finance.
    # When (purchase + rehab) exceeds arv × cap, the gap is franchisee cash
    # ("cash overlay"). Default None = no cap modeled (legacy behavior).
    # Typical HM lenders cap 65–75% of ARV.
    "lender_ltv_cap_hard_money": None,

    # Rental closing fixed costs
    "inspection": 500,
    "appraisal": 600,
    "lender_fee_rate": 0.02,    # 2% — points + origination on investment loans
    "attorney": 800,
    "recording": 200,
    "other_closing": 900,

    # Assignment defaults
    "assignment_fee_default": 15000,
    "assignment_earnest_money": 1000,
    "assignment_marketing": 500,

    # BRRRR defaults
    "brrrr_refi_ltv": 0.75,              # cash-out refi at 75% of post-rehab ARV
    "brrrr_refi_rate": 0.075,            # DSCR loan rate, slightly higher than purchase
    "brrrr_refi_term_years": 30,
    "brrrr_refi_closing_pct": 0.025,     # title + lender points + appraisal on refi
    "brrrr_stabilization_months": 6,     # rehab + lease-up + seasoning
    "brrrr_target_cash_left": 5000,      # buy-box target — $0 ideal, ≤$5k acceptable
    "brrrr_holding_posture": "cash",     # most BRRRRs entered all-cash or LOC

    # Franchise fee schedule (% of sale price, full franchise)
    "franchise_fee_schedule": {1: 0.030, 2: 0.020, 3: 0.015, 4: 0.0125, 5: 0.010, 6: 0.008},
    "franchise_associate_uplift": 0.020,
    "franchise_fee_default_level": 4,           # mid-table fallback
    "franchise_fee_default_type": "full",

    # Pre-Offer (walk-in number): purchase ceiling as % of ARV, repairs NOT
    # subtracted from the base. Distinct from target_entry_pct_arv, which is
    # an ALL-IN ceiling (purchase + rehab + closing). Pre-offer is purchase-only.
    "pre_offer_pct": 0.65,
    # Quick rehab estimation by condition tier ($/sqft). Used for a
    # repair-adjusted pre-offer when sqft + tier are known but no detailed
    # rehab estimate exists. forVEX-tunable.
    "rehab_per_sqft": {"light": 15, "medium": 25, "heavy": 40, "gut": 60},

    # Buy-box targets (forVEX defaults; per-user overrides via my-buy-box.md)
    "target_profit_assignment": 15000,
    "target_profit_wholesale": 15000,
    "target_roi_wholesale": 0.25,
    "target_profit_wholetail": 25000,
    "target_margin_wholetail": 0.15,
    "target_profit_flip": 40000,
    "target_roi_flip": 0.25,
    "target_margin_flip": 0.18,
    "target_cashflow_annual": 3000,
    "target_dscr": 1.25,
    "target_coc": 0.10,
    "target_entry_pct_arv": 0.65,
    "ideal_rehab_ratio": 0.6,
    "target_brrrr_cash_left": 5000,
    "target_brrrr_cashflow_annual": 3000,

    # Verdict thresholds by risk appetite
    "verdict_buy_threshold": {"conservative": 8.0, "balanced": 7.0, "aggressive": 6.0},
    "verdict_negotiate_threshold": {"conservative": 6.0, "balanced": 5.0, "aggressive": 4.0},

    # Market risk by location type
    "market_risk_by_location": {"urban": 0.5, "suburban": 0.5, "rural": 0.65},
}


# ---------- Helpers ----------

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def amortize_monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    if principal <= 0:
        return 0.0
    n = years * 12
    if annual_rate <= 0:
        return principal / n
    r = annual_rate / 12
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def estimate_rehab_by_sqft(sqft: float, tier: str) -> float:
    """Quick rehab estimate by condition tier × square footage.

    tier: 'light' | 'medium' | 'heavy' | 'gut'. Used for a fast pre-offer
    repair estimate before a detailed walkthrough. Example: light ($15/sqft)
    on a 1,000 sqft house = $15,000.
    """
    rate = DEFAULTS["rehab_per_sqft"].get((tier or "").lower())
    if rate is None or not sqft:
        return 0.0
    return rate * sqft


def compute_pre_offer(arv: float, sqft: float = None, rehab_tier: str = None,
                      rehab_estimate: float = None, pre_offer_pct: float = None) -> dict:
    """walk-in 'Pre-Offer Number'.

    Base ceiling is purchase / ARV <= pre_offer_pct (default 65%), with repairs
    NOT subtracted — that's the number you walk in with before seeing the house.
    Optionally subtract a repair estimate (explicit, or tier × sqft) for a
    repair-adjusted pre-offer.

    Note: distinct from the buy-box entry ceiling (target_entry_pct_arv), which
    is all-in (purchase + rehab + closing). Pre-offer is purchase-only.
    """
    pct = pre_offer_pct if pre_offer_pct is not None else DEFAULTS["pre_offer_pct"]
    base = arv * pct  # purchase ceiling, zero repairs

    if rehab_estimate is not None:
        repairs = rehab_estimate
        repair_source = "explicit"
    elif sqft and rehab_tier:
        repairs = estimate_rehab_by_sqft(sqft, rehab_tier)
        repair_source = f"{rehab_tier} @ ${DEFAULTS['rehab_per_sqft'].get(rehab_tier.lower(), 0)}/sqft"
    else:
        repairs = 0.0
        repair_source = "none (compute on-site)"

    return {
        "pct_of_arv": pct,
        "base": round(base, -2),                       # ARV × 65%, no repairs
        "repairs_estimate": round(repairs, 2),
        "repair_source": repair_source,
        "adjusted": round(base - repairs, -2),         # base − repairs
    }


def franchise_fee_pct(level: int = None, ftype: str = None) -> float:
    """Look up franchise fee as a % of sale price.

    level: 1-6 (1 = newest, 6 = most senior)
    ftype: 'full' | 'associate' — associate franchises add 2%
    """
    if level is None:
        level = DEFAULTS["franchise_fee_default_level"]
    if ftype is None:
        ftype = DEFAULTS["franchise_fee_default_type"]
    schedule = DEFAULTS["franchise_fee_schedule"]
    base = schedule.get(level, schedule[DEFAULTS["franchise_fee_default_level"]])
    if ftype == "associate":
        base += DEFAULTS["franchise_associate_uplift"]
    return base


# ---------- Cost stack ----------

def build_holding_costs(purchase: float, months: int,
                        tax_rate: float = None, insurance_rate: float = None,
                        utilities_monthly: float = None) -> dict:
    tax_rate = tax_rate if tax_rate is not None else DEFAULTS["property_tax_rate"]
    insurance_rate = insurance_rate if insurance_rate is not None else DEFAULTS["insurance_rate"]
    utilities_monthly = utilities_monthly if utilities_monthly is not None else DEFAULTS["utilities_monthly"]
    monthly_tax = (purchase * tax_rate) / 12
    monthly_ins = (purchase * insurance_rate) / 12
    total = (monthly_tax + monthly_ins + utilities_monthly) * months
    return {
        "monthly_tax": monthly_tax,
        "monthly_insurance": monthly_ins,
        "monthly_utilities": utilities_monthly,
        "months": months,
        "total": total,
    }


def build_financing_costs(basis: float, posture: str, months: int,
                          arv: float = None, lender_ltv_cap: float = None,
                          hm_rate: float = None, hm_points: float = None) -> dict:
    """Posture: 'cash' | 'company' | 'loc' | 'hard_money'.

    Default is hard_money per forVEX bias. LOC charges internal cost of capital
    (7% default) with no points — like company money but reflects opportunity
    cost on franchise's own line of credit.

    Optional: `arv` + `lender_ltv_cap` — when both provided AND posture is
    hard_money, the lender finances at most `arv × cap`. The gap above that
    is `cash_overlay` (franchisee cash). Interest and points accrue on the
    financed portion only. When cap is None (default), legacy behavior:
    full basis financed, no overlay computed.

    Optional: `hm_rate` / `hm_points` — per-franchisee HM terms override
    (e.g., 0.10 / 0.01 for a senior franchisee with better lender pricing).
    """
    posture = (posture or "hard_money").lower().replace("-", "_").replace(" ", "_")
    if posture == "cash":
        return {"posture": "cash", "interest": 0, "points": 0, "total": 0,
                "cash_overlay": 0, "financed_basis": 0}
    if posture == "company":
        interest = (basis * DEFAULTS["company_rate"] / 12) * months
        return {"posture": "company", "interest": interest, "points": 0,
                "total": interest, "cash_overlay": 0, "financed_basis": basis}
    if posture in ("loc", "line_of_credit"):
        interest = (basis * DEFAULTS["loc_rate"] / 12) * months
        return {"posture": "loc", "interest": interest, "points": 0,
                "total": interest, "cash_overlay": 0, "financed_basis": basis}
    if posture in ("hard_money", "hardmoney"):
        rate = hm_rate if hm_rate is not None else DEFAULTS["hard_money_rate"]
        pts = hm_points if hm_points is not None else DEFAULTS["hard_money_points"]
        # LTV cap: only applied when arv AND cap both provided (opt-in to
        # preserve legacy fixture behavior).
        if arv and lender_ltv_cap:
            max_financed = arv * lender_ltv_cap
            financed_basis = min(basis, max_financed)
            cash_overlay = max(0, basis - financed_basis)
        else:
            financed_basis = basis
            cash_overlay = 0
        interest = (financed_basis * rate / 12) * months
        points = financed_basis * pts
        return {"posture": "hard_money", "interest": interest, "points": points,
                "total": interest + points, "cash_overlay": cash_overlay,
                "financed_basis": financed_basis, "rate": rate, "points_pct": pts}
    return {"posture": posture, "interest": 0, "points": 0, "total": 0,
            "cash_overlay": 0, "financed_basis": basis}


def build_sale_fees(sale_price: float, marketing: float = 0,
                    franchise_level: int = None, franchise_type: str = None,
                    other_rate: float = None) -> dict:
    """Sale-side costs: franchise transaction fee + other + marketing.

    Franchise fee replaces the prior flat transaction_fee_rate. It's computed
    from the franchisee's level + type per franchise fee schedule.
    """
    fee_pct = franchise_fee_pct(franchise_level, franchise_type)
    other = sale_price * (other_rate if other_rate is not None else DEFAULTS["other_sale_fee_rate"])
    franchise_fee = sale_price * fee_pct
    return {
        "franchise_fee_pct": fee_pct,
        "franchise_fee": franchise_fee,
        "other": other,
        "marketing": marketing,
        "total": franchise_fee + other + marketing,
    }


def realtor_fee(sale_price: float, strategy_preference: str = "default") -> float:
    if strategy_preference == "wholesale_focused":
        return sale_price * DEFAULTS["realtor_discount"]
    return sale_price * DEFAULTS["realtor_regular"]


def title_fee(purchase: float, multiplier: float = 1.0) -> float:
    return purchase * DEFAULTS["title_rate"] * multiplier


# ---------- Strategy: Assignment ----------

def calc_assignment(inputs: dict) -> dict:
    """Pure assignment — contract assigned to an investor; assignor never closes.

    No rehab, no double close, no hidden buffer. The disciplined end-buyer pays
    ``wholesale_entry_pct`` of ARV minus the FULL repairs. My fee is the spread
    between that price and what I tie the seller up at; my MAO is the highest
    offer that still clears my minimum fee. One lever each (entry % and min fee),
    so the number is transparent and there's no double-counted buffer.

    Parity contract: mirrors recontrol nativeEngine.ts::calcAssignment exactly.
    """
    offer = inputs.get("purchase", 0)  # my contract price with the seller
    arv = inputs.get("arv", 0)
    full_rehab = inputs.get("rehab", 0)
    earnest = inputs.get("earnest_money", DEFAULTS["assignment_earnest_money"])
    marketing = inputs.get("assignment_marketing", DEFAULTS["assignment_marketing"])
    # Buy-box prefs: the disciplined end-buyer's entry % and my minimum assignment fee.
    wholesale_entry_pct = inputs.get("wholesale_entry_pct", DEFAULTS["wholesale_entry_pct"])  # 0.80
    min_fee = inputs.get(
        "min_assignment_fee",
        inputs.get("assignment_fee", DEFAULTS["assignment_fee_default"]),
    )  # 15000

    investor_price = max(0, wholesale_entry_pct * arv - full_rehab)
    assignment_fee = investor_price - offer
    mao = investor_price - min_fee

    spread_limited = assignment_fee < min_fee  # fee doesn't clear my floor
    cost_basis = earnest + marketing
    net_profit = assignment_fee - marketing
    roi = (net_profit / cost_basis) * 100 if cost_basis > 0 else 0

    warnings = []
    if net_profit < 0:
        warnings.append({"id": "negative_profit", "label": "Negative Profit"})
    if 0 < assignment_fee < 5000:
        warnings.append({"id": "thin_assignment", "label": "Thin Assignment Fee"})
    if spread_limited:
        warnings.append({"id": "spread_limited", "label": "Below Min Fee"})

    # Marketplace Triage (Stage 1) net-spread economics. Inputs default to 0 when absent, so
    # net_spread == assignment_fee for every existing (non-marketplace) caller — fully additive.
    source_split = inputs.get("source_split", 0)
    dispo_cost = inputs.get("dispo_cost", 0)
    transactional_funding = inputs.get("transactional_funding", 0)
    net_spread = assignment_fee - source_split - dispo_cost - transactional_funding
    # Surface a thin/negative net spread WITHOUT entering the scored `warnings` array — this slice
    # only describes the economics; it must not move deal_score, verdict, or buy-box fit.
    net_spread_warnings = []
    if net_spread <= 0:
        net_spread_warnings.append({"id": "negative_net_spread", "label": "Negative Net Spread"})
    elif net_spread < 5000:
        net_spread_warnings.append({"id": "thin_spread", "label": "Thin Net Spread"})

    return {
        "strategy": "assignment",
        "assignment_fee": round(assignment_fee, 2),
        # The disciplined end-buyer price the fee/MAO hang off of, and the max offer at the fee floor.
        "investor_price": round(investor_price, 2),
        "mao": round(mao, 2),
        "wholesale_entry_pct": wholesale_entry_pct,
        "min_fee": min_fee,
        "target_fee": min_fee,
        "max_feasible_fee": round(assignment_fee, 2),  # simple model: the spread at this offer, no buffer cap
        "spread_limited": spread_limited,
        "earnest_money": earnest,
        "marketing": marketing,
        "predicted_sale": round(investor_price, 2),
        "rehab_used": 0,
        "rehab_ref": full_rehab,
        "holding_months": 0,
        "holding_total": 0,
        "realtor_fee": 0,
        "title_fee": 0,
        "financing": {"posture": "cash", "interest": 0, "points": 0, "total": 0},
        "sale_fees": {"franchise_fee": 0, "franchise_fee_pct": 0, "other": 0,
                      "marketing": marketing, "total": marketing},
        "total_cost_basis": cost_basis,
        "net_profit": round(net_profit, 2),
        "roi": min(roi, 9999),
        "margin": 1.0 if assignment_fee > 0 else 0,
        "rehab_ratio": 0,
        "warnings": warnings,
        # Marketplace Triage Stage 1 — net-spread economics. Self-describing: echo inputs + result.
        "net_spread": round(net_spread, 2),
        "source_split": source_split,
        "dispo_cost": dispo_cost,
        "transactional_funding": transactional_funding,
        "net_spread_warnings": net_spread_warnings,
    }


# ---------- Strategy: Retail Flip ----------

def calc_retail_flip(inputs: dict) -> dict:
    purchase = inputs["purchase"]
    arv = inputs["arv"]
    rehab = inputs["rehab"]
    months = inputs.get("holding_retail", DEFAULTS["holding_retail"])
    posture = inputs.get("posture", "hard_money")
    sale_pct = inputs.get("retail_sale_pct", DEFAULTS["retail_sale_pct"])
    level = inputs.get("franchise_level")
    ftype = inputs.get("franchise_type")

    predicted_sale = arv * sale_pct
    holding = build_holding_costs(purchase, months,
                                  tax_rate=inputs.get("property_tax_rate"),
                                  insurance_rate=inputs.get("insurance_rate"))
    realtor_amt = realtor_fee(predicted_sale, "default")
    title = title_fee(purchase)
    financing = build_financing_costs(
        purchase + rehab, posture, months,
        arv=arv, lender_ltv_cap=inputs.get("lender_ltv_cap"),
        hm_rate=inputs.get("hm_rate"), hm_points=inputs.get("hm_points"),
    )
    sale_fees = build_sale_fees(predicted_sale, marketing=DEFAULTS["marketing_retail"],
                                franchise_level=level, franchise_type=ftype)

    cost_basis = (purchase + rehab + holding["total"] + realtor_amt + title +
                  financing["total"] + sale_fees["total"])
    net_profit = predicted_sale - cost_basis
    roi = (net_profit / cost_basis) * 100 if cost_basis > 0 else 0
    margin = (net_profit / predicted_sale) if predicted_sale > 0 else 0
    rehab_ratio = rehab / max(net_profit, 1)

    warnings = []
    if net_profit < 0:
        warnings.append({"id": "negative_profit", "label": "Negative Profit"})
    if roi < 10:
        warnings.append({"id": "low_roi", "label": "Low ROI"})
    if rehab_ratio > 1.0:
        warnings.append({"id": "high_rehab", "label": "High Rehab"})
    if 0 < margin < 0.10:
        warnings.append({"id": "thin_margin", "label": "Thin Margin"})

    annualized_roi = roi * (12.0 / months) if months > 0 else roi
    profit_per_month = net_profit / months if months > 0 else net_profit

    return {
        "strategy": "retail_flip",
        "predicted_sale": round(predicted_sale, 2),
        "rehab_used": rehab,
        "holding_months": months,
        "holding_total": round(holding["total"], 2),
        "realtor_fee": round(realtor_amt, 2),
        "title_fee": round(title, 2),
        "financing": financing,
        "sale_fees": sale_fees,
        "total_cost_basis": round(cost_basis, 2),
        "net_profit": round(net_profit, 2),
        "roi": round(roi, 2),
        "annualized_roi": round(annualized_roi, 2),
        "profit_per_month": round(profit_per_month, 2),
        "margin": round(margin, 4),
        "rehab_ratio": round(rehab_ratio, 3),
        "warnings": warnings,
    }


# ---------- Strategy: Wholetail ----------

def calc_wholetail(inputs: dict) -> dict:
    purchase = inputs["purchase"]
    arv = inputs["arv"]
    full_rehab = inputs["rehab"]
    partial_rehab = inputs.get("partial_rehab", round(full_rehab * 0.55))
    months = inputs.get("holding_wholetail", DEFAULTS["holding_wholetail"])
    posture = inputs.get("posture", "hard_money")
    level = inputs.get("franchise_level")
    ftype = inputs.get("franchise_type")

    rehab_progress = clamp(partial_rehab / full_rehab if full_rehab > 0 else 0)
    sale_pct = min(1.0, DEFAULTS["wholetail_base_pct"] + rehab_progress * DEFAULTS["wholetail_uplift"])
    predicted_sale = arv * sale_pct

    holding = build_holding_costs(purchase, months,
                                  tax_rate=inputs.get("property_tax_rate"),
                                  insurance_rate=inputs.get("insurance_rate"))
    realtor_amt = realtor_fee(predicted_sale, "wholesale_focused")
    title = title_fee(purchase)
    financing = build_financing_costs(
        purchase + partial_rehab, posture, months,
        arv=arv, lender_ltv_cap=inputs.get("lender_ltv_cap"),
        hm_rate=inputs.get("hm_rate"), hm_points=inputs.get("hm_points"),
    )
    sale_fees = build_sale_fees(predicted_sale, franchise_level=level, franchise_type=ftype)

    cost_basis = (purchase + partial_rehab + holding["total"] + realtor_amt + title +
                  financing["total"] + sale_fees["total"])
    net_profit = predicted_sale - cost_basis
    roi = (net_profit / cost_basis) * 100 if cost_basis > 0 else 0
    margin = (net_profit / predicted_sale) if predicted_sale > 0 else 0
    rehab_ratio = partial_rehab / max(net_profit, 1)

    warnings = []
    if net_profit < 0:
        warnings.append({"id": "negative_profit", "label": "Negative Profit"})
    if roi < 15:
        warnings.append({"id": "low_roi", "label": "Low ROI"})
    if rehab_ratio > 1.2:
        warnings.append({"id": "high_rehab", "label": "High Rehab"})
    if 0 < margin < 0.10:
        warnings.append({"id": "thin_margin", "label": "Thin Margin"})

    annualized_roi = roi * (12.0 / months) if months > 0 else roi
    profit_per_month = net_profit / months if months > 0 else net_profit

    return {
        "strategy": "wholetail",
        "predicted_sale": round(predicted_sale, 2),
        "sale_pct_of_arv": round(sale_pct, 4),
        "rehab_used": partial_rehab,
        "holding_months": months,
        "holding_total": round(holding["total"], 2),
        "realtor_fee": round(realtor_amt, 2),
        "title_fee": round(title, 2),
        "financing": financing,
        "sale_fees": sale_fees,
        "total_cost_basis": round(cost_basis, 2),
        "net_profit": round(net_profit, 2),
        "roi": round(roi, 2),
        "annualized_roi": round(annualized_roi, 2),
        "profit_per_month": round(profit_per_month, 2),
        "margin": round(margin, 4),
        "rehab_ratio": round(rehab_ratio, 3),
        "warnings": warnings,
    }


# ---------- Strategy: Wholesale (possession or double_close) ----------

def calc_wholesale(inputs: dict) -> dict:
    """Wholesale = take possession (default) or simultaneous double-close.

    Assignment is its own strategy now — see calc_assignment.
    """
    purchase = inputs["purchase"]
    arv = inputs["arv"]
    full_rehab = inputs["rehab"]
    months = inputs.get("holding_wholesale", DEFAULTS["holding_wholesale"])
    posture = inputs.get("posture", "hard_money")
    variant = inputs.get("wholesale_variant", "possession")
    level = inputs.get("franchise_level")
    ftype = inputs.get("franchise_type")

    predicted_sale = DEFAULTS["wholesale_sale_pct"] * max(0, arv - full_rehab)

    if variant == "double_close":
        holding_total = 0
        title = title_fee(purchase, multiplier=2.0)
        realtor_amt = realtor_fee(predicted_sale, "wholesale_focused")
        financing = build_financing_costs(
            purchase, posture, 0,
            arv=arv, lender_ltv_cap=inputs.get("lender_ltv_cap"),
            hm_rate=inputs.get("hm_rate"), hm_points=inputs.get("hm_points"),
        )
        if posture in ("hard_money", "hardmoney"):
            pts = inputs.get("hm_points") if inputs.get("hm_points") is not None else DEFAULTS["hard_money_points"]
            financing["points"] = financing.get("financed_basis", purchase) * pts
            financing["total"] = financing["points"]
        sale_fees = build_sale_fees(predicted_sale, franchise_level=level, franchise_type=ftype)
    else:  # possession (default)
        holding = build_holding_costs(purchase, months,
                                      tax_rate=inputs.get("property_tax_rate"),
                                      insurance_rate=inputs.get("insurance_rate"))
        holding_total = holding["total"]
        title = title_fee(purchase)
        realtor_amt = realtor_fee(predicted_sale, "wholesale_focused")
        financing = build_financing_costs(
            purchase, posture, months,
            arv=arv, lender_ltv_cap=inputs.get("lender_ltv_cap"),
            hm_rate=inputs.get("hm_rate"), hm_points=inputs.get("hm_points"),
        )
        sale_fees = build_sale_fees(predicted_sale, franchise_level=level, franchise_type=ftype)

    cost_basis = (purchase + holding_total + realtor_amt + title +
                  financing["total"] + sale_fees["total"])
    net_profit = predicted_sale - cost_basis
    roi = (net_profit / cost_basis) * 100 if cost_basis > 0 else 0
    margin = (net_profit / predicted_sale) if predicted_sale > 0 else 0
    rehab_ratio = full_rehab / max(net_profit, 1)

    warnings = []
    if net_profit < 0:
        warnings.append({"id": "negative_profit", "label": "Negative Profit"})
    if roi < 25:
        warnings.append({"id": "low_roi", "label": "Low ROI"})
    if rehab_ratio > 0.8:
        warnings.append({"id": "high_rehab", "label": "High Rehab"})

    effective_months = months if variant != "double_close" else 1  # avoid div-by-zero
    annualized_roi = roi * (12.0 / effective_months)
    profit_per_month = net_profit / effective_months

    return {
        "strategy": "wholesale",
        "variant": variant,
        "predicted_sale": round(predicted_sale, 2),
        "rehab_used": 0,
        "rehab_ref": full_rehab,
        "holding_months": months if variant != "double_close" else 0,
        "holding_total": round(holding_total, 2),
        "realtor_fee": round(realtor_amt, 2),
        "title_fee": round(title, 2),
        "financing": financing,
        "sale_fees": sale_fees,
        "total_cost_basis": round(cost_basis, 2),
        "net_profit": round(net_profit, 2),
        "roi": round(roi, 2),
        "annualized_roi": round(annualized_roi, 2),
        "profit_per_month": round(profit_per_month, 2),
        "margin": round(margin, 4),
        "rehab_ratio": round(rehab_ratio, 3),
        "warnings": warnings,
    }


# ---------- Strategy: Rental ----------

def calc_rental(inputs: dict) -> dict:
    purchase = inputs["purchase"]
    full_rehab = inputs.get("rehab", 0)
    # Rentals only need rent-ready condition, not retail-grade finish.
    # Use partial_rehab (defaults to 55% of full, same rule as wholetail).
    rehab = inputs.get("partial_rehab", round(full_rehab * 0.55))
    rent = inputs.get("rent")
    if not rent:
        rent = round(purchase * 0.01)
        rent_was_defaulted = True
    else:
        rent_was_defaulted = False

    down_pct = inputs.get("down_payment_pct", DEFAULTS["down_payment_pct"])
    loan_rate = inputs.get("loan_rate", DEFAULTS["loan_rate"])
    term = inputs.get("loan_term_years", DEFAULTS["loan_term_years"])
    tax_rate = inputs.get("property_tax_rate", DEFAULTS["property_tax_rate"])
    insurance_rate = inputs.get("insurance_rate", DEFAULTS["insurance_rate"])
    vacancy_rate = inputs.get("vacancy_rate", DEFAULTS["vacancy_rate"])
    other_income = inputs.get("other_income", 0)

    loan_amount = purchase * (1 - down_pct)
    monthly_payment = amortize_monthly_payment(loan_amount, loan_rate, term)
    down_payment = purchase - loan_amount

    title = purchase * DEFAULTS["title_rate"]
    closing_total = (title + DEFAULTS["inspection"] + DEFAULTS["appraisal"] +
                     loan_amount * DEFAULTS["lender_fee_rate"] +
                     DEFAULTS["attorney"] + DEFAULTS["recording"] +
                     DEFAULTS["other_closing"])

    cash_invested = down_payment + closing_total + rehab

    vacancy_loss = rent * vacancy_rate
    effective_income = rent - vacancy_loss + other_income

    monthly_tax = (purchase * tax_rate) / 12
    monthly_insurance = (purchase * insurance_rate) / 12
    maintenance = rent * DEFAULTS["maintenance_rate"]
    management = rent * DEFAULTS["management_rate"]
    capex = rent * DEFAULTS["capex_rate"]
    utilities = inputs.get("utilities_monthly", 0)
    total_expenses = (monthly_tax + monthly_insurance + maintenance +
                      management + capex + utilities)

    monthly_cashflow = effective_income - total_expenses - monthly_payment
    annual_cashflow = monthly_cashflow * 12

    noi_monthly = effective_income - total_expenses
    noi_annual = noi_monthly * 12
    cap_basis_dp = down_payment + closing_total
    cap_rate = (noi_annual / cap_basis_dp) * 100 if cap_basis_dp > 0 else 0
    cash_on_cash = (annual_cashflow / cash_invested) * 100 if cash_invested > 0 else 0
    dscr = noi_monthly / monthly_payment if monthly_payment > 0 else 0
    expense_ratio = total_expenses / effective_income if effective_income > 0 else 0

    warnings = []
    if monthly_cashflow < 0:
        warnings.append({"id": "negative_cashflow", "label": "Negative Cashflow"})
    elif monthly_cashflow < 100:
        warnings.append({"id": "low_cashflow", "label": "Thin Cashflow"})
    if cash_on_cash < 8:
        warnings.append({"id": "low_coc", "label": "Low CoC"})
    if dscr < 1.2:
        warnings.append({"id": "low_dscr", "label": "Low DSCR"})
    if expense_ratio > 0.5:
        warnings.append({"id": "high_expense_ratio", "label": "High Expense Ratio"})

    return {
        "strategy": "rental",
        "rent_used": rent,
        "rent_was_defaulted": rent_was_defaulted,
        "rehab_used": rehab,
        "rehab_ref": full_rehab,
        "loan_amount": round(loan_amount, 2),
        "down_payment": round(down_payment, 2),
        "monthly_payment": round(monthly_payment, 2),
        "closing_costs": round(closing_total, 2),
        "cash_invested": round(cash_invested, 2),
        "effective_income": round(effective_income, 2),
        "total_expenses": round(total_expenses, 2),
        "expense_breakdown": {
            "tax": round(monthly_tax, 2),
            "insurance": round(monthly_insurance, 2),
            "maintenance": round(maintenance, 2),
            "management": round(management, 2),
            "capex": round(capex, 2),
            "utilities": utilities,
        },
        "monthly_cashflow": round(monthly_cashflow, 2),
        "annual_cashflow": round(annual_cashflow, 2),
        "noi_annual": round(noi_annual, 2),
        "cap_rate": round(cap_rate, 2),
        "cash_on_cash": round(cash_on_cash, 2),
        "dscr": round(dscr, 3),
        "expense_ratio": round(expense_ratio, 3),
        "warnings": warnings,
    }


# ---------- Strategy: BRRRR ----------

def calc_brrrr(inputs: dict) -> dict:
    """BRRRR — Buy, Rehab, Rent, Refi, Repeat.

    All-cash (or LOC) entry, stabilize the property, then cash-out refi at
    typical 75% LTV of post-rehab ARV. Key metric is cash_left_in_deal:
    when refi proceeds recover initial investment, the strategy enables
    portfolio velocity. Differs from `rental` in capital path: rental
    finances at acquisition; BRRRR refis after stabilization.
    """
    purchase = inputs["purchase"]
    arv = inputs["arv"]
    rehab = inputs["rehab"]
    rent = inputs.get("rent")
    if not rent:
        rent = round(purchase * 0.01)
        rent_was_defaulted = True
    else:
        rent_was_defaulted = False

    posture = inputs.get("brrrr_posture", DEFAULTS["brrrr_holding_posture"])
    stabilization_months = inputs.get("brrrr_stabilization_months",
                                      DEFAULTS["brrrr_stabilization_months"])
    refi_ltv = inputs.get("brrrr_refi_ltv", DEFAULTS["brrrr_refi_ltv"])
    refi_rate = inputs.get("brrrr_refi_rate", DEFAULTS["brrrr_refi_rate"])
    refi_term = inputs.get("brrrr_refi_term_years", DEFAULTS["brrrr_refi_term_years"])
    refi_closing_pct = inputs.get("brrrr_refi_closing_pct", DEFAULTS["brrrr_refi_closing_pct"])
    tax_rate = inputs.get("property_tax_rate", DEFAULTS["property_tax_rate"])
    insurance_rate = inputs.get("insurance_rate", DEFAULTS["insurance_rate"])

    # Phase 1: Buy + Rehab + Stabilize (all-cash or LOC during stabilization)
    purchase_closing = purchase * (DEFAULTS["title_rate"] + 0.005)  # title + transfer
    holding = build_holding_costs(purchase, stabilization_months,
                                  tax_rate=tax_rate, insurance_rate=insurance_rate)
    stabilization_financing = build_financing_costs(purchase + rehab, posture,
                                                    stabilization_months)
    cash_in_initial = (purchase + rehab + purchase_closing +
                       holding["total"] + stabilization_financing["total"])

    # Phase 2: Refi
    new_loan = arv * refi_ltv
    refi_closing = new_loan * refi_closing_pct + DEFAULTS["appraisal"]
    cash_recovered = max(0, new_loan - refi_closing)
    cash_left_in_deal = cash_in_initial - cash_recovered

    # Phase 3: Hold long-term with new mortgage
    new_monthly_payment = amortize_monthly_payment(new_loan, refi_rate, refi_term)

    vacancy_loss = rent * DEFAULTS["vacancy_rate"]
    effective_income = rent - vacancy_loss + inputs.get("other_income", 0)
    monthly_tax = (purchase * tax_rate) / 12  # tax base often stays at purchase price
    monthly_insurance = (arv * insurance_rate) / 12  # but insurance is based on rebuild cost
    maintenance = rent * DEFAULTS["maintenance_rate"]
    management = rent * DEFAULTS["management_rate"]
    capex = rent * DEFAULTS["capex_rate"]
    utilities = inputs.get("utilities_monthly", 0)
    total_expenses = (monthly_tax + monthly_insurance + maintenance +
                      management + capex + utilities)

    monthly_cashflow = effective_income - total_expenses - new_monthly_payment
    annual_cashflow = monthly_cashflow * 12

    noi_monthly = effective_income - total_expenses
    dscr = noi_monthly / new_monthly_payment if new_monthly_payment > 0 else 0
    coc_on_residual = ((annual_cashflow / cash_left_in_deal) * 100
                       if cash_left_in_deal > 0 else float("inf"))
    infinite_return = cash_left_in_deal <= 0

    warnings = []
    if monthly_cashflow < 0:
        warnings.append({"id": "negative_cashflow", "label": "Negative Cashflow"})
    elif monthly_cashflow < 100:
        warnings.append({"id": "low_cashflow", "label": "Thin Cashflow"})
    if dscr < 1.20:
        warnings.append({"id": "low_dscr", "label": "Low DSCR (refi qualifying)"})
    if cash_left_in_deal > 20000:
        warnings.append({"id": "high_cash_left", "label": "High Cash Left in Deal"})
    if not infinite_return and coc_on_residual < 8:
        warnings.append({"id": "low_coc", "label": "Low CoC on Residual"})

    return {
        "strategy": "brrrr",
        "rent_used": rent,
        "rent_was_defaulted": rent_was_defaulted,
        "stabilization_months": stabilization_months,
        "phase1_initial_investment": round(cash_in_initial, 2),
        "phase1_breakdown": {
            "purchase": purchase,
            "rehab": rehab,
            "closing": round(purchase_closing, 2),
            "holding": round(holding["total"], 2),
            "financing": round(stabilization_financing["total"], 2),
        },
        "phase2_refi": {
            "ltv": refi_ltv,
            "new_loan": round(new_loan, 2),
            "rate": refi_rate,
            "closing_costs": round(refi_closing, 2),
            "cash_recovered": round(cash_recovered, 2),
        },
        "cash_left_in_deal": round(cash_left_in_deal, 2),
        "infinite_return": infinite_return,
        "new_monthly_payment": round(new_monthly_payment, 2),
        "effective_income": round(effective_income, 2),
        "total_expenses": round(total_expenses, 2),
        "monthly_cashflow": round(monthly_cashflow, 2),
        "annual_cashflow": round(annual_cashflow, 2),
        "dscr": round(dscr, 3),
        "coc_on_residual": ("infinite" if infinite_return
                            else round(coc_on_residual, 2)),
        "net_profit": round(annual_cashflow, 2),  # for cross-strategy comparison
        "warnings": warnings,
    }


# ---------- Scoring ----------

STRATEGY_WEIGHTS = {
    "assignment": {"profit": 1.0, "roi": 0.0, "third": 0.0},
    "wholesale": {"profit": 0.30, "roi": 0.50, "third": 0.20},
    "wholetail": {"profit": 0.40, "roi": 0.40, "third": 0.20},
    "retail_flip": {"profit": 0.50, "roi": 0.30, "third": 0.20},
    "rental": {"profit": 0.50, "roi": 0.30, "third": 0.20},
    "brrrr": {"cashflow": 0.35, "cash_left": 0.40, "dscr": 0.25},
}


def score_assignment(strategy: dict, target_fee: float) -> float:
    profit_s = clamp(strategy["assignment_fee"] / target_fee) if target_fee > 0 else 0
    base = profit_s * 10
    penalty = 0.5 * len(strategy.get("warnings", []))
    return max(0.0, min(10.0, base - penalty))


def score_flip(strategy: dict, target_profit: float, target_roi: float) -> float:
    profit_s = clamp(strategy["net_profit"] / target_profit) if target_profit > 0 else 0
    roi_s = clamp(strategy["roi"] / (target_roi * 100)) if target_roi > 0 else 0
    rr = strategy["rehab_ratio"]
    third_s = 1.0 if rr <= DEFAULTS["ideal_rehab_ratio"] else clamp(DEFAULTS["ideal_rehab_ratio"] / max(rr, 1e-6))
    w = STRATEGY_WEIGHTS[strategy["strategy"]]
    base = (profit_s * w["profit"] + roi_s * w["roi"] + third_s * w["third"]) * 10
    penalty = 0.5 * len(strategy.get("warnings", []))
    return max(0.0, min(10.0, base - penalty))


def score_rental(strategy: dict, target_cashflow: float, target_coc: float, target_dscr: float) -> float:
    profit_s = clamp(strategy["annual_cashflow"] / target_cashflow) if target_cashflow > 0 else 0
    roi_s = clamp((strategy["cash_on_cash"] / 100) / target_coc) if target_coc > 0 else 0
    dscr = strategy["dscr"]
    third_s = 1.0 if dscr >= target_dscr else clamp(dscr / target_dscr)
    w = STRATEGY_WEIGHTS["rental"]
    base = (profit_s * w["profit"] + roi_s * w["roi"] + third_s * w["third"]) * 10
    penalty = 0.5 * len(strategy.get("warnings", []))
    return max(0.0, min(10.0, base - penalty))


def score_brrrr(strategy: dict, target_cash_left: float, target_cashflow: float) -> float:
    """BRRRR scoring rewards low cash-left and positive cashflow.

    cash_left_score = 1.0 if cash_left <= target (typically ≤ $5k); falls
    linearly to 0 at $30k cash left. Negative cash left ("infinite return")
    caps at 1.0.
    """
    cash_left = strategy["cash_left_in_deal"]
    if cash_left <= target_cash_left:
        cash_left_s = 1.0
    elif cash_left >= 30000:
        cash_left_s = 0.0
    else:
        cash_left_s = 1.0 - ((cash_left - target_cash_left) / (30000 - target_cash_left))
    cashflow_s = clamp(strategy["annual_cashflow"] / target_cashflow) if target_cashflow > 0 else 0
    dscr_s = 1.0 if strategy["dscr"] >= 1.25 else clamp(strategy["dscr"] / 1.25)
    w = STRATEGY_WEIGHTS["brrrr"]
    base = (cashflow_s * w["cashflow"] + cash_left_s * w["cash_left"] + dscr_s * w["dscr"]) * 10
    penalty = 0.5 * len(strategy.get("warnings", []))
    return max(0.0, min(10.0, base - penalty))


# ---------- Buy-box fit ----------

def buy_box_fit_assignment(strategy: dict, target_fee: float) -> str:
    if strategy["assignment_fee"] >= target_fee:
        return "fit"
    if strategy["assignment_fee"] >= target_fee * 0.9:
        return "stretch"
    return "fail"


def buy_box_fit_flip(strategy: dict, target_profit: float, target_entry_pct: float,
                     arv: float, all_in_cost: float) -> str:
    passes = 0
    near = 0
    total = 3
    if strategy["net_profit"] >= target_profit:
        passes += 1
    elif strategy["net_profit"] >= target_profit * 0.9:
        near += 1
    entry_pct = (all_in_cost / arv) if arv > 0 else 1.0
    if entry_pct <= target_entry_pct:
        passes += 1
    elif entry_pct <= target_entry_pct + 0.05:
        near += 1
    if strategy.get("margin", 0) >= 0.10:
        passes += 1
    elif strategy.get("margin", 0) >= 0.09:
        near += 1
    pass_rate = passes / total
    if pass_rate >= 0.75:
        return "fit"
    if pass_rate >= 0.40 or (passes >= 1 and near >= 1):
        return "stretch"
    return "fail"


def buy_box_fit_brrrr(strategy: dict, target_cash_left: float,
                      target_cashflow: float, target_dscr: float) -> str:
    passes = 0
    near = 0
    checks_passed_so_far = []
    # Cash left in deal
    if strategy["cash_left_in_deal"] <= target_cash_left or strategy.get("infinite_return"):
        passes += 1
    elif strategy["cash_left_in_deal"] <= target_cash_left + 5000:
        near += 1
    # Annual cashflow
    if strategy["annual_cashflow"] >= target_cashflow:
        passes += 1
    elif strategy["annual_cashflow"] >= target_cashflow * 0.9:
        near += 1
    # DSCR on refi
    if strategy["dscr"] >= target_dscr:
        passes += 1
    elif strategy["dscr"] >= target_dscr * 0.95:
        near += 1
    pass_rate = passes / 3
    if pass_rate >= 0.75:
        return "fit"
    if pass_rate >= 0.40 or (passes >= 1 and near >= 1):
        return "stretch"
    return "fail"


def buy_box_fit_rental(strategy: dict, target_cashflow: float, target_dscr: float,
                       target_coc: float) -> str:
    passes = 0
    near = 0
    checks = [
        (strategy["annual_cashflow"], target_cashflow),
        (strategy["dscr"], target_dscr),
        (strategy["cash_on_cash"] / 100, target_coc),
        (strategy["monthly_cashflow"], 100),
    ]
    for actual, target in checks:
        if actual >= target:
            passes += 1
        elif actual >= target * 0.9:
            near += 1
    pass_rate = passes / len(checks)
    if pass_rate >= 0.75:
        return "fit"
    if pass_rate >= 0.40 or (passes >= 1 and near >= 1):
        return "stretch"
    return "fail"


# ---------- Risk Score ----------

def compute_risk(strategy: dict, all_in: float, arv: float,
                 target_profit: float, target_roi: float,
                 market_risk: float = 0.5) -> dict:
    profit = strategy.get("net_profit") or strategy.get("annual_cashflow", 0)
    roi_or_coc = strategy.get("roi") or strategy.get("cash_on_cash", 0)
    profit_short = 1 - clamp(profit / target_profit) if target_profit > 0 else 0
    roi_short = 1 - clamp(roi_or_coc / (target_roi * 100)) if target_roi > 0 else 0
    entry_pct = (all_in / arv) if arv > 0 else 0.75
    entry_agg = clamp((entry_pct - 0.65) / 0.10)
    deal_math_risk = clamp(0.35 * profit_short + 0.25 * roi_short + 0.40 * entry_agg)

    flag_weights = {
        "negative_profit": 0.30, "negative_cashflow": 0.30,
        "thin_margin": 0.15, "thin_assignment": 0.20,
        "low_dscr": 0.15, "low_coc": 0.10, "low_cashflow": 0.10,
        "high_rehab": 0.15, "high_expense_ratio": 0.10,
        "low_roi": 0.10,
    }
    exec_risk = clamp(sum(flag_weights.get(f["id"], 0) for f in strategy.get("warnings", [])))

    composite = 100 * clamp(0.45 * market_risk + 0.35 * deal_math_risk + 0.20 * exec_risk)

    if composite <= 25:
        label = "Low"
    elif composite <= 50:
        label = "Moderate"
    elif composite <= 75:
        label = "Elevated"
    else:
        label = "High"

    return {
        "score": round(composite, 1),
        "label": label,
        "components": {
            "market": round(market_risk, 3),
            "deal_math": round(deal_math_risk, 3),
            "execution": round(exec_risk, 3),
        },
    }


# ---------- Signals (positive badges) ----------

def compute_signals(assignment: dict, retail: dict, wholetail: dict,
                    wholesale: dict, rental: dict) -> list:
    """Independent positive signals. We removed redundant 'badge restates fact'
    items — kept only signals that carry information beyond the deal score.
    """
    signals = []

    # Strategy-spread signals
    if wholesale["net_profit"] >= 15000:
        signals.append("Strong Spread")
    if retail["margin"] >= 0.18:
        signals.append("High Margin")

    # Rental quick-reads (fast mobile glance for rentals)
    if rental["monthly_cashflow"] > 0:
        signals.append("Cash Flow Positive")
    if rental["dscr"] > 1.2:
        signals.append("DSCR > 1.2")

    # The rare deal that works as 2+ strategies
    strong_count = sum([
        1 if (assignment.get("deal_score", 0) >= 7) else 0,
        1 if (wholesale.get("deal_score", 0) >= 7) else 0,
        1 if (wholetail.get("deal_score", 0) >= 7) else 0,
        1 if (retail.get("deal_score", 0) >= 7) else 0,
        1 if (rental.get("deal_score", 0) >= 7) else 0,
    ])
    if strong_count >= 2:
        signals.append("Multi-Strategy Fit")

    return signals


# ---------- Confidence ----------

def compute_confidence(inputs: dict) -> str:
    critical = ["purchase", "arv", "rehab"]
    have_all = all(k in inputs and inputs[k] for k in critical)
    if not have_all:
        return "limited"
    if not inputs.get("rent"):
        return "partial"
    return "full"


# ---------- MAO ----------

def mao_retail(arv: float, rehab: float, target_profit: float = None,
               franchise_level: int = None, franchise_type: str = None) -> float:
    target = target_profit or DEFAULTS["target_profit_flip"]
    predicted_sale = arv * DEFAULTS["retail_sale_pct"]
    franchise = franchise_fee_pct(franchise_level, franchise_type)
    sale_side_fees = predicted_sale * (DEFAULTS["realtor_regular"] + franchise +
                                       DEFAULTS["other_sale_fee_rate"]) + DEFAULTS["marketing_retail"]
    rhs = predicted_sale - rehab - sale_side_fees - target
    return max(0, rhs / 1.0071)


def mao_wholesale(arv: float, rehab: float, target_profit: float = None,
                  franchise_level: int = None, franchise_type: str = None) -> float:
    target = target_profit or DEFAULTS["target_profit_wholesale"]
    predicted_sale = DEFAULTS["wholesale_sale_pct"] * max(0, arv - rehab)
    franchise = franchise_fee_pct(franchise_level, franchise_type)
    sale_side = predicted_sale * (DEFAULTS["realtor_discount"] + franchise +
                                   DEFAULTS["other_sale_fee_rate"])
    rhs = predicted_sale - sale_side - target
    return max(0, rhs / 1.005)


def mao_wholetail(arv: float, rehab: float, partial_rehab: float = None,
                  target_profit: float = None,
                  franchise_level: int = None, franchise_type: str = None) -> float:
    target = target_profit or DEFAULTS["target_profit_wholetail"]
    if partial_rehab is None:
        partial_rehab = round(rehab * 0.55)
    rehab_progress = clamp(partial_rehab / rehab if rehab > 0 else 0)
    sale_pct = min(1.0, DEFAULTS["wholetail_base_pct"] + rehab_progress * DEFAULTS["wholetail_uplift"])
    predicted_sale = arv * sale_pct
    franchise = franchise_fee_pct(franchise_level, franchise_type)
    sale_side = predicted_sale * (DEFAULTS["realtor_discount"] + franchise +
                                   DEFAULTS["other_sale_fee_rate"])
    rhs = predicted_sale - partial_rehab - sale_side - target
    return max(0, rhs / 1.006)


def mao_rental(rent: float, target_dscr: float = None, loan_rate: float = None,
               loan_term: int = None) -> float:
    target = target_dscr or DEFAULTS["target_dscr"]
    r = loan_rate or DEFAULTS["loan_rate"]
    t = loan_term or DEFAULTS["loan_term_years"]
    lo, hi = 1000, 5_000_000
    for _ in range(60):
        mid = (lo + hi) / 2
        loan = mid * 0.80
        payment = amortize_monthly_payment(loan, r, t)
        eff = rent - rent * DEFAULTS["vacancy_rate"]
        expenses = (mid * DEFAULTS["property_tax_rate"] / 12 +
                    mid * DEFAULTS["insurance_rate"] / 12 +
                    rent * (DEFAULTS["maintenance_rate"] + DEFAULTS["management_rate"] +
                            DEFAULTS["capex_rate"]))
        noi = eff - expenses
        dscr = noi / payment if payment > 0 else 0
        if dscr > target:
            lo = mid
        else:
            hi = mid
    return round(lo, -2)


# ---------- Payoff sanity-check ----------

def estimate_payoff_range(last_sold_price: float, last_sold_year: int,
                          current_year: int = 2026) -> dict:
    """Estimate likely remaining mortgage balance from last sale data.

    Used in the appointment-prep brief to gate "is there room for a deal":
    if estimated payoff > likely offer, the math is dead regardless of
    seller motivation. Assumes:
      - Down payment between 10% and 20% of last_sold_price (era-typical SFR)
      - 30-year fixed at the prevailing rate when last sold
      - No refi (flagged as the main caveat; refi can shift payoff materially)
      - Standard amortization, on-time payments

    Rates approximated by purchase year (30yr conventional, FRED H.15):
      2017 4.0%, 2018 4.5%, 2019 4.0%, 2020 3.25%, 2021 3.0%,
      2022 5.5%, 2023 6.8%, 2024 6.9%, 2025 6.7%, default 6.5%.
    """
    era_rates = {
        2015: 0.040, 2016: 0.037, 2017: 0.040, 2018: 0.045, 2019: 0.040,
        2020: 0.0325, 2021: 0.030, 2022: 0.055, 2023: 0.068, 2024: 0.069,
        2025: 0.067, 2026: 0.065,
    }
    rate = era_rates.get(last_sold_year, 0.065)
    months_elapsed = max(0, (current_year - last_sold_year) * 12)
    if months_elapsed <= 0:
        return {
            "low": last_sold_price * 0.80,
            "mid": last_sold_price * 0.85,
            "high": last_sold_price * 0.90,
            "assumed_rate": rate,
            "months_elapsed": 0,
            "caveat": "Just purchased — payoff approximates loan amount.",
        }

    def remaining_balance(principal: float, annual_rate: float, term_years: int, paid_months: int) -> float:
        n = term_years * 12
        r = annual_rate / 12
        if r == 0:
            return max(0, principal * (1 - paid_months / n))
        # Remaining balance after k payments on a fully-amortized loan
        return principal * ((1 + r) ** n - (1 + r) ** paid_months) / ((1 + r) ** n - 1)

    # 20% down scenario (lower payoff)
    loan_20 = last_sold_price * 0.80
    payoff_20 = remaining_balance(loan_20, rate, 30, months_elapsed)
    # 10% down scenario (higher payoff)
    loan_10 = last_sold_price * 0.90
    payoff_10 = remaining_balance(loan_10, rate, 30, months_elapsed)
    # 5% down sanity (occasional FHA/conv)
    loan_5 = last_sold_price * 0.95
    payoff_5 = remaining_balance(loan_5, rate, 30, months_elapsed)

    return {
        "low": round(payoff_20, -2),
        "mid": round(payoff_10, -2),
        "high": round(payoff_5, -2),
        "assumed_rate": rate,
        "months_elapsed": months_elapsed,
        "caveat": ("Range assumes no refi; cash-out refi could raise payoff "
                   "materially. Verify with seller on-site."),
    }


# ---------- Main orchestration ----------

def underwrite(inputs: dict) -> dict:
    for k in ("purchase", "arv", "rehab"):
        if k not in inputs or inputs[k] is None:
            return {"error": f"missing required input: {k}"}

    # Resolve market_risk from location_type if given
    location_type = inputs.get("location_type")
    if location_type and "market_risk" not in inputs:
        inputs["market_risk"] = DEFAULTS["market_risk_by_location"].get(location_type, 0.5)
    market_risk = inputs.get("market_risk", 0.5)

    risk_appetite = inputs.get("risk_appetite", "balanced")

    # Run all six strategies
    assignment = calc_assignment(inputs)
    wholesale = calc_wholesale(inputs)
    wholetail = calc_wholetail(inputs)
    retail = calc_retail_flip(inputs)
    rental = calc_rental(inputs)
    brrrr = calc_brrrr(inputs)

    # Score
    assignment["deal_score"] = round(score_assignment(assignment, DEFAULTS["target_profit_assignment"]), 1)
    wholesale["deal_score"] = round(score_flip(wholesale, DEFAULTS["target_profit_wholesale"], DEFAULTS["target_roi_wholesale"]), 1)
    wholetail["deal_score"] = round(score_flip(wholetail, DEFAULTS["target_profit_wholetail"], DEFAULTS["target_roi_flip"]), 1)
    retail["deal_score"] = round(score_flip(retail, DEFAULTS["target_profit_flip"], DEFAULTS["target_roi_flip"]), 1)
    rental["deal_score"] = round(score_rental(rental, DEFAULTS["target_cashflow_annual"], DEFAULTS["target_coc"], DEFAULTS["target_dscr"]), 1)
    brrrr["deal_score"] = round(score_brrrr(brrrr, DEFAULTS["target_brrrr_cash_left"], DEFAULTS["target_brrrr_cashflow_annual"]), 1)

    # Buy-box fit
    arv = inputs["arv"]
    rehab = inputs["rehab"]
    purchase = inputs["purchase"]
    all_in_retail = purchase + rehab + retail["holding_total"] + retail["title_fee"]
    all_in_wholetail = purchase + wholetail["rehab_used"] + wholetail["holding_total"] + wholetail["title_fee"]
    all_in_wholesale = purchase + wholesale["holding_total"] + wholesale["title_fee"]

    assignment["fit"] = buy_box_fit_assignment(assignment, DEFAULTS["target_profit_assignment"])
    wholesale["fit"] = buy_box_fit_flip(wholesale, DEFAULTS["target_profit_wholesale"], DEFAULTS["target_entry_pct_arv"], arv, all_in_wholesale)
    wholetail["fit"] = buy_box_fit_flip(wholetail, DEFAULTS["target_profit_wholetail"], DEFAULTS["target_entry_pct_arv"], arv, all_in_wholetail)
    retail["fit"] = buy_box_fit_flip(retail, DEFAULTS["target_profit_flip"], DEFAULTS["target_entry_pct_arv"], arv, all_in_retail)
    rental["fit"] = buy_box_fit_rental(rental, DEFAULTS["target_cashflow_annual"], DEFAULTS["target_dscr"], DEFAULTS["target_coc"])
    brrrr["fit"] = buy_box_fit_brrrr(brrrr, DEFAULTS["target_brrrr_cash_left"], DEFAULTS["target_brrrr_cashflow_annual"], DEFAULTS["target_dscr"])

    # Risk
    assignment["risk"] = compute_risk(
        {"net_profit": assignment["net_profit"], "roi": assignment["roi"], "warnings": assignment["warnings"]},
        assignment["total_cost_basis"], arv, DEFAULTS["target_profit_assignment"], 0.30, market_risk
    )
    retail["risk"] = compute_risk(retail, all_in_retail, arv, DEFAULTS["target_profit_flip"], DEFAULTS["target_roi_flip"], market_risk)
    wholetail["risk"] = compute_risk(wholetail, all_in_wholetail, arv, DEFAULTS["target_profit_wholetail"], DEFAULTS["target_roi_flip"], market_risk)
    wholesale["risk"] = compute_risk(wholesale, all_in_wholesale, arv, DEFAULTS["target_profit_wholesale"], DEFAULTS["target_roi_wholesale"], market_risk)
    rental_all_in = rental["cash_invested"]
    rental["risk"] = compute_risk(
        {"net_profit": rental["annual_cashflow"], "cash_on_cash": rental["cash_on_cash"], "warnings": rental["warnings"]},
        rental_all_in, arv if arv else purchase * 1.3,
        DEFAULTS["target_cashflow_annual"], DEFAULTS["target_coc"], market_risk
    )
    brrrr["risk"] = compute_risk(
        {"net_profit": brrrr["annual_cashflow"], "warnings": brrrr["warnings"]},
        brrrr["phase1_initial_investment"], arv,
        DEFAULTS["target_brrrr_cashflow_annual"], DEFAULTS["target_coc"], market_risk
    )

    # Pick best strategy. Sort by deal_score, then fit, then absolute profit.
    # Last tiebreaker matters when multiple strategies hit max score: prefer
    # the one capturing more dollars.
    strategies = [assignment, wholesale, wholetail, retail, rental, brrrr]
    fit_priority = {"fit": 2, "stretch": 1, "fail": 0}
    def absolute_profit(s):
        return s.get("net_profit") or s.get("annual_cashflow", 0)
    best = max(strategies, key=lambda s: (
        s["deal_score"],
        fit_priority.get(s.get("fit", "fail"), 0),
        absolute_profit(s),
    ))
    best_score = best["deal_score"]

    # Verdict — gated by risk appetite
    buy_threshold = DEFAULTS["verdict_buy_threshold"].get(risk_appetite, 7.0)
    negotiate_threshold = DEFAULTS["verdict_negotiate_threshold"].get(risk_appetite, 5.0)
    has_critical = any(f["id"] in ("negative_profit", "negative_cashflow") for f in best.get("warnings", []))

    if best_score >= buy_threshold and not has_critical and best.get("fit") == "fit":
        verdict = "BUY"
    elif best_score >= negotiate_threshold and not has_critical:
        verdict = "NEGOTIATE"
    else:
        verdict = "PASS"

    # MAOs
    level = inputs.get("franchise_level")
    ftype = inputs.get("franchise_type")
    maos = {
        "retail_at_target": round(mao_retail(arv, rehab, franchise_level=level, franchise_type=ftype), -2),
        "wholetail_at_target": round(mao_wholetail(arv, rehab, franchise_level=level, franchise_type=ftype), -2),
        "wholesale_at_target": round(mao_wholesale(arv, rehab, franchise_level=level, franchise_type=ftype), -2),
        "rental_at_dscr": mao_rental(rental["rent_used"]),
    }

    # Cash-overlay summary (when hard_money + lender_ltv_cap set). Surfaces
    # the largest overlay across flip strategies — the franchisee's
    # out-of-pocket cash above what the HM lender will fund.
    cash_overlay_by_strategy = {
        "retail_flip": retail["financing"].get("cash_overlay", 0),
        "wholetail": wholetail["financing"].get("cash_overlay", 0),
        "wholesale": wholesale["financing"].get("cash_overlay", 0),
    }
    max_overlay = max(cash_overlay_by_strategy.values()) if cash_overlay_by_strategy else 0
    cash_overlay_summary = {
        "cap_applied": inputs.get("lender_ltv_cap") is not None,
        "lender_ltv_cap": inputs.get("lender_ltv_cap"),
        "max_overlay": round(max_overlay, 2),
        "by_strategy": {k: round(v, 2) for k, v in cash_overlay_by_strategy.items()},
    }

    # Payoff estimate (when last-sale data provided). Used by appointment-prep
    # to gate whether a deal is possible at all (payoff > likely offer = dead).
    payoff_estimate = None
    if inputs.get("last_sold_price") and inputs.get("last_sold_year"):
        payoff_estimate = estimate_payoff_range(
            inputs["last_sold_price"],
            int(inputs["last_sold_year"]),
            current_year=int(inputs.get("current_year", 2026)),
        )

    # Pre-Offer (walk-in number): purchase / ARV ≤ 65%, repairs handled
    # separately. If sqft given, also surfaces a repair-adjusted version.
    pre_offer = compute_pre_offer(
        arv,
        sqft=inputs.get("sqft"),
        rehab_tier=inputs.get("rehab_tier"),
        rehab_estimate=inputs.get("rehab") if inputs.get("rehab") else None,
        pre_offer_pct=inputs.get("pre_offer_pct"),
    )

    # Signals
    signals = compute_signals(assignment, retail, wholetail, wholesale, rental)

    # BRRRR-specific signal
    if brrrr.get("infinite_return"):
        signals.append("BRRRR Recoverable")

    # Buy-Box Match signal (computed here since needs `best`)
    if best.get("fit") == "fit":
        signals.append("Buy-Box Match")

    confidence = compute_confidence(inputs)

    return {
        "calc_version": __version__,
        "address": inputs.get("address", "(no address provided)"),
        "verdict": verdict,
        "best_strategy": best["strategy"],
        "best_deal_score": best_score,
        "confidence": confidence,
        "risk_appetite": risk_appetite,
        "signals": signals,
        "inputs_echo": {
            "purchase": purchase,
            "arv": arv,
            "rehab": rehab,
            "rent": rental["rent_used"],
            "rent_defaulted": rental["rent_was_defaulted"],
            "posture": inputs.get("posture", "hard_money"),
            "franchise_level": level,
            "franchise_type": ftype,
            "franchise_fee_pct": franchise_fee_pct(level, ftype),
            "location_type": location_type,
            "market_risk": market_risk,
        },
        "strategies": {
            "assignment": assignment,
            "wholesale": wholesale,
            "wholetail": wholetail,
            "retail_flip": retail,
            "rental": rental,
            "brrrr": brrrr,
        },
        "mao": maos,
        "pre_offer": pre_offer,
        "cash_overlay": cash_overlay_summary,
        "payoff_estimate": payoff_estimate,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", help="JSON string of inputs")
    args = parser.parse_args()

    if args.inputs:
        inputs = json.loads(args.inputs)
    else:
        data = sys.stdin.read()
        if not data.strip():
            print(json.dumps({"error": "no input provided"}))
            sys.exit(1)
        inputs = json.loads(data)

    result = underwrite(inputs)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
