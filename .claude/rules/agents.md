# Running the agents

## Phase 0 is the foundation only

The architect decides only what is expensive to reverse *and* needed by slice
1: the stack and hosting, and the core of the data model. It drafts the phase
plan in `CLAUDE.md` under `## Phases`, for the developer to approve. Nothing
else. Phase 0's gate is the critic, then the developer arguing with at least two
decisions.

## Every later phase is one slice

A slice is a piece of the product a user could try. Slice 1 is the core loop
for the person in "Who this is for", end to end, on the real services, and good
enough that they would come back to it. Admin and operator screens,
observability, billing and other infrastructure come in the slice whose
experience needs them, not before. Within a slice the roles run small and in
order:

1. the architect, for only the decisions this slice needs;
2. product, and the designer if the project has a UI, in parallel, for this
   slice's flows only; the designer designs each screen whole, every state, at
   phone and desktop size, before it is built;
3. the builder implements, with the tester writing the acceptance tests and the
   slice's exit test alongside, and the editor writing content alongside if the
   content module is on;
4. the gate.

Alongside, as the slice needs them: ops from the first slice that deploys
anywhere; security at the gate of a slice that touched auth, sessions, personal
data, payments, secrets, external input or file handling; the ai agent whenever
a prompt, model or guardrail changes (ai module); legal before a slice collects
personal data, takes payment or serves a new country (legal module). Each runs
when its trigger is met, not at every gate.

The phase plan names, for each slice, what a user can do at the end of it, its
exit test (one observable check), and the decisions and research it needs. The
**Next:** line in `CLAUDE.md` points at the current slice.

**Why:** in an earlier project the registry, the operator pages, tracing and
many review loops came before one screen felt good to its user, and its
developer judged the result rigid and plain.

## Every decision names when it is needed

Each ADR header carries `Needed by: slice N`. A decision the current slice does
not need is not made now: it goes in the phase plan under the slice that needs
it, and its research goes to `docs/research/backlog.md`.

## The gate

A slice is done when the three levels of `.claude/rules/done.md` hold, its exit
test passes, the critic has reviewed it (with the fix-check limit below), any
security review it triggered has no open blocking finding, and then the
developer has tried it. The developer is never the first person to use a build.
The critic also runs before any decision that is expensive to reverse. An
enthusiastic review is a failed review.

## A review loop has an exit

- After a review's blocking findings are addressed, the critic runs a **fix
  check**: it reads only those fixes, and appends the result to the same review
  under `## Resolved`. A fix check is not a new numbered review.
- A new numbered review is written only at a phase gate, before a decision that
  is expensive to reverse, or when a fix check finds the fix itself broke a
  non-negotiable.
- At most two fix checks per review. If blocking findings remain after the
  second, the main session stops and brings them to the developer.
- Problems a fix check notices that the fix did not cause go into the review's
  `## Non-blocking` list, unless they break a non-negotiable.

**Why:** in an earlier project, nine reviews in a row each reviewed the previous
one's fixes, and the loop never had a reason to stop.

## Only the main session spends money or reads secrets

No agent but the main session reads `.env` files or other secrets, or runs a
command that costs money (a paid model or API call, a deploy). An agent
that needs one says so in its report, and the main session runs it.

The deny rules in `.claude/settings.json` stop the Read tool, not a
shell command. This rule is the guard.

**Why:** in an earlier project an agent loaded the repo's `.env` and ran a paid
test after being told not to.

## Models

Architect, product, designer, critic, security, editor, ai, the builder and
the 100x-engineer run on Opus: they judge, decide, or write what the product
is. The researcher, legal, tester and ops run on Sonnet: they gather evidence
within a set depth, draft for counsel, or carry out what specs, ADRs and
runbooks already say. To run an agent on another model, such as Fable,
`majles detach` its file and edit `model:`.
`.claude/settings.json` sets a session-wide `fallbackModel` of Opus, which
triggers only when a model is overloaded or unavailable, **not on rate limits**.

## Loading and routing

Agent definitions in `.claude/agents/` load when a session starts, so start a new
session after changing one. If an agent is never picked for work that is plainly
its job, fix its `description` field. No description says "use proactively".
