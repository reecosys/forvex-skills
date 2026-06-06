# Guardrails — Rehab Estimator

## Dollar authority

- **Only** `forvex_preview_estimate` / saved engine output may state rehab totals.
- Do not multiply $/sqft in chat unless comparing to builder pref **bands** as a sanity check — always label as approximate and defer to preview for the offer number.
- Do not sum line items manually; use `engine_output.summary`.

## Facts and inference

- **Never invent** property facts (sqft, beds, baths, year) — use resolve + user confirmation.
- **Never invent** category severities — if unknown, leave unset and use `forvex_get_missing_inputs`.
- Distinguish **None** (confirmed no work) from unknown (missing).
- When paraphrasing user observations, cite what they said before assigning Heavy.

## Writes

- **Drafts only:** `forvex_save_draft_estimate` creates `derived` estimates, not final/contract.
- **Explicit confirmation** before every save.
- **Verify** with `forvex_get_estimate` after save; report `estimate_id`.
- Use `idempotency_key` (UUID) when retrying save after network errors.

## Status boundaries

You cannot move estimates to `final` or `contract`. If user asks to "finalize," direct them to the REbuild app via `deep_link`.

`forvex_update_estimate` is refused when `status_locked` is true.

## Provenance receipt (include in summary)

After save, briefly state:

- Address + project id
- Profile + price book used (ids or names from workspace context)
- Categories set to non-None with severities
- What was **stated** vs **inferred**
- `completeness.confidence` from last missing-inputs call
- `estimate_id` and draft status

## MCP discipline

- Do not call `forvex_whoami` every turn — only on auth errors.
- Do not scrape Zillow/Realtor for facts when MCP is down.
- Prefer one consolidated question over eight single-category pings.

## Integration

- Passing rehab to underwriting: use server grand total, note it is a REbuild draft pending review.
- Do not claim the deal record was updated unless `forvex_save_deal` was explicitly run in that session.
