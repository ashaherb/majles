# Contributing to Majles

Thank you for wanting to help. Majles is small and run by one maintainer, so
the most useful contributions are clear bug reports, and pull requests that
change one thing and say why.

## Before you start

Open an issue first for anything bigger than a fix: a new agent, a new rule, a
new module, or a change to how `sync` behaves. Every project made with Majles
receives the shared files at its next sync, so a change there reaches people
who never asked for it. It is worth agreeing on first.

Read `MAINTAINING.md` (the maintainer guide) and `DECISIONS.md`. A pull request
that reverses a recorded decision needs to say so and argue for it.

## How the repo is laid out

- The **shared** files sit at their shipped paths: `.claude/agents/`,
  `.claude/rules/`, `docs/*/README.md`, `tools/`. `sync` keeps every project
  identical to them.
- The files a project **owns** are templates. They are copied once and never
  touched again: `template/CLAUDE.md`, `template/README.md`,
  `.claude/settings.json`, `.claude/rules/constraints.md` and a few more.
- **Modules** are in `optional/`.
- `majles/manifest.txt` lists every shipped file as `shared` or `once`, by
  module. `majles/cli.py` is the command-line tool.

Three rules keep the template usable by anyone:

1. A shared file never contains a `{{PLACEHOLDER}}`, and never names a
   particular product. Project facts go in owned files.
2. Every rule carries its reason, as a **Why:** line, so a reader can tell when
   it no longer applies.
3. A new shipped file goes in the manifest, under the right module.

`majles/test_template.py` checks all three.

## Making a change

```bash
git clone <your fork> && cd majles
git config core.hooksPath .githooks     # refuses pushes to main
git checkout -b short-name-for-the-change
# edit, then run the tests (Python 3.10 or later, standard library only):
python3 -m unittest discover -s majles -p 'test_*.py'
python3 -m unittest tools/test_render_decisions.py tools/test_render_status.py
```

- One change per pull request, under about 1,000 added lines.
- Add a test for anything the CLI does differently.
- Majles uses only the Python standard library. Please keep it that way.
- Commit subjects are imperative and lowercase, under about 70 characters, with
  no trailing period: `add a dry run to adopt`.
- Open the pull request as a draft, and mark it ready when it is done. CI runs
  on ready pull requests only.
- A change to a shared file says in the pull request what changes in a user's
  project after `sync`, not only what changed in the template. That line
  also goes in `CHANGELOG.md`.

## Licence

Majles is Apache 2.0. By opening a pull request you agree that your
contribution is licensed under it too (section 5 of `LICENSE`). There is no
separate contributor agreement.

## Conduct

Everyone taking part follows the `CODE_OF_CONDUCT.md`.
