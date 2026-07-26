#!/usr/bin/env python3
"""Regression tests for weekstamp.py. Run before changing scoring logic:
    python test_weekstamp.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(HERE, "weekstamp.py")


def run(*args, payload=None):
    argv = [sys.executable, WS, *args]
    if payload is not None:
        argv.append(json.dumps(payload))
    out = subprocess.run(argv, capture_output=True, text=True)
    if out.returncode != 0:
        raise AssertionError(f"script failed: {out.stderr}")
    return json.loads(out.stdout)


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


failures = []


def check(name, cond):
    if cond:
        print(f"  ✓ {name}")
    else:
        failures.append(name)
        print(f"  ✗ {name}")


# ---------------------------------------------------------------- stamps
print("ISO week stamps")

r = run("--date", "2026-07-26")   # a Sunday — last day of its ISO week
check("Sunday resolves to its own ISO week", r["current_week"]["stamp"] == "2026-W30")
check("week starts Monday", r["current_week"]["week_start"] == "2026-07-20")
check("week ends Sunday", r["current_week"]["week_end"] == "2026-07-26")
check("prior week is W29", r["prior_week"]["stamp"] == "2026-W29")
check("next week is W31", r["next_week"]["stamp"] == "2026-W31")

r = run("--date", "2026-07-20")   # the Monday of the same week
check("Monday lands in the same week as its Sunday", r["current_week"]["stamp"] == "2026-W30")

# Year boundaries are where hand-computed week numbers go wrong.
r = run("--date", "2027-01-01")   # a Friday — ISO week 53 of 2026
check("Jan 1 2027 is 2026-W53 (ISO year rollback)", r["current_week"]["stamp"] == "2026-W53")
r = run("--date", "2026-01-01")   # a Thursday — ISO week 1 of 2026
check("Jan 1 2026 is 2026-W01", r["current_week"]["stamp"] == "2026-W01")
r = run("--date", "2025-12-29")   # Monday starting ISO week 1 of 2026
check("Dec 29 2025 is 2026-W01", r["current_week"]["stamp"] == "2026-W01")
check("week stamp is zero-padded", run("--date", "2026-02-03")["current_week"]["stamp"]
      == "2026-W06")

# ---------------------------------------------------------------- scoring
print("\nScorecard")

BASE = {
    "date": "2026-07-26",
    "commitments": [
        {"text": "Send 40 letters", "status": "done"},
        {"text": "Call 5 sellers", "status": "partial", "carried": 1},
        {"text": "622 marketing", "status": "missed", "carried": 2},
        {"text": "Rewrite the SOP", "status": "dropped", "carried": 3},
    ],
}

r = run("--score", payload=BASE)
check("dropped excluded from denominator", r["scored"] == 3)
check("earned = 1 done + 0.5 partial", approx(r["earned"], 1.5))
check("rate = 1.5 / 3", approx(r["rate"], 0.5))
check("rate_pct rounds to 50", r["rate_pct"] == 50)
check("headline counts done only", r["headline"] == "1/3 landed (50%)")
check("counts by status", r["counts"] == {"done": 1, "partial": 1, "missed": 1, "dropped": 1})
check("stamps included in score output", r["stamps"]["current_week"]["stamp"] == "2026-W30")

check("rollover covers partial + missed", len(r["rollover"]) == 2)
check("rollover increments carry", sorted(x["next_carry"] for x in r["rollover"]) == [2, 3])
check("repeat carry flagged at threshold", [x["text"] for x in r["repeat_carries"]]
      == ["622 marketing"])
check("has_repeat_carry flag", r["flags"]["has_repeat_carry"] is True)

# Dropped items never surface as carries, however many weeks they ran.
check("dropped never rolls over", all("SOP" not in x["text"] for x in r["rollover"]))

# Empty / all-dropped weeks must not report 0% — that reads as total failure.
r = run("--score", payload={"date": "2026-07-26", "commitments": [
    {"text": "x", "status": "dropped"}]})
check("all-dropped week has null rate", r["rate"] is None)
check("no_scoreable_commitments flag", r["flags"]["no_scoreable_commitments"] is True)
check("headline degrades gracefully", "nothing scoreable" in r["headline"])

r = run("--score", payload={"date": "2026-07-26", "commitments": []})
check("empty week has null rate", r["rate"] is None)

# Clean sweep.
r = run("--score", payload={"date": "2026-07-26", "commitments": [
    {"text": "a", "status": "done"}, {"text": "b", "status": "done"}]})
check("clean sweep rate 1.0", approx(r["rate"], 1.0))
check("clean_sweep flag", r["flags"]["clean_sweep"] is True)

# Over-commitment: >5 scoreable items.
r = run("--score", payload={"date": "2026-07-26", "commitments": [
    {"text": f"c{i}", "status": "done"} for i in range(6)]})
check("over_committed flag at 6", r["flags"]["over_committed"] is True)

# ---------------------------------------------------------------- trend
print("\nTrend")

r = run("--score", payload={**BASE, "history": [0.6, 0.4]})
check("trend up vs most recent prior", r["trend"]["direction"] == "up")
check("trend clause reads from prior", r["trend"]["clause"] == "up from 40%")
check("trend delta", approx(r["trend"]["delta"], 0.1))

r = run("--score", payload={**BASE, "history": [0.4, 0.8]})
check("trend down", r["trend"]["direction"] == "down")

r = run("--score", payload={**BASE, "history": [0.9, 0.5]})
check("trend flat within tolerance", r["trend"]["direction"] == "flat")

r = run("--score", payload={**BASE, "history": []})
check("no history → no trend", r["trend"]["direction"] is None)
check("no history → no sustained_low", r["trend"]["sustained_low"] is False)

# Sustained low needs two priors plus this week, all under 50%.
r = run("--score", payload={**BASE, "history": [0.4, 0.3]})
check("sustained_low needs this week under .5", r["flags"]["sustained_low"] is False)  # .50 not < .50
r = run("--score", payload={"date": "2026-07-26", "history": [0.4, 0.3], "commitments": [
    {"text": "a", "status": "missed"}, {"text": "b", "status": "done"},
    {"text": "c", "status": "missed"}]})
check("sustained_low over three sub-half weeks", r["flags"]["sustained_low"] is True)
r = run("--score", payload={"date": "2026-07-26", "history": [0.3], "commitments": [
    {"text": "a", "status": "missed"}]})
check("sustained_low not claimed on one prior", r["flags"]["sustained_low"] is False)

# ---------------------------------------------------------------- validation
print("\nValidation")

r = run("--score", payload={"commitments": [{"text": "a", "status": "kinda"}]})
check("bad status is an error, not a guess", "errors" in r)
check("error names the field", "commitments[0]" in r["errors"][0])

r = run("--score", payload={"commitments": [{"text": "a", "status": "DONE"}]})
check("status is case-insensitive", approx(r["rate"], 1.0))

r = run("--score", payload={"commitments": [{"text": "a", "status": "missed", "carried": -3}]})
check("negative carry clamps to 0", r["rollover"][0]["next_carry"] == 1)

check("calc_version emitted", "calc_version" in run("--date", "2026-07-26"))

# ----------------------------------------------------------------
print()
if failures:
    print(f"FAILED ({len(failures)}): " + ", ".join(failures))
    sys.exit(1)
print("All tests passed.")
