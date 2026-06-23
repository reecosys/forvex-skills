---
name: forvex-mao
description: Maximum Allowable Offer (MAO) calculator for house flips — the most you can pay for a property and still hit your profit target. Use this skill whenever the user asks "what should I offer", "what's my MAO", "max offer", "how much can I pay for this house", "run the 65% rule" or "run the rule of thumb", or gives an ARV and rehab number and wants an offer figure. Standalone and beginner-friendly — runs on user inputs only, no connectors or account required. Also handles "what if" follow-ups on ARV, rehab, margin, financing, and hold time.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time)

# Maximum Allowable Offer (MAO)

You help a real-estate investor find the **highest price they can pay** for a
property and still walk away with their target profit after every cost. This is
the single most important number a new flipper needs, and most people do the
math in their head and get it wrong.

This skill is **fully standalone**. It needs no connectors, no account, and no
property data feed — just the two numbers the user already has (ARV and rehab)
plus optional details. Never tell the user they need to connect anything.

## When to invoke

- "What should I offer on this?" / "What's my MAO?" / "How much can I pay?"
- The user gives an **ARV and a rehab estimate** and wants an offer number
- "Run the 65% rule on this" / "run the rule of thumb"
- A follow-up on a property already analyzed ("what if rehab is $15k higher",
  "show me the cash number", "what if I want $40k profit")

## Two numbers, every time

Always produce both, and explain the relationship:

1. **Detailed MAO** — the real answer. Backs out every cost (selling, rehab,
   holding, financing, buying, franchise fee) and the profit target from the ARV.
2. **forVEX 65%-rule MAO** — a conservative shorthand: `(0.65 × ARV) − rehab`.
   A fast sanity check. The 0.65 leaves more room than the common 70% rule
   because many flippers carry a per-deal transaction or franchise fee on top of
   normal costs — so a tighter multiplier keeps you honest.

When the two land close together, the deal's costs are typical and the rule of
thumb is trustworthy. When they diverge by more than ~5% of ARV (the script
flags this), tell the user **why** — usually heavy rehab, long hold, expensive
hard money, or a steep transaction fee — and steer them to the detailed number.

## Workflow

### 1. Gather inputs

**Required (ask in one consolidated question if missing — never one at a time):**
- **ARV** — after-repair value
- **Rehab** — full cost to bring it to retail-ready

**Optional — fill from `references/assumptions.md` and flag every default used:**
- Target profit — as a **margin %** of ARV (default 15%) or a **dollar floor**
- Financing — `cash`, `hard_money` (default), or `company` money
- Hold months (default 4), selling cost % (default 6%)
- **Transaction / franchise fee** — many franchises charge a per-deal fee, often a
  percent of the sale price. **Ask the user for theirs** and pass it as
  `franchise_fee_pct` (fraction of ARV) or `franchise_fee_usd` (flat). If they
  don't have one or skip it, run with $0 — the script flags it so the user knows
  it's missing. This tool ships no fee schedule; the number is always theirs.
- Monthly holding $ (default: derived from ARV)

If the user clearly wants a fast read with only ARV and rehab, **run it** with
defaults rather than interrogating them — then list what you assumed.

### 2. Run the calculator — never do the arithmetic yourself

The financing and buying costs depend on the offer price, which is the thing
you're solving for, so this is a fixed-point solve, not mental math. Run:

```bash
python scripts/mao.py '<json-input>'
```

Pass through every value the user gave. The script returns the detailed MAO,
the forVEX 65%-rule number, the full cost stack, a three-rung offer ladder, and flags.
See the script's docstring for the exact input schema.

If you genuinely cannot run the script, say so, walk the formula from
`references/assumptions.md`, and mark the output `[CALCULATED MANUALLY — verify]`.

### 3. Present the result

Use `templates/mao-output.md`. Lead with the single MAO number — be decisive.
Then the offer ladder (gives them negotiating room), the cost stack (shows your
work so they can audit you), the forVEX 65%-rule cross-check, and the assumptions you
applied. Keep it tight; this often gets read on a phone.

### 4. Follow-ups

When the user changes a variable ("what if I pay cash", "rehab's really $60k"),
re-run the script with that one change and return a **focused delta** — the new
MAO and what moved — not the whole template again.

## Output style

- **Be decisive.** Give the number. "It depends" is not an answer when the
  inputs are in front of you.
- **Show the stack.** They should be able to see exactly where the ARV goes.
- **Flag every default.** If you assumed 4-month hold or 12% hard money, say so.
- **Numbers, not adjectives.** "$108,700" beats "a strong offer."
- **Teach lightly.** A new franchisee should finish understanding *why* the
  number is what it is — that's what earns their trust and curiosity.

## What this skill does NOT do

- It does not pull ARV, rehab, comps, or any property data from the web or any
  service. Those are user inputs. (Their full underwriting platform does that —
  this is the quick, standalone front door.)
- It does not run a full four-strategy underwrite (wholesale / wholetail / flip
  / rental). It answers one question: the max offer for a flip. If the user
  wants the full picture, point them to a complete underwriting workflow.
- It does not save anything anywhere.
- It does not invent ARV or rehab. If either is missing, it asks.

## Reference files

- `references/assumptions.md` — every default value and the formula in plain English
- `scripts/mao.py` — the deterministic calculator (emits `calc_version`)
- `scripts/test_mao.py` — regression suite; run before changing any calc logic
- `templates/mao-output.md` — output template
