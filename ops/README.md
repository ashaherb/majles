# Ops

Owner: **ops**. Nobody else writes here.

How the system is deployed, watched, backed up and recovered. The ops agent
starts work in the first slice that deploys anywhere. Until then, this directory
holds only this file. Hosting itself is the architect's ADR; ops implements it.

## Layout

```
ops/
  environments.md   each environment: what runs where, how it differs, how it is reached
  monitoring.md     what is watched, what alerts, who hears it, and how the one number is measured
  backups.md        what is backed up, how often, where, and the last restore that was run
  runbooks/         one runbook per failure
```

The CI configuration lives where the CI system requires it (for example
`.github/workflows/`), and ops owns that directory too
(`.claude/rules/ownership.md`). So does `.githooks/pre-push.local`, the
project's own pre-push checks; `.githooks/pre-push` is the template's
guard on `main` and is not edited here.

## When CI runs

Once per unit of work, when its pull request is marked ready
(`.claude/rules/git.md`). On GitHub Actions, start from this, with the stack's
own steps in the single job:

```yaml
on:
  pull_request:
    types: [opened, reopened, ready_for_review, synchronize]  # a draft is skipped by the job's `if`, at no cost
    paths-ignore: ['docs/**', 'plan/**', '**/*.md']
  workflow_dispatch:
  workflow_call:
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
jobs:
  ci:
    if: github.event_name != 'pull_request' || !github.event.pull_request.draft
    runs-on: ubuntu-latest
    steps: []  # checkout, install once, then every check, ending with the end-to-end tests
```

A deploy workflow calls this one (`uses: ./.github/workflows/ci.yml`) rather
than repeating the checks.

## The minutes budget

GitHub Free gives a private repository 2,000 Actions minutes a month, with a
spending limit of zero (checked 2026-10-26). Keep the estimate here: minutes
per run, runs per week, and the month's total against the allowance.

## A runbook

```markdown
# <the failure>

Symptom: what someone sees.
Detected by: the alert or check that notices it, or "nothing yet".

## What the system does on its own

## What a person does

Numbered steps, exact commands.

## How to confirm it recovered
```

Every alert names its runbook. A failure with no runbook is a gap, and goes in
`monitoring.md` as one.
