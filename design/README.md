# Design

Owner: **designer**. Nobody else writes here.

## Where this stands

There is no design system yet. The designer establishes it from research, not
from whatever was here first. If `.claude/rules/constraints.md` names existing
design material, that material is an input and nothing depends on it.

## Once the design system is decided

One token file becomes the single source of visual truth. On the web it is
`design/tokens.css`. In a stack that can only load visual resources from its own
source tree, the tokens live there in the stack's own format, in a folder the
designer owns, and a project rule records the carve-out (`ownership.md`). Either
way there is one copy, never a source here and a mirror there.

No component anywhere in the repo hardcodes a colour, size, spacing value or
radius. If a value is missing, add it to the token file with a name that
explains its *role*, not its appearance, then use the token.

A preview (a page, or a scene) that renders every token and primitive ships
with it and keeps working. A token added without a preview entry is invisible.
