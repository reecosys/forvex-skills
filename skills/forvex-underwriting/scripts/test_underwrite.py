#!/usr/bin/env python3
"""
Regression tests for underwrite.py.

Run before any commit that changes the calculator:
    python3 test_underwrite.py

Each test asserts the calculator's output for a known input matches a
snapshot. When the math intentionally changes, bump __version__ in
underwrite.py and update the snapshot values here in the same commit.
"""

import json
import os
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(__file__), "underwrite.py")


def run_calc(inputs: dict) -> dict:
    result = subprocess.run(
        ["python3", SCRIPT, "--inputs", json.dumps(inputs)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def assert_close(actual, expected, tol, label):
    if abs(actual - expected) > tol:
        raise AssertionError(
            f"{label}: expected {expected} ± {tol}, got {actual}"
        )


def assert_eq(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


# ---------- Fixtures (snapshot at calc_version 0.2.0) ----------

FIXTURES = [
    {
        "name": "T1 — Dallas BUY rental",
        "inputs": {
            "address": "123 Main St, Dallas TX",
            "purchase": 135000, "arv": 215000, "rehab": 32000, "rent": 1650,
            "posture": "cash", "franchise_level": 6, "franchise_type": "full",
            "location_type": "suburban",
        },
        "expected": {
            "verdict": "BUY",
            "best_strategy": "rental",
            "best_deal_score": 9.7,
            "confidence": "full",
        },
        "tolerances": {"score": 0.3},
    },
    {
        "name": "T2 — Memphis PASS (all underwater)",
        "inputs": {
            "address": "456 Oak Ave, Memphis TN",
            "purchase": 210000, "arv": 230000, "rehab": 40000, "rent": 1400,
            "posture": "hard_money", "franchise_level": 4, "franchise_type": "full",
            "location_type": "suburban",
        },
        "expected": {
            "verdict": "PASS",
            "best_deal_score": 0.0,
            "confidence": "full",
        },
        "tolerances": {"score": 0.1},
    },
    {
        "name": "T3 — Atlanta NEGOTIATE",
        "inputs": {
            "address": "789 Pine, Atlanta GA",
            "purchase": 185000, "arv": 250000, "rehab": 35000, "rent": 1800,
            "posture": "cash", "franchise_level": 4, "franchise_type": "full",
            "location_type": "suburban",
        },
        "expected": {
            "verdict": "NEGOTIATE",
            "best_strategy": "rental",
            "confidence": "full",
        },
        "tolerances": {"score": 0.3},
    },
    {
        "name": "T4 — Birmingham deep spread BUY wholetail",
        "inputs": {
            "address": "222 Elm St, Birmingham AL",
            "purchase": 45000, "arv": 135000, "rehab": 50000,
            "posture": "cash", "franchise_level": 4, "franchise_type": "full",
            "location_type": "urban",
        },
        "expected": {
            "verdict": "BUY",
            "best_strategy": "wholetail",
            "confidence": "partial",
        },
        "tolerances": {"score": 0.5},
    },
    {
        "name": "T5 — Tulsa incomplete data",
        "inputs": {
            "address": "555 Birch, Tulsa OK",
            "purchase": 95000, "arv": 145000, "rehab": 18000,
            "posture": "hard_money", "franchise_level": 4, "franchise_type": "full",
            "location_type": "suburban",
        },
        "expected": {
            "verdict": "PASS",
            "best_strategy": "rental",
            "confidence": "partial",
        },
        "tolerances": {"score": 0.5},
    },
    {
        "name": "Franchise fee — Associate L1 (5%)",
        "inputs": {
            "address": "test", "purchase": 100000, "arv": 200000, "rehab": 25000,
            "franchise_level": 1, "franchise_type": "associate",
        },
        "expected": {"franchise_fee_pct": 0.05},
        "tolerances": {},
        "check_field": "inputs_echo.franchise_fee_pct",
    },
    {
        "name": "Franchise fee — L6 Full (0.8%)",
        "inputs": {
            "address": "test", "purchase": 100000, "arv": 200000, "rehab": 25000,
            "franchise_level": 6, "franchise_type": "full",
        },
        "expected": {"franchise_fee_pct": 0.008},
        "tolerances": {},
        "check_field": "inputs_echo.franchise_fee_pct",
    },
    {
        "name": "BRRRR strategy is computed",
        "inputs": {
            "address": "test", "purchase": 80000, "arv": 180000, "rehab": 30000,
            "rent": 1700, "posture": "cash", "franchise_level": 4, "franchise_type": "full",
        },
        "expected": {"has_brrrr": True},
        "tolerances": {},
        "check_field": "strategies.brrrr.cash_left_in_deal",  # exists if BRRRR computed
    },
    {
        "name": "calc_version present in output",
        "inputs": {
            "address": "test", "purchase": 100000, "arv": 200000, "rehab": 25000,
        },
        "expected": {"has_version": True},
        "tolerances": {},
        "check_field": "calc_version",
    },
    {
        "name": "Time-adjusted metrics present on flip strategies",
        "inputs": {
            "address": "test", "purchase": 100000, "arv": 200000, "rehab": 25000,
        },
        "expected": {"has_annualized_roi": True},
        "tolerances": {},
        "check_field": "strategies.retail_flip.annualized_roi",
    },
    {
        "name": "Pre-Offer base = ARV x 65%",
        "inputs": {
            "address": "test", "purchase": 100000, "arv": 200000, "rehab": 25000,
        },
        "expected": {"pre_offer_base": 130000},  # 200000 * 0.65
        "tolerances": {},
        "check_field": "pre_offer.base",
    },
    {
        "name": "Pre-Offer $/sqft tier estimate (light, 1000sqft = $15k)",
        "inputs": {
            "address": "test", "purchase": 80000, "arv": 150000, "rehab": 0,
            "sqft": 1000, "rehab_tier": "light",
        },
        "expected": {"pre_offer_adjusted": 82500},  # 150000*0.65 - 15000
        "tolerances": {},
        "check_field": "pre_offer.adjusted",
    },
]


def get_nested(d: dict, path: str):
    keys = path.split(".")
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return None
    return d


def run_test(fixture: dict) -> tuple[bool, str]:
    try:
        result = run_calc(fixture["inputs"])
        expected = fixture["expected"]
        tolerances = fixture.get("tolerances", {})

        if "check_field" in fixture:
            actual = get_nested(result, fixture["check_field"])
            exp_value = list(expected.values())[0]
            if isinstance(exp_value, bool):
                if (actual is not None) != exp_value:
                    return False, f"check_field {fixture['check_field']}: present={actual is not None}, expected={exp_value}"
            else:
                if abs(actual - exp_value) > 0.001:
                    return False, f"check_field {fixture['check_field']}: got {actual}, expected {exp_value}"
            return True, "ok"

        if "verdict" in expected:
            assert_eq(result["verdict"], expected["verdict"], "verdict")
        if "best_strategy" in expected:
            assert_eq(result["best_strategy"], expected["best_strategy"], "best_strategy")
        if "best_deal_score" in expected:
            assert_close(
                result["best_deal_score"],
                expected["best_deal_score"],
                tolerances.get("score", 0.1),
                "best_deal_score",
            )
        if "confidence" in expected:
            assert_eq(result["confidence"], expected["confidence"], "confidence")
        return True, "ok"
    except AssertionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    passed, failed = 0, 0
    for fixture in FIXTURES:
        ok, msg = run_test(fixture)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {fixture['name']}")
        if not ok:
            print(f"       {msg}")
            failed += 1
        else:
            passed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
