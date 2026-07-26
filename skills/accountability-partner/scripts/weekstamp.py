#!/usr/bin/env python3
"""
Accountability week stamps + commitment scorecard.

Two jobs, both deterministic, both things a language model gets wrong by hand:

  1. ISO week arithmetic. "What week is this?" and "what week was last week?"
     are calendar questions with exact answers (ISO-8601: weeks start Monday,
     week 1 contains the first Thursday of the year). Never eyeball them.

  2. The scorecard. Completion rate, trend against prior weeks, and the
     repeat-carry flags that drive the session's pattern callout.

Usage:
    python weekstamp.py                          # stamps for today
    python weekstamp.py --date 2026-07-26        # stamps for a given date
    python weekstamp.py --score '<json-input>'   # scorecard (+ stamps)
    echo '<json>' | python weekstamp.py --score

Score input:
{
  "date": "2026-07-26",            # optional; defaults to today
  "commitments": [
    {"text": "Send 40 letters", "status": "done",    "carried": 0},
    {"text": "Call 5 sellers",  "status": "partial", "carried": 1},
    {"text": "622 marketing",   "status": "missed",  "carried": 2},
    {"text": "Rewrite the SOP", "status": "dropped", "carried": 3}
  ],
  "history": [0.60, 0.80]          # optional, oldest → newest prior rates (0–1)
}

status ∈ done | partial | missed | dropped. Dropped commitments leave the
ledger: they are excluded from the denominator, by design — abandoning
something deliberately is a decision, not a failure, and scoring it as a miss
punishes the one behavior that keeps the ledger honest.

Rate = (done + 0.5 × partial) / (done + partial + missed).
A week with nothing scoreable returns rate: null, not 0.
"""

import json
import sys
from datetime import date, timedelta

CALC_VERSION = "accountability-partner-1.0.0"

SCOREABLE = ("done", "partial", "missed")
VALID_STATUS = SCOREABLE + ("dropped",)
WEIGHTS = {"done": 1.0, "partial": 0.5, "missed": 0.0}

# A commitment at or above this carry count is an unmade decision, not a
# scheduling problem. See references/coaching.md — "the repeat carry".
REPEAT_CARRY_THRESHOLD = 2


def _parse_date(value):
    if not value:
        return date.today()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip())


def stamp(day):
    """ISO stamp block for the week containing `day`."""
    iso_year, iso_week, iso_weekday = day.isocalendar()
    monday = day - timedelta(days=iso_weekday - 1)
    return {
        "stamp": f"{iso_year}-W{iso_week:02d}",
        "week_start": monday.isoformat(),
        "week_end": (monday + timedelta(days=6)).isoformat(),
    }


def stamps(day):
    """Current, prior and next week stamps relative to `day`."""
    return {
        "date": day.isoformat(),
        "current_week": stamp(day),
        "prior_week": stamp(day - timedelta(days=7)),
        "next_week": stamp(day + timedelta(days=7)),
    }


def _trend(rate, history):
    """Compare this week's rate to the most recent prior rate."""
    prior = [h for h in (history or []) if h is not None]
    if rate is None or not prior:
        return {"direction": None, "prior_rate": None, "delta": None,
                "clause": None, "sustained_low": False}

    last = float(prior[-1])
    delta = rate - last
    if abs(delta) < 0.005:
        direction, clause = "flat", "flat"
    elif delta > 0:
        direction, clause = "up", f"up from {round(last * 100)}%"
    else:
        direction, clause = "down", f"down from {round(last * 100)}%"

    # Three straight weeks under half means the list is too long, not the
    # operator too lazy. Only claim it with two priors plus this week.
    recent = prior[-2:] + [rate]
    sustained_low = len(recent) == 3 and all(r < 0.5 for r in recent)

    return {"direction": direction, "prior_rate": round(last, 4),
            "delta": round(delta, 4), "clause": clause,
            "sustained_low": sustained_low}


def score(payload):
    day = _parse_date(payload.get("date"))
    raw = payload.get("commitments") or []

    commitments = []
    errors = []
    for i, item in enumerate(raw):
        status = str(item.get("status", "")).strip().lower()
        if status not in VALID_STATUS:
            errors.append(f"commitments[{i}]: bad status {item.get('status')!r} "
                          f"(expected one of {', '.join(VALID_STATUS)})")
            continue
        try:
            carried = int(item.get("carried") or 0)
        except (TypeError, ValueError):
            errors.append(f"commitments[{i}]: carried must be an integer")
            carried = 0
        commitments.append({"text": item.get("text", ""), "status": status,
                            "carried": max(0, carried)})

    if errors:
        return {"calc_version": CALC_VERSION, "errors": errors}

    counts = {s: sum(1 for c in commitments if c["status"] == s) for s in VALID_STATUS}
    scoreable = [c for c in commitments if c["status"] in SCOREABLE]
    earned = sum(WEIGHTS[c["status"]] for c in scoreable)
    rate = (earned / len(scoreable)) if scoreable else None

    # Carry counts on the block describe weeks already slipped. A commitment
    # that just slipped again rolls forward at carried + 1.
    repeat_carries = [
        {"text": c["text"], "carried": c["carried"], "next_carry": c["carried"] + 1}
        for c in commitments
        if c["status"] in ("partial", "missed") and c["carried"] >= REPEAT_CARRY_THRESHOLD
    ]
    rollover = [
        {"text": c["text"], "status": c["status"], "next_carry": c["carried"] + 1}
        for c in commitments if c["status"] in ("partial", "missed")
    ]

    trend = _trend(rate, payload.get("history"))

    return {
        "calc_version": CALC_VERSION,
        "stamps": stamps(day),
        "counts": counts,
        "scored": len(scoreable),
        "earned": round(earned, 2),
        "rate": round(rate, 4) if rate is not None else None,
        "rate_pct": round(rate * 100) if rate is not None else None,
        "headline": (f"{counts['done']}/{len(scoreable)} landed "
                     f"({round(rate * 100)}%)") if rate is not None
                    else "nothing scoreable this week",
        "trend": trend,
        "rollover": rollover,
        "repeat_carries": repeat_carries,
        "flags": {
            "no_scoreable_commitments": rate is None,
            "over_committed": len(scoreable) > 5,
            "sustained_low": trend["sustained_low"],
            "has_repeat_carry": bool(repeat_carries),
            "clean_sweep": rate == 1.0 if rate is not None else False,
        },
    }


def main():
    args = sys.argv[1:]

    if "--score" in args:
        i = args.index("--score")
        raw = args[i + 1] if len(args) > i + 1 else sys.stdin.read()
        print(json.dumps(score(json.loads(raw)), indent=2))
        return

    day = None
    if "--date" in args:
        i = args.index("--date")
        day = args[i + 1] if len(args) > i + 1 else None

    out = stamps(_parse_date(day))
    out["calc_version"] = CALC_VERSION
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
