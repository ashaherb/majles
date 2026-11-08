# Majlis decisions

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

**Consequence:** the README can say plainly that Majlis makes no network calls.
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
`majlis/test_template.py` fails if either is listed as shipped, or carries a
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
environment and runs `majlis new`.

**Consequence:** while private, macOS behaviour is checked only by local runs.

## 5. The studio module is not part of Majlis

Problem. The `studio` module harvested reusable game code into one shared
repository on the author's machine. It assumed a particular way of working
across several games, which most users do not have.

Choice. It is not shipped. `majlis enable` offers `ui`, `i18n`, `content`,
`ai`, `legal` and `beads`.

**Consequence:** sync would have deleted the studio files from a project that
had the module, since they left the manifest. `RETIRED` in `majlis/cli.py`
names a retired module's files, and sync keeps them as the project's own
(detached) and turns the module off. Any module retired later goes in that list
too.
