#!/usr/bin/env python3
"""
majles: create projects from the Majles template, and keep them in step with it.

Zero dependencies. Python 3.10+. Run it from anywhere (or as `python3 -m majles`):

    majles new <slug>                    create <root>/<slug>
    majles adopt [project] --modules M,... [--apply]
                                           bring an existing project under Majles
    majles enable <module> [project]        turn a module on (ui, i18n, content, ai, legal, beads)
    majles disable <module> [project]       turn a module off
    majles sync [project] [--apply] [--diff] [--take PATH ...]
    majles sync --all [--apply]             every project under <root>
    majles check [project]                  notice if behind or lint finds anything;
                                           the SessionStart hook
    majles detach <path> [project]          the project takes over a shared file
    majles lint [project]                   check research, ADRs, standing-text size and the main guard
    majles placeholders [project]           placeholders left in the files the project owns
    majles research-find <words...>         find earlier research in every project
    majles migrate [project]               move a project made before the rename onto Majles

[project] defaults to the current directory. <root>, the directory that holds
your projects, is --root if given, else $MAJLES_ROOT, else the current
directory. A path given to `new` that contains a slash, or is absolute, is used
as is.

majles/manifest.txt sorts every file into "shared" (Majles owns it; sync
keeps projects identical to it) or "once" (a template copied at
creation that the project owns from then on).

Each project records what it received in .majles.json: the Majles version it
last synced to, its modules, and a hash of every shared file as it
was delivered. A shared file whose hash no longer matches was edited in the
project. Sync reports it and leaves it alone rather than overwrite that work.

The template comes from one of two places. Run from a git checkout of Majles,
content comes from the checkout's committed HEAD, never from its working tree,
and the lock records that commit. Installed as a package (pip, pipx), content
comes from the template packaged with it, and the lock records the package
version. An installed package holds only its own version's files, which is
enough: sync needs the new files, and the hashes in the lock to see edits.

lint and research-find read projects and change nothing. lint checks the rules
in .claude/rules/research.md that a script can check, so they do not rest on
prose alone.
"""

import argparse
import collections
import datetime
import difflib
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

from . import __version__

BP_ROOT = pathlib.Path(__file__).resolve().parent.parent  # the checkout, when run from one
PACKAGED = pathlib.Path(__file__).resolve().parent / "template"  # the template, in a built wheel
MANIFEST = "majles/manifest.txt"
LOCK = ".majles.json"
# Compatibility with projects made under the earlier names: "boilerplate", then "Majlis".
LEGACY_MANIFESTS = ("majlis/manifest.txt", "boilerplate/manifest.txt")  # where the manifest sat at older commits
LEGACY_LOCKS = (".majlis.json", ".boilerplate.json")  # newest first
# The old SessionStart hooks: the boilerplate script by its path, then the `majlis` command.
LEGACY_HOOK_MARKS = ("/boilerplate/", "majlis check")
RENAMED = {  # old dest -> new dest
    ".claude/rules/boilerplate.md": ".claude/rules/majles.md",
    ".claude/rules/majlis.md": ".claude/rules/majles.md",
}
# Modules Majles no longer ships, with the shared files each one installed. Sync keeps
# those files as the project's own (detached) and turns the module off; it never deletes them.
RETIRED = {"studio": (".claude/agents/studio.md", ".claude/rules/studio.md")}
HOOK_COMMAND = 'command -v majles >/dev/null 2>&1 && majles check "$CLAUDE_PROJECT_DIR" 2>/dev/null; exit 0'
DEFAULT_MODULES = ["core", "ui", "beads"]
SELF = "majles"
# Where adopt writes the template CLAUDE.md when the project already has its own. Setup
# merges the two (SETUP.md, "An adopted project") and deletes this file.
CLAUDE_BESIDE = "CLAUDE.majles.md"
# Project-owned files adopt keeps, and which template lines it reports their copy lacks.
COMPARED = {
    ".gitignore": lambda line: line and not line.startswith("#"),  # every pattern
    "README.md": lambda line: line.startswith("## ") and "{{" not in line,  # the sections
}
ROOT_ENV = "MAJLES_ROOT"
LEGACY_ROOT_ENV = "MAJLIS_ROOT"  # still read when the new one is not set


class MajlesError(Exception):
    """A problem the user must fix; printed without a traceback."""


# ---------------------------------------------------------------- the Majles checkout


def git(bp, *args):
    r = subprocess.run(["git", "-C", str(bp), *args], capture_output=True)
    if r.returncode:
        raise MajlesError(f"git {' '.join(args)} failed in {bp}: {r.stderr.decode().strip()}")
    return r.stdout


def head(bp):
    return git(bp, "rev-parse", "HEAD").decode().strip()


def read_at(bp, commit, path):
    return git(bp, "show", f"{commit}:{path}")


