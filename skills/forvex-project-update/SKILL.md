---
name: forvex-project-update
description: Log a progress note on an active REbuild rehab project — "drywall finished on Maple", "plumbing rough-in done at Stevenson", "crew didn't show today on Kim Dr", "permits pulled for Cool Brook", "inspection passed on Dresden". Use for project-execution updates (milestones, blockers, crew status, inspections) that go on the timeline but do NOT change dollars or scope. For scope/dollar changes use forvex-change-order. For pipeline status moves (REHAB → LISTED) use forvex-deal-disposition.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# forVEX Project Update

You capture rehab-execution progress notes against the project timeline. Same write discipline as `forvex-activity-log` — echo, confirm, write, verify — but scoped to active rehabs and tagged for project-execution context.

## When to invoke

- "Drywall done at Maple"
- "Plumbing rough-in passed inspection on Stevenson"
- "Crew didn't show today on Kim Dr"
- "Permits pulled for Cool Brook"
- "Found knob-and-tube on Dresden" *(if just noting — for actual scope/dollar change hand to change-order)*
- "Tile delivery delayed two weeks"
- "Walked the property with the GC today"

**Not for**:
- Scope or dollar changes → `forvex-change-order`
- Pipeline status moves (REHAB → LISTED, etc.) → `forvex-deal-disposition`
- New estimates → `forvex-rehab-estimator`
- Lead-side touches → `forvex-activity-log`

## Canonical authority

| Concern | Tool |
|---|---|
| Resolve property → deal/project | `forvex_resolve_property` + `forvex_list_deals` |
| Open project (idempotent) | `forvex_open_or_create_project` |
| Persist update | `forvex_log_activity` (with `activity_type: "project_update"`) |
| Verify | `forvex_get_deal_history` |

Project updates land on the same timeline as deal activity. The `activity_type` tag is what distinguishes them in the in-app view.

## Workflow

### 1. Resolve

Follow `references/platform/resolve-context.md`. Confirm `{ deal_id, property_id, address, status }`.

If the deal status is **not** `UNDER_CONTRACT | INVENTORY | REHAB | LISTED`, ask: *"This deal is in {STATUS} — are you sure you want a project update, or did you mean an activity log?"* (LEAD-stage walkthroughs are activity-log territory; rehab execution is project-update territory.)

Confirm `project_id` via `forvex_open_or_create_project({ core_deal_id })`. Cache.

### 2. Extract update facts

From the user's message, identify:

- **`notes`** — verbatim, lightly cleaned
- **`activity_type`** — pick from the project-update taxonomy below
- **`outcome`** — pick if clearly implied; untagged is fine

#### Project-update activity_type tags

| Tag | When |
|---|---|
| `milestone` | A scope phase completed (demo, framing, drywall, paint, etc.) |
| `inspection` | Inspector / appraiser / GC walk visit |
| `permit` | Permit pulled, issued, or denied |
| `delivery` | Materials arrived / delayed / wrong |
| `crew` | Crew showed / no-show / change |
| `blocker` | Something stopped work (weather, supply, dispute) |
| `walkthrough` | Owner / GC / agent property walk |
| `observation` | Found something on-site (note only — for actual scope change use change-order) |
| `photo` | Captured progress photos (referenced in notes) |
| `note` | Catch-all for project-execution context |

#### Outcomes

`complete`, `partial`, `failed`, `delayed`, `passed`, `denied`, `info_gathered`, `escalation_needed`. Untagged is fine.

### 3. Echo-back gate (required)

```
Logging project update on {address} ({DEAL_STATUS}, project `{project_id_short}`):

> {notes}

Tags: {activity_type} / {outcome or "—"}. Confirm?
```

Wait for explicit yes. **No silent writes.**

### 4. Write

Call `forvex_log_activity` with:

- `deal_id`
- `notes` (verbatim from echo)
- `activity_type` (from project taxonomy above)
- `outcome` if tagged
- `workspace_id` only when multiple

### 5. Verify

Call `forvex_get_deal_history({ deal_id })`. Confirm the new note is the latest entry. Report:

> *"✅ Logged on {address} at {ts}. Anything else on the project?"*

### 6. Scope-creep handoff

If the user's update implies a scope change ("found knob-and-tube, need to add full rewire"), capture the **observation** here, then explicitly offer:

> *"That sounds like a scope change — want me to draft a change order to add the rewire to the estimate?"* → `forvex-change-order`

Do NOT bundle the change-order write into this confirmation. Each skill owns its own echo-back.

## Batched updates

If the user dumps several updates in one message ("demo done, drywall in progress, tile delivery delayed"), resolve once, then echo all updates as a single confirmation list before writing each. One verify call at the end.

## Guardrails

- **No dollar changes.** Updates never alter the estimate. If scope changes, hand to `forvex-change-order`.
- **No status moves.** Updates never alter pipeline status. If user says "we listed it" inside an update, capture the milestone AND flag the disposition move separately.
- **No editorializing.** Don't comment on whether the project is behind, over budget, or whether the crew is the issue. Capture and write.
- **No invented details.** Names, dates, quantities — only what the user said.
- **Same-timeline as activity.** Project updates use the same `log_activity` tool; the taxonomy distinguishes them.
- **MCP offline = stop.**

## References

- `references/platform/resolve-context.md` — address → deal/project resolution

## Related skills

- **forvex-project-status** — read-only project state
- **forvex-change-order** — when an observation triggers a scope/dollar change
- **forvex-deal-disposition** — pipeline status moves (REHAB → LISTED, etc.)
- **forvex-activity-log** — lead-side touches (LEAD / OFFER stages)
