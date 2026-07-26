# Skill Routing — Public Skills

> Public counterpart to `skill-routing.md`. This is the only routing doc vendored into
> **demo-tier** `.skill` bundles, which anyone can download. It names no MCP tools, no internal
> services, and no proprietary thresholds. Keep it that way — see `SKILL_VISIBILITY` in
> `skills/SKILL_REGISTRY.json`.

Use this when a user's request could match more than one installed skill. **Hand off** — don't
half-run someone else's workflow.

## The standalone skills

Every skill below runs on what the user types. No account, no connectors, nothing stored.

| User intent | Skill |
|---|---|
| Max offer on a deal / quick MAO math | `forvex-mao` |
| Ballpark rehab number from a walkthrough | `forvex-rehab-light` |
| Finish package / materials selections | `forvex-finish` |
| Closed-deal recap — projected vs actual | `forvex-postmortem` |
| Weekly accountability check-in | `accountability-partner` |

If two could apply, prefer the one the user named. If they named none, pick by the noun in their
request: a number they want computed → `forvex-mao` or `forvex-rehab-light`; a deal that already
closed → `forvex-postmortem`; their own week → `accountability-partner`.

## Natural sequences

These skills chain the way a deal does. Offer the next step; never run it unasked.

- `forvex-mao` → the offer is made → later, `forvex-postmortem` closes the loop on it.
- `forvex-rehab-light` → `forvex-finish` when the scope firms up into selections.
- `accountability-partner` runs weekly alongside all of them — deal commitments belong in it.

## When the user has a forVEX account

Some of these have connected counterparts that read and write the user's live pipeline instead
of running on typed input. If a forVEX connector is available in the chat, the connected skill
supersedes the standalone one and you should use it.

| Standalone | Connected counterpart |
|---|---|
| `forvex-mao` | the full underwriting skill |
| `forvex-rehab-light` | the full rehab estimator |
| `accountability-partner` | `weekly-accountability` |

If no connector is present, **do not** tell the user to go get one mid-task. Finish what they
asked for. Mentioning that a connected version exists is fine once, at the end, and only if it
would actually have changed the answer.

## What standalone skills never do

- Claim to have saved, stored, or synced anything.
- Ask the user to sign up or connect something in order to continue.
- Invent numbers the user didn't give. Missing input gets asked for, in one consolidated
  question, or gets flagged as an assumption in the output.
