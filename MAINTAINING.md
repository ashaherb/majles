# Maintaining Majles

The starting point for every new product. It provides an
agent team (architect, product, designer, builder, tester, critic, security,
ops, researcher), a research protocol that runs only what blocks, working rules, and an architecture decision
log with a published page generated from the repo. There is no stack and no
product code; those are the first decisions of each project.

It is also how projects stay current. The files a project *shares* with the
template are updated by one reviewed command. Everything else belongs to the
project.

## Starting a new project

```bash
export MAJLES_ROOT=~/projects       # where your projects live; default: the current directory
majles new <project-slug>           # creates $MAJLES_ROOT/<project-slug>
cd "$MAJLES_ROOT/<project-slug>"
claude
```

The projects root is `--root` if given, else `$MAJLES_ROOT`, else the current
directory. `new`, `sync --all` and `research-find` use it. A path given to `new`
that contains a slash, or is absolute, is used as is. The project's name, the
slug or the path's last part, must be lowercase letters and digits with single
hyphens between words; `new` refuses anything else before it writes a file.

Then say **"set up this project"** and describe it, in as much or as little
detail as you have. Claude shows what it understood from what you said, asks
for the rest in five short rounds, confirms one summary with you, and does the
setup below.

`majles new` copies only what a project ships with. This file, `majles/`
and `optional/` stay here. It also writes `.majles.json`, which records what
the project received, and is how it stays in step with the template later.

Install `majles` with `pipx install majles` or `uv tool install majles` (or
`pip install .` from a checkout). Installed, it carries the template for its own version and records
that version in `.majles.json`. To track `main` instead, run it from a checkout
of this repository: put a `majles` on your PATH that runs `python3 -m majles`
from it (for example a one-line shell script), or run `python3 -m majles` from
the checkout itself. Run from a checkout, it reads the checkout's committed
HEAD and records the commit. The SessionStart hook calls `majles check`, and
stays silent when `majles` is not on PATH.

## Keeping projects up to date

A project **shares** the agents, most rules, the `docs/` READMEs and the
renderer with the template. It **owns** `CLAUDE.md`, `README.md`,
`constraints.md`, its settings, and anything it creates.
`majles/manifest.txt` is the full list.

When the template changes, each project's next session opens with a notice
that updates are available. Nothing changes until you ask:

```bash
majles sync                  # preview this project's update: what changes, +/- lines
majles sync --diff           # the same, with full diffs
majles sync --apply          # write it; then review with git diff, commit on a branch, open a PR
majles sync --all            # preview every project under the projects root
majles sync --all --apply    # update them all; each still needs its own commit
```

If a project has edited a shared file, sync reports a **conflict** and leaves
that file alone, while everything else still updates. Resolve it one of two
ways:

- `--take <path>` replaces the project's edit with the template's version.
- `majles detach <path>` makes the file the project's own, and sync skips it
  from then on.

The project's recorded version does not advance while a conflict stands, so the
notice keeps appearing until the conflict is resolved.

Sync only reaches projects that have a `.majles.json`. A project without one
is never touched.

When the template renames a shared file, sync moves it: the old path is removed
and the new one written, provided the project had not edited it. An edited one
is a conflict, resolved the same way.

### Projects made before the rename

Projects made under Majles's earlier name have the lock file under that name,
and a SessionStart hook that calls the old script by path. The CLI still reads
the old lock file when `.majles.json` is missing, and `check` says so. To move
a project over:

```bash
majles migrate [project]   # renames the lock file, and rewrites the old SessionStart hook
majles sync --apply        # moves the renamed rule to .claude/rules/majles.md
```

## Checking research and ADRs

```bash
majles lint [project] [--strict]   # read only; exit 0 when clean, 1 otherwise
majles assumptions [project]       # the register, by status, with each open one's age
majles research-find <words...>    # earlier research in every project, newest first
```

`lint` checks the research rules a script can check. Every open request (a
`request.md` with no `findings.md` yet) needs `Depth:` and `Blocks:` in its
header, one depth, at most 4 questions, and a `Changes:` line under each. There
are at most 4 open requests. Every task with findings has a `decision.md`.
Every ADR has a `Status:` and a `Research:` line, and an accepted one dated
after 2026-10-22 has `Needed by: slice N`, and no slice needs more than five.
`CLAUDE.md` should not still carry the Phase 0 brief once an ADR is accepted,
and stays under 16 KB, with no rule over 5 KB, since both go with every agent
call. And in a clone with `.githooks/pre-push`, `core.hooksPath` points at it. Completed research is
only checked for its `decision.md`, so a project that predates these rules is
not flooded with findings about work already done.

