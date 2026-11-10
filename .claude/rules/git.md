# Git

This project's account specifics (the remote, the commit identity, which `gh`
account writes) are in `.claude/rules/git-account.md`, which the project owns.
The rules that hold everywhere:

- Never force-push, and never rewrite pushed history.
- Never commit secrets: keys, `.env` files, service-account JSON.

## main changes only through a merged pull request

`main` holds only work that passed the gate. Nobody pushes to it.

1. **One branch per unit of work:** a milestone, a fix round, a docs change.
   Name it for the work: `s3-lesson-narration`, `fix-refusal-line`.
2. **Commit and push to the branch freely.** Pushing a branch runs no CI, so
   work is safe as soon as it is pushed, at no cost.
3. **Open the pull request as a draft** when the branch is first pushed.
4. **Mark it ready when the unit of work is done** (`.claude/rules/done.md`).
   That is when CI runs. A push after that runs it again, so finish first.
5. **Squash-merge** with `gh pr merge --squash --delete-branch` once CI is
   green. `main` then reads as one commit per unit of work, and its subject
   follows the commit style: imperative, lowercase, under ~70 characters.

`.githooks/pre-push` refuses any push to `main`. Turn it on once per clone with
`git config core.hooksPath .githooks`; `majles lint` reports a clone where it is
off. The only exception is the first push of a new repo, before a pull request
can exist: `ALLOW_MAIN_PUSH=1 git push -u origin main`.

**A pull request stays under about 1,000 added lines,** not counting deletions
and lockfiles, so a person can review it. The main session splits a unit of
work before it starts (for example new screens, their design previews, and the
deletion of the old ones go in separate pull requests). `.githooks/pre-push`
warns when a branch is over; it does not refuse the push. **Why:** in an
earlier project, one pull request at +11,973 −12,839 lines could not be
reviewed.

Parallel agents each work in their own git worktree, on their own branch (the
`Agent` tool's `isolation: "worktree"`). The main session merges their branches
into the unit's branch locally; that costs no CI.

**Why:** in an earlier project every commit was pushed to `main`, and every push
ran the full CI: 129 runs in one day, five of them within six minutes, used
about 2,400 Actions minutes, more than the free plan's month, on the second day.
GitHub Free does not enforce branch protection on a private repo, so the guard
has to be local.

## "Verified" means the gate passed on the pull request

Not a local run. A local run is progress; the pull request's CI run on its last
commit, or the local gate where CI is off, is the evidence.
