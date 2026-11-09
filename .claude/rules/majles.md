# Files shared with Majles

This project was created from the Majles template.
`.majles.json` lists the files Majles owns: the agents, most of
these rules, the `docs/` READMEs and the renderer.

## Do not edit a shared file in the project

To change one, change it in the Majles repository, commit there, then run
`majles sync` here.

**Why:** a shared file edited here stops receiving updates. Sync reports it and
leaves it alone rather than overwrite the edit.

## Project-specific rules go in files the project owns

That means `constraints.md`, or a new file in `.claude/rules/`. Any file not
listed in `.majles.json` belongs to the project.

## Diverging on purpose is allowed, and recorded

If this project needs its own version of a shared file (for example, a renamed
editor agent), run `majles detach <path>`. Sync then skips that file for good.

## Sync only when the developer asks

When the session starts with a notice that Majles has updates, tell the
developer. Do not sync on your own.
