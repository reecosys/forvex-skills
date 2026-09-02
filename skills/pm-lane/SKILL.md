---
name: pm-lane
description: Property-ops Cowork lane. Run a weekly portfolio reconcile or PM review, then emit a workspace event so Readvise sees that the review happened. Optionally emit per-property follow-ups. Use for CRG weekly PM reconcile, portfolio ops, occupancy/maintenance triage. Requires the forVEX Control MCP connector.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time) · MCP data: `references/data-sources.md`

# PM Lane

You work property operations and **emit** when a review or reconcile finishes. Readvise reasons
over the ledger; do not dump the review transcript into pulse.

## Emission is definition-of-done

After a weekly PM reconcile / portfolio review, emit then stop. Scheduled runs must not finish
silent.

## Workspace rollup (always)

```
forvex_emit_event({
  lane: "pm",
  verb: "portfolio_reconciled",
  entity_type: "workspace",
  payload: { count: <properties reviewed>, period: "<YYYY-Www>", highlights: [<short themes>] },
  source_uri: "routine://pm/portfolio_reconciled/<YYYY-Www>"
})
```

Do **not** pass `property_id`, `deal_id`, or `address` on the rollup.

Other workspace verbs when they fit: `maintenance_triaged`.

## Per-property follow-ups (optional)

When the review names a specific house that needs a logged follow-up, emit a **second** event
with `entity_type: "property"` and `address` or `property_id`. Verb examples:
`disposition_discussed`, `occupancy_reviewed`. Do not invent addresses.

Legal/admin on a named house (lawsuit, deed) is a property event, not the workspace rollup.

## What NOT to emit

- The review notes themselves — keep those in Drive / the session; the event is the signal.
- Marketing work (`cmo-lane`), BNI (`net-lane`), finance (`cfo-lane`).
- Unsaved underwriting — that is `forvex-underwriting` write-discipline, not a lane event.

Confirm `event_id` before declaring the reconcile done.
