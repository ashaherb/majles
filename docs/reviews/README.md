# Reviews

Owner: **critic**. Nobody else writes here.

The critic runs at the end of every phase and before any decision that would be
expensive to reverse. Between those, it runs only fix checks (below). Its findings live here rather than only in the session
transcript, because a review that exists only in a transcript gets re-litigated
next session.

`NNNN-what-was-reviewed.md`, numbered in the order the reviews happened.

## Shape

```markdown
# NNNN. Review of <what>

Date: YYYY-MM-DD
Reviewed: <the files or decisions, by path>

## Blocking

Numbered. What is wrong, why it matters, what to do instead.

## Non-blocking

Same shape. These are opinions and are labelled as such.

## What I checked and found sound

Briefly. So the next reviewer does not repeat it.
```

Blocking and non-blocking stay separate. Conflating "this is wrong" with "I would
have done it differently" wastes the reader's attention, and both are useful.

A review that finds nothing serious says so plainly. Padding a review with minor
points to look thorough is a failed review.

## Resolution, and the fix check

When blocking findings are addressed, the critic runs a **fix check**: it reads
only the fixes for those findings, and appends the result to the same review
under `## Resolved`, naming the commit that settled each one. Do not delete the
finding. A fix check is not a new numbered review.

- **At most two fix checks per review.** If blocking findings remain after the
  second, the main session stops and brings them to the developer.
- **What the fix did not cause is non-blocking.** A problem the fix check
  notices that was there before goes into this review's `## Non-blocking` list,
  unless it breaks a non-negotiable.
- **A new numbered review** is written only at a phase gate, before a decision
  that is expensive to reverse, or when a fix check finds the fix itself broke a
  non-negotiable.

The limit exists because a review of the last review's fixes always finds
something. Without an exit, the loop never ends.
