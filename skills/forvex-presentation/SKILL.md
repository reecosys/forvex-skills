---
name: forvex-presentation
description: Render an already-analyzed forVEX deal, or a seller appointment that just happened, into a richer artifact — interactive HTML dashboard with charts, a 5-slide deal deck, a print-ready PDF one-pager, an internal deal sheet, an appointment debrief, or a rehab scope sheet. Use when the user asks "render this as a dashboard", "make this a slide deck", "give me a PDF", "show me this visually", "wrap up the appointment", "debrief that meeting", "what happened at the appointment", "appointment recap", "render the rehab scope", or "show me the estimate breakdown". Does NOT re-run the math — calls forvex_render_presentation, which fills HTML from the saved analysis (modes 1–4), a typed debrief payload (mode 5), or a saved estimate plus observations (mode 6).
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# forVEX Presentation — Rich Artifact Rendering

You take something that already happened — a completed deal analysis, a seller
appointment the operator just walked out of, or a saved REbuild rehab estimate —
and render it as a richer artifact. You do not re-run the math. You do not
change any numbers. You do not reconstruct events you weren't told about.

The **`forvex_render_presentation`** MCP tool owns assembly and HTML. This skill
picks the mode, makes sure modes 1–4 have a **saved** analysis, fills the Mode
5/6 payload from the conversation, calls the tool, and **re-emits `html` as the
artifact**. MCP does not auto-promote tool HTML to an Artifact — you must
present `html` yourself, the same way `forvex-wholesale-sheet` does.

This is the **operator** view (verdict, deal score, buy-box, MAO, cost basis,
assignment spread). Buyer-facing sheets are **`forvex-wholesale-sheet`**.

## When to invoke

- "Render this as a dashboard"
- "Make a slide deck for this deal"
- "Give me a PDF I can share with [buyer / capital partner / spouse]"
- "Show me a chart of the sensitivity"
- "Wrap up the appointment" / "debrief that meeting" / "appointment recap"
- After a deal analysis, when the user wants something more than markdown
- After a seller appointment, when the user narrates how it went (Mode 5)
- "Render the rehab scope" / "show me the estimate breakdown" / "does this estimate match what we saw?" (Mode 6)

## Modes

| Mode | Tool `mode` | Input | Who authors content |
|------|-------------|-------|---------------------|
| 1 Dashboard | `dashboard` | Saved analysis | Server (Chart.js HTML) |
| 2 Deck | `deck` | Saved analysis | Server (5-slide HTML) |
| 3 PDF one-pager | `pdf` | Saved analysis | Server (print-CSS HTML) |
| 4 Internal deal sheet | `internal_sheet` | Saved analysis | Server (strategy-aware operator HTML) |
| 5 Appointment debrief | `appointment_debrief` | Operator recount | **You** build the typed `debrief` payload; server stamps HTML only |
| 6 Rehab scope | `rehab_scope` | Saved estimate + optional observations | Dollars from the estimate; **you** pass `rehab.observations[]` |

## Required prerequisites

**Modes 1–4** need a **saved** analysis on the deal. Preferred handles:

- conversation context from `forvex-underwriting` (after `forvex_save_deal`)
- `deal_id` / `property_id` / `address` / `readvise_property_id`

If there is no saved analysis, refuse: *"I render a saved analysis. Run
`forvex-underwriting` and save the deal, then ask me to render it."* Do not
fill HTML from conversation-only numbers.

**Mode 5** needs the **operator's recount** of the appointment — who was there,
what was said, what was offered, what happens next. An underwriting analysis is
optional garnish for the numbers strip. If the user asks for a debrief without
telling you how the appointment went, **ask**. Do not reconstruct an appointment
from property data. The tool **refuses** an empty debrief payload.

**Mode 6** needs a **saved REbuild estimate** (`estimate_id` or `project_id`).
Walkthrough observations are optional; without them the tool drops reconciliation
and says the estimate is unreconciled. Never recompute totals — pass observations
only. If there's no saved estimate, refuse and route to `forvex-rehab-estimator`.

## Workflow

### 1. Pick the mode

Ask once if it isn't obvious. Default: dashboard if they say "show me visually",
PDF if they say "one-pager / print / send", deck if they say "slides / present",
internal sheet if they say "internal / desk / operator sheet", debrief if they
just left a meeting, rehab scope if they mean the estimate.

### 2. Call the tool — never assemble HTML yourself

```
forvex_render_presentation({
  mode,                              // required
  deal_id | property_id | address | readvise_property_id,
  estimate_id? | project_id?,        // rehab_scope
  debrief?,                          // appointment_debrief — see payload below
  rehab?,                            // rehab_scope observations
  next_step?, brand_name?, brand_contact?
})
```

The tool returns `{ schema_version, mode, data, html }`:

- `data` — address, verdict, score, strategy, brand (enough for a one-line summary)
- `html` — the self-contained artifact. **Present this as the deliverable.**

If the tool errors (no saved analysis, empty debrief, missing estimate), relay
it plainly and say what to do.

### 3. Present the result

- Re-emit `html` as the artifact. The user saves it and prints to PDF (browser
  print) or opens it later in Operate / readvise-mobile (same HTML via
  `POST /api/operate/presentation` — you do not call that).
