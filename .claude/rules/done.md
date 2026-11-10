# What "done" means

A passing test proves the code does what the test says. It does not prove the
product works. Work is done only with evidence from the real thing, at three
levels.

## 1. The gate passed on the pull request

CI, or the local gate where CI is off, passed on the pull request's last commit,
and that gate runs the end-to-end tests (`.claude/rules/git.md`). A local run
is progress, not verification.

## 2. Every external service was called for real

A change that touches a model, a payment provider or any outside API makes one
cheap, real call per route before the gate, with a spending cap. Fakes keep the
suite fast and free; they cannot show a rejected parameter, a rate limit or a
reply that does not parse. Only the main session makes paid calls
(`.claude/rules/agents.md`).

## 3. Someone used it as the user

Before the developer is told a build is ready, the main session, or an agent it
briefs for this alone, uses the real app as the person in "Who this is for":

- the core flow end to end, on the real services;
- at a phone and a desktop size, in every language and theme the product has;
- reading every screenshot, not only checking that the script finished. Every
  wait in a try script has a time limit.

Then it writes, in a few honest lines, how it felt to use, and fixes or reports
what that person would trip over. A screen that works but would not make them
come back is not done.

## A change to what a user sees

The agent that made it runs the end-to-end tests for that screen and looks at
it in a browser, at phone and desktop size, before it reports. Its report names
the tests it ran. Markup rendered without a layout cannot show a broken screen.

## Before any agent reports

It stops every server, watcher and background command it started, and says so.

**Why:** in an earlier project every test and eval passed on a fake model
while the real one refused nearly every request; 1,885 tests passed while the
screens were visibly broken; its developer found the defects one screen at a
time, as the first person to use the product; and a dev server an agent left
running stopped the next test run from starting.
