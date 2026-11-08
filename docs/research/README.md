# Research

Research on this project runs when its answer can change a decision the next
step waits on, and every choice made from it is written down. This directory
holds both, and the backlog of questions that do not block yet. The rules and
their reasoning are in `.claude/rules/research.md`.

## The rule

An agent commissions research only when the answer could change a decision it
must make before the current phase's next step. Everything else goes to
`backlog.md`. When research does run, the agent does not start the work it
feeds until it has:

1. written a research request here, with what it blocks and what would change
   the decision,
2. received the researcher's findings, and
3. written down which findings it used, which it rejected, and why.

Reading the repo, reading one documentation page to confirm a single behaviour,
following an existing ADR, bug fixes and copy edits are not research. For the
one page, ask for a Shallow request, or state the behaviour labelled
"unverified" and let the critic spot-check it.

**The budget:** at most 4 open requests per project, and at most 4 questions per
request. A request is open until its `findings.md` is saved. Going over needs
the developer's yes, asked once, with the requests ranked by what they block.

`majlis lint` checks open requests against this page.

## One directory per research task

```
docs/research/
  backlog.md       questions that do not block yet; any agent appends
  2026-09-28-designer-type-and-colour/
    request.md     written by the requesting agent
    findings.md    the researcher's reply, saved unedited by the main session
    decision.md    written by the requesting agent
```

Named `YYYY-MM-DD-<requester>-<slug>`, so the list sorts by date and two agents
working in parallel can never pick the same name.

**Ownership here is per file, not per directory.** Everywhere else in the repo one
agent writes to a directory (`.claude/rules/ownership.md`). Here, three files in one directory have
three fixed writers by role, because a reader needs the question, the evidence and
the reasoning side by side. The invariant that rule protects still holds: no two
agents ever write the same file. `backlog.md` is the exception: append-only, and
any agent may append.

## Depth

The requester sets **one depth per request**. Questions of different depths go
in separate requests, so a Shallow answer never waits for a Deep one. Pick the
depth by the cost of being wrong, not by how interesting the question is.
**Shallow is the default.**

| Depth | Use it for | The researcher | You get back | Ceiling |
|---|---|---|---|---|
| **Shallow** | One fact the decision hinges on. Does X support Y? What does it cost? Is it maintained? | Checks primary sources only: official docs, changelog, pricing page: and confirms they are current. No survey of alternatives. | A direct answer, one to three dated sources, a confidence level. | 250 words per question |
| **Medium** | Choosing between options you can already name. Name them in the request. | Compares the named options against the constraints you stated, using primary sources plus evidence of real-world use. Adds an option only if one is clearly missing. | A tradeoff table, evidence for each option, confidence, what was not determined. | 800 words per question |
| **Deep** | Only a decision that will become an ADR (expensive to reverse, and later work builds on it), or when the developer asks for it. | Surveys beyond the options you named. Hunts counter-evidence: failure reports, migrations away, open issues. Checks the product-specific concerns that `CLAUDE.md` and the rules call out. Looks for production examples. | Everything Medium gives, plus options you did not name, known failure modes, open questions, and what observation would change the answer. | 2,000 words per question |

The depth is a ceiling, not a target. The researcher answers each question's
`Changes:` bar first and stops when it is answered. If it thinks a depth was
too shallow, it answers at the depth asked for and says why in a depth note.
Asking again is your call.

## Reuse before research

Before starting a researcher, the main session searches every project's
research:

```bash
majlis research-find <words...>
```

It lists matching requests and decisions, newest first, and marks those older
than 90 days `stale`. A match from another project within 90 days goes to the
researcher as prior findings, with the instruction to confirm what changed since
rather than start over. The findings name it in their header.

## How the loop runs

1. **The requesting agent** writes `request.md`, one directory per request,
   then stops and hands back to the main session with the paths, and with any
   questions it has for the developer.
2. **The main session** puts those questions to the developer first. A request
   whose questions could change what it asks waits for the answers; the
   requesting agent records them in the request before research starts. A
   request no question touches may start at once.
3. **The main session** runs `majlis lint`, checks the budget, and runs
   `majlis research-find` for each request.
4. **The main session** starts a `researcher` per request, in parallel when
   they are independent, and saves each reply, unedited, as `findings.md`.