`lint` also traces each limit to its source (`.claude/rules/assumptions.md`,
`DECISIONS.md` entry 15). A cited `A-N` must be an entry in `docs/assumptions.md`
that is not lifted, and each entry needs `Status:` (assumed, confirmed or lifted),
`Assumed by:` with a date, `Why:`, `Costs the user:`, `Enforced in:` and
`To lift:`, plus `Decided: d-N` once confirmed or lifted; anything else fails.
Two things only warn, and fail under `--strict`: a paragraph, list item or table
row that says "never", "must", "only" or "at most" and cites no `d-N` or `A-N`,
in a rule the project wrote, an ADR or a spec; and an `ASSUMPTION(` marker with
no `A-N`. Code fences, headings and `**Why:**` paragraphs are skipped; so are
Majles's shared rules, and limits altogether while `SETUP.md` is there. Markers
are found with `git grep` over files git tracks or would track, leaving out
Markdown and `.claude/`. The heuristic is four words on purpose: a false alarm
costs one citation, and a cleverer one would be harder to predict.

The session-start hook runs `lint` too, and adds one line to its notice when it
finds anything. Existing projects get this without changing their settings,
because the hook already calls `majles check`.

The board is never off quietly (`DECISIONS.md`, entry 12). While the beads module
is off, or `bd` or `bdui` is not on the `PATH`, the notice carries one more line
naming what is off, with `majles board`. That line looks only at the lock and the
`PATH`, so the hook stays fast, and stays silent while `SETUP.md` is still there.
`majles board` does the full check: `bd` and its version, Node 22 or later, and
beads-ui, each with its install commands for macOS or Linux, and it turns the
beads module on once `bd` is there. It exits 0 only when the whole board works.
`majles board --off` records a no on purpose as `board_declined`, a date, in the
lock (entry 13); with it, the line shows once every 7 days. The date it last showed
is `majles-board-notice` in the git directory, shared by worktrees and never in the
working tree. `majles board` deletes the no once `bd` is there.

The notice also lists every assumption still `assumed` in `docs/assumptions.md`,
oldest first with its age in days, at most five by name and the rest as a count.
It reads only that file.
`BD_VERSION` and `QUEUE_SETUP` in `cli.py` must match `template/SETUP.md`; a test
in `test_template.py` fails when they drift.

`research-find` searches the request titles and "The decision" sections of every
project under the projects root, case-insensitively, for all the words given. Matches
older than 90 days are marked `stale`. The main session runs it before starting
any researcher (`.claude/rules/research.md`).

## Bringing an existing project in

```bash
majles adopt <project> --modules core,ui,i18n,content              # dry run
majles adopt <project> --modules core,ui,i18n,content --apply
```

Adoption sets every shared file to the template's version, adding missing
ones and replacing ones that differ. It never overwrites a file the project
owns. The dry run lists each replacement. Before applying, move anything
project-specific out of those files and into ones the project owns
(`CLAUDE.md`, `constraints.md`, `content/README.md`), or it is lost. The project
is a git repo, so `git diff` shows exactly what adoption changed.

A project's own `CLAUDE.md` is kept, and the template goes beside it as
`CLAUDE.majles.md`; setup merges the two (`SETUP.md`, "An adopted project").
For a kept `.gitignore` and `README.md`, adopt lists the template's patterns and
sections each one lacks. Then say "set up this project from SETUP.md" in Claude.

## What setup does

The setup procedure ships with every project as `SETUP.md` (its source is
`template/SETUP.md`), so a project made from the installed package has it too. The
template `CLAUDE.md` points a new session at it, and setup deletes it when done.

## What is in here

