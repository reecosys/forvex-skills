# Guardrails

## Human-in-the-loop (default)

Mirror `forvex-underwriting`:

1. Draft a 3–5 line preview (intent, property link, content snippet).
2. Wait for explicit save confirmation.
3. Write → `readvise_get_today_summary` → quote id back.

Opt-out: `quick:` prefix or "just save it".

## Property linkage rules

| Intent | Property rule |
|--------|---------------|
| Note | **Required.** Refuse write without resolved `property_id`. Offer `forvex_list_deals` or `readvise_resolve_property` picks. |
| Task | Optional. Warn when saved without link (`warning` in tool response). |
| Pulse | Optional. Warn when user mentioned a property that did not resolve. |
| Advisor action | Optional property identifiers. |

## Pulse semantics

- `readvise_append_pulse_today` → `entry_type='pulse'`, one row per user per day, append mode.
- `readvise_create_advisor_action` → `entry_type='action'`, always new row, requires `advisor_tag`.

Do not merge advisor actions into the daily pulse row.

## Out of scope

- No debrief enqueue tool in this skill.
- Do not change deal pipeline status — use `forvex_update_deal_disposition` from underwriting skills instead.
- Do not use `forvex_log_activity` for structured capture intents — use the `readvise_*` tools above.

## MCP failures

If auth fails, tell the user to reconnect MCP at Claude → Settings → Connectors. Do not invent saved rows.
