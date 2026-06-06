#!/usr/bin/env python3
"""Regression tests for postmortem.py. Run before changing calc logic:
    python test_postmortem.py
"""
import json
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PM = os.path.join(HERE, "postmortem.py")


def run(payload):
    out = subprocess.run([sys.executable, PM, json.dumps(payload)],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise AssertionError(f"script failed: {out.stderr}")
    return json.loads(out.stdout)


def approx(a, b, tol=1.0):
    return abs(a - b) <= tol


BASE = {
    "projected": {"purchase": 110000, "rehab": 45000, "sale": 220000, "hold_months": 4},
    "actual":    {"purchase": 112000, "rehab": 58000, "sale": 213000, "hold_months": 6},
}


def test_requires_both_sides():
    out = subprocess.run([sys.executable, PM, json.dumps({"projected": {}})],
                         capture_output=True, text=True)
    assert out.returncode != 0
    print("ok: requires projected and actual")


def test_bridge_reconciles():
    """The profit bridge must sum exactly to the profit variance."""
    r = run(BASE)
    total = sum(d["profit_impact"] for d in r["profit_bridge"])
    assert approx(total, r["profit_variance"]), f"{total} vs {r['profit_variance']}"
    assert r["flags"]["bridge_reconciles"] is True
    print("ok: profit bridge reconciles to profit variance")


def test_overruns_reduce_profit():
    r = run(BASE)
    # rehab blew up and sale came under => actual profit < projected
    assert r["actual_profit"] < r["projected_profit"]
    assert r["verdict"] in ("MISSED PLAN", "LOST MONEY")
    print("ok: cost overruns + low sale reduce profit and trip verdict")


def test_beat_plan():
    r = run({
        "projected": {"purchase": 110000, "rehab": 50000, "sale": 215000, "hold_months": 5},
        "actual":    {"purchase": 108000, "rehab": 44000, "sale": 224000, "hold_months": 3},
    })
    assert r["actual_profit"] > r["projected_profit"]
    assert r["verdict"] == "BEAT PLAN"
    print("ok: under-budget + over-ARV + faster sale => BEAT PLAN")


def test_lost_money():
    r = run({
        "projected": {"purchase": 150000, "rehab": 40000, "sale": 220000, "hold_months": 4},
        "actual":    {"purchase": 150000, "rehab": 95000, "sale": 195000, "hold_months": 9},
    })
    assert r["flags"]["lost_money"] is True
    assert r["verdict"] == "LOST MONEY"
    print("ok: severe overruns flagged as LOST MONEY")


def test_explicit_profit_mismatch_flagged():
    r = run({
        "projected": {"purchase": 110000, "rehab": 45000, "sale": 220000, "profit": 99999},
        "actual":    {"purchase": 112000, "rehab": 58000, "sale": 213000},
    })
    assert r["flags"]["projected_profit_mismatch_vs_stack"] is True
    print("ok: user-supplied profit that disagrees with the stack is flagged")


def test_rehab_overrun_lesson_present():
    r = run(BASE)
    joined = " ".join(r["lessons"]).lower()
    assert "rehab" in joined and "over" in joined
    print("ok: rehab-overrun lesson generated")


def test_fee_defaults_to_zero_and_flags():
    r = run(BASE)  # no fee supplied
    assert r["line_items"]["franchise_fee"]["projected"] == 0.0
    assert r["line_items"]["franchise_fee"]["actual"] == 0.0
    assert r["flags"]["transaction_fee_not_set"] is True
    print("ok: no fee supplied => $0 on both sides and flagged")


def test_percent_fee_applied_per_side():
    r = run({**BASE, "franchise_fee_pct": 0.05})
    li = r["line_items"]["franchise_fee"]
    assert approx(li["projected"], 0.05 * 220000), li["projected"]
    assert approx(li["actual"], 0.05 * 213000), li["actual"]
    assert r["flags"]["transaction_fee_not_set"] is False
    print("ok: percent fee applied to each side's sale price")


def test_flat_dollar_fee_wins():
    r = run({**BASE, "franchise_fee_usd": 3000, "franchise_fee_pct": 0.05})
    li = r["line_items"]["franchise_fee"]
    assert approx(li["projected"], 3000) and approx(li["actual"], 3000)
    print("ok: flat-dollar fee beats percent on both sides")


def test_cash_no_financing():
    r = run({
        "projected": {"purchase": 110000, "rehab": 45000, "sale": 220000},
        "actual":    {"purchase": 112000, "rehab": 58000, "sale": 213000},
        "financing_type": "cash",
    })
    assert r["line_items"]["financing"]["projected"] == 0.0
    assert r["line_items"]["financing"]["actual"] == 0.0
    print("ok: cash deal has zero financing on both sides")


def test_annualized_roi_reflects_hold():
    r = run(BASE)
    pm = r["metrics"]["actual"]
    # 6-month hold => annualized roughly 2x the period ROI
    assert pm["annualized_roi_on_all_in"] is not None
    assert pm["annualized_roi_on_all_in"] > pm["roi_on_all_in"]
    print("ok: annualized ROI scales up a sub-12-month hold")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print(f"\nAll {len(fns)} tests passed.")