def has_commit(bp, commit):
    return subprocess.run(
        ["git", "-C", str(bp), "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True
    ).returncode == 0


def parse_manifest(text):
    """Return a list of (module, kind, src, dest)."""
    entries, module = [], None
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            module = line[1:-1].strip()
            continue
        kind, _, rest = line.partition(" ")
        if kind not in ("shared", "once") or not rest.strip() or module is None:
            raise MajlesError(f"{MANIFEST}:{n}: expected 'shared|once <path>' under a [module]")
        src, arrow, dest = rest.strip().partition("->")
        src, dest = src.strip(), (dest.strip() if arrow else src.strip())
        entries.append((module, kind, src, dest))
    return entries


def manifest_at(bp, commit):
    for path in (MANIFEST, *LEGACY_MANIFESTS):
        try:
            return parse_manifest(read_at(bp, commit, path).decode())
        except MajlesError:
            continue  # a commit from before a rename keeps its manifest elsewhere
    raise MajlesError(f"no manifest at {commit}")


class GitSource:
    """The template at commits of a Majles git checkout. The lock records a commit."""

    kind = "commit"

    def __init__(self, root):
        self.root = pathlib.Path(root)

    def current(self):
        return head(self.root)

    def read(self, ref, path):
        return read_at(self.root, ref, path)

    def manifest(self, ref):
        return manifest_at(self.root, ref)

    def has(self, ref):
        return has_commit(self.root, ref)

    def label(self, ref):
        return ref[:7]

    def describe(self):
        return str(self.root).replace(str(pathlib.Path.home()), "~")


class PackageSource:
    """The template packaged with an installed Majles. It holds one version only,
    so it can read files at that version and no other. The lock records the version."""

    kind = "version"

    def __init__(self, root, version=__version__):
        self.root, self.version = pathlib.Path(root), version

    def current(self):
        return self.version

    def read(self, ref, path):
        if ref != self.version:
            raise MajlesError(f"this project is on Majles {ref}, and the installed Majles is {self.version}. "
                              f"Run `{SELF} sync --apply` first, or install majles=={ref}.")
        return (self.root / path).read_bytes()

    def manifest(self, ref):
        return parse_manifest(self.read(ref, MANIFEST).decode())

    def has(self, ref):
        return ref == self.version

    def label(self, ref):
        return ref

    def describe(self):
        return "majles package"


def as_source(bp):
    """A source from a path: a git checkout is read by commit, anything else as a packaged template."""
    if isinstance(bp, (GitSource, PackageSource)):
        return bp
    bp = pathlib.Path(bp)
    return GitSource(bp) if (bp / ".git").exists() else PackageSource(bp)


def default_source():
    """The checkout this module runs from, else the template packaged with it."""
    if (BP_ROOT / ".git").exists() and (BP_ROOT / MANIFEST).is_file():
        return GitSource(BP_ROOT)
    if (PACKAGED / MANIFEST).is_file():
        return PackageSource(PACKAGED)
    if (BP_ROOT / MANIFEST).is_file():  # a source tree without git, such as an unpacked sdist
        return PackageSource(BP_ROOT)
    raise MajlesError(f"no template found: neither a git checkout at {BP_ROOT} nor a packaged one at {PACKAGED}")


def recorded(lock):
    """(kind, ref) of what the project last synced to: a version, or a commit."""
    if "version" in lock:
        return "version", lock["version"]
    return "commit", lock.get("commit")


def lock_ref(src, lock):
    """The project's recorded ref if `src` can read it, else None (it was synced from the other kind)."""
    kind, ref = recorded(lock)
    return ref if kind == src.kind else None


def recorded_label(lock):
    kind, ref = recorded(lock)
    return (ref or "?")[:7] if kind == "commit" else ref


def set_ref(src, lock, ref):
    lock.pop("commit", None)
    lock.pop("version", None)
    lock[src.kind] = ref
    lock["source"] = src.describe()


def ref_for_modules(src, lock):
    """The ref enable and disable read the manifest at: the one the project is on."""
    ref = lock_ref(src, lock)
    if ref is None:
        raise MajlesError(f"this project was last synced from a Majles {recorded(lock)[0]}, and this Majles "
                          f"reads by {src.kind}. Run `{SELF} sync --apply` first.")
    return ref


# ---------------------------------------------------------------- project


def digest(data):
    return hashlib.sha256(data).hexdigest()


def lock_path(project):
    """The project's lock file: .majles.json, or the pre-rename name while it is not migrated."""
    if not (project / LOCK).exists():
        for old in LEGACY_LOCKS:
            if (project / old).exists():
                return project / old
    return project / LOCK


def has_lock(project):
    return lock_path(project).exists()


def load_lock(project):
    path = lock_path(project)
    if not path.exists():
        raise MajlesError(f"{project} has no {LOCK}: it was not created with Majles")
    return json.loads(path.read_text(encoding="utf-8"))


def save_lock(project, lock):
    lock_path(project).write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write(project, dest, data):
    p = project / dest
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    if dest.startswith(".githooks/"):
        p.chmod(0o755)  # git silently skips a hook that is not executable


def projects_root(arg=None):
    """Where projects live: --root, then $MAJLES_ROOT, then the current directory."""
    chosen = arg or os.environ.get(ROOT_ENV) or os.environ.get(LEGACY_ROOT_ENV) or "."
    return pathlib.Path(chosen).expanduser().resolve()


def resolve_project(arg):
    return pathlib.Path(arg).expanduser().resolve() if arg else pathlib.Path.cwd()


# ---------------------------------------------------------------- commands


def cmd_new(bp, target, root=None):
    project = pathlib.Path(target).expanduser()
    if "/" not in target and not project.is_absolute():
        project = (root or projects_root()) / target
    project = project.resolve()
    if project.exists() and any(project.iterdir()):
        raise MajlesError(f"{project} already exists and is not empty")
    source = as_source(bp)
    ref = source.current()
    lock = {"modules": list(DEFAULT_MODULES), "files": {}, "once": [], "detached": []}
    set_ref(source, lock, ref)
    for module, kind, src, dest in source.manifest(ref):
        if module not in DEFAULT_MODULES:
            continue
        data = source.read(ref, src)
        write(project, dest, data)
        if kind == "shared":
            lock["files"][dest] = digest(data)
        else:
            lock["once"].append(dest)
    lock["once"].sort()
    save_lock(project, lock)
    print(f"Created {shown(project)} from Majles @{source.label(ref)}.")
    print(f"Next: cd {shown(project)} && claude, then say \"set up this project\".")
    return 0


def cmd_enable(bp, module, project):
    source = as_source(bp)
    lock = load_lock(project)
    if module in lock["modules"]:
        print(f"{module} is already on.")
        return 0
    ref = ref_for_modules(source, lock)
    entries = [e for e in source.manifest(ref) if e[0] == module]
    if not entries:
        raise MajlesError(f"no module '{module}' in the Majles version this project is on "
                      f"(@{source.label(ref)}). Sync first, or check the name.")
    clashes = [d for _, k, s, d in entries
               if k == "shared" and (project / d).exists()
               and (project / d).read_bytes() != source.read(ref, s)]
    if clashes:
        raise MajlesError("these files already exist with different content: " + ", ".join(clashes))
    for _, kind, src, dest in entries:
        data = source.read(ref, src)
        if kind == "shared":
            write(project, dest, data)
            lock["files"][dest] = digest(data)
            print(f"  added   {dest}")
        elif not (project / dest).exists():
            write(project, dest, data)
            lock["once"] = sorted(set(lock["once"]) | {dest})
            print(f"  added   {dest}  (template: fill it in; the project owns it)")
    lock["modules"].append(module)
    save_lock(project, lock)
    print(f"{module} is on.")
    return 0


def cmd_disable(bp, module, project):
    if module == "core":
        raise MajlesError("core cannot be turned off")
    lock = load_lock(project)
    if module not in lock["modules"]:
        print(f"{module} is already off.")
        return 0
    source = as_source(bp)
    entries = [e for e in source.manifest(ref_for_modules(source, lock)) if e[0] == module]
    edited = [d for _, k, _, d in entries if k == "shared" and d in lock["files"]
              and (project / d).exists() and digest((project / d).read_bytes()) != lock["files"][d]]
    if edited:
        raise MajlesError("edited in this project, so not removed: " + ", ".join(edited)
                      + ". Restore them or delete them by hand first.")
    for _, kind, _, dest in entries:
        if kind == "shared" and dest in lock["files"]:
            (project / dest).unlink(missing_ok=True)
            del lock["files"][dest]
            print(f"  removed {dest}")
        elif kind == "once" and (project / dest).exists():
            print(f"  kept    {dest}  (project-owned; delete by hand if unwanted)")
    lock["modules"].remove(module)
    save_lock(project, lock)
    print(f"{module} is off.")
    return 0


def cmd_adopt(bp, project, modules, apply, show_diff):
    """Bring a project that was not created with `new` under Majles.

    Every shared file is set to the Majles version: added where missing,
    replaced where it differs. The dry run lists each replacement, so anything
    project-specific in those files can be moved to a project-owned file first.
    Once files are never overwritten; a missing one is added as a template. A kept
    CLAUDE.md gets the template beside it, for setup to merge, and a kept .gitignore
    or README.md is listed with the template lines it lacks."""
    if has_lock(project):
        raise MajlesError(f"{project} already has {lock_path(project).name}; use sync")
    if "core" not in modules:
        modules = ["core"] + modules
    source = as_source(bp)
    ref = source.current()
    entries = source.manifest(ref)
    unknown = sorted(set(modules) - {m for m, _, _, _ in entries})
    if unknown:
        raise MajlesError(f"unknown modules: {', '.join(unknown)}")
    lock = {"modules": modules, "files": {}, "once": [], "detached": []}
    set_ref(source, lock, ref)
    print(f"{project.name}: adopting Majles @{source.label(ref)} with modules {', '.join(modules)}")
    plan = []
    for module, kind, src, dest in entries:
        if module not in modules:
            continue
        data, p = source.read(ref, src), project / dest
        if kind == "once":
            lock["once"].append(dest)
            if not p.exists():
                plan.append(("add-template", dest, data))
            elif dest == "CLAUDE.md" and p.read_bytes() != data:
                print(f"  keep    {dest}  (project-owned; the template goes beside it as "
                      f"{CLAUDE_BESIDE}, and setup merges the two)")
                plan.append(("add", CLAUDE_BESIDE, data))
            else:
                print(f"  keep    {dest}  (project-owned)")
                for line in lacking(dest, p.read_bytes(), data):
                    print(f"          lacks: {line}")
            continue
        lock["files"][dest] = digest(data)
        if not p.exists():
            plan.append(("add", dest, data))
        elif p.read_bytes() != data:
            plan.append(("update", dest, data))
    for action, dest, data in plan:
        describe(project, action, dest, data, show_diff)
    if not apply:
        print("  (dry run: nothing written. Move anything project-specific out of the files\n"
              "   marked 'update' first, since they are replaced. Then add --apply.)")
        return 0
    for action, dest, data in plan:
        write(project, dest, data)
    lock["once"].sort()
    save_lock(project, lock)
    print(f"  adopted. Review with `git diff`, then: "
          f"git add -A && git commit -m \"adopt majles @{source.label(ref)}\"")
    print("  Next: in Claude, say \"set up this project from SETUP.md\".")
    return 0


def lacking(dest, ours, template):
    """The lines of the template `dest` that the project's own copy does not have, for the
    files in COMPARED: .gitignore patterns and README.md section headings. Others: none."""
    counts = COMPARED.get(dest)
    if counts is None:
        return []
    have = {line.strip() for line in ours.decode("utf-8", errors="replace").splitlines()}
    lines = (line.strip() for line in template.decode("utf-8", errors="replace").splitlines())
    return [line for line in lines if counts(line) and line not in have]


def plan_sync(bp, project, lock, commit, take=()):
    """Work out what a sync to `commit` (a commit or a version) would do. Returns (actions, conflicts).

    It reads files only at the target, and compares the project's files with the
    hashes recorded in the lock, so it works when the old version's files are gone."""
    source = as_source(bp)
    entries = [e for e in source.manifest(commit) if e[0] in lock["modules"]]
    detached = set(lock.get("detached", []))
    actions, conflicts = [], []
    wanted = set()
    moved = {}  # new dest -> old dest, for shared files Majles renamed
    shared_dests = {d for _, k, _, d in entries if k == "shared"}
    for old, new in RENAMED.items():
        if old not in lock["files"] or old in detached or new in lock["files"] or new not in shared_dests:
            continue
        p = project / old
        if p.exists() and digest(p.read_bytes()) != lock["files"][old] and old not in take:
            conflicts.append((old, f"renamed to {new}, but edited here"))
            wanted |= {old, new}  # leave both alone until the conflict is resolved
        else:
            moved[new] = old
            wanted.add(old)
    for _, kind, src, dest in entries:
        if dest in detached or (dest in wanted and dest not in moved):
            continue
        if dest in moved:
            wanted.add(dest)
            actions.append(("move", dest, source.read(commit, src), moved[dest]))
            continue
        p = project / dest
        if kind == "once":
            # The setup guide is for a project being set up, so `new` and `adopt` bring it;
            # sync never adds it to a project that already exists.
            if dest == SETUP_GUIDE:
                continue
            if dest not in lock.get("once", []) and not p.exists():
                actions.append(("add-template", dest, source.read(commit, src)))
            continue
        wanted.add(dest)
        new = source.read(commit, src)
        recorded = lock["files"].get(dest)
        if not p.exists():
            if recorded is None or dest in take:
                actions.append(("add", dest, new))
            else:
                conflicts.append((dest, "deleted in this project"))
            continue
        current = digest(p.read_bytes())
        if current == digest(new):
            if recorded != current:
                actions.append(("track", dest, new))
            continue
        if (recorded is None or current != recorded) and dest not in take:
            why = "exists here but was never synced" if recorded is None else "edited in this project"
            conflicts.append((dest, why))
            continue
        actions.append(("update", dest, new))
    for module, files in RETIRED.items():
        if module in lock["modules"]:
            for dest in files:
                if dest in lock["files"] and dest not in detached and (project / dest).exists():
                    wanted.add(dest)
                    actions.append(("release", dest, None))
    for dest, recorded in lock["files"].items():
        if dest in wanted or dest in detached:
            continue
        p = project / dest
        if not p.exists():
            actions.append(("forget", dest, None))
        elif digest(p.read_bytes()) == recorded or dest in take:
            actions.append(("remove", dest, None))
        else:
            conflicts.append((dest, "removed from Majles, but edited here"))
    return [a if len(a) == 4 else (*a, None) for a in actions], conflicts


def describe(project, action, dest, data, show_diff, old=None):
    if action == "move":
        print(f"  move    {old} -> {dest}")
    elif action == "update":
        old = (project / dest).read_text(encoding="utf-8", errors="replace").splitlines()
        new = data.decode("utf-8", errors="replace").splitlines()
        diff = list(difflib.unified_diff(old, new, f"a/{dest}", f"b/{dest}", lineterm=""))
        plus = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
        minus = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
        print(f"  update  {dest}  (+{plus} -{minus})")
        if show_diff:
            print("\n".join("          " + l for l in diff))
    elif action == "release":
        print(f"  keep    {dest}  (its module left Majles: the file is now the project's own)")
    elif action in ("add", "add-template", "remove"):
        label = {"add": "add", "add-template": "add", "remove": "remove"}[action]
        extra = "  (template: the project owns it)" if action == "add-template" else ""
        print(f"  {label:<7} {dest}{extra}")


def cmd_sync(bp, project, apply, show_diff, take):
    source = as_source(bp)
    lock = load_lock(project)
    commit = source.current()
    take = {t.strip("/") for t in take}
    actions, conflicts = plan_sync(source, project, lock, commit, take)
    visible = [a for a in actions if a[0] not in ("track", "forget")]
    print(f"{project.name}: @{recorded_label(lock)} -> majles @{source.label(commit)}")
    if not visible and not conflicts:
        print("  up to date")
    for action, dest, data, old in actions:
        describe(project, action, dest, data, show_diff, old)
    for dest, why in conflicts:
        print(f"  CONFLICT {dest}: {why}. Left untouched.")
    if conflicts:
        print(f"  Resolve each one: `--take {conflicts[0][0]}` replaces it with the Majles "
              f"version, or `majles detach {conflicts[0][0]}` keeps this project's version for good.")
    if not apply:
        if visible:
            print("  (dry run: nothing written. Add --apply to write.)")
        return 1 if conflicts else 0
    for action, dest, data, old in actions:
        if action == "move":
            write(project, dest, data)
            (project / old).unlink(missing_ok=True)
            lock["files"].pop(old, None)
            lock["files"][dest] = digest(data)
        elif action in ("add", "update", "track"):
            if action != "track":
                write(project, dest, data)
            lock["files"][dest] = digest(data)
        elif action == "add-template":
            write(project, dest, data)
            lock["once"] = sorted(set(lock.get("once", [])) | {dest})
        elif action in ("remove", "forget"):
            (project / dest).unlink(missing_ok=True)
            lock["files"].pop(dest, None)
        elif action == "release":
            lock["files"].pop(dest, None)
            lock["detached"] = sorted(set(lock.get("detached", [])) | {dest})
    lock["modules"] = [m for m in lock["modules"] if m not in RETIRED]
    if not conflicts:
        set_ref(source, lock, commit)
    save_lock(project, lock)
    if visible or not conflicts:
        state = "synced" if not conflicts else "partly synced; the recorded version stays until conflicts are resolved"
        print(f"  {state}. Review with `git diff`, then: "
              f"git add -A && git commit -m \"sync majles @{source.label(commit)}\"")
    return 1 if conflicts else 0


def cmd_sync_all(bp, apply, show_diff, root=None):
    bp = as_source(bp)
    root = root or projects_root()
    projects = sorted(p for p in root.iterdir()
                      if p.is_dir() and has_lock(p) and p.resolve() != bp.root.resolve())
    if not projects:
        print(f"No projects under {root} were created with Majles.")
        return 0
    status = 0
    for p in projects:
        status |= cmd_sync(bp, p, apply, show_diff, ())
        print()
    return status


def update_notice(bp, project):
    source = as_source(bp)
    lock = load_lock(project)
    commit = source.current()
    ref = lock_ref(source, lock)
    if commit == ref:
        return None
    if source.kind == "commit" and ref is not None and not source.has(ref):
        changed = ["(recorded commit not found in the Majles checkout)"]
    else:
        actions, conflicts = plan_sync(source, project, lock, commit)
        changed = [d for a, d, _, _ in actions if a not in ("track", "forget")] + [d for d, _ in conflicts]
    if not changed:
        return None
    n = len(changed)
    return (f"Majles update available: {n} shared file{'s' if n != 1 else ''} changed "
            f"since this project last synced. Preview with: {SELF} sync")


def lint_notice(project):
    n = len(lint(project))
    if not n:
        return None
    return f"Lint: {n} finding{'s' if n != 1 else ''}. Run: {SELF} lint"


def cmd_check(bp, project):
    """For the SessionStart hook: say something only when there is something to do.
    Never fails loudly; a broken check must not break a session, and a broken
    lint must not hide the update notice."""
    try:
        bp = as_source(bp)
        if not has_lock(project) or project.resolve() == bp.root.resolve():
            return 0
    except Exception:
        return 0
    notices = []
    for notice in (lambda: update_notice(bp, project), lambda: lint_notice(project),
                   lambda: migrate_notice(project)):
        try:
            msg = notice()
        except Exception:
            msg = None
        if msg:
            notices.append(msg)
    if not notices:
        return 0
    msg = "\n".join(notices)
    try:
        print(json.dumps({
            "systemMessage": msg,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": msg + "\nMention this to the developer once. Do not sync unless "
                                           "they ask (.claude/rules/majles.md).",
            },
        }))
    except Exception:
        pass
    return 0


