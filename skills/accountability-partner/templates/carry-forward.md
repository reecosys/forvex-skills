# Carry-forward block template

Emit this in a **single fenced code block** so the user can copy it in one click. Omit any
section with nothing real in it — do not pad. Target under 40 lines.

```
<!-- ACCOUNTABILITY-CARRY-FORWARD v1 -->
# Accountability — {NEXT_WEEK_STAMP} (week of {NEXT_WEEK_START})

Closed {CLOSED_WEEK_STAMP}: {DONE}/{SCORED} · {RATE}%{TREND_CLAUSE}
Read: {MOOD} · momentum {MOMENTUM} · energy {ENERGY}/10

## Commitments for {NEXT_WEEK_STAMP}
- [ ] {COMMITMENT} — due {DAY}
- [ ] {COMMITMENT} — due {DAY} (carried {N}×)

## Last week ({CLOSED_WEEK_STAMP})
- done — {COMMITMENT}
- partial — {COMMITMENT} — {WHAT REMAINS}
- missed — {COMMITMENT} — {WHY, one clause}

## Wins
- {WIN, with a number}

## Blockers
- {BLOCKER, stated as a condition}

## Decisions
- {DECISION MADE THIS WEEK}

## Dropped this week
- {COMMITMENT} — {REASON}

## For next session
- {WHAT TO PRESS ON: the deferred decision, the third carry, the blocker talked around}
<!-- END ACCOUNTABILITY-CARRY-FORWARD -->
```

## Field notes

- `{NEXT_WEEK_STAMP}` / `{CLOSED_WEEK_STAMP}` — ISO stamps like `2026-W31`, from
  `scripts/weekstamp.py`. Never hand-compute the week number.
- `{TREND_CLAUSE}` — ` (up from 60%)` / ` (down from 80%)` / ` (flat)`, only when a prior rate is
  known. Omit on a first session.
- `Read:` line — include only the parts actually captured. Drop the whole line if none were.
- Carry markers — omit entirely at zero. `(carried 1×)` and up otherwise.
- On a first session, drop `Last week`, the score line, and `Dropped this week`; open the block
  with the commitments and write a `For next session` line that says it's the baseline week.
- On a recalled week (block was lost), write the score line as `Closed {STAMP}: not scored —
  recalled` rather than inventing a rate.
