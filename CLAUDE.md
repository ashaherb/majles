# Majlis maintainer notes

This repo is the source of Majlis, not a project made with it. Majlis gives a
Claude Code project an agent team, working rules and a decision log, and keeps
them current with `majlis sync`.

**Never fill a `{{PLACEHOLDER}}` here, and never run setup on this repo.** The
template is what ships to projects:

- The shared files sit at their shipped paths: `.claude/agents/`,
  `.claude/rules/`, `docs/*/README.md`, `tools/`. Editing one changes every
  project at its next sync, so keep them product-neutral.
- The files a project owns ship from `template/` (its `CLAUDE.md` and
  `README.md`) or from their own paths (`.claude/settings.json`,
  `.claude/rules/constraints.md`, `docs/direction.md`, `docs/research/backlog.md`).
- Modules are in `optional/`. `majlis/manifest.txt` is the full list.
- This file, `README.md`, `LICENSE`, `DECISIONS.md`, `CHANGELOG.md`, the
  packaging files and `.github/` belong to this repo and never ship.
  `majlis/test_template.py` keeps that list.

The agents and rules in `.claude/` load here too, because the template is
dogfooded. Where one of them gives a per-project instruction (Phase 0, slices,
ADRs), it does not apply to this repo.

## Working here

- Read `MAINTAINING.md` (the maintainer guide) and `DECISIONS.md` first.
- One change is one branch and one pull request, under about 1,000 added lines.
  Open it as a draft, mark it ready when done, and squash-merge on green CI
  (`.claude/rules/git.md`). Turn on the guard once per clone:
  `git config core.hooksPath .githooks`.
- Tests, about 30 seconds:

  ```bash
  python3 -m unittest discover -s majlis -p 'test_*.py'
  python3 -m unittest tools/test_render_decisions.py tools/test_render_status.py
  ```

- A change that reaches projects gets a line in `CHANGELOG.md` saying what
  changes in a user's project after `sync`.
- Record every settled decision in `DECISIONS.md` in the same commit as the
  code it explains.
- The logo in `.github/` is a copy. Its source lives with the project's brand,
  outside this repo; replace the copy, never edit it here.