def migrate_notice(project):
    if lock_path(project).name in LEGACY_LOCKS:
        return f"This project predates the rename to Majles. Run: {SELF} migrate"
    return None


def old_hook_commands(settings):
    """The SessionStart hook commands in `settings` that call the pre-rename script."""
    found = []
    for group in settings.get("hooks", {}).get("SessionStart", []):
        for hook in group.get("hooks", []):
            command = hook.get("command", "")
            if any(mark in command for mark in LEGACY_HOOK_MARKS) and " check " in command:
                found.append(command)
    return found


def cmd_migrate(project):
    """Move a project made under an earlier name onto Majles: the lock file and the hook.
    The renamed shared rule is moved by the next sync."""
    if not project.is_dir():
        raise MajlesError(f"{project} is not a directory")
    changed = False
    new_lock = project / LOCK
    old_locks = [project / old for old in LEGACY_LOCKS if (project / old).exists()]
    if old_locks and new_lock.exists():
        raise MajlesError(f"{project} has both {old_locks[0].name} and {LOCK}; keep one by hand")
    if len(old_locks) > 1:
        raise MajlesError(f"{project} has {' and '.join(p.name for p in old_locks)}; keep one by hand")
    if old_locks:
        old_lock = old_locks[0]
        lock = json.loads(old_lock.read_text(encoding="utf-8"))
        if "boilerplate" in lock:  # the oldest key for where the project came from
            lock["source"] = lock.pop("boilerplate")
        old_lock.rename(new_lock)
        save_lock(project, lock)
        print(f"  renamed {old_lock.name} -> {LOCK}")
        changed = True
    elif not new_lock.exists():
        raise MajlesError(f"{project} has no {LOCK}: it was not created with Majles")
    settings_path = project / ".claude" / "settings.json"
    if settings_path.exists():
        raw = settings_path.read_text(encoding="utf-8")
        try:
            commands = old_hook_commands(json.loads(raw))
        except (ValueError, AttributeError):
            commands = []
            print("  skipped .claude/settings.json: not valid JSON")
        for command in commands:
            raw = raw.replace(json.dumps(command), json.dumps(HOOK_COMMAND))  # keeps the file's layout
        if commands:
            settings_path.write_text(raw, encoding="utf-8")
            print("  updated the SessionStart hook in .claude/settings.json")
            changed = True
    if not changed:
        print(f"{project.name}: already on Majles")
        return 0
    print(f"{project.name}: migrated. Next: `{SELF} sync` (moves the renamed rule), "
          "then review with `git diff` and commit on a branch.")
    return 0


