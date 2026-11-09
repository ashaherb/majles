<!-- SETUP: this whole block is deleted once the project is set up. -->
# Setup: delete this section when done

**If this directory is the Majles repository itself (it has `MAINTAINING.md`
at its root), you are maintaining the template. Fill nothing in, and follow
`MAINTAINING.md`.**

Otherwise, this project was just created from the Majles template and is not set
up yet. Before any other work, follow `SETUP.md` in this project. In short:

1. Get the project description from the developer.
2. Fill every `{{PLACEHOLDER}}` you can derive. Ask for the rest in one batch.
3. Turn modules on or off with `majles`.
4. Create the repo, unless the project was adopted and has one.
5. Publish the decision log.
6. Delete this section, the template line in `README.md`, and `SETUP.md`.
<!-- /SETUP -->

# {{PROJECT_NAME}}

{{ONE_PARAGRAPH_DESCRIPTION}}

Working name: **{{PROJECT_NAME}}**. {{NAME_STATUS}}

## The thesis, in one line

{{THESIS}}

## Who this is for

{{WHO_IT_IS_FOR}}

Every decision gets checked against that person.

## Non-negotiables

{{NON_NEGOTIABLES}}

Each line is marked as the developer's words, with its entry in
`docs/direction.md`, or as drafted. A drafted line never becomes a gate without
the developer's yes (`.claude/rules/asking.md`).

## The MVP

**The core loop.** {{CORE_LOOP}}

**It must do this:**
{{MVP_MUST_DO}}

**Out of scope for the MVP, but the design must not make impossible:**
{{OUT_OF_SCOPE_BUT_KEEP_POSSIBLE}}

**Constraints.** {{CONSTRAINTS}}

**Languages.** {{LANGUAGES}}

**The one number.** {{SUCCESS_METRIC}}

## Current phase

**Phase 0, the foundation.** The team is configured: agents, a research
protocol and working rules. Nothing has been researched yet, there are no ADRs,
and there is no phase plan.

**Next:** the architect's foundation pass. Start it with "run the architect on
the Phase 0 brief in CLAUDE.md".

This section is the project's status: the phase, what exists, and one
**Next:** line, which points at the current slice once there are slices. Change
**Next:** in the same commit as the work that makes it wrong. **Next:** holds
only what is next; finished work is in git. This file goes with every call of
every agent, so it stays under 16 KB (`.claude/rules/tokens.md`).

## Phases

Phase 0 is the foundation. Every phase after it is one slice of the product
that a user could try: slice 1 is the core loop for the person in "Who this is
for", end to end, on the real services, and good enough to come back to; each
later slice adds to it, and infrastructure comes in the slice that needs it
(`.claude/rules/agents.md`). Slices beyond the next two live in
`docs/phases.md`, read when needed. The flows the
slices are cut from: {{CORE_FLOWS}}.

The architect drafts this plan in Phase 0 and the developer approves it. One
short block per slice:

```markdown
### Slice N. <name>

What a user can do at the end of it.

Exit test: one observable check.

Needs: the decisions (with `Needed by: slice N`) and the research it depends on.
```

Not drafted yet.

## Phase 0 brief

The architect decides only what is expensive to reverse *and* needed by slice
1. Anything else becomes a decision under the slice that needs it.

1. **Research first**, through `docs/research/`:
   - **Deep:** the stack and hosting, at current versions and prices.
   - **Deep:** {{HARDEST_TECHNICAL_QUESTION}}, as far as it constrains the
     stack.
   - **Medium:** how the data model can carry the out-of-scope features above
     later, without a migration that rewrites everything.

   Everything else the architect wants to know goes to
   `docs/research/backlog.md`. Write a `decision.md` for each before the ADR
   that depends on it.
2. **Two ADRs**, numbered from the next free number in `docs/adr/`, each citing
   its research and marked `Needed by: slice 1`:
   - **The stack:** framework, language, data layer and hosting, with the
     rejected options written down.
   - **The core data model:** the entities slice 1 needs, and one sentence per
     out-of-scope feature on where it would attach later. Not a design of them.
3. **The phase plan**, in `## Phases` above, for the developer to approve.
   Decisions not needed by slice 1 go under the slice that needs them.
4. **`docs/open-questions.md`:** everything the architect was not confident
   about. Ten honest open questions beat a plan that pretends to be certain.
5. **Only the scaffolding the stack itself needs**, inside the layout in
   `.claude/rules/ownership.md`, with `README.md` updated to say how to run it:
   the formatter, the lint and module-README checks
   (`.claude/rules/code-organization.md`), the local pre-push checks in
   `.githooks/pre-push.local`, and CI that runs once per ready pull request
   (`.claude/rules/git.md`, `ops/README.md`). No feature code.

Stop there. The critic then reviews, including whether the research went deep
enough and whether the decisions follow from it. Then the developer argues with
at least two decisions; accepting the whole plan outsources the learning. No
feature code is written until that is done.

When Phase 0 closes, delete this Phase 0 brief section and rewrite **Next:** to
point at slice 1.

---

# How we work

The working rules are in `.claude/rules/`. They load into every session and
every agent automatically, and each rule is short and carries its reason:

- `decisions.md`: where each kind of decision is recorded. ADRs are for
  architecture only; what the user gets is a spec.
- `done.md`: what counts as done: the gate on the pull request, real calls,
  and a try as the user.
- `asking.md`: the developer's words, verbatim; when to ask, and when to decide.
- `tokens.md`: short-lived agents, short reports, short standing text.
- `code-organization.md`: code a person can maintain.
- `ownership.md`: which agent writes in which directory.
- `research.md`: research only what blocks, how deep, the budget and the
  backlog.
- `agents.md`: phase order, models, and how agents load.
- `constraints.md`: this project's standing constraints.
- `working-style.md`: disagree out loud, and give the tradeoff.
- `git.md`: branches and pull requests; nothing is pushed to `main`.
- `git-account.md`: this project's remote, commit identity and `gh` account.
- `majles.md`: which files come from the Majles template, and how they update.
- `beads.md`: the work queue: only the main session writes to it; every
  agent's report ends with the `bd` commands it needs.

Where the reasoning lives: architecture in `docs/adr/`, what the user gets in
`docs/specs/`, choices made from research in `docs/research/`, the developer's
own words in `docs/direction.md`, and everything above in the rules. The
rendered decision log:
{{DECISION_LOG_URL}}

Where we are, with the real screens (`python3 tools/render_status.py`):
{{STATUS_PAGE_URL}}