- One-line summary from `data` (verdict, score, strategy) so they can sanity-check.
- On iPhone Claude, warn that Chart.js dashboards may have reduced interactivity;
  the native app WebView is the better host.
- **Mode 5:** render **inline**. Never publish a shareable artifact URL. Tag is
  Internal · Confidential.
- **Mode 6:** not a contractor bid. Don't let it be handed to a trade as one.

## Mode 5 payload (`debrief`)

You author this from the conversation. The server does not invent people,
quotes, or next actions. Pass what you were told; omit empty arrays.

```
debrief: {
  date_range, attendees, ran_by,     // strings or omit
  offer_made, stands, next_touch,
  read_p1, read_p2,                  // the read — two short paragraphs
  position_p1, position_p2,          // our posture
  people: [{ name, role, stake, stance }],   // stance: yes | maybe | swing | unknown
  objections: [{ quote, response, status }], // status: open | part | closed
  timeline: [{ time, event }],
  learned: [{ head, detail }],
  next_actions: [{ action, how, when }]      // each closes a named unknown
}
```

At least one of `people`, `read_p1`, `offer_made`, or `stands` must be present.

After rendering, **hand off, don't write:**

- the touch itself → `forvex-activity-log`
- a pipeline move → `forvex-deal-disposition`

Say what you'd log and let the user confirm.

## Mode 6 payload (`rehab`)

Dollars come from `estimate_id` / `project_id`. You only pass observations and
operator notes. Every reconciliation row must cite a **stated observation**.
You flag that a line may not be *needed*. You never argue a line is priced
*wrong*.

```
rehab: {
  estimate_id?, project_id?,
  reconcile_source,                  // e.g. "Aug 22 walkthrough"
  read_p1, read_p2, read_p3,
  observations: [{ item, sku?, saw, status }],
    // status: confirmed | verify | likely_remove | missing
  exclusions: string[],
  outside_note,                      // any figure NOT from the engine
  next_checks: [{ do, why }],
  net_effect, contingency_note,
  lane?: { label, total?, desc?, items: [{ name, amount }], rollup? },
  fallback?: { label, total?, desc? }
}
```

If you have no walkthrough observations, omit `observations` (or pass `[]`) —
the tool drops reconciliation and labels the estimate unreconciled.

After rendering, hand off: scope/dollar changes → `forvex-change-order`;
progress notes → `forvex-project-update`.

## Buyer-facing? Use forvex-wholesale-sheet instead

Never hand verdict / deal score / MAO / assignment spread to a buyer. When the
user wants something to send a cash buyer, wholesale desk, or buyers list, route
to **`forvex-wholesale-sheet`**. Mode 4 here is the *operator* twin of that
buyer sheet.

## Before vs. after the appointment

| The user wants | Skill |
|---|---|
| To walk into a meeting prepared | **`forvex-appointment-prep`** |
| To capture a meeting that already happened | **Mode 5 here** |
| To log the touch | **`forvex-activity-log`** |
| To move pipeline status | **`forvex-deal-disposition`** |

## Rendering a REbuild estimate vs. checking one

| The user wants | Skill |
|---|---|
| A fast read on project state | **`forvex-project-status`** |
| The estimate rendered, reconciled against the visit | **Mode 6 here** |
| To change scope or dollars | **`forvex-change-order`** |
| To log progress with no scope change | **`forvex-project-update`** |
| To draft a new estimate | **`forvex-rehab-estimator`** |

## What this skill does NOT do

- Does not re-run the math or fill HTML templates locally
- Does not write to the deal or the estimate
- Does not produce actual PDFs or PPTX files — it produces HTML
- Does not invent visualizations beyond the six modes
- Does not persist Mode 5 as a shareable URL

## Emit after a batch (definition-of-done)

After you finish rendering (one artifact or a Monday-style batch), emit so Readvise sees the
activity. Do not skip this.

1. **Workspace rollup** — always, when you produced one or more presentations this session:

```
forvex_emit_event({
  lane: "cmo",
  verb: "presentations_produced",
  entity_type: "workspace",
  payload: { count: <N>, areas: [<mode or topic strings>], period: "<YYYY-Www>" },
  source_uri: "routine://cmo/presentations_produced/<YYYY-Www>"
})
```

If this was a one-off, still emit with `count: 1` and a session `source_uri` (not the weekly
routine URI) so a later Monday batch does not collapse it.

2. **Per-property** — when the presentation is about a resolved address, also emit:

```
forvex_emit_event({
  lane: "cmo",
  verb: "content_published",
  entity_type: "property",
  address: "<full address>",
  payload: { format: "<dashboard|deck|pdf|...>" },
  source_uri: "<artifact or session link>"
})
```

Confirm `event_id` (or `deduped: true`) before telling the operator you are done.

## MCP notes

- Requires MCP. `forvex_render_presentation` owns numbers + HTML; this skill
  orchestrates mode, save-first for 1–4, Mode 5/6 payload, and presentation.
- Prefer `deal_id` from `forvex://deal/{deal_id}/analysis` over asking the user
  to paste numbers.
- Output schema is `presentation.v1`. Operate and readvise-mobile consume the
  same HTML later via `POST /api/operate/presentation`.
- Default brand is **forVEX Edge**.
