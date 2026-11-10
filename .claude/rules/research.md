# Research

The protocol, file formats and the main session's steps are in
`docs/research/README.md`; read it before writing a request or running one.
The rules:

## Research only what blocks

An agent commissions research only when the answer could change a decision it
must make before the current phase's next step. Everything else goes to
`docs/research/backlog.md`, to run when it does block. The agent writes
`docs/research/YYYY-MM-DD-<agent>-<slug>/request.md` and hands back; after the
findings, it writes `decision.md` (what it used, what it rejected, and why)
before it starts, and cites the research directory in what it produces.

**Why:** in an earlier project, most findings were never used by the decision
they fed, and every request held up the phase.

## Every question states what would change the decision

A request carries `Blocks:` in its header: the next step that waits for it.
Each question carries `Changes:`: the decision it feeds, and the answer that
would make the agent choose differently. A question that cannot fill `Changes:`
is curiosity, and goes to the backlog.

## Shallow is the default

- **Shallow:** one fact, checked in primary sources. The default.
- **Medium:** compare a named set of options. Without the names, it is Shallow.
- **Deep:** survey the whole space and look for counter-evidence. Only for a
  decision that will become an ADR, or when the developer asks.

The researcher treats the depth as a ceiling. A request holds questions of one
depth only.

**Why:** in an earlier project, 34 of 113 questions were asked Deep in one day,
and the findings ran to about 595 KB, far more than the decisions used.

## A budget

At most 4 open research requests per project, and at most 4 questions per
request. A request is open from `request.md` until its `findings.md` is saved.
Going over needs the developer's yes, asked once, with the requests ranked by
what they block. `majles lint` checks these rules.

## Only the main session starts the researcher

No agent has the `Agent` tool. An agent that needs research writes its requests
and hands back, naming their paths. The main session runs `majles lint` and
`majles research-find` (a match from another project within 90 days goes to the
researcher as prior findings to confirm, not redo), starts the researchers, and
saves each reply, **unedited**, as `findings.md`. Only the researcher searches
the web; the critic may spot-check a claim.

**Why:** this keeps one writer for `findings.md`, and the reply is saved as
the researcher gave it, by the one session that sees every request. Majles chose
it because a subagent reports back as text; whether a subagent in the current
Claude Code can write the file itself is not checked here, and the protocol does
not depend on it.

## Late answers are kept, and the research stands

Answers from the developer that arrive after research started are added to
`request.md`, dated and labelled late, and weighed in `decision.md`. Nobody
reverts them or reruns the research because of the timing.

## Deciding against the evidence is allowed; hiding it is not

A `decision.md` that goes against the findings says so and says why.

## Not research

Reading the repo, reading one documentation page to confirm a single behaviour
about to be relied on, and following an existing ADR. For the one page, label
the behaviour "unverified" and let the critic spot-check it.