5. **The main session** resumes the requesting agent, with its context intact.
6. **The requesting agent** reads `findings.md`, writes `decision.md`, and only
   then does the work, citing the research directory in what it produces.

Why it runs through the main session: Claude Code does not let a subagent write
report files, so the researcher returns its findings as text, and agents cannot
start other agents (`.claude/rules/research.md`).

### When the developer's answers arrive after research has started

This happens: a team asks questions and researches in parallel. Keep both. Never
revert the answers, and never rerun research just because an answer came late.

- The requesting agent adds the answers to `request.md` under **The developer's
  answers**, dated, and says whether they came before research ran or after the
  findings were written. It adds; it does not rewrite the original questions,
  because the findings answer those.
- `findings.md` stays as it is.
- `decision.md` weighs each late answer against the findings, in its own
  section. Where the findings do not cover an answer, it says so. It writes a
  follow-up request only if the gap would change the decision.

## The backlog

`backlog.md` holds the questions that do not block the current phase's next
step. Writing one down there instead of researching it is the normal case, not
a failure: most questions become answerable, or stop mattering, once something
runs.

Any agent appends an entry, one per line:

```markdown
- YYYY-MM-DD, <agent>: <the question>. Needed before: <the phase or event
  that makes it blocking>. Depth when it runs: <Shallow | Medium | Deep>.
```

- Agents append; nobody edits or deletes another agent's entry.
- At each phase gate, the main session shows the developer the entries whose
  "Needed before" has arrived. Those become requests under the normal budget.
- An entry that is run gets ` (run: docs/research/<task>/)` appended to its
  line.

## request.md

```markdown
# Research request: <the decision this feeds>

Requested by: <agent>
Date: YYYY-MM-DD
Depth: Shallow | Medium | Deep
Blocks: <the next step that waits for this>
Feeds: <what will be produced: ADR, spec, design file, content>

## The decision I have to make

One paragraph. What is being chosen, and why it matters now.

## What I already believe

My current assumptions, stated so the research can confirm or break them.

## Constraints the answer must respect

The non-negotiables from CLAUDE.md that bear on this, and any earlier ADR.

## The developer's answers (added YYYY-MM-DD, before research ran | after the findings were written)

Only when the developer answered questions about this request. Added, never
edited into the sections above.

## Questions

At most 4.

### Q1. <the question>

Changes: <the decision this feeds, and the answer that would make me choose
differently>.

What a good answer lets me do. For Medium, the options to compare.
```

`Depth:` holds one word. A question that cannot fill `Changes:` goes to the
backlog instead.

## findings.md

```markdown
# Findings: <title>

Researched by: researcher
Saved by: main session, from the researcher's reply, unedited
Date: YYYY-MM-DD
Prior findings: <path> | none

## Summary

Q1: flips | holds | not determined
Q2: ...

One line per question, measured against its `Changes:` line: "flips" means the
answer is the one that changes the decision. Then what the requester most
needs to know, most important first, in three to five lines.

## Q1. <the question>

### Answer
### Options            (Medium and Deep: a tradeoff table)
### Evidence           (source, what it says, version, date accessed)
### Confidence         (high / medium / low, and why)
### Against            (counter-evidence, failure reports, what would change this)
### Not determined     (including anything cut to stay under the ceiling)

## Researcher's reading

How the evidence bears on this project's constraints. Labelled as opinion, and
kept separate from the evidence so the requester can disagree without redoing
the work.

## Depth note

Only when a question needed more depth than was requested, or had no
`Changes:` line, and why.
```

Each question's section stays under its depth's ceiling. Anything cut for
length is named in "Not determined".

## decision.md

```markdown
# Decision: <what was decided, as a claim>

Decided by: <agent>
Date: YYYY-MM-DD
Based on: findings.md

## What I took from the findings

## What I rejected from the findings, and why

## Where I went against the evidence, and why

Omit only if there is nothing here. Deciding against the evidence is allowed.
Doing it without saying so is not.

## Answers that arrived after the findings

Only when there were any. Each answer, what the findings say about it, and any
gap. A follow-up request only if the gap changes the decision.

## The decision

## What this feeds

The ADR, spec, design file or content that now depends on this.
```
