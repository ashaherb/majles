# Status

Owner: **main session**. The inputs to the status page, which
`tools/render_status.py` builds together with the slice headings in
`CLAUDE.md`'s `## Phases` and the diagrams in `docs/architecture.md`. The page
is read in under a minute: where the project is, what is happening, what comes
next, what it looks like and how it is built. It is republished to one stable
URL at each milestone (`.claude/rules/decisions.md`), and never holds a decision
that is not also in the repo. `CLAUDE.md`'s prose never reaches it.

```
docs/status/
  tldr.md      three to five lines, one statement per line: where the project is
  now.md       what is being built: a handful of one-line `- ` items
  next.md      what comes after: a handful of one-line `- ` items
  waiting.md   what waits on the developer: one numbered line each, newest last
  spend.md     spend against the budget, as a short table under a `# ` title
  screens/     screenshots from the latest try as the user (.claude/rules/done.md),
               named so they sort in the order a user meets them; not committed
    captions.md  optional, one `- <file>: <caption>` line per screenshot
```

Every input is optional; the page leaves out a section whose input is missing
and lists what is missing at its foot. Write for the developer: short, plain,
no history. The renderer warns when the TLDR runs past five lines, or now or
next past seven. A screenshot without a caption is captioned from its file
name, without a leading number (`03-lesson-phone.png` reads "Lesson phone").

Publish the page with the screenshot files the renderer lists, at the same
relative paths (`screens/<file>` beside the page). `--root <dir>` renders
another project with this copy of the renderer.

## The slice strip

One segment per `### Slice N. <name>` heading under `## Phases` in `CLAUDE.md`,
and one for a `### Slices N to M` heading. The chip comes from the heading or the
first line under it (`Built`, `Gate open`, `In progress`, `Not started`, `Done`).
The slice named first in `## Current phase` is marked as now; later slices
without a state read as planned.

## Architecture, C1 to C4

The architect draws each level in `docs/architecture.md` as a fenced `c4` block,
usually under its `## C1` to `## C4` heading. Prose around the blocks stays in
the file and is not drawn. Each block is one diagram; the renderer lays it out,
so no coordinates are written:

````
```c4
level C2                      # optional under a `## C2` heading
title Containers              # optional; defaults to the heading or the level's name
inside app                    # the box one level up that this diagram opens

person    parent "Parent" : sets the rules
container web "Web app" : routes and screens
store     db "Postgres"
external  models "Model provider"

parent -> web : HTTPS
web -> db : SQL
web -> models : every call, through one gateway
```
````

- A box is `<kind> <id> "<label>" : <description>`. Kinds: `person`, `system`,
  `container`, `component`, `code`, `store` (data), `external` (outside the
  system, drawn dashed). The description is optional and is cut at three lines.
- An arrow is `<id> -> <id> : <label>`; label every arrow, in a few words.
- Boxes flow from the people at the top down to what they depend on.
- A box another diagram is `inside` gets a + and opens that diagram: C1's
  system opens C2, a container opens its C3, a component its C4. One diagram
  shows at a time, with the levels as tabs above it.
- Keep each diagram to about eight boxes; split a bigger one by `inside`.

A line the renderer does not understand, or an arrow to a box that is not in
its diagram, is left out with a warning.
