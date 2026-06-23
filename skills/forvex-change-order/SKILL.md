---
name: forvex-change-order
description: Update an existing REbuild rehab estimate when scope changes — "found knob-and-tube, add full rewire on Maple", "bump Systems to Heavy on Stevenson", "add a mini-split to the Cool Brook scope", "tile pricing came back $4k over, adjust the bath line", "remove the deck from the scope". Re-runs the engine, presents the delta, and on confirm saves the update. Refuses to touch locked estimates. For NEW estimates use forvex-rehab-estimator. For progress notes (no scope change) use forvex-project-update.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# forVEX Change Order

You apply a scope delta to a saved estimate. The franchisee has already approved a baseline; you only need sign-off on the **change**. Re-preview, show the delta, confirm, save, verify.

## When to invoke

- "Found knob-and-tube, add full rewire on Maple"
- "Bump Systems to Heavy on Stevenson"
- "Add a mini-split for the Cool Brook addition"
- "Remove the deck from the scope on Kim Dr"
- "Tile came in $4k over budget, adjust the bath line"
- "Foundation crack worse than I thought — change to Heavy"

**Not for**:
- New estimates → `forvex-rehab-estimator`
- Progress notes without scope change → `forvex-project-update`
- "What's the current estimate?" → `forvex-project-status`
- Pipeline status moves → `forvex-deal-disposition`

## Canonical authority

| Concern | Tool |
|---|---|
| Resolve property → deal/project | `forvex_resolve_property` + `forvex_list_deals` |
| Open project (idempotent) | `forvex_open_or_create_project` |
| Load saved estimate | `forvex_get_estimate` |
| Re-run engine on delta | `forvex_preview_estimate` |
| SKU lookup for bottom-up adds | `forvex_map_observations_to_skus` |
| Persist delta | `forvex_update_estimate` |
| Verify | `forvex_get_estimate` (after save) |

**Engine is authoritative for dollars** — same rule as `forvex-rehab-estimator`. Never recompute totals in prose.

If MCP is offline, announce and stop.

## Workflow

### 1. Resolve and load baseline

- Follow `references/platform/resolve-context.md` to confirm `{ deal_id, project_id, address }`.
- Call `forvex_open_or_create_project({ core_deal_id })` for `project_id`.
- Call `forvex_get_estimate({ project_id })`.

If no estimate exists: *"No estimate saved yet on this project — let's draft one instead."* → hand to `forvex-rehab-estimator`.

### 2. Lock check (hard stop)

If `estimate.status_locked === true`:

> *"This estimate is locked (finalized in REbuild). I can't update it from chat. Open the project in REbuild to make the change."*

Stop. Do not preview. Do not propose workarounds.

### 3. Identify the delta

From the user's words, determine which kind of change (see `references/scope-deltas.md`):

- **Category severity shift** — e.g. Systems Medium → Heavy
- **Bottom-up add** — new SKU + quantity
- **Bottom-up remove** — drop a SKU
- **Quantity / allowance adjustment** — change qty or mark a line as allowance

Preserve original `mode`, `profile_id`, `price_book_id` unless the user explicitly asks to change them.

For bottom-up adds, call `forvex_map_observations_to_skus({ text: "<user's words>" })` to find the right SKU. If multiple candidates, ask which.

**Never invent** quantities. If the user says "add a mini-split" without size, ask: "What capacity? 9k / 12k / 18k BTU?"

### 4. Re-preview

Call `forvex_preview_estimate` with the modified inputs:

- `project`: same sqft/beds/baths/year_built/contingency as baseline
- `category_conditions`: baseline + the shift (for category-shift deltas)
- `user_overrides`: baseline overrides + the add/remove (for bottom-up deltas)
- `mode`: same as baseline
- `profile_id` / `price_book_id`: same as baseline

### 5. Echo-back as a delta (required)

Use the shape in `references/scope-deltas.md`. Lead with what changed and the dollar delta — not a full estimate dump. Show line-item diffs (added / removed / changed) only for the affected lines.

```
Change order on {address} (estimate `{estimate_id_short}`):
  Change: {what}
  Previous total: ${old}
  New total:      ${new}
  Delta:          {±$X} ({±%})
  Lines affected: + ... / - ... / ~ ...
  Variance after change: {ok or ⚠️ flagged}

Save this update?
```

Wait for explicit yes. If the user adjusts, re-preview and re-echo.

### 6. Save and verify

Call `forvex_update_estimate` with:

- `estimate_id`
- `engine_output` (the full output from the **last preview**, not synthesized)
- `profile_id`, `price_book_id` (preserved)
- `source: "forvex-change-order"`
- `idempotency_key` (UUID) if retrying after a network error

Then `forvex_get_estimate({ estimate_id })` and confirm:

- `summary.grand_total_cost` matches the previewed new total
- Line item count matches expected
- Status is still `draft` / `derived` (not locked, not advanced)

Report:

> *"✅ Change order saved on {address}. New total ${new_total}, was ${old_total} ({±$X}). Estimate `{estimate_id_short}` — still in draft."*

If verification fails, flag the failure — don't claim success.

### 7. Suggest natural follow-ups (lightly)

- If the delta is large (>15% swing): *"That's a meaningful change — want me to re-run underwriting against the new rehab?"* → hand to `forvex-underwriting`.
- If the change came from an on-site observation: *"Want me to also log this as a project update for the timeline?"* → hand to `forvex-project-update`.

One line each, no auto-runs.

## Multiple deltas in one message

If the user packs multiple changes in one go ("Systems to Heavy, add a mini-split, remove the deck"), apply all of them in **one preview** and echo as a single combined delta. Don't write one estimate update per change — that produces a noisy history and inflates idempotency complexity.

## Guardrails

- **Engine is authoritative.** Never recompute. Never round. The save call uses the previewed `engine_output` verbatim.
- **Locked estimates are off-limits.** Hard stop, no preview, no workaround.
- **Preserve baseline context.** Same mode, same profile, same pricebook unless explicitly changed.
- **No editorializing.** Don't comment on whether the change is a good idea, whether the project is over budget, or whether they should walk. Surface the delta; the user decides.
- **No new estimates from this skill.** If the change is really "let's start over," hand to `forvex-rehab-estimator`.
- **Idempotency keys** on retry only — fresh UUID per save attempt after a failed network call.
- **MCP offline = stop.**

## References

- `references/platform/resolve-context.md` — address → deal/project resolution
- `references/scope-deltas.md` — delta patterns, echo-back shape, lock-check, allowances

## Related skills

- **forvex-rehab-estimator** — new estimates from scratch
- **forvex-project-status** — read-only state check before a change
- **forvex-project-update** — capture an on-site observation that doesn't change scope
- **forvex-underwriting** — re-run deal economics after a large delta