def cmd_detach(project, path):
    lock = load_lock(project)
    path = path.strip("/")
    if path not in lock["files"]:
        raise MajlesError(f"{path} is not a shared file in this project")
    del lock["files"][path]
    lock["detached"] = sorted(set(lock.get("detached", [])) | {path})
    save_lock(project, lock)
    print(f"{path} now belongs to this project. Sync will skip it.")
    return 0


# ---------------------------------------------------------------- research


DEPTHS = ("Shallow", "Medium", "Deep")
MAX_OPEN = 4
MAX_QUESTIONS = 4
STALE_DAYS = 90
MAX_ADRS_PER_SLICE = 5
MAX_CLAUDE_BYTES = 16_000
MAX_RULE_BYTES = 5_000
NEEDED_BY_SINCE = "2026-10-23"  # ADRs dated before slices existed are not asked for `Needed by:`
QUESTION = re.compile(r"^###\s+(Q\d+)\b(.*)$")
DEPTH_WORD = re.compile(r"\b(Shallow|Medium|Deep)\b", re.I)


def read_lines(path):
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def field(lines, key):
    """The value of a `Key: value` line, allowing **bold** around the key; None if absent."""
    pattern = re.compile(rf"^\**{re.escape(key)}\**:\**\s*(.*)$", re.I)
    for line in lines:
        m = pattern.match(line.strip())
        if m:
            return m.group(1).strip()
    return None


