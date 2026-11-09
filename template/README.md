# {{PROJECT_NAME}}

> Created from the Majles template. Setup deletes this line.

{{ONE_PARAGRAPH_DESCRIPTION}}

## Where things are

```
docs/
  adr/            architecture decisions only: the hard-to-reverse ones
  specs/          one spec per user flow, written per slice
  reviews/        critic's findings, one per phase gate
  security/       the threat model, and security reviews of sensitive slices
  research/       one directory per research task: request, findings, decision;
                  and backlog.md, for questions that do not block yet
design/           the design system, once it has been researched
ops/              deployment, monitoring, backups and runbooks
plan/             business plan, phases, distribution, pricing
tools/
  render_decisions.py  builds the published log from docs/ and .claude/rules/
```

With the ai module, `evals/` holds the model evals; with the legal module,
`docs/legal/` holds the obligations register and the questions for counsel.

Every directory has one agent that writes to it, and a `README.md` saying so.
The agents are in `.claude/agents/`; they research what blocks the next step
and write the rest in `docs/research/backlog.md`. The working rules, each with
its reason, are in `.claude/rules/`.

## How to run it

There is no application yet. Phase 0 is planning, and the stack is undecided by
design. The **Next:** line in `CLAUDE.md` says what comes next.

## How to test it

The product has nothing to test yet. The one tested tool is the decision-log
renderer:

```bash
python3 -m unittest tools/test_render_decisions.py
```

## How to deploy it

Undecided. The stack ADR decides.
