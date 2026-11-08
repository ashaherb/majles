# Who writes where

## One writer per directory

| Directory | Written by | Holds |
|---|---|---|
| `docs/adr/` | architect | Architecture decision records |
| `docs/architecture.md` | architect | The C4 view of what is built, once there is code |
| `docs/phases.md` | architect | The plan for slices beyond the next two, which the developer approves |
| `docs/specs/` | product | One spec per user flow |
| `docs/direction.md` | main session | The developer's words, verbatim and dated |
| `docs/status/` | main session | The status page's inputs: the TLDR, now and next, what waits on the developer, spend, screenshots |
| the tester's folder, in the builder's home | tester | Acceptance and end-to-end tests, and each slice's exit test |
| `docs/reviews/` | critic | One review per phase gate |
| `docs/engineering/` | 100x-engineer | Specs for the builder: changes with a visible payoff and their evidence |
| `docs/security/` | security | The threat model, and one review per slice that touched a sensitive area |
| `docs/research/` | per file, see below | One directory per research task |
| `design/` | designer | The design system, once researched (projects with a UI) |
| `content/` | editor | The product's core content (content module only) |
| `evals/` | ai | Eval sets, rubrics and results (ai module only) |
| `docs/legal/` | legal | Obligations register, questions for counsel, drafts (legal module only) |
| `ops/`, the CI directory (for example `.github/workflows/`), and `.githooks/pre-push.local` | ops | Deployment, environments, monitoring, backups, runbooks, and the project's pre-push checks |
| `plan/` | the developer | Startup plan, phases, distribution, money |
| `tools/` | anyone | Standalone scripts with no product dependency |
| `.claude/rules/` | main session, at the developer's direction | These rules; shared ones change in the Majlis repository |

Read a directory's `README.md` before writing there. An agent asked to write
outside its own directory says so and stops. A new top-level directory needs a
`README.md` naming its owner before anything goes in it.

**Why:** agents cannot see each other's sessions. Two agents editing one file
overwrite each other's reasoning silently, with no review step to catch it.

## docs/research/ is owned per file

In each task directory, the requesting agent writes `request.md` and
`decision.md`. The main session writes `findings.md`: the researcher's reply,
unedited.

`docs/research/backlog.md` is append-only, and any agent may append. Nobody
edits or deletes another agent's entry; the only change to an existing line is
the ` (run: ...)` mark when it is researched.

**Why:** a reader needs the question, the evidence and the reasoning side by
side. The invariant that matters still holds: no two agents write the same file,
except the backlog, where nobody rewrites a line another agent wrote.

## Some roles own one folder inside the builder's home

Where a role's files must live in the stack's source tree, that role owns one
named folder there, and the builder uses it without editing it. The project
records each folder in a rule file it owns, once the stack ADR exists. A missing
value goes to the folder's owner as a request; a missing hook in the code goes
from the owner to the builder.

- **designer:** the design tokens, when the stack can only load visual resources
  from its own source tree.
- **tester:** acceptance and end-to-end tests, and each slice's exit test.
- **ai** (ai module only): the prompts the product sends to a model.

**Why:** one copy of the tokens, in the format the stack reads, cannot drift. A
source in `design/` mirrored into the source tree needs a generator and a
staleness check to stay true. And a test the builder can edit can be made to
pass by changing the test.

## No app/ directory until the stack ADR exists

Builder's home is whatever the stack ADR decides.

**Why:** creating a source directory now pre-commits the framework choice before
the architect has made it.

## The 100x-engineer may touch anything

It owns `docs/engineering/`, and it may change any file when that is the
fastest safe way to an improvement, saying so in its report. Its default is a
spec the builder carries out.

**Why:** debt that crosses every module needs one reviewer who can see all of
it. Writing it down for the builder keeps each folder's owner the one who
changes it.
