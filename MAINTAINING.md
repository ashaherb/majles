# Maintaining Majlis

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
export MAJLIS_ROOT=~/projects       # where your projects live; default: the current directory
majlis new <project-slug>           # creates $MAJLIS_ROOT/<project-slug>
cd "$MAJLIS_ROOT/<project-slug>"
claude
```

The projects root is `--root` if given, else `$MAJLIS_ROOT`, else the current
directory. `new`, `sync --all` and `research-find` use it. A path given to `new`
that contains a slash, or is absolute, is used as is.

Then say **"set up this project"** and describe it, in as much or as little
detail as you have. Claude fills in what it can from what you said, asks one
batch of questions for the rest, and does the setup below.

`majlis new` copies only what a project ships with. This file, `majlis/`
and `optional/` stay here. It also writes `.majlis.json`, which records what
the project received, and is how it stays in step with the template later.

Install `majlis` with `pipx install majlis` (or `pip install .` from a
checkout). Installed, it carries the template for its own version and records
that version in `.majlis.json`. To track `main` instead, run it from a checkout
of this repository: put a `majlis` on your PATH that runs `python3 -m majlis`
from it (for example a one-line shell script), or run `python3 -m majlis` from
the checkout itself. Run from a checkout, it reads the checkout's committed
HEAD and records the commit. The SessionStart hook calls `majlis check`, and
stays silent when `majlis` is not on PATH.

## Keeping projects up to date

A project **shares** the agents, most rules, the `docs/` READMEs and the
renderer with the template. It **owns** `CLAUDE.md`, `README.md`,
`constraints.md`, its settings, and anything it creates.
`majlis/manifest.txt` is the full list.

When the template changes, each project's next session opens with a notice
that updates are available. Nothing changes until you ask:

```bash
majlis sync                  # preview this project's update: what changes, +/- lines
majlis sync --diff           # the same, with full diffs
majlis sync --apply          # write it; then review with git diff, commit on a branch, open a PR
majlis sync --all            # preview every project under the projects root
majlis sync --all --apply    # update them all; each still needs its own commit
```

If a project has edited a shared file, sync reports a **conflict** and leaves
that file alone, while everything else still updates. Resolve it one of two
ways:

- `--take <path>` replaces the project's edit with the template's version.
- `majlis detach <path>` makes the file the project's own, and sync skips it
  from then on.

The project's recorded version does not advance while a conflict stands, so the
notice keeps appearing until the conflict is resolved.

Sync only reaches projects that have a `.majlis.json`. A project without one
is never touched.

When the template renames a shared file, sync moves it: the old path is removed
and the new one written, provided the project had not edited it. An edited one
is a conflict, resolved the same way.

### Projects made before the rename

Projects made under Majlis's earlier name have the lock file under that name,
and a SessionStart hook that calls the old script by path. The CLI still reads
the old lock file when `.majlis.json` is missing, and `check` says so. To move
a project over:

```bash
majlis migrate [project]   # renames the lock file, and rewrites the old SessionStart hook
majlis sync --apply        # moves the renamed rule to .claude/rules/majlis.md
```

## Checking research and ADRs

```bash
majlis lint [project]              # read only; exit 0 when clean, 1 otherwise
majlis research-find <words...>    # earlier research in every project, newest first
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

The session-start hook runs `lint` too, and adds one line to its notice when it
finds anything. Existing projects get this without changing their settings,
because the hook already calls `majlis check`.

`research-find` searches the request titles and "The decision" sections of every
project under the projects root, case-insensitively, for all the words given. Matches
older than 90 days are marked `stale`. The main session runs it before starting
any researcher (`.claude/rules/research.md`).

## Bringing an existing project in

```bash
majlis adopt <project> --modules core,ui,i18n,content              # dry run
majlis adopt <project> --modules core,ui,i18n,content --apply
```

