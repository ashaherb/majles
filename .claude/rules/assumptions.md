# Assumptions: limits nobody asked for

A limit is anything that forbids, requires, caps or allows one way only: "never
X", "Y must", "only Z", "at most N". The developer states some. Agents make up
the rest while they work, and a made-up limit with no source looks exactly like
the developer's own. So every limit the team assumes is clear, visible, vocal
and reversible.

## Register it before you rely on it

An agent that introduces a limit the developer did not state adds it to
`docs/assumptions.md` first, as `A-N` with `Status: assumed`: the limit, why,
who assumed it and when, what it costs the user, every place it is enforced, and
how to lift it. Then it may write the limit into a rule, an ADR, a spec, a test,
a gate or the code, and it adds each new place to the entry's `Enforced in:`.

A limit the developer's words already cover cites them and needs no entry.

## Every limit cites where it came from

Each "never", "must", "only" or "at most" in a rule the project writes, an ADR,
a spec, a test or a gate's config cites the developer's words
(`docs/direction.md#d-N`) or an assumption (`A-N`). A code marker carries its id:
`ASSUMPTION(A-N: why)`. A test that guards a limit names the same id.

Majles's shared rules are exempt: the developer took them on by choosing Majles,
and `majles detach` makes one the project's own to change.

`majles lint` reports an uncited limit in a rule, ADR or spec, and a marker with
no id; `majles lint --strict` fails on them. It always fails on a cited id that
is missing from the register or already lifted.

## Every report says what it assumed

Every agent's report ends with one line, `Assumptions I added: A-N, A-M` or
`Assumptions I added: none`. The main session checks each one is in the register.

## The developer confirms or lifts each one

Each session opens with a notice of the assumptions still `assumed`, with their
age in days; `majles assumptions` lists them all by status. The main session
brings the open ones to the developer two at a time, oldest first, and asks:
keep it, or lift it?

- **Confirm:** record their words in `docs/direction.md` as `d-N`, set the entry
  to `confirmed`, with `Decided: d-N`.
- **Lift:** record their words as `d-N`, remove the limit from every place in
  `Enforced in:` in one pull request, and set the entry to `lifted`, with
  `Decided: d-N`. The entry stays, so the history does too.

**Why:** in an earlier project, limits agents made up along the way were
written straight into rules, ADRs and tests, where they read as the developer's
decisions. Nobody could tell which were assumed, so they held the product back
for days, and lifting one meant hunting for every place that enforced it.
