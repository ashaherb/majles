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

The interview is five short rounds, in this order, then one summary. Nothing is
written to a file until the developer has confirmed the summary.

**Every round goes the same way.** Open it with its heading, as below, and say
which round it is ("Round 2 of 5: the product"). Then:

1. **Show what you already understood** for this round, from the developer's
   description (and, in an adopted project, its old `CLAUDE.md`), in a few short
   lines, for them to correct. Mark each as what they said or what you guessed.
2. **Ask at most four questions**, only for what is still missing, and for any
   guess where a wrong guess would be costly. Never ask for what the
   description already says. Where a question has an obvious set of answers
   (yes or no, a default to accept, a short list), ask it as a choice with
   Claude Code's question tool (`AskUserQuestion`), whose "Other" lets the
   developer answer in their own words; ask the rest in plain text. Where the
   session has no question tool, ask all of them in plain text, numbered. If a
   round has nothing left to ask, its one question is whether what you
   understood is right.
3. **Follow up** only when one of the three triggers below holds, then go on to
   the next round.

Each row below is one question. The numbers are the interview's questions; a row
with several numbers asks them together, as one question.

### Round 1 of 5: the idea

| # | Question | Fills |
|---|---|---|
| 1 | What is it, in a paragraph? | `ONE_PARAGRAPH_DESCRIPTION` |
| 5 | Who is it for? What do they know, how do they arrive, how long do they give it? | `WHO_IT_IS_FOR` |
| 4 | The one-line thesis: why it should exist, and what it refuses to be? | `THESIS` |
| 2 | What is it called, and is the name settled? A choice: settled, or a working name | `PROJECT_NAME`, `NAME_STATUS`, and the name rule in `constraints.md` |

### Round 2 of 5: the product

| # | Question | Fills |
|---|---|---|
| 7 | What is the core loop, the one thing a user does? | `CORE_LOOP`, `CORE_FLOWS` |
| 8 | What must the MVP do? | `MVP_MUST_DO` |
| 9 | What is out of scope, but must stay possible later? | `OUT_OF_SCOPE_BUT_KEEP_POSSIBLE` |
| 11 | What single number says it is working? | `SUCCESS_METRIC` |

### Round 3 of 5: the limits

| # | Question | Fills |
|---|---|---|
| 6 | What must never be compromised? | `NON_NEGOTIABLES`, each marked as the developer's words or drafted |
| 10, 19 | Constraints: team, skills, budget, timeline, what you want to learn; and any other standing rule every agent must respect? | `CONSTRAINTS`; `CONSTRAINT_TITLE`, `CONSTRAINT_BODY` and `CONSTRAINT_WHY` in `constraints.md`, one section per standing rule |
| 18 | Are any users minors, or does it take payments, handle health or financial data, or serve a regulated client? A choice, several allowed, or none | the legal module |
| 12 | What is the hardest technical question it poses? | `HARDEST_TECHNICAL_QUESTION` |

### Round 4 of 5: the shape

| # | Question | Fills |
|---|---|---|
| 13 | Which languages? Is any right-to-left? A choice, with the language of the description first | `LANGUAGES`; more than one language turns on the i18n module |
| 15, 14, 17 | Which of these does it have: a visual interface; content that is itself the product (articles, templates, courses, skills); an AI model it calls while it runs? A choice, several allowed, or none | whether the ui module stays on (15); the content module (14), with `CONTENT_UNIT`, `CONTENT_FORMAT`, `CONTENT_HARD_RULES` and `EDITORIAL_STANDARD` taken from the answers or written as working assumptions; the ai module (17) |
| 16 | Anything already made (drafts, designs, specs) to treat as input? | `EXISTING_MATERIAL` and `EXISTING_MATERIAL_PATH` in `constraints.md` |
| 20 | A shared work queue with a local board, so agents and sessions claim work and post progress? A choice: yes (the default), or not now | whether the beads module stays on; a no goes to step 4b, never straight to `majles disable beads` |

A no to question 20 is not acted on here. Step 4b tells the developer what the
board gives them, and that `majles board` turns it on later, before it honours
the no.

### Round 5 of 5: the setup facts

Show what this machine already says: the slug given to `majles new` (or, in an
adopted project, the `origin` remote), `gh auth status`, and
`git config user.email`.

| # | Question | Fills |
|---|---|---|
| 3 | Directory and repo name? Default: the slug given to `majles new` | `REPO_SLUG` |
| 21 | Which GitHub account owns the repo, and which address do you commit with? A choice: the active `gh` account and the current email, or others. The repo is private unless you say otherwise | the owner in step 4, `GIT_EMAIL`, `GH_ACCOUNT` and `REPO_VISIBILITY` in `git-account.md` |

### Follow-up questions

Ask a follow-up only for one of three reasons, and say which one in the
question:

- **Vague:** the answer cannot be checked. Asked who it is for, the developer
  says "runners". "That is too vague to check: who uses it in its first month,
  and how do they find it?"
- **Contradiction:** two answers disagree. Round 2 says members see which runs
  they went to; round 3 says no accounts. "These two contradict: tracking who
  went needs some kind of account. Which one gives way?"
- **Costly guess:** a wrong guess would be expensive to undo. The active `gh`
  account looks like a work account. "A wrong guess here is costly, because a
  repo made under the wrong owner is hard to move: which account should own
  it?"

Ask at most two follow-ups at a time. If an answer is still unsure after one
follow-up, write the working assumption and label it as one; do not ask again.

### The summary