Adoption sets every shared file to the template's version, adding missing
ones and replacing ones that differ. It never overwrites a file the project
owns. The dry run lists each replacement. Before applying, move anything
project-specific out of those files and into ones the project owns
(`CLAUDE.md`, `constraints.md`, `content/README.md`), or it is lost. The project
is a git repo, so `git diff` shows exactly what adoption changed.

## What setup does

This section is Claude's procedure. Follow it in order.

### 1. Interview

From the developer's description, fill as many of the answers below as can be
derived. Then ask **one batch** of questions: for what is missing, and for
anything guessed where a wrong guess would be costly. Never ask for what the
description already says.

| # | Question | Fills |
|---|---|---|
| 1 | What is it, in a paragraph? | `ONE_PARAGRAPH_DESCRIPTION` |
| 2 | What is it called, and is the name settled? | `PROJECT_NAME`, `NAME_STATUS`, and the name rule in `constraints.md` |
| 3 | Directory and repo name? Default: the slug given to `majlis new` | `REPO_SLUG` |
| 4 | The one-line thesis: why it should exist, and what it refuses to be? | `THESIS` |
| 5 | Who is it for? What do they know, how do they arrive, how long do they give it? | `WHO_IT_IS_FOR` |
| 6 | What must never be compromised? | `NON_NEGOTIABLES`, each marked as the developer's words or drafted |
| 7 | What is the core loop, the one thing a user does? | `CORE_LOOP`, `CORE_FLOWS` |
| 8 | What must the MVP do? | `MVP_MUST_DO` |
| 9 | What is out of scope, but must stay possible later? | `OUT_OF_SCOPE_BUT_KEEP_POSSIBLE` |
| 10 | Constraints: team, skills, budget, timeline, what you want to learn? | `CONSTRAINTS` |
| 11 | What single number says it is working? | `SUCCESS_METRIC` |
| 12 | What is the hardest technical question it poses? | `HARDEST_TECHNICAL_QUESTION` |
| 13 | Which languages? Is any right-to-left? | `LANGUAGES`; more than one language turns on the i18n module |
| 14 | Is the content itself the product: articles, templates, courses, skills? | the content module: `CONTENT_UNIT`, `CONTENT_FORMAT`, `CONTENT_HARD_RULES`, `EDITORIAL_STANDARD` |
| 15 | Does it have a visual interface? | whether the ui module stays on |
| 16 | Anything already made (drafts, designs, specs) to treat as input? | `EXISTING_MATERIAL` and `EXISTING_MATERIAL_PATH` in `constraints.md` |
| 17 | Does it call an AI model while it runs? | the ai module |
| 18 | Are any users minors, or does it take payments, handle health or financial data, or serve a regulated client? | the legal module |
| 19 | Any other standing constraints every agent must respect? | `CONSTRAINT_TITLE`, `CONSTRAINT_BODY` and `CONSTRAINT_WHY` in `constraints.md`, one section per constraint |
| 20 | Do you want a shared work queue with a local board, so agents and sessions claim work and post progress? Default: yes | whether the beads module stays on |

Write every answer in the developer's terms, specific and checkable. A vague
thesis or audience makes every agent downstream worse. Where the developer is
unsure, write the working assumption and label it as one.

Record what the developer actually said, quoted and dated, in
`docs/direction.md`. A non-negotiable the developer stated links to its entry;
one you drafted from their description is marked "drafted", and never becomes a
gate without their yes (`.claude/rules/asking.md`). Ask at most two questions
at a time beyond the first batch.

### 2. Fill the placeholders

Placeholders look like `{{LIKE_THIS}}`. List them with:

```bash
grep -rnoE '\{\{[A-Z_]+\}\}' --exclude-dir=.git .
```

They appear only in files the project owns: `CLAUDE.md`, `README.md`,
`.claude/rules/constraints.md`, `.claude/rules/git-account.md` (filled in step
4), and `content/README.md` if the content module
is on. Never put project facts in a shared file. Sync would overwrite them.

