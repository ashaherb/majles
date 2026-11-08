# Architecture decision records

Owner: **architect**. Nobody else writes here.

This is where to look to understand why the system is built the way it is. It
holds architecture decisions only. Choices made from research live in
`docs/research/`, and how the team works lives in `.claude/rules/`. The
threshold is in `.claude/rules/decisions.md`: a decision belongs here when it is
expensive to reverse *and* later work builds on it. The stack, the data store,
the content model, hosting, auth, the i18n architecture if there is one. Expect a handful per
slice; `majlis lint` flags more than five. What the user sees, hears or can do is
not architecture: it goes in a spec in `docs/specs/`, which can change.

A fix found by review is never an ADR. It goes in the commit message. If the
fix changes which option an existing ADR chose, write a new ADR that supersedes
it; otherwise there is no ADR.

## Rules

Numbered with four digits, in order: `NNNN-short-slug.md`, starting at 0001.

**Append only.** Never edit or delete an accepted ADR. When a decision changes,
write a new one that says what changed and why, with `Supersedes: NNNN` in its
header, and set the old one's status to `superseded by NNNN`. That status line
is the only edit an accepted ADR ever gets.

Commit an ADR in the same commit as the code it explains. If the decision comes
first, commit it alone.

Keep to the Markdown subset `tools/render_decisions.py` documents, since the
published log is generated from these files.

## Template

```markdown
# NNNN. The decision, stated as a claim

Status: proposed | accepted | superseded by NNNN
Date: YYYY-MM-DD
Needed by: slice N

## Context

What was actually hard, in one or two paragraphs. End with
`Research: docs/research/<task>/`.

## Options considered

Each option as a paragraph opening with its name in bold. The rejected ones say
why they lost; the winner says "Chosen."

Build or adopt: for infrastructure, the maintained tools or services that do
this, and why we adopt one or build. Omit for a decision that is not
infrastructure.

What the user loses: only when the decision limits what the product may say,
show or do for the user, with the developer's yes (`docs/direction.md` entry).

## Decision

What we settled on. State confidence, and say so if it was a coin flip.

## Consequences

What this now forces, forbids, or deletes.

## What would make us revisit this

The observation that should reopen it.
```

An ADR without a `Research:` line is a blocking finding for the critic.

`Needed by:` names the slice of the phase plan in `CLAUDE.md` that first needs
the decision (Phase 0's decisions say `slice 1`). A decision no current slice
needs is not made yet (`.claude/rules/agents.md`). `majlis lint` checks for the
`Status:`, `Research:` and `Needed by:` lines.
