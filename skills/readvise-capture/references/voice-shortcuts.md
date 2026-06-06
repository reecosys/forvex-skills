# Voice shortcuts

## Quick save (skip preview confirm)

User may opt out of human-in-the-loop preview when they:

- Prefix the message with `quick:` — e.g. `quick: note that 123 Main seller is motivated`
- Say "just save it" or "save without preview" in the same turn

Still call `readvise_get_today_summary` after write and quote the new id.

## Explicit confirm phrases

Treat these as approval after a preview:

- "save", "yes", "do it", "go ahead", "confirm", "looks good"

## Link to property

When user says "link to X" or "on [address]":

1. Run `readvise_resolve_property` with X.
2. Pass resolved `property_id` to note/task tools, or `property_identifiers` to pulse/action tools.

## Read-back

After every write, call `readvise_get_today_summary` and tell the user:

- Note → `note_id` from recent_notes
- Task → `task_id`
- Pulse → `pulse_id` and `mode` (inserted vs appended)
- Advisor action → `pulse_id` + `advisor_tag`