- `DECISION_LOG_URL` and `STATUS_PAGE_URL` are filled in step 5.
- `CORE_FLOWS` names the flows the phase plan's slices are cut from. Phase 0
  makes only two ADRs, the stack and the core data model; any other
  foundational decision the developer names goes in the Phase 0 brief's item 3,
  as a decision under the slice that needs it.
- When the i18n module is on, add to item 3 of the Phase 0 brief: "The i18n
  and RTL ADR goes under slice 1, `Needed by: slice 1`." Every screen is built
  on it.
- In `constraints.md`, delete every section that does not apply, including
  its italic "keep only if" note.

### 3. Modules

```bash
majlis enable i18n      # more than one language, or any right-to-left one
majlis enable content   # the content is the product; adds the editor and content/README.md
majlis disable ui       # no visual interface: removes the designer and design/
majlis enable ai        # calls a model at runtime: adds the ai agent, its rule,
                       # and evals/README.md
majlis enable legal     # minors, payments, health or financial data, or a
                       # regulated client: adds the legal agent and docs/legal/
majlis disable beads    # no shared work queue: removes .claude/rules/beads.md.
                       # On by default; set it up in step 4b
```

After `enable i18n` or `enable ai`, add `i18n.md` or `ai.md` to the rules list
in `CLAUDE.md`; after `disable beads`, remove `beads.md` from it. If the
content role has a better name in this domain (a marketplace of templates
might call it "curator"), leave `editor.md` alone. Instead, `majlis detach
.claude/agents/editor.md`, then rename the file and its `name:` field.

### 4. Repo

1. `git init -b main`, and set `git config user.email` to the address the
   developer commits with.
2. Check `gh auth status`, and that the active account is the one that should
   own the repo.
3. `gh repo create <owner>/<slug> --private`, then add the remote it prints
   as `origin`.
4. Fill `.claude/rules/git-account.md`: `GIT_REMOTE` (the `origin` URL),
   `GIT_EMAIL` (the commit address), `GH_ACCOUNT` (how a writing `gh` command
   runs, for example plain `gh` or `GH_TOKEN=$(gh auth token --user <owner>) gh`
   when the machine has several accounts), and `REPO_VISIBILITY` (`private`
   unless the developer says otherwise).
5. Turn on the guard that keeps `main` for merged pull requests:
   `git config core.hooksPath .githooks`. Every later clone needs it too;
   `majlis lint` reports one that does not.

### 4b. The work queue (beads module, on by default)

Beads (`bd`) and its board, beads-ui, are both open source (MIT), self-hosted
and free. Nothing here talks to a hosted service. `<prefix>` is a short issue
prefix, such as the slug's initials.

```bash
brew install beads              # or the GitHub release binary, checked against checksums.txt
npm i -g beads-ui               # the board: bdui

bd init -p <prefix> -q --skip-hooks --skip-agents --setup-exclude
bd config set dolt.local-only true   # refuses any push to a remote
bd metrics off                       # usage metrics are on by default

ex="$(git rev-parse --git-common-dir)/info/exclude"
grep -vE '(RECOVERY|SESSION)\*\.md' "$ex" > "$ex.tmp" && mv "$ex.tmp" "$ex"
```

The flags matter. A bare `bd init` points `core.hooksPath` at `.beads/hooks`,
which silently turns off `.githooks/pre-push` and its guard on `main`. It also
makes its own commit, and writes `AGENTS.md`, `CLAUDE.md` text, a SessionStart
hook in `.claude/settings.json` and files for other editors, whose instructions
conflict with the rules here. `--setup-exclude` keeps `.beads/` out of git,
which stays, and also hides `RECOVERY*.md` and `SESSION*.md` files, which the
last line undoes.

Check that it did no harm:

```bash
git config core.hooksPath       # still .githooks
git status --short              # no AGENTS.md, no .beads/, no settings change
git log --oneline -3             # no commit made by bd
```

