# Majles decisions

Why the code looks the way it does. Newest last. An entry is never rewritten or
deleted; a later one supersedes it and says why.

Entries 1 to 4 were made before the first public commit and are restated here
from the pre-release log.

## 1. Apache 2.0

Problem. An open-source licence has to be chosen before the first public
commit, and changing it later needs every contributor's consent.

Choice. Apache 2.0. It is permissive, carries an explicit patent grant that
enterprise users look for, and keeps a paid enterprise layer possible later.
MIT was the alternative: simpler, but without the patent grant.

**Consequence:** contributions come in under the same licence (section 5), so
no separate contributor agreement is needed.

## 2. No telemetry in v0.1

Problem. Usage data would show which modules matter, but a tool that runs in
every session of someone's project has to earn trust before it asks for any.

Choice. v0.1 sends nothing. Any telemetry is a later release, opt-in and off
until the user says yes.

**Consequence:** the README can say plainly that Majles makes no network calls.
Adoption is measured from outside the tool until then: stars, downloads,
issues.

## 3. A project's CLAUDE.md and README.md ship from template/

Problem. The template's `CLAUDE.md` and `README.md` sat at the repo root, where
they doubled as the repo's own. A Claude Code session opened here read a setup
block telling it to set up a new project, and a visitor to the public repo
would have seen a page of placeholders.

Choice. They live in `template/`, and the manifest ships them to the project's
root (`once template/CLAUDE.md -> CLAUDE.md`). The root `CLAUDE.md` is
maintainer notes, and the root `README.md` is the public page.
`majles/test_template.py` fails if either is listed as shipped, or carries a
placeholder or a setup block.

**Consequence:** a project's lock file records these files by their
destination, so projects see no change. The other owned templates
(`.claude/settings.json`, `constraints.md`, `docs/direction.md`) stay at their
shipped paths, because they do no harm as this repo's own.

## 4. CI runs on Linux while the repo is private, then on macOS too

Problem. The tests need Python 3.10 to 3.13 on Linux and macOS. On a private
repo, a macOS minute costs ten Linux minutes from the monthly allowance. The
tests also need a real version matrix: `render_status.py` once held a Python
3.12-only f-string that no local run on 3.13 could catch.

Choice. One workflow, on ready pull requests only, matching
`.claude/rules/git.md`. It runs Python 3.10 to 3.13 on Linux always, and adds
macOS only when the repo is public, where Actions minutes are free. The switch
is an expression on `github.event.repository.private`, so going public needs no
edit. Each job also builds the wheel, installs it into a fresh virtual
environment and runs `majles new`.

**Consequence:** while private, macOS behaviour is checked only by local runs.

## 5. The studio module is not part of Majles

Problem. The `studio` module harvested reusable game code into one shared
repository on the author's machine. It assumed a particular way of working
across several games, which most users do not have.

Choice. It is not shipped. `majles enable` offers `ui`, `i18n`, `content`,
`ai`, `legal` and `beads`.

**Consequence:** sync would have deleted the studio files from a project that
had the module, since they left the manifest. `RETIRED` in `majles/cli.py`
names a retired module's files, and sync keeps them as the project's own
(detached) and turns the module off. Any module retired later goes in that list
too.

## 6. The name is Majles

Problem. The tool was named Majlis while it was being built. Before launch, the
maintainer settled on Majles, the same word ("the sitting"), spelled as it is said.

Choice. Majles everywhere: the package, the module, the `majles` command, the lock file
`.majles.json`, the shared rule `.claude/rules/majles.md`, the docs and these entries,
which were renamed in place because none of it had been released. The Arabic name,
مجلس, does not change.

**Consequence:** projects made under the earlier names keep working. The CLI reads
`.majlis.json` and `.boilerplate.json`, `majles migrate` converts them and the old
SessionStart hook, and the next sync moves the old rule file. The old name appears only
in that compatibility code, its tests, and the changelog.

## 7. CI proves the install against the built wheel, not PyPI

Problem. Launch needs `pipx install majles` and `uv tool install majles` to work on a
clean Linux, but nothing is on PyPI until launch day, and a check against PyPI would
test whatever is published, not the pull request.

