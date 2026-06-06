# Activity Taxonomy

`forvex_log_activity` accepts free-form `notes` plus two optional tags: `activity_type` and `outcome`. Pick them from the lists below — don't invent new tags, the in-app timeline filters by these.

## `activity_type`

| Tag | When |
|---|---|
| `call` | Phone call (in or out), voicemail counts |
| `text` | SMS / iMessage |
| `email` | Email sent or received |
| `drive_by` | Physical drive-by, no contact |
| `walkthrough` | On-site interior visit |
| `offer` | Offer presented (verbal or written) |
| `counter` | Seller counter received |
| `negotiation` | Back-and-forth that isn't a discrete offer/counter |
| `inspection` | Inspector / contractor / appraiser visit |
| `mail` | Letter / postcard sent |
| `referral` | Lead source mentioned a relevant party |
| `walkaway` | We disengaged (use disposition skill for the status move too) |
| `note` | Catch-all for context that doesn't fit |

## `outcome`

| Tag | When |
|---|---|
| `no_contact` | Tried but didn't reach |
| `contact_made` | Reached the seller / party |
| `info_gathered` | Got new facts (price, condition, motivation) |
| `accepted` | Offer accepted (also move disposition) |
| `declined` | Offer / counter declined |
| `pending` | Awaiting their response |
| `follow_up_scheduled` | Specific next touch set |

## Inference rules

- "Called Wally, no answer" → `call` / `no_contact`
- "Talked to seller, she said $190k" → `call` / `info_gathered`
- "Drove by, vacant, side window broken" → `drive_by` / `info_gathered`
- "Offered 125, waiting" → `offer` / `pending`
- "They countered at 165" → `counter` / `contact_made`
- "Sent a postcard" → `mail` / `no_contact`

When the user is ambiguous, ask once — don't tag wrong. Untagged is better than mistagged.

## What does NOT belong here

- **Status moves** (LEAD → OFFER, etc.) → use `forvex_update_deal_disposition`. Activity logs don't shift pipeline state.
- **Rehab scope changes** → use `forvex-rehab-estimator` or `forvex-change-order`.
- **Personal reminders** ("call them Tuesday") → also create a `readvise_create_task` so it surfaces in the daily pulse.
