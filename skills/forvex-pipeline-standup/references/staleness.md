# Staleness Heuristics

A "stale" deal is one where pipeline state hasn't moved in long enough that it deserves attention. Defaults below — adjustable per user pref.

## Default thresholds (days since last activity OR last status change)

| Status | Stale after |
|---|---|
| LEAD | 7 days |
| OFFER | 5 days |
| UNDER_CONTRACT | 14 days (long pre-close timelines normal) |
| INVENTORY | 10 days (sitting without rehab kickoff) |
| REHAB | 30 days (rehab durations vary; flag only if no activity in 30) |
| LISTED | 14 days |
| PENDING | 21 days |

`SOLD` and `LOST` are terminal — not surfaced in standup unless asked.

## "Last activity" definition

Compute from `forvex_get_deal_history`:
- Most recent `lifecycle` event timestamp, OR
- Most recent `activity` note timestamp,
whichever is more recent.

If both are missing (newly imported lead with no touches), use `updated_at` from `list_deals`.

## Standup output shape

For each stale deal, emit one line:

```
{address} — {STATUS}, {N} days stale — last: {one-line excerpt of last activity or transition}
```

Group by status (LEAD section, OFFER section, etc.), sorted by staleness descending.

## What to suggest

After the list, offer **one** next action per deal — match the status:

- **LEAD** stale → "Drive-by or call this week?"
- **OFFER** stale → "Counter or walk away?"
- **UNDER_CONTRACT** stale → "Inspection / appraisal status?"
- **INVENTORY** stale → "Ready to kick off rehab?"
- **REHAB** stale → "Crew update?"
- **LISTED** stale → "Price drop or stay the course?"
- **PENDING** stale → "Closing date / hold-up?"

Keep it short. The user is using standup to triage, not to read essays.

## Pagination

`forvex_list_deals` returns 25 by default, max 100. For a standup, paginate to fetch up to 200 active deals (8 pages of 25, or 2 pages of 100). Don't go further — a workspace with >200 active deals needs a filtered view, not a firehose.

For each deal that crosses the staleness threshold, call `forvex_get_deal_history` to fetch the last-event detail. Cap deal-history calls at 25 per standup to keep the response fast — if more are stale, report the count and ask the user to narrow scope (by status or zip).

## What standup does NOT do

- **No writes.** Read-only. If the user wants to act on a stale deal, hand to `forvex-activity-log` or `forvex-deal-disposition`.
- **No buy-box judgments.** Don't say "this lead doesn't match your buy-box" — that's `forvex-underwriting`.
- **No editorializing prices.** Same rule as the other PM skills.
