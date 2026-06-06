# Readvise capture — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

All tools use the standard recontrol envelope: success → `structuredContent`; errors → `isError: true`.

## readvise_resolve_property

**Read.** Disambiguate property mentions.

| Input | Type | Required |
|-------|------|----------|
| `query` | string | yes |
| `workspace_id` | uuid | no |

**Output:** `{ matches: [{ id, address, name }], count }`

## readvise_create_property_note

**Write.** AI-sourced property note.

| Input | Type | Required |
|-------|------|----------|
| `property_id` | uuid | yes |
| `body` | string | yes |
| `workspace_id` | uuid | no |

**Output:** `{ note_id, property_id, created_at }`

## readvise_create_task

**Write.** Pending task (`status=pending`, `source=ai`).

| Input | Type | Required |
|-------|------|----------|
| `label` | string | yes |
| `description` | string | no |
| `property_id` | uuid | no |
| `unresolved_property_identifier` | string | no — surfaces warning when property did not resolve |
| `workspace_id` | uuid | no |

**Output:** `{ task_id, label, property_id, warning? }`

## readvise_append_pulse_today

**Write.** One `entry_type='pulse'` row per user per day; second call appends into `edited_content`.

| Input | Type | Required |
|-------|------|----------|
| `content` | string | yes |
| `tags` | string[] | no |
| `property_identifiers` | string[] | no |
| `workspace_id` | uuid | no |

**Output:** `{ pulse_id, mode: 'inserted' | 'appended' }`

## readvise_create_advisor_action

**Write.** Discrete `entry_type='action'` row (never edits existing pulse).

| Input | Type | Required |
|-------|------|----------|
| `content` | string | yes |
| `advisor_tag` | string | yes |
| `tags` | string[] | no |
| `property_identifiers` | string[] | no |
| `coordinator_meta` | object | no |
| `workspace_id` | uuid | no |

**Output:** `{ pulse_id, advisor_tag }`

## readvise_get_today_summary

**Read.** Post-write verifier.

| Input | Type | Required |
|-------|------|----------|
| `workspace_id` | uuid | no |

**Output:** `{ pulse, actions[], open_tasks[], recent_notes[] }`
