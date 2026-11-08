# Code a person can maintain

The developer maintains this code, so it is organised and documented for a
person finding their way around it, not for the agent that wrote it. The stack
ADR settles the specifics: the formatter and its line length, the layout, and
the check below. A project rule records them once the ADR exists.

## Layout by feature

- Each module owns one feature or concern, in one folder, with one front door
  (an index or public file). Other modules import only the front door, and a
  linter enforces it.
- The code for a feature lives together. A feature spread across four
  top-level folders, or a flat folder of every component, is a finding.
- Entry points (routes, handlers, commands) parse the input, check who is
  asking, and call one module function. They hold no logic of their own.

## A formatter, in the gate

One formatter, run in the gate. Nobody formats by hand against it.

## Documentation the gate checks

- Each module has a `README.md`: what it is for and where to start reading; the
  invariants that must never break, and the test that guards each one; how to
  change it safely.
- A short manual for the codebase as a whole: where to start, how a request
  flows through it, the data model, and the conventions.
- A check in the gate fails when a module has no `README.md`.

A change that makes a module's `README.md` or the manual wrong fixes it in the
same commit.

**Why:** in an earlier project the developer could not find their way around the
code: no formatter, hundreds of lines over 160 characters, a flat components
folder, each feature spread across four folders, and no code documentation.
Code the developer cannot read, the developer cannot fix.
