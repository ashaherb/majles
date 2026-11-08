# Security

Owner: **security**. Nobody else writes here.

The threat model, and the security reviews of each slice that touched a
sensitive area: auth, sessions, personal data, payments, secrets, external
input or file handling. The security agent runs at those slice gates and before
any launch, not at every gate.

## threat-model.md

One file, kept current. Updated at each slice the security agent reviews, so it
describes the system that exists.

```markdown
# Threat model

Updated: YYYY-MM-DD, at slice N

## What is worth attacking

The assets: data, money, accounts, access, reputation. Most valuable first.

## Who would try, and how

Each attacker or accident, what they want, and the path they would take.

## Controls

| Threat | Control | Where it lives | Status |
|---|---|---|---|
| ... | ... | the code, config or test that enforces it | in place / missing |

## Accepted risks

What we chose not to defend, why, and who agreed.
```

A control without a "Where it lives" is not in place.

## Reviews

`NNNN-what-was-reviewed.md`, numbered in the order the reviews happened.

```markdown
# NNNN. Security review of <slice or change>

Date: YYYY-MM-DD
Reviewed: <commit range, and the areas touched>

## Blocking

Numbered. The attack, what an attacker gets, and what to do instead.

## Non-blocking

Same shape, labelled as opinions.

## What I checked and found sound

Briefly, so the next review does not repeat it.
```

When blocking findings are fixed, the security agent runs a fix check and
appends `## Resolved` to the same review, naming the commit for each. At most
two fix checks per review; then the main session brings what remains to the
developer. This is the same limit as `docs/reviews/`.