Pick a free local port for the board and write it into `README.md`, under how
to run it: `bdui start --port <port>`, then `http://127.0.0.1:<port>`. It
binds to this machine; never pass `--host`. Never run `bd dolt push`,
`bd sync`, or point `bd backup` at DoltHub or any hosted service; `bd` backs
the queue up to `.beads/backup` by itself (`.claude/rules/beads.md`).

### 5. Decision log

Render the page into the scratchpad:

```bash
python3 tools/render_decisions.py <scratchpad>/<slug>-decisions.html
```

Publish it as a **new** Artifact, and write its URL into `DECISION_LOG_URL` in
`CLAUDE.md`. Then render the status page and publish it as a second new
Artifact, writing its URL into `STATUS_PAGE_URL`:

```bash
python3 tools/render_status.py <scratchpad>/<slug>-status.html --decisions-url <DECISION_LOG_URL>
```

Then run the tests:

```bash
python3 -m unittest tools/test_render_decisions.py tools/test_render_status.py
```

### 6. Finish

1. Delete the setup block at the top of `CLAUDE.md`, and the template line
   under the heading in `README.md`.
2. Run the placeholder `grep` above. It must return nothing.
3. Make one commit, "initial commit from majlis", including `.majlis.json`,
   and push it. This is the one push to `main` there will
   ever be, before a pull request can exist:
   `ALLOW_MAIN_PUSH=1 git push -u origin main`. Everything after goes through a
   branch and a pull request (`.claude/rules/git.md`).
4. Tell the developer to start a new session so the agents, rules and hook
   load, and that Phase 0 starts with "run the architect on the Phase 0 brief
   in CLAUDE.md".

## What is in here

```
MAINTAINING.md            this guide; stays here
majlis/cli.py             new, adopt, enable, disable, sync, check, detach,
                          lint, research-find, migrate; `python3 -m majlis`
majlis/manifest.txt       every shipped file, as shared or once, by module
majlis/test_*.py          tests for the CLI, and checks on the template itself
.githooks/pre-push        refuses pushes to main, then runs pre-push.local
template/CLAUDE.md        template: the product, the MVP, the current phase
template/README.md        template: what it is, and how to run, test and deploy
CLAUDE.md, README.md      this repo's own, for its maintainers and visitors;
                          never shipped
LICENSE, DECISIONS.md     this repo's own; never shipped
pyproject.toml, setup.py  the package; setup.py copies the manifest's files into
                          the wheel under majlis/template/
CHANGELOG.md              what changes in a project at each release
.claude/agents/           architect, product, designer, builder, tester, critic,
                          security, ops, researcher
.claude/rules/            decisions, done, asking, tokens, code-organization,
                          ownership, research, agents, working-style, git,
                          majlis (shared); constraints, git-account (template)
.claude/settings.json     template: the fallback model, the .env read-deny, and
                          the update-notice hook
docs/                     adr, specs, reviews, security, research and status, each
                          with its README; research/backlog.md and direction.md
                          (templates)
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
checkout `majlis` runs from, so keep that checkout on `main` and pull it after
each merge. Projects on the installed package receive it at the next release.

To release, bump `__version__` in `majlis/__init__.py`, add a `CHANGELOG.md`
entry that says what changes in a project, and build with
`python3 -m pip wheel . --no-deps -w dist`. The wheel holds only the files
the manifest lists, so a file missing from the manifest never ships.

Keep every shared file product-neutral and free of placeholders. A fact about a
specific product belongs in a file the project owns. A behaviour only some
projects need belongs in a module.

To add a file, put it in `majlis/manifest.txt` under the right module, as
`shared` or `once`. Before committing, run:

```bash
python3 -m unittest discover -s majlis -p 'test_*.py'
python3 -m unittest tools/test_render_decisions.py tools/test_render_status.py
```

`test_template.py` fails in any of these cases:

- a file is missing from the manifest;
- a shared file contains a placeholder;
- a placeholder is not documented in this guide;
- a product-specific word appears in a shipped file.
