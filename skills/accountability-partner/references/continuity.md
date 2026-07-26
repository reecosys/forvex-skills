# Continuity — how memory works without a database

This skill has no storage. Everything that survives between sessions lives in one plain-text
**carry-forward block** that the user keeps. The block is the ledger.

## Design rules

1. **One block per session.** It always describes the week just closed *and* the week ahead.
2. **Self-contained.** Someone reading only the latest block can run next week's session. Never
   split state across blocks.
3. **Copy-pasteable.** Plain markdown, no tables in the block, wrapped in HTML comment markers so
   it can be found in a long chat.
4. **Small.** Target under 40 lines. It is a ledger entry, not a journal.

## Block markers

Always open with `<!-- ACCOUNTABILITY-CARRY-FORWARD v1 -->` and close with
`<!-- END ACCOUNTABILITY-CARRY-FORWARD -->`. When looking for prior context, search for the
opening marker first — it is the fastest reliable hit in an attached file, a Project doc, or a
long thread.

## Where the user keeps it

Offer these in order of how well they hold up, and let the user pick:

| Method | Works when | Notes |
|---|---|---|
| **Project knowledge doc** | Chat is inside a Project | Best: the block is in context automatically next week. Doc name: `Accountability Ledger`. |
| **File in the working directory** | The environment has file access | `accountability/ledger.md`, newest entry appended at the top. |
| **Pasted into the next chat** | Always | Simplest. The user keeps it in any notes app. |
| **Emailed to self / calendar note** | Always | Same as above; put it on the weekly reminder that prompts the session. |

Never assume a method is available. Ask once, in one line, then move on.

## Carry counting

Every commitment carries an integer **carry count** — how many prior weeks it has already been
committed to and not finished.

- New commitment → `carried 0` (omit the marker entirely).
- Rolled over once → `(carried 1×)`.
- Rolled over twice → `(carried 2×)` — call it out in the session.
- Three or more → `(carried 3×)` — treat it as a decision the user is avoiding, not a task they
  keep running out of time for. Offer to drop it explicitly. Dropping is a legitimate, healthy
  outcome; a ledger full of zombie commitments makes the whole practice worthless.

A commitment marked **dropped** leaves the ledger and does not count against the completion rate.
Record it once in `Dropped this week` so the decision is visible, then let it go.

## Ledger fields

The block carries exactly these sections. Omit any section that is genuinely empty — do not pad.

- **Header** — week stamp (`2026-W31`), the date the week starts.
- **Score** — completion rate for the week just closed, plus trend if prior weeks are known.
- **Read** — mood / momentum / energy, only if captured.
- **Commitments for next week** — unchecked boxes, each with a due day where one exists, each
  with a carry marker where the count is above zero.
- **Last week** — one line per prior commitment with its status.
- **Wins** — up to three, with numbers.
- **Blockers** — what's actually in the way, stated as a condition, not a feeling.
- **Decisions** — decisions made this week. Cheap to write, expensive to lose.
- **Dropped this week** — abandoned commitments, one line each, with the reason.
- **For next session** — what *you* should press on next time: the deferred decision, the
  commitment on its third carry, the blocker the user talked around. This is the section that
  makes next week's session sharp. Write it for your future self.

## When the block is lost

It happens. Do not stall the session over it.

1. Say plainly that there's no prior context, so this week runs without a review.
2. Ask one recall question: *"What did you say you'd do last week?"*
3. Take whatever they can state and mark each item `[recalled, unverified]`. Do not score a
   recalled week — a made-up completion rate is worse than none.
4. Rebuild carry counts from zero. Note in `For next session` that counts restarted, so a real
   repeat-carry doesn't look like a fresh commitment three weeks from now.

## Multiple blocks in context

If more than one block is available, use the **most recent by week stamp**, and read up to three
prior blocks for trend and carry counts. Ignore anything older — an eight-week-old commitment
that never came back is not a carry, it's a drop that was never recorded.

If two blocks share the same week stamp, the later one in the source wins (the user re-ran the
week).
