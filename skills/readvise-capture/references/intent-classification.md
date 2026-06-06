# Intent classification

Map user phrasing to tool + required fields.

| Cue | Tool | Property required? | advisor_tag |
|-----|------|-------------------|-------------|
| "note that", "add a note", "log on [property]" | `readvise_create_property_note` | **Yes** | — |
| "add a task", "remind me to", "todo", "follow up to" | `readvise_create_task` | No (warn if unlinked) | — |
| "pulse:", "today I", "recap my day", "log today", "end of day" | `readvise_append_pulse_today` | No (warn if unlinked) | — |
| "for the business", "advisor lane:", "strategic note:", "debrief this:" | `readvise_create_advisor_action` | No | **Yes** |

## advisor_tag inference

| Phrasing | Tag |
|----------|-----|
| business, franchise ops, marketing, team | `business` |
| offer, counter, seller negotiation | `negotiation` |
| coordinator, inbound, lead routing | `coordinator` |
| franchise, HomeVestors corporate | `franchise` |

When ambiguous, ask one clarifying question before save.

## Property resolution flow

1. Extract address or property name from utterance.
2. `readvise_resolve_property({ query })`.
3. Apply guardrails from `guardrails.md` based on intent type.
