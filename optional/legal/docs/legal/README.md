# Legal

Owner: **legal**. Nobody else writes here.

What the law asks of this product, and what only a lawyer can settle. Nothing
here is legal advice. The legal agent's main output is the list of questions
for counsel; the register and the drafts exist so that a lawyer's time goes to
those questions, not to finding out what the product is.

## Layout

```
docs/legal/
  obligations.md            the register
  questions-for-counsel.md  ranked by what each blocks
  drafts/                   privacy notices and terms, each marked as a draft for counsel
```

## obligations.md

```markdown
# Obligations

| Obligation | Applies because | Where (country), read as of | Evidence | Status | Met by |
|---|---|---|---|---|---|
| ... | the user group, data or activity that triggers it | country, YYYY-MM-DD | docs/research/<task>/ | met / needs work / needs a lawyer | the spec, ADR or code that meets it |
```

Each row names its research. A row without evidence is a guess and says so.

## questions-for-counsel.md

```markdown
# Questions for counsel

## 1. <the question, specific enough to answer>

Blocks: the slice, launch or decision that waits for the answer.
Context: the facts a lawyer needs, and the sources read so far.
Our reading: labelled as such, so counsel can correct it.
```

Ranked by what each blocks, most urgent first. When counsel answers, the answer
is added under its question with the date and who gave it, and the register is
updated.

## Drafts

Every draft opens with this line, unchanged:

> **Draft for counsel. Not reviewed by a lawyer. Do not publish.**

The line is removed only by the developer, after a lawyer has reviewed the text.
