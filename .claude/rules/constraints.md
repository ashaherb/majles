# Standing constraints

Project-specific constraints every agent must respect. They are filled in when
the project is set up. Delete any section that does not apply, and add one per
real constraint.

## {{CONSTRAINT_TITLE}}

{{CONSTRAINT_BODY}}

**Why:** {{CONSTRAINT_WHY}}

## The product's name stays out of every identifier

*Keep this section only if the name is undecided.*

The name never goes in a package name, directory, database identifier, config
key, environment variable, or domain wired into code. The repo stays
`{{REPO_SLUG}}`, and code uses neutral terms. The display name is one editable
content value. A working name is fine in prose.

**Why:** keeping the name out of identifiers makes choosing it later a content
edit instead of a rename.

## Existing material is an input, not a standard

*Keep this section only if the project starts with prior drafts, designs or
specs.*

{{EXISTING_MATERIAL}} is kept unedited in `{{EXISTING_MATERIAL_PATH}}`. Nothing
depends on it. The agent that owns that area establishes the real version from
research, and may keep a part only where the research supports it, saying why in
its `decision.md`.

**Why:** early drafts were never tested against alternatives. Upholding them
locks in the first idea by default.
