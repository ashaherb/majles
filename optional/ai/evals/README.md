# Evals

Owner: **ai**. Nobody else writes here.

How the product's model behaviour is measured, and the evidence for every
choice made from it. Git holds the method, the data and a short evidence record
per decision; the project's eval tool holds the detail of each run
(`.claude/rules/ai.md`).

## Layout

```
evals/
  <eval-name>/
    README.md      what it measures, why, and the threshold, written before any run
    cases.jsonl    the inputs, and expected outcomes or rubric labels, one case per line
    rubric.md      how an answer is scored, when it is not exact-match
  evidence/
    <task>.md      one entry per decision about that task's model, prompt or guardrail
```

No run output is committed: no per-case outputs, traces or score files. They go
to the eval tool, and the evidence entry links to them.

One eval per behaviour that matters: the core task, each refusal the product
must make, each guardrail. Cases include the hard ones: the input the product
must refuse, the user who pushes, the answer that is confident and wrong.

## An eval's README.md

```markdown
# <eval name>

Measures: the behaviour, in one sentence.
Threshold: the pass mark, and why that number.
Set: YYYY-MM-DD, before <the change it was written for>.
Repeat: the command that runs it, and the variables it needs.
```

The threshold is committed before the change it judges. Changing it later is a
new line with its own date and reason, never an edit of the old one.

## An evidence entry

Appended to `evidence/<task>.md`, newest last, never edited; a later entry
supersedes an earlier one by saying so. A task is a model purpose, a guard or a
prompt. Keep each entry to what an agent needs to know why, and to repeat it:

```markdown
## YYYY-MM-DD: <the change, as a claim>

Commit: <sha> · Dataset: evals/<eval>/cases.jsonl @ <version or sha>
Command: <the exact command; say "paid" and the total cost if it called a real model>
Run: <link or id in the eval tool>

| Model | <bar 1> (≥ N) | <bar 2> (≥ N) | Cost/interaction | Median latency |
|---|---|---|---|---|
| <model> | 0.91 ✓ | 0.97 ✓ | $0.0011 | 1.4 s |
| <model> | 0.88 ✓ | 0.93 ✗ | $0.0006 | 0.9 s |

Chosen: <model or version>, and why: the cheapest that meets every bar, or
what else decided it.
Failures worth reading: the cases that failed, and what they show, in a line or two.
```

A run on the fake provider never makes an evidence entry: it proves the
plumbing, not quality.
