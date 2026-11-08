# Specs

Owner: **product**. Nobody else writes here.

One file per user flow, named for the flow as the user would describe it:
for example `sign-up.md` or `export-a-report.md`. Specs are written per slice
of the phase plan in `CLAUDE.md`, for the flows in that slice only.

A spec is finished only when it contains all six:

1. **The job**: what the user is trying to get done, in their words.
2. **The experience**: what the user should feel and notice, what makes it
   good rather than merely working, and what the product does on its own
   initiative.
3. **Happy path**: step by step, from arrival.
4. **Empty state**: exact copy, in every supported language.
5. **Error state**: exact copy, and what the user can still do.
6. **Loading state**: what is on screen before data arrives.

Then acceptance criteria, written so the tester can test against them. And
where the flow touches it, how "The one number" in `CLAUDE.md` is measured: the
event, when it fires, and what counts, for ops to wire.

Every spec cites the research behind it in a `Research:` line at the top. A claim
about how users behave that no research supports is written as an assumption
and labelled as one.

A spec missing the empty, error or loading state is unfinished. Those three
states decide whether the person in "Who this is for" trusts the product, so they are
not a polish pass.

Specs are living: what the user gets is decided here, not in an ADR, and is
edited in place as the product is tried (`.claude/rules/decisions.md`).

Specs describe behaviour, never implementation. If a spec names a framework or a
table, it has crossed into the architect's territory.