def section(lines, heading):
    """The lines under `## heading`, up to the next `## `."""
    out, inside = [], False
    for line in lines:
        if line.startswith("## "):
            inside = line[3:].strip().lower() == heading.lower()
            continue
        if inside:
            out.append(line)
    return out


def lint_request(lines):
    """What an open request.md breaks in the research rules."""
    out = []
    first = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    header = lines[:first]
    depth = field(header, "Depth")
    named = {d.capitalize() for d in DEPTH_WORD.findall(depth or "")}
    if depth is None:
        out.append("no `Depth:` line in the header")
    elif len(named) != 1:
        out.append(f"`Depth: {depth}` must name exactly one of Shallow, Medium, Deep")
    if not field(header, "Blocks"):
        out.append("no `Blocks:` line in the header: name the next step that waits for this")

    questions, current = [], None
    for line in lines[first:]:
        m = QUESTION.match(line)
        if m:
            current = {"id": m.group(1), "depths": DEPTH_WORD.findall(m.group(2)), "body": []}
            questions.append(current)
        elif line.startswith("#"):
            current = None
        elif current is not None:
            current["body"].append(line)
    if not questions:
        out.append("no questions: write each as `### Q1. <the question>`")
    if len(questions) > MAX_QUESTIONS:
        out.append(f"{len(questions)} questions; at most {MAX_QUESTIONS} per request")
    for q in questions:
        named |= {d.capitalize() for d in q["depths"]}
        if not field(q["body"], "Changes"):
            out.append(f"{q['id']} has no `Changes:` line: the decision it feeds, and the answer that flips it")
    if len(named) > 1:
        out.append(f"mixed depths ({', '.join(d for d in DEPTHS if d in named)}): "
                   "split into one request per depth")
    return out


