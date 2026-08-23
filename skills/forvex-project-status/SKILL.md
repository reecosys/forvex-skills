---
name: forvex-project-status
description: Read-only status check on a REbuild rehab project — current estimate total, variance flags, line-item summary, last activity, and whether the estimate is locked. Use when the franchisee asks "where are we on [address]", "what's the rehab on Maple", "what's our estimate on Stevenson", "show me the project for Kim Dr", "are we over budget on anything", "any locked estimates", or wants to see project state without changing it. Does NOT write anything — for changes use forvex-project-update or forvex-change-order.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# forVEX Project Status

You give the franchisee a fast read on the rehab project for a specific property — or a fleet-view across all active REbuild projects. Read-only. No engine runs. No writes.

## When to invoke

- "Where are we on 113 Stevenson?"
- "What's the estimate on Maple?"
- "Show me the rehab project for Kim Dr"
- "Any projects over budget?"
- "Are any estimates locked?"
- "Status check on Cool Brook"

**Not for** scope changes (→ `forvex-change-order`), progress logs (→ `forvex-project-update`), or new estimates (→ `forvex-rehab-estimator`).

## Canonical authority

| Concern | Tool |
|---|---|
| Resolve property → deal/project | `forvex_resolve_property` + `forvex_list_deals` (see `references/platform/resolve-context.md`) |
| Project row + estimate id | `forvex_open_or_create_project` (idempotent — safe for read) |
| Estimate detail (totals, line items, status) | `forvex_get_estimate` |
| Project history (notes, transitions) | `forvex_get_deal_history` |
| Active projects fleet view | `forvex_list_deals({ status: "REHAB" })` and `{ status: "INVENTORY" })` |

If MCP is offline, announce and stop.

## Workflow — single-property read

### 1. Resolve

Follow `references/platform/resolve-context.md`. Confirm `{ deal_id, property_id, address, status }`.

If `status` is not in `{ UNDER_CONTRACT, INVENTORY, REHAB, LISTED }`, say so — there may not be an active rehab project yet. Offer to open one via `forvex-rehab-estimator`.

### 2. Load project + estimate

Call `forvex_open_or_create_project({ core_deal_id })` to get the `project.id` (idempotent — won't duplicate). Then `forvex_get_estimate({ project_id })`.

If no estimate exists yet, say: *"Project is open but no estimate saved yet. Want to draft one?"* → hand to `forvex-rehab-estimator`.

### 3. Present

One screen, three blocks. Pull every dollar figure straight from `get_estimate` — **never recompute**.

```
{address} — {DEAL_STATUS}, deal `{deal_id_short}`, project `{project_id_short}`

Estimate (status: {estimate.status}, mode: {estimate.mode})
  Total: ${total_rehab}
  Sqft band: {low}–{mid}–{high}
  Variance: {flagged? "⚠️ flagged" : "ok"} ({variance_pct}%)
  Last updated: {ts}

Categories (non-None severities)
  Kitchen: Heavy
  Bath: Medium
  Systems: Light
  …

Recent (last 3 activity / lifecycle events)
  • 2026-06-04 — drive_by — "fence is down"
  • 2026-05-28 — lifecycle UNDER_CONTRACT → INVENTORY
  …
```

If `estimate.status_locked` is true, surface it prominently: *"⚠️ Estimate is locked — finalized in REbuild. Read-only from chat."*

### 4. Offer next steps (lightly)

End with one line:

> *"Want to log a project update, draft a change order, or see line-item detail?"*

Do not auto-call. Wait.

## Workflow — fleet view ("any projects over budget?", "all active rehabs")

1. `forvex_list_deals({ status: "REHAB" })` and `{ status: "INVENTORY" })` in parallel.
2. For each (cap at 25), call `forvex_get_estimate({ project_id })` after resolving project via `open_or_create_project`. Cap at 25 to stay fast — if more, ask to narrow.
3. Group by:
   - **Variance-flagged** (variance.flagged === true) — surface first
   - **Locked** — second
   - **Healthy active** — third (one-liners only)
4. One line per project; offer drill-in.

## Line-item drill-in

If the user asks "show me the line items" or "what's the breakdown":

- Display `lineItems[]` from `get_estimate` grouped by category.
- For each: `{name} — {qty} × ${unit} = ${total}` plus `{allowance? "(allowance)" : ""}`.
- Quote `engine_output.summary.grand_total_cost` as the total, not a recomputation.

## Guardrails

- **Read-only.** No writes ever. No engine previews (those mutate nothing but cost MCP calls and produce numbers the user might mistake for saved state).
- **Never recompute totals.** Every dollar figure comes from `forvex_get_estimate`. If the user asks "what if we add X?", hand to `forvex-change-order`.
- **No editorializing.** Don't comment on whether the rehab is too high, too low, or whether they should adjust scope. Surface the numbers; let the user decide.
- **Locked estimates are clearly flagged.** Once locked, chat cannot modify — direct user to REbuild app.
- **Cap fleet calls** at 25 estimates loaded per fleet view.
- **MCP offline = stop.**

## References

- `references/platform/resolve-context.md` — address → deal/project resolution (shared)

## Rendering it as an artifact

When the franchisee wants the estimate as something to look at rather than read
in chat — "render the rehab scope", "show me the estimate breakdown", "does this
estimate match what we saw?" — route to **`forvex-presentation` Mode 6 — Rehab
scope**. It renders the categories, the line items with SKUs, the operator-lane
vs fallback scopes, and reconciles the estimate against the walkthrough.

**This is not a way around the no-editorializing rule above.** Mode 6 may flag
that a line looks unnecessary *only* by citing a stated observation from the
visit ("the family said both AC units were replaced"). It may never argue a line
is priced wrong — unit costs and the engine total stay the engine's authority,
here and there.

## Related skills

- **forvex-presentation** (Mode 6) — render the estimate as a scope artifact
- **forvex-rehab-estimator** — draft a new estimate or substantially revise one
- **forvex-change-order** — delta updates (add a line, change a severity)
- **forvex-project-update** — log progress notes on the project timeline
- **forvex-pipeline-standup** — pipeline-wide view (not project-specific)
