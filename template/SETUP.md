# Setting up this project

This is Claude's procedure for setting up a project made or adopted with Majles.
Follow it in order. The last step deletes this file.

**An adopted project** (brought in with `majles adopt`, not made with
`majles new`) already has its own files and history. Three things differ:

- If adopt kept the project's own `CLAUDE.md`, the template is beside it as
  `CLAUDE.majles.md`. Before step 1, make that the new `CLAUDE.md`: carry
  everything the old one says that still holds into its sections (what fits
  none goes under a heading of its own), keep its setup block, and delete
  `CLAUDE.majles.md`. The old `CLAUDE.md` is the interview's first source.
  Add the lines adopt listed as missing from `.gitignore` and `README.md`,
  where they apply.
- Step 4 is shorter: the repo already exists.
- Step 6's commit goes on a branch and a pull request, never straight to `main`.

## 1. Interview

From the developer's description, fill as many of the answers below as can be
derived. Then ask **one batch** of questions: for what is missing, and for
anything guessed where a wrong guess would be costly. Never ask for what the
description already says.

| # | Question | Fills |
|---|---|---|
| 1 | What is it, in a paragraph? | `ONE_PARAGRAPH_DESCRIPTION` |
| 2 | What is it called, and is the name settled? | `PROJECT_NAME`, `NAME_STATUS`, and the name rule in `constraints.md` |
| 3 | Directory and repo name? Default: the slug given to `majles new` | `REPO_SLUG` |
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

## 2. Fill the placeholders

Placeholders look like `{{LIKE_THIS}}`. List them with:

```bash
majles placeholders
```

It reads only the files the project owns (the "once" list in `.majles.json`), never
footage, generated files or anything else in the repo.

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

## 3. Modules

```bash
majles enable i18n      # more than one language, or any right-to-left one
majles enable content   # the content is the product; adds the editor and content/README.md
majles disable ui       # no visual interface: removes the designer and design/
majles enable ai        # calls a model at runtime: adds the ai agent, its rule,
                       # and evals/README.md
majles enable legal     # minors, payments, health or financial data, or a
                       # regulated client: adds the legal agent and docs/legal/
majles disable beads    # no shared work queue: removes .claude/rules/beads.md.
                       # On by default; set it up in step 4b
```

After `enable i18n` or `enable ai`, add `i18n.md` or `ai.md` to the rules list
in `CLAUDE.md`; after `disable beads`, remove `beads.md` from it. If the
content role has a better name in this domain (a marketplace of templates
might call it "curator"), leave `editor.md` alone. Instead, `majles detach
.claude/agents/editor.md`, then rename the file and its `name:` field.

## 4. Repo

**An existing repo** (an adopted project, where `git remote get-url origin`
prints a URL): skip 1 to 3. Check that `git config user.email` is the address
the developer commits with, then do 4 and 5, with `GIT_REMOTE` taken from the
existing `origin`.

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
   `majles lint` reports one that does not.

## 4b. The work queue (beads module, on by default)

Beads (`bd`) and its board, beads-ui, are both open source (MIT), self-hosted
and free. Nothing here talks to a hosted service. `<prefix>` is a short issue
prefix, such as the slug's initials.

First see what is already there: `command -v bd bdui`, `node --version`,
`command -v brew`. Install only what is missing, and stop at the first way that
works.

`bd`, the queue:

- with Homebrew (macOS or Linux): `brew install beads`;
- with Node 22 or later: `npm i -g @beads/bd`;
- otherwise, the release binary for this machine, checked against the
  release's checksums. This needs `gh`, which step 4 uses anyway:

  ```bash
  os=$(uname -s | tr A-Z a-z); arch=$(uname -m | sed 's/x86_64/amd64/; s/aarch64/arm64/')
  tmp=$(mktemp -d) && cd "$tmp"
  gh release download -R gastownhall/beads -p "beads_*_${os}_${arch}.tar.gz" -p checksums.txt
  shasum -a 256 -c --ignore-missing checksums.txt   # must print OK; on Linux sha256sum works too
  tar xzf beads_*.tar.gz bd && mkdir -p ~/.local/bin && mv bd ~/.local/bin/
  cd - && rm -rf "$tmp"
  ```

  If `~/.local/bin` is not on `PATH`, tell the developer which line to add to
  their shell profile.

`bdui`, the board, needs Node 22 or later: `npm i -g beads-ui`. If that fails
with a permission error, never use `sudo`; run
`npm i -g --prefix ~/.local beads-ui` instead. The board is only a view: with
no Node, skip it, say so in `README.md`, and use `bd` alone.

If `bd` cannot be installed, or the developer does not want the queue, run
`majles disable beads`, remove `beads.md` from the rules list in `CLAUDE.md`,
and skip the rest of this step. `majles enable beads` brings it back later.

Then set up the queue:

```bash
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

## 5. Decision log

The two pages are published as claude.ai Artifacts when this session can
publish them: it needs a claude.ai sign-in and a tool for publishing Artifacts.
Check that before rendering. If it cannot, or publishing fails, do not stop:
keep the pages as files in the project instead, which `.gitignore` already
leaves out of git, and write their paths in place of the URLs:

```bash
python3 tools/render_decisions.py docs/status/decisions.html
python3 tools/render_status.py docs/status/status.html --decisions-url decisions.html
```

`DECISION_LOG_URL` is then `docs/status/decisions.html` and `STATUS_PAGE_URL`
is `docs/status/status.html`. The developer opens them in a browser, and
regenerating them is how they are published from then on. Tell the developer
which way was used. Then skip to the tests below.

With Artifacts, render the page into the scratchpad:

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

## 6. Finish

1. Delete the setup block at the top of `CLAUDE.md`, the template line under the
   heading in `README.md`, and this file, `SETUP.md`.
2. Run `majles placeholders`. It must find none. From now on `majles lint` reports
   any placeholder left in the project's own files.
3. Make one commit, "initial commit from majles", including `.majles.json`,
   and push it. This is the one push to `main` there will
   ever be, before a pull request can exist:
   `ALLOW_MAIN_PUSH=1 git push -u origin main`. Everything after goes through a
   branch and a pull request (`.claude/rules/git.md`). An adopted project
   already has `main`, so its commit goes on a branch, such as `adopt-majles`,
   and reaches `main` through a pull request like any other change.
4. Tell the developer to start a new session so the agents, rules and hook
   load, and that Phase 0 starts with "run the architect on the Phase 0 brief
   in CLAUDE.md".
