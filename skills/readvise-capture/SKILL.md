---
name: readvise-capture
description: Capture notes, tasks, daily pulse, and advisor-lane actions into Readvise via MCP. Use when the user says "note that", "add a task", "pulse:", "today I", "recap", "for the business", "advisor lane:", "debrief this", or prefixes with "quick:".
---

# Readvise Capture

You capture franchisee intent into Readvise through the recontrol MCP server. You classify phrasing, resolve properties when needed, preview the payload, wait for explicit confirmation (unless opted out), write via MCP, then read back with `readvise_get_today_summary`.

## When to invoke

- Property notes: "note that…", "add a note…", "log on [property]…"
- Tasks: "add a task…", "remind me to…", "todo…"
- Daily pulse: "pulse:", "today I…", "recap my day", "log today"
- Advisor lane: "for the business…", "advisor lane:", "strategic note:", "debrief this:"
- Quick capture: user prefixes with `quick:` or says "just save it"

## Workflow

1. **Classify intent** using `references/intent-classification.md`.
2. **Resolve property** when the intent links to one:
   - Call `readvise_resolve_property({ query })`.
   - 0 matches + note intent → ask user to pick from `forvex_list_deals` or abort.
   - 0 matches + task/pulse → proceed unlinked; warn.
   - N>1 matches → ask user to pick one.
3. **Draft payload** and show a 3–5 line preview (tool, property link, body/label).
4. **Confirm** — wait for "save" / "yes" / "do it" unless `quick:` prefix or "just save it".
5. **Write** via the mapped tool, then **verify** with `readvise_get_today_summary` and quote the new row id.

## MCP tools

See `references/data-sources.md` for inputs, outputs, and envelopes.

| Intent | Tool |
|--------|------|
| Property note | `readvise_create_property_note` |
| Task | `readvise_create_task` |
| Daily pulse | `readvise_append_pulse_today` |
| Advisor action | `readvise_create_advisor_action` |
| Read-back | `readvise_get_today_summary` |
| Property lookup | `readvise_resolve_property` |

## Guardrails

- Notes **require** a resolved `property_id`.
- Tasks and pulse may save without a property link; surface the warning when unlinked.
- Advisor actions **require** `advisor_tag` — infer from phrasing (`business`, `negotiation`, `coordinator`, `franchise`).
- Never enqueue debrief enrichment from this skill (out of scope).

See `references/guardrails.md`, `references/voice-shortcuts.md`.
