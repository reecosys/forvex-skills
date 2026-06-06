#!/usr/bin/env python3
"""Regression tests for rehab_light.py. Run before changing calc logic:
    python test_rehab_light.py
"""
import json
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RL = os.path.join(HERE, "rehab_light.py")


def run(payload):
    out = subprocess.run([sys.executable, RL, json.dumps(payload)],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise AssertionError(f"script failed: {out.stderr}")
    return json.loads(out.stdout)


def approx(a, b, tol=1.0):
    return abs(a - b) <= tol


def test_requires_sqft():
    out = subprocess.run([sys.executable, RL, json.dumps({"condition": "cosmetic"})],
                         capture_output=True, text=True)
    assert out.returncode != 0
    print("ok: requires sqft")


def test_heavy_condition_rejected():
    out = subprocess.run([sys.executable, RL, json.dumps({"sqft": 1600, "condition": "gut"})],
                         capture_output=True, text=True)
    assert out.returncode != 0, "gut/heavy should be rejected by the LIGHT tool"
    print("ok: heavy/gut condition pushed to the full tool")


def test_moderate_costs_more_than_cosmetic():
    cos = run({"sqft": 1600, "condition": "cosmetic"})
    mod = run({"sqft": 1600, "condition": "moderate"})
    assert mod["expected_cost"] > cos["expected_cost"]
    assert mod["flags"]["moderate_condition"] is True
    print("ok: moderate condition costs more than cosmetic")


def test_finish_level_scales_material_categories():
    rental = run({"sqft": 1600, "finish_level": "rental"})
    moveup = run({"sqft": 1600, "finish_level": "moveup"})
    assert moveup["expected_cost"] > rental["expected_cost"]
    # flooring is finish-sensitive; should rise with finish level
    f_rental = next(c["cost"] for c in rental["cosmetic_breakdown"] if c["key"] == "flooring")
    f_moveup = next(c["cost"] for c in moveup["cosmetic_breakdown"] if c["key"] == "flooring")
    assert f_moveup > f_rental
    print("ok: higher finish level scales finish-sensitive categories up")


def test_paint_not_finish_sensitive():
    rental = run({"sqft": 1600, "finish_level": "rental"})
    luxury = run({"sqft": 1600, "finish_level": "luxury"})
    p_rental = next(c["cost"] for c in rental["cosmetic_breakdown"] if c["key"] == "paint")
    p_luxury = next(c["cost"] for c in luxury["cosmetic_breakdown"] if c["key"] == "paint")
    assert approx(p_rental, p_luxury), "paint should not move with finish level"
    print("ok: non-finish-sensitive categories (paint) ignore finish level")


def test_big_ticket_flips_scope_verdict():
    light = run({"sqft": 1600, "condition": "cosmetic"})
    assert light["flags"]["beyond_light_rehab"] is False
    heavy = run({"sqft": 1600, "condition": "cosmetic",
                 "big_ticket": {"roof": True, "hvac": True}})
    assert heavy["flags"]["beyond_light_rehab"] is True
    assert heavy["big_ticket_subtotal"] > 0
    assert len(heavy["big_ticket_items"]) == 2
    print("ok: any big-ticket item flips the scope verdict to 'beyond light'")


def test_big_ticket_outside_cosmetic_engine():
    """A roof should add to big-ticket, not change the cosmetic subtotal."""
    base = run({"sqft": 1600})
    with_roof = run({"sqft": 1600, "big_ticket": {"roof": True}})
    assert approx(base["cosmetic_subtotal"], with_roof["cosmetic_subtotal"]), \
        "big-ticket must not alter the cosmetic engine"
    assert with_roof["big_ticket_subtotal"] > 0
    print("ok: big-ticket items live outside the cosmetic engine")


def test_big_ticket_override_used():
    r = run({"sqft": 1600, "big_ticket": {"roof": True},
             "big_ticket_overrides": {"roof": 15000}})
    roof = next(b for b in r["big_ticket_items"] if b["key"] == "roof")
    assert approx(roof["cost"], 15000)
    assert roof["source"] == "your number"
    print("ok: big-ticket override replaces the placeholder")


def test_cost_multiplier_scales_everything():
    base = run({"sqft": 1600, "big_ticket": {"roof": True}})
    hi = run({"sqft": 1600, "big_ticket": {"roof": True}, "cost_multiplier": 1.4})
    assert hi["cosmetic_subtotal"] > base["cosmetic_subtotal"]
    assert hi["big_ticket_subtotal"] > base["big_ticket_subtotal"]  # roof scales too
    print("ok: cost multiplier scales cosmetic AND big-ticket")


def test_range_brackets_expected():
    r = run({"sqft": 1600, "condition": "moderate"})
    assert r["range_low"] < r["expected_cost"] < r["range_high"]
    print("ok: low < expected < high band holds")


def test_bath_count_drives_bathroom_cost():
    one = run({"sqft": 1600, "bath_count": 1})
    three = run({"sqft": 1600, "bath_count": 3})
    b1 = next(c["cost"] for c in one["cosmetic_breakdown"] if c["key"] == "bathroom")
    b3 = next(c["cost"] for c in three["cosmetic_breakdown"] if c["key"] == "bathroom")
    assert approx(b3, b1 * 3)
    print("ok: bathroom cost scales with bath count")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print(f"\nAll {len(fns)} tests passed.")
