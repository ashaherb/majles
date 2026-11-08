# Security

Majlis runs inside your projects. Its SessionStart hook executes a command at
the start of every Claude Code session, and its rules decide what the agents
may read. A flaw in either matters, so please report one privately.

## Reporting a vulnerability

Use GitHub's private reporting: the **Security** tab of this repository, then
**Report a vulnerability**. Please do not open a public issue.

Say what an attacker could do, and how to reproduce it. You will get an answer
within seven days. A fix goes out as a release with a note in the changelog,
and you are credited unless you ask not to be.

## What is in scope

- The SessionStart hook, and anything else that runs code without the user
  asking for it.
- `majlis` writing outside the project it was pointed at, or overwriting a file
  the project owns.
- Rules or settings that let an agent read a secret: `.env` files, keys,
  service-account files.
- The renderers producing a page that runs script from a project's content.

## Supported versions

Only the latest release receives fixes.
