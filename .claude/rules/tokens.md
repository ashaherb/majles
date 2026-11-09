# Tokens go into the work

Every model call re-sends everything the agent has seen, so cost is calls ×
context size. A call late in a long run costs many times one early in it, for
the same work.

## Short-lived agents, one narrow task each

An agent gets one task it can finish in about 150 calls. A bigger task is split
before briefing, or the agent stops at a coherent point, commits, and hands over
a short note (what is done, what is next, which files) for a fresh agent. No
agent runs for a whole slice. Never resume an agent whose context is already
large when a fresh one with a note would do.

## Short reports

An agent's report is under about 300 words: what changed, the evidence, what is
open. The detail is in its commits and files. The main session reads reports,
never transcripts.

## Long output stays out of context

- Tests, lint, type checks and builds: show the failures and the summary line
  only, never the full run. Rerun one failing file, not the suite, while fixing.
- Logs: grep for the event; never print the file.
- Files: grep first, read by line range; read a whole file only when the whole
  file is the task.

## A fresh main session at each milestone

When a milestone lands, the main session makes sure the status and **Next:** in
`CLAUDE.md` and the status page are current, then tells the developer it is a
good point to start a fresh session. Nothing that matters lives only in the
conversation.

## Short standing instructions

`CLAUDE.md` and these rules go with every call of every agent. They hold only
what every agent needs on every task: the product, the non-negotiables, the
current slice and status, and how we work. Plans for later slices, history and
detail live in `docs/` and are read when needed. Finished work is in git, not
in **Next:**. `majles lint` flags a `CLAUDE.md` over 16 KB and a rule over 5 KB.

**Why:** in an earlier project, measured over one day: 109 agents, about 21,000
calls. One builder ran 3,060 calls at about 500,000 tokens of context each, 23%
of the day alone; the main session ran at about 390,000 tokens per call; and
about 23,000 tokens of standing instructions went with every call.
