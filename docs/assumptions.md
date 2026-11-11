# What we assumed for you

Owner: **main session**; any agent adds an entry before it relies on a limit the
developer did not state (`.claude/rules/assumptions.md`). One entry per assumed
limit, numbered `A-N`, newest last. An entry is never deleted: confirming or
lifting it changes its `Status:` and adds `Decided:`, so the history stays.
Anything that forbids, requires, caps or allows one way only, and cites an `A-N`,
is explained here.

Format, one entry per limit:

```markdown
## A-N. The limit, as one sentence

Status: assumed
Assumed by: the agent or session, YYYY-MM-DD
Why: what made it seem needed, and what it protects.
Costs the user: what they cannot do, or wait for, while it holds.
Enforced in: `path/to/rule.md`, `path/to/test_x.py`, every place that applies it
To lift: what to remove or change, and what replaces it, if anything.
Decided: d-N, once the developer confirms or lifts it
```

`Status:` is `assumed` (nobody asked the developer yet), `confirmed` (they kept
it) or `lifted` (they removed it, and every place in `Enforced in:` went with
it). `Decided:` cites their words in `docs/direction.md`. `majles lint` checks
each entry has these lines, and `majles assumptions` lists them by status.
