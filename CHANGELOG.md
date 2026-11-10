# Changelog

Each entry says what changes in your project when you sync to that version.
Run `majles sync` to preview it, and `majles sync --apply` to write it.

## 0.1.0: the launch release, not out yet

The first public release. (On PyPI, 0.0.1 is only a placeholder that reserves the name.)

### What you get

- **`majles new <slug>`** makes a Claude Code project with an agent team: architect,
  product, designer, builder, tester, critic, security, ops, researcher and a
  100x-engineer, each with one job, on Opus or Sonnet.
- **Working rules with their reasons**, in `.claude/rules/`: research only what blocks
  the next step, record each decision in one place, keep pull requests reviewable, and
  never call work done until someone has used it as the user would.
- **A setup guide**, `SETUP.md`: say "set up this project", answer one batch of
  questions, and Claude fills in the project, creates a private GitHub repo, turns on a
  guard against pushes to `main`, and publishes the decision log.
- **Modules** you turn on or off: `ui`, `beads` (a local work queue and board), `i18n`,
  `content`, `ai` and `legal`.
- **The board is never off quietly.** If `bd`, Node 22 or the board view is missing,
  setup stops, says what and why, gives the install commands and asks you. While the
  board is off, every session opens with one line saying so, and `majles board` checks
  what is missing and turns it on. If you say no on purpose (in setup, or with
  `majles board --off`), the line shows once a week instead.
- **Staying current:** `majles sync` previews and applies template updates without
  touching the files your project owns, and `majles lint` checks the research and ADR
  rules.

### If your project was made before 0.1.0

Everything below is for a project made from an earlier, unreleased version of the
template, under this name or an earlier one. A new project needs none of it.

- **Rules no longer quote dated words as yours.** Several shared rules cited what
  "the developer" said on a date in Majles's own history; in your project that read as
  something you said. They now say "in an earlier project". `docs/direction.md` is
  still the only place your words are kept.
- **A board that is off now says so.** With this `majles` installed, every session
  start says when the `beads` module is off, or `bd` or beads-ui is missing, until
  `majles board` lists nothing missing. Your hook already calls `majles check`, so
  nothing in the project changes for this. Sync changes one line of
  `.claude/rules/beads.md`, which now points at `majles board` for the `bd init` flags.
- **Wider read-deny rules for secrets.** New projects deny Claude's Read tool on `.env`
  variants (not `.env.example`), `*.pem`, `*.key` and service-account JSON.
  `.claude/settings.json` is yours, so sync does not change it: copy the `deny` list
  from a new project if you want it. A deny rule cannot stop a shell command from
  reading a file; `.claude/rules/agents.md` says so.
- **Setup pins Beads to 1.3.4**, and installs the release binary only after its
  checksum passes. This changes only `SETUP.md`, which new projects get.
- **The tool is called Majles.** The CLI is `majles`. Install it with
  `pipx install majles` or `uv tool install majles`, and it works from any directory.
  Your project's lock file becomes `.majles.json`, and the shared rule about template
  files becomes `.claude/rules/majles.md`.
- **`majles migrate` moves an older project over.** A project made under an earlier
  name still works: the CLI reads its old lock file (`.majlis.json`, or the older
  `.boilerplate.json`), and `majles check` tells you it needs migrating. Run
  `majles migrate` once. It renames the lock file and rewrites the SessionStart hook
  in `.claude/settings.json` so it calls `majles check`. Then `majles sync --apply`
  moves the renamed rule, unless you edited it, in which case it is a conflict you
  resolve with `--take` or `detach`. Review with `git diff` and commit on a branch.
- **The setup guide comes with your project.** A new project gets `SETUP.md`, the
  step-by-step setup procedure, and `CLAUDE.md` points at it, so setup works from the
  installed package without the Majles repository. Setup deletes it when it is done.
  `majles new` and `majles adopt` bring it; `sync` never adds it to an existing project.
- **Adopting a project with its own `CLAUDE.md` now works.** `majles adopt` keeps the
  project's `CLAUDE.md` and writes the template beside it as `CLAUDE.majles.md`; setup
  merges the two and deletes it. For a kept `.gitignore` and `README.md`, adopt lists the
  template lines each one lacks. Setup's repo step has a short path for a project that
  already has a repo, and its first commit goes through a pull request.
- **`majles placeholders` lists what setup still has to fill**, reading only the files
  your project owns (the "once" list in `.majles.json`), never footage or generated
  files. Once setup has deleted `SETUP.md`, `majles lint` reports any placeholder left.
- **The push guard does not count files Majles installed unchanged**, so a first
  adoption or a sync does not trip the 1,000-line warning.
- **Your projects live wherever you say.** Set `MAJLES_ROOT` (or the older
  `MAJLIS_ROOT`) to the directory that holds your projects, or pass `--root`. Without either, `majles new`,
  `sync --all` and `research-find` use the current directory. Nothing assumes
  a particular folder on your machine any more.
- **Your git account details move to a file you own.** `.claude/rules/git.md`
  now holds only the rules that apply to every project: branches, pull
  requests, and nothing pushed to `main`. Your remote, commit email, which `gh`
  account writes, and the repo's visibility go in a new
  `.claude/rules/git-account.md`, which sync adds as a template for you to
  fill in. If your old `git.md` carried account details, copy them into
  `git-account.md` before you sync, since sync replaces `git.md`.
- **The studio module is no longer part of Majles.** If your project had it
  on, sync keeps `.claude/agents/studio.md` and `.claude/rules/studio.md` as
  your own files (as if you had run `majles detach` on them) and turns the
  module off. Nothing is deleted.
- **The SessionStart hook stays quiet without Majles.** It runs
  `majles check` only when `majles` is on your PATH, and never fails a session.
- **The 100x-engineer runs on Opus**, not Fable, so every agent needs only
  Opus or Sonnet. To keep it on Fable, run
  `majles detach .claude/agents/100x-engineer.md` before you sync, and the
  file stays as it is.
- **Projects without Artifacts keep the decision log as files.** The
  decisions rule now says that where `CLAUDE.md` records
  `docs/status/decisions.html` and `docs/status/status.html` instead of
  URLs, rendering to those paths is the publishing. New projects ignore
  `docs/status/*.html` in git; add that line to your `.gitignore` if you use it.
- **Setup installs Beads without Homebrew**, from npm or the checked release
  binary, and turns the module off when it cannot. This changes only
  `SETUP.md`, which new projects get.
- **`majles new` refuses a name that is not a plain lowercase slug**, such as
  one with spaces or capitals, before it writes anything, and quotes the path
  in the "Next:" line it prints. No change to existing projects.

### How sync knows what you received

Installed from a package, `.majles.json` records the Majles version your
project is on, such as `"version": "0.1.0"`. Run from a git clone of Majles, it
records the commit instead, as before. Either way, the lock holds a hash of
every shared file as delivered, which is how sync tells your edits from the
template's changes. A project synced from a clone can move to the installed
package with one `majles sync --apply`.