def lint(project):
    """Findings, one string each, for the rules a script can check.

    A research task is open while it has request.md and no findings.md. Only open
    requests are held to the request format: completed tasks are checked only for
    their decision.md, so research done before these rules is not flagged."""
    out = []
    research = project / "docs" / "research"
    open_requests = []
    for task in sorted(p for p in research.glob("*") if p.is_dir()):
        rel = task.relative_to(project).as_posix()
        if (task / "findings.md").exists():
            if not (task / "decision.md").exists():
                out.append(f"{rel}/: has findings.md but no decision.md")
            continue
        if (task / "request.md").exists():
            open_requests.append(rel)
            out += [f"{rel}/request.md: {m}" for m in lint_request(read_lines(task / "request.md"))]
    if len(open_requests) > MAX_OPEN:
        out.append(f"docs/research/: {len(open_requests)} open requests; at most {MAX_OPEN} "
                   "without the developer's yes")

    accepted = False
    per_slice = collections.Counter()
    for adr in sorted((project / "docs" / "adr").glob("[0-9][0-9][0-9][0-9]-*.md")):
        rel, lines = adr.relative_to(project).as_posix(), read_lines(adr)
        status = field(lines, "Status")
        if status is None:
            out.append(f"{rel}: no `Status:` line")
        elif status.lower().startswith("accepted"):
            accepted = True
            if (field(lines, "Date") or "") >= NEEDED_BY_SINCE and field(lines, "Needed by") is None:
                out.append(f"{rel}: accepted with no `Needed by: slice N` line")
        if field(lines, "Research") is None:
            out.append(f"{rel}: no `Research:` line")

        needed = (field(lines, "Needed by") or "").lower()
        if status and status.lower().startswith("accepted") and needed.startswith("slice"):
            per_slice[needed.split()[1].rstrip(".,;") if len(needed.split()) > 1 else "?"] += 1
    for n, count in sorted(per_slice.items()):
        if count > MAX_ADRS_PER_SLICE:
            out.append(f"docs/adr/: {count} accepted ADRs needed by slice {n}; expect a handful. "
                       "What a user gets belongs in a spec, not an ADR (.claude/rules/decisions.md)")

    claude = project / "CLAUDE.md"
    if accepted and claude.exists() and any(l.strip() == "## Phase 0 brief" for l in read_lines(claude)):
        out.append("CLAUDE.md: still has the Phase 0 brief, but docs/adr/ holds an accepted ADR. "
                   "The status may be stale.")
    out += lint_standing(project)
    out += lint_main_guard(project)
    # Before setup, placeholders are expected; after it (no setup block in CLAUDE.md), one left is a slip.
    if setup_done(project):
        out += [f"{f}: placeholder left after setup" for f in placeholders(project)]
    return out


