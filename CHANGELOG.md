# Changelog

Each entry says what changes in your project when you sync to that version.
Run `majlis sync` to preview it, and `majlis sync --apply` to write it.

## 0.1.0

The first release under the name Majlis.

### What changes in your project

- **The tool has a new name and a new command.** The CLI is `majlis`. Install
  it with `pipx install majlis`, and it works from any directory. Your
  project's lock file becomes `.majlis.json`, and the shared rule about
  template files becomes `.claude/rules/majlis.md`.
- **`majlis migrate` moves an older project over.** A project made before the
  rename still works: the CLI reads its old lock file, and `majlis check` tells
  you it needs migrating. Run `majlis migrate` once. It renames the lock file
  and rewrites the SessionStart hook in `.claude/settings.json` so it calls
  `majlis check`. Then `majlis sync --apply` moves the renamed rule, unless you
  edited it, in which case it is a conflict you resolve with `--take` or
  `detach`. Review with `git diff` and commit on a branch.
- **Your projects live wherever you say.** Set `MAJLIS_ROOT` to the directory
  that holds your projects, or pass `--root`. Without either, `majlis new`,
  `sync --all` and `research-find` use the current directory. Nothing assumes
  a particular folder on your machine any more.
- **Your git account details move to a file you own.** `.claude/rules/git.md`
  now holds only the rules that apply to every project: branches, pull
  requests, and nothing pushed to `main`. Your remote, commit email, which `gh`
  account writes, and the repo's visibility go in a new
  `.claude/rules/git-account.md`, which sync adds as a template for you to
  fill in. If your old `git.md` carried account details, copy them into
  `git-account.md` before you sync, since sync replaces `git.md`.
- **The studio module is no longer part of Majlis.** If your project had it
  on, sync keeps `.claude/agents/studio.md` and `.claude/rules/studio.md` as
  your own files (as if you had run `majlis detach` on them) and turns the
  module off. Nothing is deleted.
- **The SessionStart hook stays quiet without Majlis.** It runs
  `majlis check` only when `majlis` is on your PATH, and never fails a session.

### How sync knows what you received

Installed from a package, `.majlis.json` records the Majlis version your
project is on, such as `"version": "0.1.0"`. Run from a git clone of Majlis, it
records the commit instead, as before. Either way, the lock holds a hash of
every shared file as delivered, which is how sync tells your edits from the
template's changes. A project synced from a clone can move to the installed
package with one `majlis sync --apply`.
