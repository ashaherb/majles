# The work queue: Beads

Every unit of work is one issue in Beads (`bd`, open source, MIT). It is the
one place that says what is open, who has it, and what blocks what, for every
session and worktree at once. The database is `.beads/` in the main checkout,
kept out of git by `.git/info/exclude`; worktrees share it automatically.

**Why:** agents cannot see each other's sessions. Without one queue, two of
them take the same work, and a new session rebuilds what is in flight from
git history.

## Only the main session writes to the queue

- **Agents** may read the queue (`bd show`, `bd ready`, `bd list`) and never
  change it. A report ends with a `bd` block: the exact commands for what the
  agent did, found and left, for example
  `bd comments add <id> "pre-push passed on <commit>"`,
  `bd create "…" -t bug -p 1 -l role:<agent>`,
  `bd dep add <blocked> <blocker>` (the first waits on the second),
  `bd close <id> --reason "<PR>, <evidence>"`. No block means nothing changed.
- **The main session** claims the issue before briefing an agent
  (`bd update <id> --claim --actor <role>`) and names it in the brief. When the
  report arrives it runs the block, checking each `close` against
  `.claude/rules/done.md` first. Work no issue covers gets one before it starts.

**Why:** agents are not given a shell for this. One writer keeps the queue
consistent, and every change still comes from the agent that knows it.

## The product agent owns what is in the queue

The product agent decides the queue's content: what is filed from specs and
the developer's direction, priority, `role:<agent>` labels, blockers, and what
is closed or reopened on the evidence. It hands those over as a `bd` block like
any agent. Issues labelled `developer` wait on the developer; no agent takes
one.

## The board

[beads-ui](https://github.com/mantoni/beads-ui) (MIT) is a view over the same
database: `bdui start --port <port>`, with the port the project's `README.md`
names, then `http://127.0.0.1:<port>`. It binds to this machine only; never
pass `--host`.

## What stays where it is

Beads holds the queue, not the reasoning. Decisions still go where
`decisions.md` says, and the developer's words in `docs/direction.md`.

Never run `bd init` without the flags in the Majlis setup, or
`bd setup`, `bd hooks install` or a `bd prime` hook. Default init points
`core.hooksPath` away from `.githooks`, which silently turns off the guard on
`main`; it also makes its own commit and writes agent instructions that
conflict with these rules.

## Self-hosted, nothing paid

The queue lives on this machine. `bd` backs it up to `.beads/backup` every 15
minutes by itself, and `bd backup restore .beads/backup` brings it back.
Never run `bd dolt push`, `bd sync`, or a `bd backup init` that points at
DoltHub or any hosted service. `dolt.local-only` is set, so a push is refused
anyway, and usage metrics are off.

**Why:** the developer wants the self-hosted option and no payments at all. A
hosted sync is a service, and a bill, nobody asked for.