Choice. One extra job, `install`, builds the sdist and wheel with `python -m build`,
installs the wheel with `pipx` and, separately, with `uv tool install`, each into
its own temp tool directory, then runs `.github/scripts/install_smoke.sh`: `majles --version`
and `majles new` in a temp folder, asserting the expected files exist. The sdist is
installed into a venv and checked the same way. It runs on Linux only, Python 3.12,
under the same ready-pull-request trigger as the tests.

**Consequence:** the check cannot catch a PyPI-side problem (metadata rendering, a
name clash). After the first release, one manual `pipx install majles` on a clean
machine covers that.

## 8. Adopt writes the template CLAUDE.md beside the project's own

Problem. `adopt` kept an existing `CLAUDE.md`, as it keeps every file a project owns,
so the template's setup block and sections never arrived and setup had nothing to fill
(issue #4).

Choice. The template goes beside it as `CLAUDE.majles.md`, and setup's first step
merges the two into `CLAUDE.md` and deletes the extra file. Replacing `CLAUDE.md` and
moving the old one aside was the alternative: the setup block would load at once, but
the project's own instructions would stop loading until setup ran.

**Consequence:** adopt still never overwrites a file the project owns. The setup
block does not load in an adopted project until the merge, so adopt ends by telling
the user to start setup from `SETUP.md`.

## 9. Every agent runs on Opus or Sonnet

Problem. The 100x-engineer was pinned to `model: fable` (issue #25). Fable is a
model Claude Code gates behind its own consent and usage limit, so not every plan
has it. What Claude Code does when a subagent's pinned model is not on the plan is
unverified: its settings say `fallbackModel` is tried when a model is "overloaded
or unavailable", but not whether that covers a subagent's pin.

Choice. The 100x-engineer runs on Opus, like the other agents that judge. The team
then needs only Opus and Sonnet, and nothing depends on unverified fallback
behaviour. Keeping Fable and documenting the fallback was the alternative: better
reviews for those who have it, and a silent downgrade or a failure for those who do
not.

**Consequence:** a test fails if any shipped agent pins a model other than `opus`
or `sonnet`. A user who has Fable detaches the agent and changes its `model:` line.

**Still open:** whether the 100x-engineer should go back to Fable once every plan
has it.

## 10. The secrets deny list names `.env` variants instead of `.env.*`

Problem. The template denied Claude's Read tool only `.env` and `.env.local` (issue #45),
and the obvious widening, `.env.*`, also denies `.env.example`. Deny rules win over allow
rules, and the template commits `.env.example` (its `.gitignore` keeps it) for agents to
read and edit.

Choice. The list names the usual variants (`.env`, `.env.local`, `.env.*.local`,
`.env.development`, `.env.production`, `.env.staging`, `.env.test`), plus `*.pem`, `*.key`
and service-account JSON, each at the root and in any folder. The agents rule and the
README say plainly that a deny rule stops only the Read tool, not a shell command.

**Consequence:** a variant not on the list, such as `.env.prod`, is not denied. A test
checks that the listed names are denied and `.env.example` is not. A project that keeps
no `.env.example` can switch to `.env.*` in its own settings.

## 11. Private names are checked by digest

Problem. The neutrality test named the private projects, products and accounts it
guards against, so the public repo listed them (issue #46).

Choice. Generic patterns (home paths, the maintainer's public account) stay written out.
Private names are kept only as the first 16 hex digits of a SHA-256 of the lowercased
word, and every word, and every run of words joined by `.` or `-`, in each file is hashed
and compared.

**Consequence:** the test file names nothing private, and a hit reports the line, not the
word. The digests hide the names from a reader, not from someone guessing and hashing
candidate words. Adding a name means computing its digest (the test's comment has the
command).

## 12. The board is never off quietly

Problem. Setup turned the `beads` module off when `bd` could not be installed, and
skipped the board view when Node was missing, then carried on (issue #54). The README
said so in passing. A user could end up without the board and never know, and the
board is one of Majles's core features. The maintainer, on 2026-11-10: "I hate it.
This needs to be vocal. The board is one of the most important features, If it's
disabled due to missing packages, the user needs to be aware of it and there should be
a path to enable it in the future."

Choice. The board is loud while it is off, and has one way back. Setup stops when
`bd`, Node 22 or beads-ui is missing, says what and why, gives the install commands,
and asks: install now, or continue without the board for now. It never decides for
the user. While the module is off, or `bd` or `bdui` is not on the `PATH`, the
session-start notice carries one line saying so, with `majles board`, on every session.
`majles board` checks all three, prints the install commands for macOS or Linux, and
turns the module on once `bd` is there. Keeping the board optional and silent, with
the README's note as the only signal, was the alternative: fewer lines at session
start, and a user who never learns what they lost.

**Consequence:** a project that declines the board hears about it at every session
until the board works; there is no switch to quiet it. The notice reads only the lock
and the `PATH` (no subprocess), so the hook stays inside its 10-second timeout, and it
stays silent while `SETUP.md` exists. `bd`'s pin and the queue setup lines live in both
`cli.py` and `SETUP.md`, and a test keeps them equal. No install line pipes a download
into a shell, since setup runs them through Claude: Node comes from Homebrew on macOS,
the distribution's package manager on Linux, or nodejs.org's download page on both, and
a test refuses a piped line.

**Still open:** whether a user who says no on purpose should be able to quiet the
notice. Closed by entry 13.

## 13. A no to the board is quiet, but not gone

Problem. Entry 12 left a user who declines the board on purpose hearing about it at
every session, with no way to quiet it.

Choice. The maintainer's, on 2026-11-10, word for word: "Quiet, but not gone: saying
no in setup, or `majles board --off`, records the choice. The notice then shows once a
week, not every session, and `majles board` still turns it on any time." The no is
`board_declined`, a date, in `.majles.json`, because it is the project's choice and
travels with the project to every clone. The date the weekly line last showed is
machine state that changes every week, so it goes in the git directory
(`majles-board-notice`), shared by worktrees and never in the working tree. A board
that is off because something is missing, with no recorded no, still shows every
session. `majles board --off` records only; `majles disable beads` removes the module.

**Consequence:** this supersedes entry 12's "there is no switch to quiet it". Without a
git directory there is nowhere to keep the last date, so the line shows every session
from the seventh day after the no; a stamp that cannot be read counts from the no; a
date that does not parse makes the line show every session. Too loud is the safe
failure. `majles board` deletes the no once `bd` is there.

## 14. Setup interviews in five rounds, and follows up only for a reason

Problem. Setup filled what it could from the description, then asked one batch of up to
20 questions, then at most two at a time (issue #55). A batch that size is hard to
answer well, and setup never showed what it had understood, so a wrong guess went
straight into the files. The maintainer, on 2026-11-10: "For Majles, I want the initial
setup to be more structured. It should ask followup questions if it needs".

Choice. Step 1 of `SETUP.md` is five short rounds, each headed "Round N of 5": the idea,
the product, the limits, the shape, the setup facts. Each round first shows what setup
understood from the description, for the developer to correct, then asks at most four
questions, as choices with Claude Code's question tool where the answers are obvious.
Every one of the 20 questions lands in exactly one round; where a round had more than
four, related ones are asked as one (standing constraints with the team and budget; the
interface, content and AI with one multiple choice). The setup facts round adds one
question that step 4 used to settle on its own: which GitHub account owns the repo and
which address commits. A follow-up is asked only when an answer is vague or
uncheckable, when two answers contradict, or when a wrong guess would be costly, and
setup says which; an answer still unsure after one follow-up becomes a labelled working
assumption. One summary comes last, and nothing is written until the developer confirms
it. Keeping the single batch and only adding the summary was the alternative: shorter,
and still a wall of questions.

**Consequence:** setup takes five exchanges at least, even for a full description, since
each round shows its understanding before going on. Tests keep the rounds at five, each
at most four questions, each of the 20 questions in exactly one round, and each
placeholder the interview fills in exactly one round. `asking.md` is unchanged: its
"at most two at a time" is for the team after setup, and setup's follow-ups keep it.

## 15. Every assumed limit is registered, cited, surfaced and reversible

Problem. Majles kept the developer's words and the decisions, but a limit an agent made
up while working ("never", "must", "only", "at most") went straight into a rule, an ADR,
a spec or a test, where it read as the developer's own. Nothing marked it, nobody asked
about it, and lifting it meant finding every place that enforced it. The maintainer, on
2026-11-11: such rules "slipped under the rag without any traceback"; make assumptions
"clear, visible, vocal and reversible".

Choice. Clear: `docs/assumptions.md`, a file the project owns, holds one entry per
assumed limit, `## A-N. The limit`, with `Status:` (assumed, confirmed, lifted),
`Assumed by:` with a date, `Why:`, `Costs the user:`, `Enforced in:`, `To lift:` and,
once answered, `Decided: d-N`. Entries with headings, not one table row each: eight
columns do not fit a phone, and the format matches `docs/direction.md`. Traceable: the
shared rule `assumptions.md` has every limit cite `d-N` or `A-N`, every code marker read
`ASSUMPTION(A-N: why)`, and every agent report end with `Assumptions I added:`.
`majles lint` fails on an `A-N` missing from the register or lifted, and on a malformed
entry; it warns on an uncited limit word in a project-written rule, ADR or spec, and on a
marker with no id, and `--strict` fails on those. Warning by default was chosen over
failing: four words are a blunt heuristic, every existing project would fail at once, and
the lint line already shows in every session. Majles's shared rules are exempt, since the
developer took them on with Majles and can detach one. Vocal: the session notice lists
the open entries with their age, and `majles assumptions` lists all by status. Visible:
both rendered pages gain "What we assumed for you" (the status page shows only the open
ones). Reversible: lifting records the developer's words as `d-N` and removes every place
in `Enforced in:` in one pull request; the entry stays.

**Consequence:** existing projects see lint warnings for uncited limits in their ADRs and
specs after sync, until each cites its source. The check is per paragraph, list item or
table row, so one citation covers a paragraph with several limits. `CHANGELOG.md` says so.

**Still open:** whether lint should fail by default once projects have cited their
existing limits; and whether tests and gate configs, which the rule covers, should be
traced by lint too.

## 16. A published GitHub Release uploads to PyPI, through Trusted Publishing

Problem. A local upload needs a long-lived PyPI token on one machine, and nothing
checks that the tag, the version and what was tested are the same thing.

Choice. `.github/workflows/release.yml` runs on `release: published` only. One `build` job
checks the tag against `__version__`, runs the tests and builds the sdist and wheel once;
two publish jobs upload that same artifact. A pre-release goes to TestPyPI (environment
`testpypi`), a full release to PyPI (environment `pypi`), split by the release's own
pre-release flag, which `build` also checks against the version. Each environment needs a
reviewer's approval. Trusted Publishing (OIDC) means no token is stored; `id-token: write`
is on the publish jobs only. Actions are pinned to commit SHAs.

**Consequence:** nothing is uploaded from a laptop; a mismatched tag fails before any
upload; the pinned SHAs are bumped by hand.

**Still open:** the first real run is the rc1 dry run to TestPyPI.

## 17. Skipping the setup questions skips the rounds, never the summary and its yes

Problem. In a trial run, a developer said "skip the questions, pick sensible defaults",
and the setup session took that as consent to everything: it wrote every file, then
created and pushed a GitHub repo, with no summary and no yes. `SETUP.md` said to write
nothing until the summary was confirmed, but had no path for a skip, so the summary went
with the rounds.

Choice. `SETUP.md` gives the skip its own steps: fill what can be derived, make every
other answer a labelled default (a limiting one listed with its `A-N`), show the same one
summary, and ask one yes before any file is written or anything is created. A partial
answer takes the same path. The summary ends with the account setup on its own lines
(owner, remote, email, visibility), and step 4 starts only after that yes. A lighter
path that skipped the summary when the developer asks for speed was rejected: the repo
and its owner are the one thing that is hard to take back.

**Consequence:** a developer who skips still answers one question. A test keeps the skip
section before the summary, the four account lines in it, and the yes before `gh repo
create`.

**Still open:** whether Phase 0 needs a lighter path for a developer who asked for
defaults. Opening it cost about $7 in the same run; the README and setup's last step now
say so, and agent behaviour is unchanged.
