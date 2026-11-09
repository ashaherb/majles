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