def lint_standing(project):
    """CLAUDE.md and the rules go with every call of every agent (.claude/rules/tokens.md)."""
    out = []
    claude = project / "CLAUDE.md"
    if claude.exists() and claude.stat().st_size > MAX_CLAUDE_BYTES:
        out.append(f"CLAUDE.md: {claude.stat().st_size // 1000} KB; keep it under {MAX_CLAUDE_BYTES // 1000} KB. "
                   "Move later slices, history and detail to docs/ (.claude/rules/tokens.md)")
    for rule in sorted((project / ".claude" / "rules").glob("*.md")):
        if rule.stat().st_size > MAX_RULE_BYTES:
            out.append(f".claude/rules/{rule.name}: {rule.stat().st_size // 1000} KB; a rule over "
                       f"{MAX_RULE_BYTES // 1000} KB belongs in docs/ (.claude/rules/tokens.md)")
    return out


def lint_main_guard(project):
    """The main-branch guard is a local hook; it does nothing until the clone points git at it."""
    if not (project / ".githooks" / "pre-push").exists() or not (project / ".git").exists():
        return []
    r = subprocess.run(["git", "-C", str(project), "config", "core.hooksPath"], capture_output=True)
    configured = r.stdout.decode().strip()
    if configured and (project / configured).resolve() == (project / ".githooks").resolve():
        return []  # relative, or this clone's own .githooks by absolute path
    return [".githooks/pre-push is off in this clone, so nothing stops a push to main. "
            "Run: git config core.hooksPath .githooks (.claude/rules/git.md)"]


SETUP_GUIDE = "SETUP.md"  # the setup procedure, shipped once; its examples are not placeholders
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")


def placeholders(project):
    """`path:line: {{NAME}}` for every placeholder left in a file the project owns.

    Only the files Majles installed as the project's own (the lock's "once" list) are
    read, never footage, generated files or anything else in the repo."""
    lock = load_lock(project) if has_lock(project) else {"once": ["CLAUDE.md", "README.md"]}
    out = []
    for rel in sorted(set(lock.get("once", [])) - {SETUP_GUIDE}):
        f = project / rel
        if not f.is_file():
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            out += [f"{rel}:{n}: {{{{{name}}}}}" for name in PLACEHOLDER.findall(line)]
    return out


def setup_done(project):
    """Setup is done once the SETUP.md it installed is gone. Projects made before SETUP.md
    shipped never received it, so they are not checked."""
    if not has_lock(project):
        return False
    return SETUP_GUIDE in load_lock(project).get("once", []) and not (project / SETUP_GUIDE).exists()


