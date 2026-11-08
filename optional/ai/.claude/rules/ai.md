# Model behaviour

This product calls a model while it runs. The `ai` agent owns prompts, model
choice per task, guardrails, evals, and cost and latency per interaction. The
provider and the gateway's shape are the architect's ADR.

## Every model change cites its evidence

A change to a prompt, a model or a guardrail lands in the same commit as its
evidence record (below). The commit message names the record's entry.

## Git holds the method, the data and the evidence; the tool holds the detail

- **Method and data, in `evals/`:** what makes a run repeatable: the harness,
  the scorers, the rubrics and bars, and the datasets, one case per line.
- **The evidence record, in `evals/evidence/<task>.md`:** one short entry per
  decision, newest last, never edited: the commit, the dataset version, the
  command, the link to the run, each model's score against each bar with cost
  and latency, what was chosen, and why. An agent reads it to know why the
  task is set up as it is and how to repeat the run. `evals/README.md` has the
  format.
- **The detail, in the project's eval tool:** per-case outputs, traces and
  every run that decided nothing. The architect chooses the tool in an ADR,
  with a build-or-adopt line. Until it exists, the detail stays on the machine
  that ran it, and the evidence record still lands.

**Why:** a model's behaviour cannot be read from a diff, so the run is the
only evidence of what a change did. Committing every run's output made one
pull request +11,000 lines and unreviewable. The developer, 2026-10-27: "The
test should be repeatable so the results shouldn't be kept in git only how to
reach it"; and 2026-10-28: "the evidence (The reason why you chose the model,
the result of the eval) should be in the platform in order to inform the
agent about repeatability". A few lines per decision keep the reasoning in
the repo even if the tool's data is lost.

## The bar is written before the run

The eval and its threshold are written, and committed, before the change they
judge. A threshold set after seeing the result is a finding for the critic.

## A feature a model touches ships with quality evals

Product's spec names the quality the feature must reach; the ai agent turns it
into eval bars before the builder starts. Component evals judge one part (each
model purpose, each guard, each prompt); end-to-end evals judge a whole flow
through the real gateway to what the user finally sees.

## Fake runs prove plumbing, never quality

Runs on the fake provider show that the harness, the contracts and the scorers
work, and they run in CI. A claim about quality comes only from a run on the
real models, with a spending cap, which the main session runs
(`.claude/rules/done.md`). Every model route gets one cheap real call before
the gate, and the full eval suite runs on the real models before each release.
A release that misses a bar does not ship unless the developer accepts the miss
in writing, recorded in `docs/direction.md` and linked from the evidence entry.

**Why:** in an earlier project every eval passed on the fake while the real
models refused nearly every request: a verdict that did not parse, a rejected
parameter, a rate limit.

## The model is a parameter of every eval

Any eval runs against any allowed model, chosen at run time. Comparing several
models on one eval set gives each bar's score, cost per interaction, latency
and failure rate side by side. The model a task uses is the cheapest one that
meets every bar, and the comparison that chose it is the task's evidence entry.

## Cost per interaction is recorded with the eval

Every run records the cost and the latency per interaction alongside the
score, and exactly what it judged: the commit, the model per task, and the
prompt and eval-set versions. A change that improves the score and doubles the
cost says so in its evidence entry.

## Any text a model reads is a prompt

System text, templates, tool names and descriptions, and schema descriptions
all live in the ai agent's prompts folder, never inline in application code.
The builder wires them in and does not edit them. A placeholder is allowed only
behind the fake provider, with a test that a real provider never receives it.

**Why:** in an earlier project placeholder tool descriptions in the builder's
code reached the real model on every request, unevaluated.

## The critic checks the evals, not only the code

At a slice gate that touched a prompt, a model or a guardrail, the critic reads
the evidence entries and their bars, checks that each bar was committed before
the change it judged, that the quality claims rest on real-model runs, and that
the linked runs exist.
