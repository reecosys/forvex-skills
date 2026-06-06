#!/usr/bin/env python3
"""Regression tests for mao.py. Run before changing any calc logic:
    python test_mao.py
"""
import json
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MAO = os.path.join(HERE, "mao.py")


def run(payload):
    out = subprocess.run(
        [sys.executable, MAO, json.dumps(payload)],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise AssertionError(f"script failed: {out.stderr}")
    return json.loads(out.stdout)


def approx(a, b, tol=1.0):
    return abs(a - b) <= tol


def test_requires_arv_and_rehab():
    out = subprocess.run([sys.executable, MAO, json.dumps({"arv": 200000})],
                         capture_output=True, text=True)
    assert out.returncode != 0, "should fail without rehab"
    print("ok: requires arv and rehab")


def test_cash_no_financing_cost():
    r = run({"arv": 200000, "rehab": 40000, "financing": "cash"})
    assert r["cost_stack"]["less_financing"] == 0.0, "cash should have zero financing"
    print("ok: cash has no financing cost")


def test_cost_stack_reconciles():
    """ARV minus every line item must equal the MAO."""
    r = run({"arv": 220000, "rehab": 45000})
    cs = r["cost_stack"]
    recomputed = (cs["arv"] - cs["less_selling_costs"] - cs["less_rehab"]
                  - cs["less_holding_soft"] - cs["less_financing"]
                  - cs["less_buying_costs"] - cs["less_franchise_fee"]
                  - cs["less_target_profit"])
    assert approx(recomputed, cs["equals_mao"]), \
        f"stack does not reconcile: {recomputed} vs {cs['equals_mao']}"
    print("ok: cost stack reconciles to MAO")


def test_higher_margin_lowers_offer():
    lo = run({"arv": 200000, "rehab": 40000, "target_margin_pct": 0.10})
    hi = run({"arv": 200000, "rehab": 40000, "target_margin_pct": 0.25})
    assert hi["detailed_mao"] < lo["detailed_mao"], "more profit demanded => lower offer"
    print("ok: higher margin lowers MAO")


def test_more_rehab_lowers_offer():
    a = run({"arv": 200000, "rehab": 20000})
    b = run({"arv": 200000, "rehab": 60000})
    assert b["detailed_mao"] < a["detailed_mao"], "more rehab => lower offer"
    print("ok: more rehab lowers MAO")


def test_profit_floor_binds():
    r = run({"arv": 200000, "rehab": 40000, "target_margin_pct": 0.10,
             "profit_floor_usd": 40000})
    assert r["flags"]["profit_floor_binds"] is True
    assert approx(r["inputs"]["target_profit_usd"], 40000)
    print("ok: dollar profit floor binds over margin %")


def test_hv_65_rule_matches_known_value():
    r = run({"arv": 300000, "rehab": 50000})
    # forVEX 65% rule: 0.65 * 300000 - 50000 = 145000
    assert approx(r["quick_mao_65_rule"], 145000), r["quick_mao_65_rule"]
    print("ok: forVEX 65% rule cross-check matches hand math")


def test_ladder_is_monotonic():
    r = run({"arv": 250000, "rehab": 50000})
    maos = [row["mao_usd"] for row in r["offer_ladder"]]
    assert maos[0] > maos[1] > maos[2], f"ladder should descend with margin: {maos}"
    print("ok: offer ladder descends as margin grows")


def test_hard_money_costs_more_than_cash():
    cash = run({"arv": 220000, "rehab": 45000, "financing": "cash"})
    hm = run({"arv": 220000, "rehab": 45000, "financing": "hard_money"})
    assert hm["detailed_mao"] < cash["detailed_mao"], "HM carry => lower MAO than cash"
    print("ok: hard money yields lower MAO than cash")


def test_fee_defaults_to_zero_and_flags():
    r = run({"arv": 200000, "rehab": 40000})
    assert r["cost_stack"]["less_franchise_fee"] == 0.0
    assert r["flags"]["franchise_fee_not_set"] is True
    print("ok: no fee entered => $0 and flagged")


def test_percent_fee_applied_on_arv():
    r = run({"arv": 200000, "rehab": 40000, "franchise_fee_pct": 0.05})
    assert approx(r["cost_stack"]["less_franchise_fee"], 10000)  # 5% of 200k
    assert r["flags"]["franchise_fee_not_set"] is False
    print("ok: percent fee applied as fraction of ARV")


def test_flat_dollar_fee_wins_over_percent():
    r = run({"arv": 200000, "rehab": 40000,
             "franchise_fee_usd": 2500, "franchise_fee_pct": 0.05})
    assert approx(r["cost_stack"]["less_franchise_fee"], 2500)
    print("ok: flat-dollar fee beats percent when both given")


def test_higher_fee_lowers_offer():
    none = run({"arv": 200000, "rehab": 40000})
    fee = run({"arv": 200000, "rehab": 40000, "franchise_fee_pct": 0.05})
    assert fee["detailed_mao"] < none["detailed_mao"]
    print("ok: adding a fee lowers the MAO")


def test_default_selling_and_hm_rate():
    r = run({"arv": 200000, "rehab": 40000})
    # selling default now 6% of ARV = 12000
    assert approx(r["cost_stack"]["less_selling_costs"], 12000), \
        r["cost_stack"]["less_selling_costs"]
    print("ok: selling default is 6% of ARV")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print(f"\nAll {len(fns)} tests passed.")
