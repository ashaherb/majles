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
