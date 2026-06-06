# MAO Assumptions & Defaults

Every default below is overridable by anything the user says this turn. When you
apply a default the user didn't set, **say so in the output** — beginners need
to know which numbers are theirs and which are the tool's.

## The formula in plain English

The detailed MAO works backward from the resale value:

```
MAO = ARV
    − selling costs        (what it costs to sell: agent + closing)
    − rehab                (the renovation)
    − holding costs        (taxes, insurance, utilities, while you own it)
    − financing costs      (interest + points, if you borrow)
    − buying costs         (closing costs when you purchase)
    − transaction fee      (per-deal franchise / transaction fee, if any)
    − target profit        (what you want to clear)
```

Financing and buying costs depend on the purchase price — the thing being
solved for — so the calculator iterates to a stable answer instead of guessing.

## The forVEX 65% rule (the shorthand)

```
Quick MAO = (0.65 × ARV) − rehab
```

The 0.65 multiplier rolls "all your costs plus your profit" into one number.
forVEX defaults to 65% rather than the common 70% because many flip operators
carry a per-deal transaction fee on top of normal selling, holding, and
financing costs — so a tighter multiplier leaves a little more cushion. It's a
fast gut-check; the detailed calc is what you act on, and the 65% number tells
you if you're in the right ballpark.

## Default values

| Input | Default | Notes |
|---|---|---|
| Target margin | 15% of ARV | The profit target. Override with a % or a $ floor. |
| Profit dollar floor | $0 | If set, binds when it's higher than the margin %. |
| Selling costs | 6% of ARV | Agent commission. Add seller closing if your market splits it out. |
| Hold time | 4 months | ~1 to buy/close, 2–3 to rehab + sell. |
| Monthly holding | 0.25% of ARV / mo | Taxes, insurance, utilities, misc. ~$500/mo on a $200k ARV. Override with a flat $. |
| Financing | Hard money | Options: `cash`, `hard_money`, `company`. |
| Hard money rate | 10% / yr | Interest on the loan over the hold. |
| Hard money points | 2 points | Upfront, on the loan amount. |
| Company money rate | 8% / yr | No points. |
| Lender LTV on cost | 90% | Fraction of (offer + rehab) the lender finances. |
| Buying costs | 2% of offer | Purchase-side closing. |
| Transaction / franchise fee | User-entered | See below — defaults to $0 if not set. |
| forVEX 65%-rule factor | 0.65 | Conservative multiplier. |

## Transaction / franchise fee

Many flippers — especially franchise operators — pay a per-deal fee, often a
**percent of the sale price**. It's a real cost that beginners routinely forget,
and it comes straight off the top, so it materially moves the offer.

This tool **ships no fee schedule**. The number is always the user's own:

- Pass `franchise_fee_pct` as a fraction of ARV (e.g. `0.05` for 5%), **or**
- Pass `franchise_fee_usd` as a flat dollar amount (this wins if both are given).

If neither is supplied the fee is treated as **$0** and the output flags it
(`franchise_fee_not_set`). When a user tells you their fee structure, plug it in;
otherwise run with zero and tell them plainly that their real fee will lower the
offer.

## The offer ladder

The calculator also returns three offer figures so the user has room to
negotiate, not just a single take-it-or-leave-it number:

- **Thin (walk-away):** 10% margin — the most you could ever justify; don't go higher.
- **Target:** the user's margin (15% default) — what you actually want to buy at.
- **Strong (opening offer):** ~20%+ margin — where you open so there's room to come up.

## Honest limitations

- Holding and financing are modeled simply — good enough to make a confident
  offer, not a substitute for a line-item rehab budget or a real loan quote.
- Costs vary by market. The defaults are reasonable national placeholders; a
  user who knows their local agent split, tax rate, or lender terms should plug
  those in for a sharper number.
- This is a flip MAO only. Wholesale, wholetail, and rental math differ.