After round 5, show one summary and ask the developer to confirm or correct it.
It lists every answer, grouped by round, each marked as the developer's words,
taken from the description, or a working assumption; the non-negotiables, each
marked as theirs or drafted; the modules that will be turned on and off; and the
repo that will be created, with its owner and visibility. Apply any correction
and show the changed lines again. Write nothing, not even `docs/direction.md`,
until they confirm.

### Then record it

Write every answer in the developer's terms, specific and checkable. A vague
thesis or audience makes every agent downstream worse. Where the developer is
unsure, write the working assumption and label it as one.

Record what the developer actually said, quoted and dated, in
`docs/direction.md`. A non-negotiable the developer stated links to its entry;
one you drafted from their description is marked "drafted", and never becomes a
gate without their yes (`.claude/rules/asking.md`).

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
majles disable beads    # only when the developer says no to the queue and its
                       # board; step 4b asks. Removes .claude/rules/beads.md
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
2. Check `gh auth status`, and that the active account is the one round 5
   named as the owner.
3. `gh repo create <owner>/<slug> --private`, then add the remote it prints
   as `origin`.
4. Fill `.claude/rules/git-account.md` from round 5's answers: `GIT_REMOTE`
   (the `origin` URL), `GIT_EMAIL` (the commit address), `GH_ACCOUNT` (how a
   writing `gh` command runs, for example plain `gh` or
   `GH_TOKEN=$(gh auth token --user <owner>) gh` when the machine has several
   accounts), and `REPO_VISIBILITY` (`private` unless the developer said
   otherwise).
5. Turn on the guard that keeps `main` for merged pull requests:
   `git config core.hooksPath .githooks`. Every later clone needs it too;
   `majles lint` reports one that does not.

## 4b. The work queue (beads module, on by default)

The board is one of Majles's core features. It is one queue of work that every
session and agent shares, with a page on this machine that shows who has what
and what blocks what. Without it, sessions cannot see each other's work, and
the developer has no one view of it.

It needs three things, all open source (MIT), self-hosted and free. Nothing
here talks to a hosted service.

- `bd`, the queue, pinned to version 1.3.4, a tested release. Never install
  1.2.1: it was published by accident, and migrates the database so that other
  versions refuse it.
- Node 22 or later, which the board view runs on.
- beads-ui (`bdui`), the board view.

If the developer said no to the queue in round 4, tell them in one line what
they give up (the opening of this section), and that `majles board` turns it on
later. If they still say no, do as "Continue without the board" says below for
a missing `bd`. Otherwise run:

```bash
majles board
```

It lists each of the three as present or missing, with the install commands for
this machine. If it lists nothing missing, go on to "Then set up the queue".

**If anything is missing, stop.** Never turn the board off, skip a part of it,
or install anything without asking. Tell the developer, in a few lines:

1. what is missing, by name;
2. why it matters, in the sentences that open this section;
3. the exact commands that install it on their machine, from `majles board`'s
   output and the ways below.

Then ask: **install it now, or continue without the board for now?** Wait for
the answer. It is theirs to make, not yours.

- **Install now:** install what is missing, in the ways below, then run
  `majles board` again until it lists nothing missing.
- **Continue without the board:** if `bd` is there and only Node or beads-ui is
  missing, keep the module on and set up the queue below: it works without its
  view. If `bd` is missing, run `majles disable beads`, remove `beads.md` from
  the rules list in `CLAUDE.md`, and skip the rest of this step. Either way,
  run `majles board --off`: it records their no, with the date, in
  `.majles.json`. Tell the developer that a session start will say the board is
  off once a week, not every session, and that `majles board` turns it on any
  time. Write the same in `README.md`, under how to run it.

The ways to install each one, using what is already there (`command -v brew`,
`node --version`). Stop at the first way that works.

`bd`:

- with Homebrew (macOS or Linux): `brew install beads`. Homebrew installs its
  own current version, not the pin; check `bd version` afterwards, and if it
  prints 1.2.1, uninstall it and use another way;
- with Node 22 or later: `npm i -g @beads/bd@1.3.4`;
- otherwise, the release binary for this machine, checked against the
  release's checksums. This needs `gh`, which step 4 uses anyway. Each line
  runs only if the one before it worked, so a checksum mismatch installs
  nothing:

  ```bash
  v=1.3.4
  os=$(uname -s | tr A-Z a-z); arch=$(uname -m | sed 's/x86_64/amd64/; s/aarch64/arm64/')
  tmp=$(mktemp -d) && cd "$tmp" &&
    gh release download "v$v" -R gastownhall/beads -p "beads_${v}_${os}_${arch}.tar.gz" -p checksums.txt &&
    shasum -a 256 -c --ignore-missing checksums.txt &&
    tar xzf "beads_${v}_${os}_${arch}.tar.gz" ./bd &&
    mkdir -p ~/.local/bin && mv bd ~/.local/bin/
  cd - && rm -rf "$tmp"
  ```

  The checksum line must print `OK` (on Linux without `shasum`, use
  `sha256sum -c --ignore-missing checksums.txt` in its place). If it prints
  `FAILED`, or any line fails, nothing was installed: do not look for another
  way past it; tell the developer, and treat `bd` as not installable. If `~/.local/bin` is not on
  `PATH`, tell the developer which line to add to their shell profile.

Node 22 or later:

- on macOS: `brew install node`;
- on Linux: the distribution's package manager, if its Node is 22 or later
  (check with `node --version` afterwards);
- otherwise, on either: the official installer or binary from
  https://nodejs.org/en/download.

Never pipe a downloaded script into a shell to install any of these.

beads-ui: `npm i -g beads-ui`. If that fails with a permission error, never use
`sudo`; run `npm i -g --prefix ~/.local beads-ui` instead.

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
   in CLAUDE.md". If the board is off, say so again: what is missing, and that
   `majles board` turns it on.