def cmd_placeholders(project):
    if not project.is_dir():
        raise MajlesError(f"{project} is not a directory")
    found = placeholders(project)
    for f in found:
        print(f)
    if not found:
        print(f"{project.name}: no placeholders left")
    return 1 if found else 0


def shown(path):
    """A path as a person reads it: under the home folder it starts with ~, so a printed
    path never spells out the user's name (and recordings of the tool stay neutral)."""
    path = pathlib.Path(path)
    try:
        return "~/" + path.resolve().relative_to(pathlib.Path.home().resolve()).as_posix()
    except ValueError:
        return str(path)


def cmd_lint(project):
    if not project.is_dir():
        raise MajlesError(f"{project} is not a directory")
    findings = lint(project)
    for f in findings:
        print(f)
    if not findings:
        print(f"{project.name}: clean")
    return 1 if findings else 0


def cmd_research_find(words, root=None, today=None):
    """List earlier research whose request title or decision matches every word."""
    today = today or datetime.date.today()
    root = root or projects_root()
    words = [w.lower() for w in words]
    hits = []
    for task in root.glob("*/docs/research/*"):
        if not task.is_dir():
            continue
        title, text = "", []
        if (task / "request.md").exists():
            lines = read_lines(task / "request.md")
            title = next((l[2:].strip() for l in lines if l.startswith("# ")), "")
            title = re.sub(r"^Research request:\s*", "", title, flags=re.I)
            text.append(title)
        if (task / "decision.md").exists():
            lines = read_lines(task / "decision.md")
            text += section(lines, "The decision")
            if not title:
                title = next((re.sub(r"^Decision:\s*", "", l[2:].strip()) for l in lines
                              if l.startswith("# ")), "")
        haystack = " ".join(text).lower()
        if haystack and all(w in haystack for w in words):
            m = re.match(r"\d{4}-\d{2}-\d{2}", task.name)
            hits.append((m.group(0) if m else "????-??-??", task, title or task.name))
    if not hits:
        print("No earlier research matches.")
        return 1
    home = str(pathlib.Path.home())
    for date, task, title in sorted(hits, key=lambda h: (h[0], str(h[1])), reverse=True):
        try:
            stale = (today - datetime.date.fromisoformat(date)).days > STALE_DAYS
        except ValueError:
            stale = True
        path = str(task).replace(home, "~", 1) + "/"
        print(f"{date}  {path}  {title}{'  stale' if stale else ''}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="majles", description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", action="version", version=f"majles {__version__}")
    ap.add_argument("--root", help="the directory that holds your projects "
                    f"(default: ${ROOT_ENV}, else the current directory)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new"); p.add_argument("slug")
    p = sub.add_parser("adopt"); p.add_argument("project", nargs="?")
    p.add_argument("--modules", default=",".join(DEFAULT_MODULES))
    p.add_argument("--apply", action="store_true"); p.add_argument("--diff", action="store_true")
    for name in ("enable", "disable"):
        p = sub.add_parser(name); p.add_argument("module"); p.add_argument("project", nargs="?")
    p = sub.add_parser("sync"); p.add_argument("project", nargs="?")
    p.add_argument("--apply", action="store_true"); p.add_argument("--diff", action="store_true")
    p.add_argument("--all", action="store_true"); p.add_argument("--take", action="append", default=[])
    p = sub.add_parser("check"); p.add_argument("project", nargs="?")
    p = sub.add_parser("detach"); p.add_argument("path"); p.add_argument("project", nargs="?")
    p = sub.add_parser("lint"); p.add_argument("project", nargs="?")
    p = sub.add_parser("placeholders"); p.add_argument("project", nargs="?")
    p = sub.add_parser("research-find"); p.add_argument("words", nargs="+")
    p = sub.add_parser("migrate"); p.add_argument("project", nargs="?")
    for p in sub.choices.values():  # --root is accepted after the command too
        p.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    root = projects_root(a.root)
    try:
        BP = default_source() if a.cmd not in ("detach", "lint", "placeholders", "research-find", "migrate") else None
        if a.cmd == "new":
            return cmd_new(BP, a.slug, root)
        if a.cmd == "adopt":
            mods = [m.strip() for m in a.modules.split(",") if m.strip()]
            return cmd_adopt(BP, resolve_project(a.project), mods, a.apply, a.diff)
        if a.cmd == "enable":
            return cmd_enable(BP, a.module, resolve_project(a.project))
        if a.cmd == "disable":
            return cmd_disable(BP, a.module, resolve_project(a.project))
        if a.cmd == "sync":
            if a.all:
                return cmd_sync_all(BP, a.apply, a.diff, root)
            return cmd_sync(BP, resolve_project(a.project), a.apply, a.diff, a.take)
        if a.cmd == "check":
            return cmd_check(BP, resolve_project(a.project))
        if a.cmd == "detach":
            return cmd_detach(resolve_project(a.project), a.path)
        if a.cmd == "lint":
            return cmd_lint(resolve_project(a.project))
        if a.cmd == "placeholders":
            return cmd_placeholders(resolve_project(a.project))
        if a.cmd == "research-find":
            return cmd_research_find(a.words, root)
        if a.cmd == "migrate":
            return cmd_migrate(resolve_project(a.project))
    except MajlesError as e:
        print(f"majles: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
