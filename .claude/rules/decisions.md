# Recording decisions

Every settled decision is written down before the work continues. It goes in
exactly one of four places.

| Kind | Where | Written by | Changes by |
|---|---|---|---|
| Architecture: hard to reverse, shapes the system | `docs/adr/NNNN-*.md` | architect | a new ADR that supersedes it |
| What the user gets: the experience, a flow's behaviour | `docs/specs/*.md` | product | editing the spec in place |
| A choice made from research | `docs/research/<task>/decision.md` | the agent that asked | a new research task |
| How the team works | `.claude/rules/*.md` | the main session, at the developer's direction | editing the rule in place (shared rules: in the Majles repository, see `majles.md`) |

The developer's own words go in `docs/direction.md`, verbatim
(`.claude/rules/asking.md`). Records cite them; they never paraphrase them as
the developer's. A limit the team assumed, which the developer has not stated,
goes in `docs/assumptions.md` and is cited by its `A-N`
(`.claude/rules/assumptions.md`).

**Why:** a decision that lives only in a transcript gets silently reversed next
session. And a log that records every small thing stops being read.

## An ADR is for architecture only

It qualifies when it is expensive to reverse *and* later work builds on it: the
stack, the data store, the content model, hosting, auth, the i18n/RTL
architecture, a dependency the architecture rests on. Process, tooling, file
layout, naming, agent config and documentation structure are rules, not ADRs.
What the user sees, hears or can do is a spec, not an ADR. Expect a handful
per slice; `majles lint` flags more than five. When unsure, it is not an ADR.

An ADR that limits what the user gets (what the product may say, show or do
for them) states what the user loses, and needs the developer's yes before it
is accepted.

A fix found by review is never an ADR. It goes in the commit message. If the
fix changes which option an existing ADR chose, write a new ADR that supersedes
it; otherwise there is no ADR.

**Why:** the ADR log is where the developer goes for insight into how the system
came to be. Process entries bury that signal fast. And in an earlier project,
the experience was decided in append-only ADRs (the shape of every lesson,
what the model could say), which made the product rigid exactly where it had
to be easiest to change; the project wrote 58 ADRs in six days.

## ADRs are append-only; rules and specs are living

Never edit or delete an accepted ADR. Supersede it with a new one saying what
changed and why. Rules, specs, READMEs and `CLAUDE.md` are edited in place, and
the commit message says what changed and why.

**Why:** an architecture decision's history is the insight. A rule's or a
spec's history is noise, and git keeps it anyway.

## Commit the record with the change

An ADR, spec, research decision or rule change goes in the same commit as the
code or docs it explains. If the decision comes before the code, commit it
alone.

## One orientation document

`CLAUDE.md` is the only orientation and status document. Do not create a
`DECISIONS.md`, `HANDOFF.md`, `KICKOFF.md` or similar.
`docs/direction.md` (the developer's words) and `docs/architecture.md` (the
architect's C4 view of what is built) are sources, not orientation.

**Why:** in an earlier project, each of these turned into a partial copy of
`CLAUDE.md` that went stale. One held the only full copy of the MVP, in a file no
agent read.

## Publish the rendered pages

After any new ADR, research decision or rule change, regenerate the decision log
with `python3 tools/render_decisions.py <out.html>` and publish it to the same
Artifact URL, never a new one. At each milestone, regenerate the status page
with `python3 tools/render_status.py <out.html> --decisions-url <log URL>` and
publish it, with the screenshot files it lists, to its own stable URL. Both
URLs are recorded at the end of `CLAUDE.md`. Never hand-edit the HTML.
Where `CLAUDE.md` records file paths instead (`docs/status/*.html`, for a
project without Artifacts), render to those paths; that is the publishing.

**Why:** if the pages are generated from the repo, they cannot drift from it.
The decision log is too long to answer "where are we?"; the status page answers
it in the developer's terms, with the real screens.