```
MAINTAINING.md            this guide; stays here
majles/cli.py             new, adopt, enable, disable, sync, check, board,
                          detach, lint, assumptions, research-find, migrate;
                          `python3 -m majles`
majles/manifest.txt       every shipped file, as shared or once, by module
majles/test_*.py          tests for the CLI, and checks on the template itself
.githooks/pre-push        refuses pushes to main, then runs pre-push.local
template/CLAUDE.md        template: the product, the MVP, the current phase
template/README.md        template: what it is, and how to run, test and deploy
template/SETUP.md         template: the setup procedure; setup deletes it
CLAUDE.md, README.md      this repo's own, for its maintainers and visitors;
                          never shipped
LICENSE, DECISIONS.md     this repo's own; never shipped
pyproject.toml, setup.py  the package; setup.py copies the manifest's files into
                          the wheel under majles/template/
CHANGELOG.md              what changes in a project at each release
.claude/agents/           architect, product, designer, builder, tester, critic,
                          security, ops, researcher
.claude/rules/            decisions, done, asking, assumptions, tokens,
                          code-organization, ownership, research, agents,
                          working-style, git, majles (shared); constraints,
                          git-account (template)
.claude/settings.json     template: the fallback model, the read-deny for secret
                          files, and the update-notice hook
docs/                     adr, specs, reviews, security, research and status, each
                          with its README; research/backlog.md, direction.md and
                          assumptions.md (templates)
ops/                      deployment, monitoring, backups and runbooks (ops)
design/                   the design system, once researched (ui module)
plan/                     the developer's business plan
tools/render_decisions.py builds the published decision log, with tests
tools/render_status.py    builds the published status page, with tests
optional/i18n/            languages and right-to-left module
optional/content/         editor agent and content/README.md template
optional/ai/              ai agent, its rule and evals/README.md, for products that call a model
optional/legal/           legal agent and docs/legal/README.md
optional/beads/           the work-queue rule, for Beads (bd) and its local board
```

## Changing the template

Make the change on a branch, open a pull request, and merge it. Projects
receive it the next time they sync. Sync reads the committed HEAD of the
checkout `majles` runs from, so keep that checkout on `main` and pull it after
each merge. Projects on the installed package receive it at the next release.

To release, bump `__version__` in `majles/__init__.py`, add a `CHANGELOG.md`
entry that says what changes in a project, and build with
`python3 -m pip wheel . --no-deps -w dist`. The wheel holds only the files
the manifest lists, so a file missing from the manifest never ships.

`__version__` is the only place the version is written: `pyproject.toml` reads
it, and so do `majles --version` and the lock of a project made from the
package. A tag is `v` plus that string, so the tag `v0.1.0rc1` goes on the
commit where `majles --version` prints `majles 0.1.0rc1`. Check that before
tagging.

Until `0.1.0` is on PyPI, `pipx install majles` gets the `0.0.1` placeholder:
pipx and uv skip a release candidate unless asked for one, so uploading
`0.1.0rc1` would not change that. The README's status banner and its
"Installing before 0.1.0" section say so, and stay until the upload. The upload
and the banner's removal are one step on launch day, in this order:

1. One pull request: set `__version__ = "0.1.0"`, change the `CHANGELOG.md`
   heading from "not out yet" to the date, and delete the README's status
   banner and its "Installing before 0.1.0" section. `test_template.py` fails
   if the banner and the version disagree, so neither can go in alone.
2. Merge it. On `main`, check that `majles --version` prints `majles 0.1.0`,
   tag that commit `v0.1.0`, build the wheel, and upload it to PyPI, at once,
   so `main` never says more than PyPI holds for longer than the upload takes.
3. On a clean machine, `pipx install majles` and `majles --version` print
   `majles 0.1.0`. If the upload failed, revert the pull request before
   anything else; the banner comes back with it.

Once its `majles` is upgraded, a project made from `0.1.0rc1` sees the update
notice at its next session, like any release.

Keep every shared file product-neutral and free of placeholders. A fact about a
specific product belongs in a file the project owns. A behaviour only some
projects need belongs in a module.

To add a file, put it in `majles/manifest.txt` under the right module, as
`shared` or `once`. Before committing, run:

```bash
python3 -m unittest discover -s majles -p 'test_*.py'
python3 -m unittest tools/test_render_decisions.py tools/test_render_status.py
```

`test_template.py` fails in any of these cases:

- a file is missing from the manifest;
- a shared file contains a placeholder;
- a placeholder is not documented in this guide;
- a product-specific word appears in a shipped file;
- a personal path or account, or a private name, appears anywhere outside the
  compatibility code. Private names are listed only by digest, so the public
  test does not name them; its comment says how to add one.
