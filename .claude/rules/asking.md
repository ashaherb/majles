# The developer's words, and when to ask

## The developer's words are kept, word for word

`docs/direction.md` holds what the developer actually said that shapes the
product: quoted exactly, dated, newest last, never summarised or edited. The
main session appends to it the moment the developer gives a direction.

A record that rests on the developer's authority ("the developer wants…") links
to its entry there. Anything else the team wrote, including what the main
session drafted during setup, is **drafted**: it says so, the team may relax it,
and it never becomes a gate without the developer's yes. A drafted limit is
registered in `docs/assumptions.md` before anything relies on it
(`.claude/rules/assumptions.md`).

**Why:** in an earlier project a line drafted during setup was later treated as
its developer's own rule and rejected several options they would have taken;
they had only said "safe first".

## Ask only what is genuinely the developer's

Make the call, and state it as a default the developer can overrule. Ask, at
most two questions at a time, only when:

- an instruction has two readings that lead to different work ("use A and C":
  two things, or one made of both?);
- the team is about to narrow what the developer asked for, and the narrowing
  costs the user a capability, or costs a new service, dependency or money;
- the developer says something is not useful: ask which questions it fails to
  answer before choosing a fix, and judge the fix by those questions.

A direction the developer repeats is acted on in the next piece of work, not
logged again.

**Why:** in an earlier project, its developer asked for fewer questions, and
also lost a round of work and money to a misread instruction, a second service
nobody asked for, and a fix to the wrong problem. Both come from asking about
the wrong things.

## Check before you argue

Before citing a rule as a blocker, quote what it forbids and check that the case
falls under it. Before arguing from how the code behaves, read the code (a grep,
a line range). Otherwise label the claim "unverified". When a restriction is
your inference, say so, and give the conditions under which the idea would work.

**Why:** in an earlier project the strongest argument against its developer's
proposal was a claim about the code nobody had read, and it was false; another
time, an idea was called "ruled out" by decisions that did not rule it out.
