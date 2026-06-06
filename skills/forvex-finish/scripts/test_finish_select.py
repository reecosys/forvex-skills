#!/usr/bin/env python3
"""Regression tests for finish_select.py. Run before changing calc logic:
    python test_finish_select.py
"""
import json
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FS = os.path.join(HERE, "finish_select.py")


def run(payload):
    out = subprocess.run([sys.executable, FS, json.dumps(payload)],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise AssertionError(f"script failed: {out.stderr}")
    return json.loads(out.stdout)


def approx(a, b, tol=1.0):
    return abs(a - b) <= tol


def test_requires_arv_and_sqft():
    out = subprocess.run([sys.executable, FS, json.dumps({"arv": 250000})],
                         capture_output=True, text=True)
    assert out.returncode != 0
    print("ok: requires arv and sqft")


def test_comp_tier_drives_target():
    r = run({"arv": 250000, "sqft": 1600, "comp_tier": "entry"})
    # ARV alone would infer 'mid', but comps say 'entry' — match the comps
    assert r["target_tier"] == "entry"
    assert "comp" in r["tier_source"]
    print("ok: comp tier overrides ARV inference (match the comps)")


def test_override_wins():
    r = run({"arv": 250000, "sqft": 1600, "comp_tier": "entry", "tier_override": "luxury"})
    assert r["target_tier"] == "luxury"
    assert r["tier_source"] == "override"
    print("ok: explicit tier override beats everything")


def test_arv_inference_monotonic():
    tiers = [run({"arv": a, "sqft": 1500})["target_tier"]
             for a in (120000, 200000, 350000, 600000)]
    ranks = [["rental", "entry", "mid", "moveup", "luxury"].index(t) for t in tiers]
    assert ranks == sorted(ranks), ranks
    assert all(run({"arv": a, "sqft": 1500})["flags"]["tier_inferred_from_national_bands"]
               for a in (120000, 600000))
    print("ok: absolute-band inference is monotonic and flagged as national")


def test_same_arv_different_tier_by_local_median():
    # The Louisville vs Miami point: same $500k ARV, different markets.
    louisville = run({"arv": 500000, "sqft": 2500, "local_median": 280000})
    miami = run({"arv": 500000, "sqft": 2500, "local_median": 650000})
    assert louisville["target_tier"] == "luxury", louisville["target_tier"]
    assert miami["target_tier"] in ("entry", "mid"), miami["target_tier"]
    assert TIER_RANK_T(louisville["target_tier"]) > TIER_RANK_T(miami["target_tier"])
    print("ok: same ARV yields higher tier in a lower-median market (Louisville vs Miami)")


def test_low_arv_in_high_median_market():
    # $150k house where median is $280k => low tier (entry)
    r = run({"arv": 150000, "sqft": 1200, "local_median": 280000})
    assert r["target_tier"] == "entry", r["target_tier"]
    assert r["flags"]["tier_inferred_from_median_ratio"] is True
    print("ok: ARV well below local median => entry tier (ratio-based)")


def test_at_median_is_mid():
    r = run({"arv": 280000, "sqft": 1600, "local_median": 280000})
    assert r["target_tier"] == "mid", r["target_tier"]
    print("ok: ARV near local median => mid tier")


def TIER_RANK_T(t):
    return ["rental", "entry", "mid", "moveup", "luxury"].index(t)


def test_allocation_sums_to_budget():
    r = run({"arv": 250000, "sqft": 1600, "comp_tier": "mid", "rehab_budget": 40000})
    total = sum(c["budget"] for c in r["budget"]["allocation"])
    assert approx(total, 40000), total
    pct = sum(c["pct"] for c in r["budget"]["allocation"])
    assert approx(pct, 1.0, 0.001), pct
    print("ok: category allocation sums to the budget (and to 100%)")


def test_thin_budget_is_under_improving():
    # $10k on 1600 sqft = $6.25/sf, below mid tier's range
    r = run({"arv": 250000, "sqft": 1600, "comp_tier": "mid", "rehab_budget": 10000})
    assert "UNDER" in r["budget"]["verdict"]
    assert r["flags"]["budget_off_target"] is True
    print("ok: thin budget flagged UNDER-IMPROVING for tier")


def test_rich_budget_is_over_improving():
    # $120k on 1600 sqft = $75/sf, above mid tier's range
    r = run({"arv": 250000, "sqft": 1600, "comp_tier": "mid", "rehab_budget": 120000})
    assert "OVER" in r["budget"]["verdict"]
    print("ok: rich budget flagged OVER-IMPROVING for tier")


def test_comp_guard_over_improve():
    r = run({"arv": 250000, "sqft": 1600, "comp_tier": "entry", "tier_override": "luxury"})
    assert r["flags"]["over_improving_vs_comps"] is True
    assert r["comp_guard"].startswith("OVER")
    print("ok: comp guard fires when target tier exceeds comp tier")


def test_comp_guard_under_improve():
    r = run({"arv": 250000, "sqft": 1600, "comp_tier": "moveup", "tier_override": "entry"})
    assert r["flags"]["under_improving_vs_comps"] is True
    print("ok: comp guard fires when target tier trails comp tier")


def test_cost_multiplier_scales_psf():
    base = run({"arv": 250000, "sqft": 1600, "comp_tier": "mid"})
    hi = run({"arv": 250000, "sqft": 1600, "comp_tier": "mid", "cost_multiplier": 1.5})
    assert hi["finish_psf_range"][0] > base["finish_psf_range"][0]
    assert approx(hi["finish_psf_range"][1], base["finish_psf_range"][1] * 1.5)
    print("ok: cost multiplier scales the $/sf benchmark")


def test_invalid_tier_errors():
    out = subprocess.run([sys.executable, FS, json.dumps(
        {"arv": 250000, "sqft": 1600, "comp_tier": "platinum"})],
        capture_output=True, text=True)
    assert out.returncode != 0
    print("ok: invalid tier name errors out")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print(f"\nAll {len(fns)} tests passed.")
