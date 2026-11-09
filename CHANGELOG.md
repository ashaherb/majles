# Changelog

Each entry says what changes in your project when you sync to that version.
Run `majles sync` to preview it, and `majles sync --apply` to write it.

## 0.1.0: the launch release, not out yet

The first release under the name Majles. (On PyPI, 0.0.1 is only a placeholder that
reserves the name.)

### What changes in your project

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

### How sync knows what you received

Installed from a package, `.majles.json` records the Majles version your
project is on, such as `"version": "0.1.0"`. Run from a git clone of Majles, it
records the commit instead, as before. Either way, the lock holds a hash of
every shared file as delivered, which is how sync tells your edits from the
template's changes. A project synced from a clone can move to the installed
package with one `majles sync --apply`.
