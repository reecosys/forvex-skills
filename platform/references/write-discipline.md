# Write Discipline — MCP Skills

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Shared rules for every forVEX skill that calls a write tool (`readOnlyHint: false`).

## Echo-back gate

Before any write:

1. Echo every field the user cares about (address, deal_id, status, amounts, notes).
2. Wait for explicit confirmation — **no silent writes**.
3. If the user adjusts anything, re-echo.

Exception: user prefixes with `quick:` or says "just save it" where the skill documents that opt-out.

## Verify by re-read

After every write, call the appropriate read tool and confirm the payload round-tripped:

| Write | Verify |
|---|---|
| `forvex_save_deal` | `forvex_get_deal` — diff `analysis_summary` |
| `forvex_update_deal_disposition` | `forvex_get_deal` or `forvex_get_deal_history` |
| `forvex_log_activity` | `forvex_get_deal_history` |
| `forvex_capture_deal_brief` | response `brief_id` + surface `data_bugs[]` |
| `forvex_record_deal_outcome` | response error % fields |
| `forvex_save_draft_estimate` | `forvex_get_estimate` |
| `readvise_*` writes | `readvise_get_today_summary` |

Only tell the user "saved" / "logged" / "moved" after verify succeeds.

## Idempotency

Write tools that accept `idempotency_key` (UUID) must get a **fresh UUID per intentional write**. Retries after MCP errors reuse the same payload with a **new** key.

## One skill, one write type per confirmation

Do not bundle disposition + activity + save under one confirmation. Each skill owns its echo-back. Hand off to the next skill when the user asks for the next action.

## MCP offline

If forVEX tools error or auth fails, announce MCP is down and **do not claim a write landed**. Retain the payload in-thread for retry when tools return.
