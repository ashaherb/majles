"""Tests for the majles CLI.   python3 -m unittest discover -s majles -p 'test_*.py'

Each test builds a throwaway Majles git repo and a project created from it.
"""

import contextlib
import datetime
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from majles import cli as bp  # noqa: E402

MANIFEST = """
[core]
shared rules/a.md
shared rules/b.md
once   CLAUDE.md

[ui]
shared design/README.md

[i18n]
shared optional/i18n/i18n.md -> rules/i18n.md
once   optional/i18n/langs.md -> langs.md

[beads]
shared optional/beads/beads.md -> rules/beads.md
"""

FILES = {
    "majles/manifest.txt": MANIFEST,
    "rules/a.md": "rule a v1\n",
    "rules/b.md": "rule b v1\n",
    "CLAUDE.md": "# {{PROJECT_NAME}}\n",
    "design/README.md": "design v1\n",
    "optional/i18n/i18n.md": "i18n v1\n",
    "optional/i18n/langs.md": "{{LANGUAGES}}\n",
    "optional/beads/beads.md": "beads v1\n",
}


def run(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def quiet(fn, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.bp = root / "majles-repo"
        self.bp.mkdir()
        run("git", "init", "-q", "-b", "main", cwd=self.bp)
        for path, text in FILES.items():
            self.put(path, text, commit=False)
        self.commit("initial")
        self.project = root / "proj"
        quiet(bp.cmd_new, self.bp, str(self.project))

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, path, text, commit=True):
        p = self.bp / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        if commit:
            self.commit(f"change {path}")

    def commit(self, msg):
        run("git", "add", "-A", cwd=self.bp)
        run("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg, cwd=self.bp)

    def lock(self):
        return json.loads((self.project / bp.LOCK).read_text())

    def read(self, path):
        return (self.project / path).read_text()

    def sync(self, apply=True, take=()):
        return quiet(bp.cmd_sync, self.bp, self.project, apply, False, list(take))


class New(Base):
    def test_copies_default_modules_and_records_them(self):
        self.assertEqual(self.read("rules/a.md"), "rule a v1\n")
        self.assertEqual(self.read("design/README.md"), "design v1\n")
        self.assertFalse((self.project / "rules/i18n.md").exists())
        lock = self.lock()
        self.assertEqual(lock["modules"], ["core", "ui", "beads"])
        self.assertEqual(self.read("rules/beads.md"), "beads v1\n")
        self.assertEqual(sorted(lock["files"]),
                         ["design/README.md", "rules/a.md", "rules/b.md", "rules/beads.md"])
        self.assertEqual(lock["once"], ["CLAUDE.md"])
        self.assertEqual(lock["commit"], bp.head(self.bp))

    def test_refuses_a_non_empty_directory(self):
        with self.assertRaises(bp.MajlesError):
            bp.cmd_new(self.bp, str(self.project))

    def test_uses_committed_content_not_the_working_tree(self):
        (self.bp / "rules/a.md").write_text("uncommitted\n")
        other = pathlib.Path(self.tmp.name) / "other"
        quiet(bp.cmd_new, self.bp, str(other))
        self.assertEqual((other / "rules/a.md").read_text(), "rule a v1\n")


class Placeholders(Base):
    """`majles placeholders` reads only the files the project owns."""

    def test_lists_the_owned_files_only(self):
        (self.project / "footage.cast").write_text('[0, "o", "{{PROJECT_NAME}}"]\n')
        code, out = quiet(bp.cmd_placeholders, self.project)
        self.assertEqual(code, 1)
        self.assertIn("CLAUDE.md:1: {{PROJECT_NAME}}", out)
        self.assertNotIn("footage.cast", out)

    def test_clean_once_filled(self):
        (self.project / "CLAUDE.md").write_text("# Demo\n")
        self.assertEqual(quiet(bp.cmd_placeholders, self.project)[0], 0)

    def test_lint_flags_a_leftover_only_after_setup(self):
        lock = self.lock()
        lock["once"] = sorted(set(lock["once"]) | {bp.SETUP_GUIDE})
        (self.project / bp.LOCK).write_text(json.dumps(lock))
        (self.project / bp.SETUP_GUIDE).write_text("Placeholders look like `{{LIKE_THIS}}`.\n")
        self.assertFalse([f for f in bp.lint(self.project) if "placeholder" in f], "setup is not done yet")
        (self.project / bp.SETUP_GUIDE).unlink()
        self.assertIn("CLAUDE.md:1: {{PROJECT_NAME}}: placeholder left after setup", bp.lint(self.project))


class Retired(Base):
    """A module Majles stops shipping: its files stay in the project, as the project's own."""

    def setUp(self):
        super().setUp()
        self.put("majles/manifest.txt", MANIFEST + "\n[old]\nshared optional/old/old.md -> rules/old.md\n",
                 commit=False)
        self.put("optional/old/old.md", "old v1\n")
        quiet(bp.cmd_sync, self.bp, self.project, True, False, [])
        quiet(bp.cmd_enable, self.bp, "old", self.project)
        self.put("majles/manifest.txt", MANIFEST, commit=False)
        (self.bp / "optional/old/old.md").unlink()
        self.commit("retire old")

    def test_sync_keeps_a_retired_module_file_and_detaches_it(self):
        with mock.patch.dict(bp.RETIRED, {"old": ("rules/old.md",)}):
            code, out = self.sync(apply=False)
            self.assertIn("keep    rules/old.md", out)
            code, out = self.sync()
            self.assertEqual(code, 0, out)
            self.assertEqual(self.read("rules/old.md"), "old v1\n")
            lock = self.lock()
            self.assertIn("rules/old.md", lock["detached"])
            self.assertNotIn("rules/old.md", lock["files"])
            self.assertNotIn("old", lock["modules"])
            self.assertIn("up to date", self.sync()[1])


class FromMajlis(Base):
    """Projects made under the name Majlis: .majlis.json, the `majlis` hook, majlis.md."""

    OLD_HOOK = ('command -v maj' 'lis >/dev/null 2>&1 && maj' 'lis check "$CLAUDE_PROJECT_DIR" '
                '2>/dev/null; exit 0')
    OLD_LOCK = ".maj" "lis.json"
    OLD_RULE = ".claude/rules/maj" "lis.md"

    def make_majlis(self):
        (self.project / bp.LOCK).rename(self.project / self.OLD_LOCK)
        settings = {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": self.OLD_HOOK}]}]}}
        (self.project / ".claude").mkdir()
        (self.project / ".claude/settings.json").write_text(json.dumps(settings, indent=2) + "\n")

    def test_the_old_lock_is_read_and_migrate_converts_it(self):
        self.make_majlis()
        self.assertIn(self.OLD_LOCK, bp.LEGACY_LOCKS)
        self.assertEqual(bp.lock_path(self.project).name, self.OLD_LOCK)
        self.assertIn("migrate", bp.migrate_notice(self.project))
        code, out = quiet(bp.cmd_migrate, self.project)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.project / self.OLD_LOCK).exists())
        self.assertTrue((self.project / bp.LOCK).exists())
        hook = json.loads(self.read(".claude/settings.json"))["hooks"]["SessionStart"][0]["hooks"][0]
        self.assertEqual(hook["command"], bp.HOOK_COMMAND)
        self.assertIsNone(bp.migrate_notice(self.project))

    def test_sync_moves_the_old_rule(self):
        old, new = self.OLD_RULE, ".claude/rules/majles.md"
        self.put(old, "rule v1\n", commit=False)
        self.put("majles/manifest.txt", MANIFEST.replace("once   CLAUDE.md", f"shared {old}\nonce   CLAUDE.md"))
        self.sync()
        run("git", "mv", old, new, cwd=self.bp)
        self.put("majles/manifest.txt", MANIFEST.replace("once   CLAUDE.md", f"shared {new}\nonce   CLAUDE.md"))
        code, out = self.sync()
        self.assertEqual(code, 0, out)
        self.assertFalse((self.project / old).exists())
        self.assertEqual(self.read(new), "rule v1\n")

    def test_the_manifest_is_found_at_a_commit_from_the_majlis_layout(self):
        old = bp.head(self.bp)
        run("git", "mv", "majles", "maj" "lis", cwd=self.bp)
        self.commit("majlis layout")
        self.assertEqual(bp.manifest_at(self.bp, bp.head(self.bp)), bp.manifest_at(self.bp, old))

    def test_the_old_root_variable_still_works(self):
        with mock.patch.dict(os.environ, {"MAJLES_ROOT": "", "MAJ" "LIS_ROOT": str(self.project.parent)}):
            os.environ.pop("MAJLES_ROOT")
            self.assertEqual(bp.projects_root(), self.project.parent.resolve())


class Legacy(Base):
    """Projects made before the rename from "boilerplate" to Majles."""

    # The old script's name is on the blocklist in test_template.py, so it is built from parts.
    OLD_HOOK = ('f="$HOME/x/project-boilerplate/boilerplate/' 'bp' '.py"; [ -f "$f" ] && '
                'python3 "$f" check "$CLAUDE_PROJECT_DIR" 2>/dev/null; exit 0')

    def make_legacy(self):
        lock = self.lock()
        lock["boilerplate"] = lock.pop("source")
        (self.project / bp.LOCK).rename(self.project / bp.LEGACY_LOCKS[-1])
        (self.project / bp.LEGACY_LOCKS[-1]).write_text(json.dumps(lock, indent=2))
        settings = {"fallbackModel": ["opus"], "hooks": {"SessionStart": [
            {"hooks": [{"type": "command", "command": self.OLD_HOOK, "timeout": 10}]}]}}
        (self.project / ".claude").mkdir()
        (self.project / ".claude/settings.json").write_text(json.dumps(settings, indent=2) + "\n")

    def test_the_old_lock_file_is_read_when_the_new_one_is_missing(self):
        self.make_legacy()
        self.put("rules/a.md", "rule a v2\n")
        code, _ = self.sync()
        self.assertEqual(code, 0)
        self.assertEqual(self.read("rules/a.md"), "rule a v2\n")
        self.assertFalse((self.project / bp.LOCK).exists())  # sync does not migrate
        self.assertEqual(json.loads((self.project / bp.LEGACY_LOCKS[-1]).read_text())["commit"], bp.head(self.bp))
        msg = json.loads(quiet(bp.cmd_check, self.bp, self.project)[1])["systemMessage"]
        self.assertIn("majles migrate", msg)

    def test_the_manifest_is_found_at_a_commit_from_before_the_rename(self):
        old = bp.head(self.bp)
        run("git", "mv", "majles", "boilerplate", cwd=self.bp)
        self.commit("old layout")
        self.assertEqual(bp.manifest_at(self.bp, bp.head(self.bp)), bp.manifest_at(self.bp, old))

    def test_migrate_renames_the_lock_and_rewrites_the_old_hook(self):
        self.make_legacy()
        code, out = quiet(bp.cmd_migrate, self.project)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.project / bp.LEGACY_LOCKS[-1]).exists())
        lock = self.lock()
        self.assertIn("source", lock)
        self.assertNotIn("boilerplate", lock)
        settings = json.loads(self.read(".claude/settings.json"))
        hook = settings["hooks"]["SessionStart"][0]["hooks"][0]
        self.assertEqual(hook["command"], bp.HOOK_COMMAND)
        self.assertEqual(hook["timeout"], 10)
        self.assertEqual(settings["fallbackModel"], ["opus"])
        self.assertIn("already on Majles", quiet(bp.cmd_migrate, self.project)[1])  # idempotent

    def test_migrate_leaves_a_custom_hook_alone(self):
        self.make_legacy()
        custom = {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "echo hi"}]}]}}
        (self.project / ".claude/settings.json").write_text(json.dumps(custom))
        quiet(bp.cmd_migrate, self.project)
        self.assertEqual(json.loads(self.read(".claude/settings.json")), custom)
        self.assertTrue((self.project / bp.LOCK).exists())

    def test_migrate_refuses_when_both_lock_files_exist(self):
        (self.project / bp.LEGACY_LOCKS[-1]).write_text("{}")
        with self.assertRaises(bp.MajlesError):
            bp.cmd_migrate(self.project)

    def renamed_rule(self):
        """A project with the old shared rule, then a Majles commit that renames it."""
        old, new = ".claude/rules/boilerplate.md", ".claude/rules/majles.md"
        self.put(old, "rule v1\n", commit=False)
        self.put("majles/manifest.txt", MANIFEST.replace("once   CLAUDE.md", f"shared {old}\nonce   CLAUDE.md"))
        self.sync()
        self.assertEqual(self.read(old), "rule v1\n")
        run("git", "mv", old, new, cwd=self.bp)
        self.put(new, "rule v2\n", commit=False)
        self.put("majles/manifest.txt", MANIFEST.replace("once   CLAUDE.md", f"shared {new}\nonce   CLAUDE.md"))
        return old, new

    def test_sync_moves_an_unchanged_renamed_rule(self):
        old, new = self.renamed_rule()
        code, out = self.sync(apply=False)
        self.assertIn(f"move    {old} -> {new}", out)
        code, out = self.sync()
        self.assertEqual(code, 0, out)
        self.assertFalse((self.project / old).exists())
        self.assertEqual(self.read(new), "rule v2\n")
        self.assertNotIn(old, self.lock()["files"])
        self.assertIn(new, self.lock()["files"])
        self.assertIn("up to date", self.sync()[1])

    def test_sync_leaves_an_edited_renamed_rule_as_a_conflict(self):
        old, new = self.renamed_rule()
        (self.project / old).write_text("ours\n")
        code, out = self.sync()
        self.assertEqual(code, 1)
        self.assertIn(f"CONFLICT {old}: renamed to {new}, but edited here", out)
        self.assertEqual(self.read(old), "ours\n")
        self.assertFalse((self.project / new).exists())
        code, _ = self.sync(take=[old])
        self.assertEqual(code, 0)
        self.assertFalse((self.project / old).exists())
        self.assertEqual(self.read(new), "rule v2\n")


class Root(Base):
    def test_root_is_the_option_then_the_env_then_the_cwd(self):
        tmp = pathlib.Path(self.tmp.name).resolve()
        with mock.patch.dict(os.environ, {"MAJLES_ROOT": str(tmp / "env")}):
            self.assertEqual(bp.projects_root(str(tmp / "opt")), tmp / "opt")
            self.assertEqual(bp.projects_root(), tmp / "env")
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch("os.getcwd", return_value=str(tmp)):
            self.assertEqual(bp.projects_root(), tmp)

    def test_new_puts_a_bare_slug_under_the_root(self):
        root = pathlib.Path(self.tmp.name) / "root"
        root.mkdir()
        quiet(bp.cmd_new, self.bp, "demo", root)
        self.assertTrue((root / "demo" / bp.LOCK).exists())

    def test_sync_all_scans_the_root(self):
        self.put("rules/a.md", "rule a v2\n")
        code, out = quiet(bp.cmd_sync_all, self.bp, True, False, pathlib.Path(self.tmp.name))
        self.assertEqual(code, 0)
        self.assertIn("proj:", out)
        self.assertEqual(self.read("rules/a.md"), "rule a v2\n")


class Sync(Base):
    def test_nothing_to_do_when_current(self):
        code, out = self.sync()
        self.assertEqual(code, 0)
        self.assertIn("up to date", out)

    def test_dry_run_reports_but_writes_nothing(self):
        self.put("rules/a.md", "rule a v2\n")
        code, out = self.sync(apply=False)
        self.assertIn("update  rules/a.md", out)
        self.assertEqual(self.read("rules/a.md"), "rule a v1\n")

    def test_apply_updates_and_advances_the_commit(self):
        self.put("rules/a.md", "rule a v2\n")
        code, _ = self.sync()
        self.assertEqual(code, 0)
        self.assertEqual(self.read("rules/a.md"), "rule a v2\n")
        self.assertEqual(self.lock()["commit"], bp.head(self.bp))

    def test_local_edit_is_a_conflict_and_is_never_overwritten(self):
        (self.project / "rules/a.md").write_text("edited here\n")
        before = self.lock()["commit"]
        self.put("rules/a.md", "rule a v2\n")
        self.put("rules/b.md", "rule b v2\n")
        code, out = self.sync()
        self.assertEqual(code, 1)
        self.assertIn("CONFLICT rules/a.md", out)
        self.assertEqual(self.read("rules/a.md"), "edited here\n")
        self.assertEqual(self.read("rules/b.md"), "rule b v2\n")  # the rest still syncs
        self.assertEqual(self.lock()["commit"], before)  # not advanced while a conflict stands

    def test_take_replaces_a_local_edit_with_the_majles_version(self):
        (self.project / "rules/a.md").write_text("edited here\n")
        self.put("rules/a.md", "rule a v2\n")
        code, _ = self.sync(take=["rules/a.md"])
        self.assertEqual(code, 0)
        self.assertEqual(self.read("rules/a.md"), "rule a v2\n")

    def test_once_files_are_never_touched(self):
        (self.project / "CLAUDE.md").write_text("# Filled in\n")
        self.put("CLAUDE.md", "# {{PROJECT_NAME}} v2\n")
        self.sync()
        self.assertEqual(self.read("CLAUDE.md"), "# Filled in\n")

    def test_new_shared_file_is_added(self):
        self.put("rules/c.md", "rule c\n", commit=False)
        self.put("majles/manifest.txt", MANIFEST.replace("once   CLAUDE.md", "shared rules/c.md\nonce   CLAUDE.md"))
        self.sync()
        self.assertEqual(self.read("rules/c.md"), "rule c\n")

    def test_new_files_in_core_reach_an_existing_project(self):
        # New shared agents and a new template, added to [core] after the project was made.
        self.put("agents/tester.md", "tester\n", commit=False)
        self.put("docs/backlog.md", "# Backlog\n", commit=False)
        self.put("majles/manifest.txt", MANIFEST.replace(
            "once   CLAUDE.md", "shared agents/tester.md\nonce   CLAUDE.md\nonce   docs/backlog.md"))
        code, out = self.sync(apply=False)
        self.assertIn("add     agents/tester.md", out)
        self.assertIn("add     docs/backlog.md  (template", out)
        self.assertIn("2 shared files changed", json.loads(quiet(bp.cmd_check, self.bp, self.project)[1])["systemMessage"])
        self.sync()
        self.assertEqual(self.read("agents/tester.md"), "tester\n")
        self.assertIn("agents/tester.md", self.lock()["files"])
        self.assertIn("docs/backlog.md", self.lock()["once"])
        (self.project / "docs/backlog.md").write_text("# Ours\n")
        self.put("docs/backlog.md", "# Backlog v2\n")
        self.sync()
        self.assertEqual(self.read("docs/backlog.md"), "# Ours\n")  # a template, never synced again

    def test_a_module_added_later_can_be_enabled_after_sync(self):
        self.put("optional/ai/ai.md", "ai\n", commit=False)
        self.put("majles/manifest.txt", MANIFEST + "\n[ai]\nshared optional/ai/ai.md -> agents/ai.md\n")
        with self.assertRaises(bp.MajlesError):  # the project's recorded version has no ai module yet
            bp.cmd_enable(self.bp, "ai", self.project)
        self.sync()
        quiet(bp.cmd_enable, self.bp, "ai", self.project)
        self.assertEqual(self.read("agents/ai.md"), "ai\n")

    def test_file_dropped_from_the_manifest_is_removed_if_unedited(self):
        self.put("majles/manifest.txt", MANIFEST.replace("shared rules/b.md\n", ""))
        self.sync()
        self.assertFalse((self.project / "rules/b.md").exists())
        self.assertNotIn("rules/b.md", self.lock()["files"])

    def test_detached_file_is_skipped_for_good(self):
        (self.project / "rules/a.md").write_text("ours now\n")
        quiet(bp.cmd_detach, self.project, "rules/a.md")
        self.put("rules/a.md", "rule a v2\n")
        code, _ = self.sync()
        self.assertEqual(code, 0)
        self.assertEqual(self.read("rules/a.md"), "ours now\n")


class Modules(Base):
    def test_enable_adds_shared_and_template_files(self):
        quiet(bp.cmd_enable, self.bp, "i18n", self.project)
        self.assertEqual(self.read("rules/i18n.md"), "i18n v1\n")
        self.assertEqual(self.read("langs.md"), "{{LANGUAGES}}\n")
        self.assertIn("i18n", self.lock()["modules"])
        self.put("optional/i18n/i18n.md", "i18n v2\n")
        self.sync()
        self.assertEqual(self.read("rules/i18n.md"), "i18n v2\n")

    def test_disable_removes_unedited_shared_files(self):
        quiet(bp.cmd_disable, self.bp, "ui", self.project)
        self.assertFalse((self.project / "design/README.md").exists())
        self.assertNotIn("ui", self.lock()["modules"])
        self.put("design/README.md", "design v2\n")
        self.sync()
        self.assertFalse((self.project / "design/README.md").exists())  # stays off

    def test_beads_is_on_by_default_and_can_be_turned_off(self):
        self.assertIn("beads", self.lock()["modules"])
        quiet(bp.cmd_disable, self.bp, "beads", self.project)
        self.assertFalse((self.project / "rules/beads.md").exists())
        self.assertNotIn("beads", self.lock()["modules"])
        self.put("optional/beads/beads.md", "beads v2\n")
        self.sync()
        self.assertFalse((self.project / "rules/beads.md").exists())  # stays off

    def test_sync_never_turns_on_a_module_an_existing_project_lacks(self):
        # A project created before beads became a default: its lock has no beads.
        lock = self.lock()
        lock["modules"].remove("beads")
        del lock["files"]["rules/beads.md"]
        (self.project / "rules/beads.md").unlink()
        bp.save_lock(self.project, lock)
        self.put("rules/a.md", "rule a v2\n")
        self.sync()
        self.assertEqual(self.read("rules/a.md"), "rule a v2\n")
        self.assertFalse((self.project / "rules/beads.md").exists())
        self.assertNotIn("beads", self.lock()["modules"])

    def test_disable_refuses_when_a_shared_file_was_edited(self):
        (self.project / "design/README.md").write_text("edited\n")
        with self.assertRaises(bp.MajlesError):
            bp.cmd_disable(self.bp, "ui", self.project)
        self.assertTrue((self.project / "design/README.md").exists())

    def test_unknown_module_is_an_error(self):
        with self.assertRaises(bp.MajlesError):
            bp.cmd_enable(self.bp, "nope", self.project)


class Adopt(Base):
    def existing(self):
        p = pathlib.Path(self.tmp.name) / "existing"
        (p / "rules").mkdir(parents=True)
        (p / "rules/a.md").write_text("rule a v1\n")          # already identical
        (p / "rules/b.md").write_text("our own rule b\n")     # differs
        (p / "CLAUDE.md").write_text("# Ours, filled in\n")   # once, present
        (p / "notes.md").write_text("project file\n")         # not in the manifest
        return p

    def test_dry_run_writes_nothing(self):
        p = self.existing()
        code, out = quiet(bp.cmd_adopt, self.bp, p, ["core"], False, False)
        self.assertIn("update  rules/b.md", out)
        self.assertEqual((p / "rules/b.md").read_text(), "our own rule b\n")
        self.assertFalse((p / bp.LOCK).exists())

    def test_apply_aligns_shared_files_and_keeps_owned_ones(self):
        p = self.existing()
        quiet(bp.cmd_adopt, self.bp, p, ["core", "i18n"], True, False)
        self.assertEqual((p / "rules/b.md").read_text(), "rule b v1\n")
        self.assertEqual((p / "rules/i18n.md").read_text(), "i18n v1\n")
        self.assertEqual((p / "langs.md").read_text(), "{{LANGUAGES}}\n")
        self.assertEqual((p / "CLAUDE.md").read_text(), "# Ours, filled in\n")
        self.assertEqual((p / "notes.md").read_text(), "project file\n")
        lock = json.loads((p / bp.LOCK).read_text())
        self.assertEqual(lock["modules"], ["core", "i18n"])
        self.assertFalse((p / "design/README.md").exists())  # ui not asked for
        self.project = p
        self.assertIn("up to date", self.sync()[1])

    def test_refuses_a_project_already_adopted(self):
        with self.assertRaises(bp.MajlesError):
            bp.cmd_adopt(self.bp, self.project, ["core"], True, False)

    def test_unknown_module_is_an_error(self):
        with self.assertRaises(bp.MajlesError):
            bp.cmd_adopt(self.bp, self.existing(), ["core", "nope"], True, False)


class Check(Base):
    def check(self):
        return quiet(bp.cmd_check, self.bp, self.project)[1]

    def test_silent_when_current(self):
        self.assertEqual(self.check(), "")

    def test_notice_when_a_shared_file_changed(self):
        self.put("rules/a.md", "rule a v2\n")
        out = json.loads(self.check())
        self.assertIn("1 shared file changed", out["systemMessage"])
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")

    def test_silent_when_only_unshipped_files_changed(self):
        self.put("NOTES.md", "not in the manifest\n")
        self.assertEqual(self.check(), "")

    def test_silent_outside_a_majles_project(self):
        self.assertEqual(quiet(bp.cmd_check, self.bp, pathlib.Path(self.tmp.name))[1], "")

    def test_never_raises(self):
        (self.project / bp.LOCK).write_text("not json")
        self.assertEqual(self.check(), "")


REQUEST = """# Research request: the stack

Requested by: architect
Date: 2026-10-22
Depth: Shallow
Blocks: the stack ADR
Feeds: ADR

## The decision I have to make

Which stack.

## Questions

At most 4.

{questions}"""

QUESTION = """### Q{n}. Does option {n} do the one thing?

Changes: the stack ADR; a no rules option {n} out.

"""

ADR = """# 0001. A decision

Status: {status}
Date: {date}

## Context

Hard.

{research}
"""


def request(n=1, swap=()):
    text = REQUEST.format(questions="".join(QUESTION.format(n=i) for i in range(1, n + 1)))
    for old, new in swap:
        assert old in text, old
        text = text.replace(old, new)
    return text


class Lint(Base):
    def task(self, name, **files):
        d = self.project / "docs/research" / name
        d.mkdir(parents=True, exist_ok=True)
        for f, text in files.items():
            (d / f"{f}.md").write_text(text)

    def adr(self, name="0001-a.md", status="accepted", date="2026-10-01", research="Research: docs/research/x/"):
        d = self.project / "docs/adr"
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(ADR.format(status=status, date=date, research=research))

    def lint(self):
        return bp.lint(self.project)

    def test_a_new_project_is_clean(self):
        self.assertEqual(self.lint(), [])
        self.assertEqual(quiet(bp.cmd_lint, self.project)[0], 0)

    def test_a_well_formed_request_passes(self):
        self.task("2026-10-22-architect-stack", request=request(4))
        self.assertEqual(self.lint(), [])

    def test_missing_depth_or_blocks_fails(self):
        self.task("2026-10-22-architect-a", request=request(swap=[("Depth: Shallow\n", "")]))
        self.task("2026-10-22-architect-b", request=request(swap=[("Blocks: the stack ADR\n", "")]))
        out = self.lint()
        self.assertEqual(len(out), 2, out)
        self.assertIn("architect-a/request.md: no `Depth:`", out[0])
        self.assertIn("architect-b/request.md: no `Blocks:`", out[1])
        self.assertEqual(quiet(bp.cmd_lint, self.project)[0], 1)

    def test_more_than_one_depth_in_the_header_fails(self):
        self.task("2026-10-22-architect-a", request=request(swap=[("Depth: Shallow", "Depth: Shallow | Medium | Deep")]))
        out = self.lint()
        self.assertEqual(len(out), 2, out)  # the header, and the request as a whole
        self.assertIn("must name exactly one", out[0])
        self.assertIn("mixed depths (Shallow, Medium, Deep)", out[1])

    def test_a_question_at_another_depth_fails(self):
        mixed = request(2).replace("### Q2. Does option 2 do the one thing?",
                                   "### Q2. Does option 2 do the one thing? — Depth: Deep")
        self.task("2026-10-22-architect-a", request=mixed)
        self.assertEqual(self.lint(), ["docs/research/2026-10-22-architect-a/request.md: "
                                       "mixed depths (Shallow, Deep): split into one request per depth"])

    def test_five_questions_fail(self):
        self.task("2026-10-22-architect-a", request=request(5))
        self.assertEqual(len(self.lint()), 1)
        self.assertIn("5 questions; at most 4", self.lint()[0])

    def test_a_question_without_changes_fails(self):
        self.task("2026-10-22-architect-a", request=request(2).replace("Changes: the stack ADR; a no rules option 2 out.", "Why."))
        out = self.lint()
        self.assertEqual(len(out), 1, out)
        self.assertIn("Q2 has no `Changes:` line", out[0])

    def test_bold_keys_are_accepted(self):
        self.task("2026-10-22-architect-a", request=request(1).replace("Changes:", "**Changes:**").replace("Blocks:", "**Blocks:**"))
        self.assertEqual(self.lint(), [])

    def test_at_most_four_open_requests(self):
        for i in range(4):
            self.task(f"2026-10-22-architect-{i}", request=request())
        self.assertEqual(self.lint(), [])
        self.task("2026-10-22-architect-4", request=request())
        self.assertEqual(self.lint(), ["docs/research/: 5 open requests; at most 4 without the developer's yes"])

    def test_completed_tasks_are_checked_only_for_their_decision(self):
        old = "# Research request: old\n\n## Questions\n\n### Q1. Anything? — Depth: Deep\n"
        self.task("2026-09-01-architect-done", request=old, findings="f", decision="d")
        for i in range(5):  # completed tasks do not count toward the open budget either
            self.task(f"2026-09-0{i + 2}-architect-old", request=old, findings="f", decision="d")
        self.assertEqual(self.lint(), [])
        self.task("2026-09-09-architect-undecided", request=old, findings="f")
        self.assertEqual(self.lint(), ["docs/research/2026-09-09-architect-undecided/: has findings.md but no decision.md"])

    def test_an_adr_needs_status_and_research(self):
        self.adr()
        self.assertEqual(self.lint(), [])
        self.adr(research="")
        self.assertEqual(self.lint(), ["docs/adr/0001-a.md: no `Research:` line"])
        (self.project / "docs/adr/0001-a.md").write_text("# 0001. A\n\nDate: 2026-10-01\n\nResearch: x\n")
        self.assertEqual(self.lint(), ["docs/adr/0001-a.md: no `Status:` line"])

    def test_an_accepted_adr_after_slices_names_its_slice(self):
        self.adr(date="2026-10-22")  # before the rule: not asked
        self.assertEqual(self.lint(), [])
        self.adr(date="2026-11-01", status="proposed")
        self.assertEqual(self.lint(), [])
        self.adr(date="2026-11-01")
        self.assertEqual(self.lint(), ["docs/adr/0001-a.md: accepted with no `Needed by: slice N` line"])
        (self.project / "docs/adr/0001-a.md").write_text(
            ADR.format(status="accepted", date="2026-11-01", research="Research: x").replace(
                "Date: 2026-11-01\n", "Date: 2026-11-01\nNeeded by: slice 1\n"))
        self.assertEqual(self.lint(), [])

    def test_phase_0_brief_left_after_an_accepted_adr_is_flagged(self):
        (self.project / "CLAUDE.md").write_text("# P\n\n## Phase 0 brief\n\n1. Research.\n")
        self.adr(status="proposed")
        self.assertEqual(self.lint(), [])
        self.adr(status="accepted")
        out = self.lint()
        self.assertEqual(len(out), 1)
        self.assertIn("CLAUDE.md: still has the Phase 0 brief", out[0])

    def test_more_than_five_adrs_for_one_slice_are_flagged(self):
        for i in range(1, 7):
            self.adr(name=f"000{i}-a.md")
            p = self.project / f"docs/adr/000{i}-a.md"
            p.write_text(p.read_text().replace("Date: 2026-10-01\n", "Date: 2026-10-01\nNeeded by: slice 2\n"))
        out = self.lint()
        self.assertEqual(len(out), 1, out)
        self.assertIn("6 accepted ADRs needed by slice 2", out[0])
        (self.project / "docs/adr/0006-a.md").unlink()
        self.assertEqual(self.lint(), [])

    def test_oversized_standing_text_is_flagged(self):
        (self.project / "CLAUDE.md").write_text("x" * (bp.MAX_CLAUDE_BYTES + 1))
        rules = self.project / ".claude/rules"
        rules.mkdir(parents=True)
        (rules / "small.md").write_text("ok\n")
        (rules / "big.md").write_text("x" * (bp.MAX_RULE_BYTES + 1))
        out = self.lint()
        self.assertEqual(len(out), 2, out)
        self.assertTrue(out[0].startswith("CLAUDE.md: 16 KB"), out[0])
        self.assertTrue(out[1].startswith(".claude/rules/big.md: 5 KB"), out[1])

    def test_main_guard_off_in_a_clone_is_flagged(self):
        hook = self.project / ".githooks/pre-push"
        hook.parent.mkdir()
        hook.write_text("#!/bin/sh\n")
        self.assertEqual(self.lint(), [])  # not a repository: nothing to check
        run("git", "init", "-q", "-b", "main", cwd=self.project)
        out = self.lint()
        self.assertEqual(len(out), 1, out)
        self.assertIn("pre-push is off in this clone", out[0])
        run("git", "config", "core.hooksPath", ".githooks", cwd=self.project)
        self.assertEqual(self.lint(), [])
        run("git", "config", "core.hooksPath", str(self.project / ".githooks"), cwd=self.project)
        self.assertEqual(self.lint(), [])
        run("git", "config", "core.hooksPath", "/elsewhere/hooks", cwd=self.project)
        self.assertEqual(len(self.lint()), 1)


class Hooks(Base):
    def test_a_synced_hook_is_executable(self):
        self.put("majles/manifest.txt", MANIFEST + "\n[core]\nshared .githooks/pre-push\n", commit=False)
        self.put(".githooks/pre-push", "#!/bin/sh\nexit 0\n")
        self.assertEqual(self.sync()[0], 0)
        self.assertTrue(os.access(self.project / ".githooks/pre-push", os.X_OK))


class ResearchFind(unittest.TestCase):
    TODAY = datetime.date(2026, 10, 22)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.put("one/docs/research/2026-10-01-architect-stack/request.md",
                 "# Research request: the stack and hosting\n\nDate: 2026-10-01\n")
        self.put("two/docs/research/2026-05-02-architect-servers/decision.md",
                 "# Decision: where it runs\n\n## What I took from the findings\n\nbilling\n\n"
                 "## The decision\n\nOne container; the stack stays portable across hosting.\n")
        self.put("two/docs/research/2026-10-10-product-onboarding/request.md",
                 "# Research request: first-run flow\n")
        self.put("two/docs/research/README.md", "# Research\n\nstack hosting\n")

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def find(self, *words):
        return quiet(bp.cmd_research_find, list(words), self.root, self.TODAY)

    def test_matches_titles_and_decisions_newest_first_and_marks_stale(self):
        code, out = self.find("Stack", "HOSTING")
        lines = out.splitlines()
        self.assertEqual(code, 0)
        self.assertEqual(len(lines), 2, out)
        self.assertTrue(lines[0].startswith("2026-10-01  "))
        self.assertTrue(lines[0].endswith("2026-10-01-architect-stack/  the stack and hosting"))
        self.assertTrue(lines[1].startswith("2026-05-02  "))
        self.assertTrue(lines[1].endswith("where it runs  stale"))

    def test_every_word_must_match(self):
        code, out = self.find("stack", "billing")  # billing is outside the decision section
        self.assertEqual(code, 1)
        self.assertIn("No earlier research matches", out)


class CheckLint(Base):
    def bad_request(self):
        d = self.project / "docs/research/2026-10-22-architect-a"
        d.mkdir(parents=True)
        (d / "request.md").write_text(request(swap=[("Blocks: the stack ADR\n", "")]))

    def test_adds_the_lint_line_when_otherwise_current(self):
        self.bad_request()
        code, out = quiet(bp.cmd_check, self.bp, self.project)
        self.assertEqual(code, 0)
        msg = json.loads(out)["systemMessage"]
        self.assertTrue(msg.startswith("Lint: 1 finding. Run: "), msg)
        self.assertIn(" lint", msg)

    def test_both_notices_one_line_each(self):
        self.bad_request()
        self.put("rules/a.md", "rule a v2\n")
        msg = json.loads(quiet(bp.cmd_check, self.bp, self.project)[1])["systemMessage"]
        self.assertEqual(len(msg.splitlines()), 2)

    def test_a_failing_lint_keeps_the_update_notice_and_exits_0(self):
        self.put("rules/a.md", "rule a v2\n")
        with mock.patch.object(bp, "lint", side_effect=RuntimeError("broken")):
            code, out = quiet(bp.cmd_check, self.bp, self.project)
        self.assertEqual(code, 0)
        self.assertIn("1 shared file changed", json.loads(out)["systemMessage"])
        self.assertNotIn("lint", json.loads(out)["systemMessage"])

    def test_a_failing_lint_alone_is_silent(self):
        with mock.patch.object(bp, "lint", side_effect=RuntimeError("broken")):
            self.assertEqual(quiet(bp.cmd_check, self.bp, self.project), (0, ""))


class Packaged(unittest.TestCase):
    """An installed Majles: the template is a plain directory with no .git, one version only."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.project = self.root / "proj"
        self.v1 = self.package("v1", FILES)
        quiet(bp.cmd_new, bp.PackageSource(self.v1, "0.1.0"), str(self.project))

    def tearDown(self):
        self.tmp.cleanup()

    def package(self, name, files):
        d = self.root / name
        for path, text in files.items():
            (d / path).parent.mkdir(parents=True, exist_ok=True)
            (d / path).write_text(text)
        return d

    def v2(self, **changes):
        files = dict(FILES)
        files.update({k.replace("__", "/").replace("_md", ".md"): v for k, v in changes.items()})
        return bp.PackageSource(self.package("v2", files), "0.2.0")

    def lock(self):
        return json.loads((self.project / bp.LOCK).read_text())

    def test_new_records_the_version_and_the_digests(self):
        lock = self.lock()
        self.assertEqual(lock["version"], "0.1.0")
        self.assertNotIn("commit", lock)
        self.assertEqual(lock["files"]["rules/a.md"], bp.digest(b"rule a v1\n"))
        self.assertEqual(lock["source"], "majles package")

    def test_a_directory_without_git_is_read_as_a_package(self):
        self.assertIsInstance(bp.as_source(self.v1), bp.PackageSource)
        other = self.root / "other"
        quiet(bp.cmd_new, self.v1, str(other))
        self.assertEqual(json.loads((other / bp.LOCK).read_text())["version"], bp.__version__)

    def test_sync_to_a_new_version_shows_exactly_the_changed_files(self):
        src = self.v2(rules__a_md="rule a v2\n")
        code, out = quiet(bp.cmd_sync, src, self.project, False, False, [])
        self.assertEqual(code, 0)
        self.assertIn("@0.1.0 -> majles @0.2.0", out)
        self.assertIn("update  rules/a.md", out)
        self.assertNotIn("rules/b.md", out)
        quiet(bp.cmd_sync, src, self.project, True, False, [])
        self.assertEqual((self.project / "rules/a.md").read_text(), "rule a v2\n")
        self.assertEqual(self.lock()["version"], "0.2.0")

    def test_an_edit_is_found_from_the_digests_without_the_old_files(self):
        (self.project / "rules/a.md").write_text("mine\n")
        code, out = quiet(bp.cmd_sync, self.v2(rules__a_md="rule a v2\n"), self.project, True, False, [])
        self.assertEqual(code, 1)
        self.assertIn("CONFLICT rules/a.md: edited in this project", out)
        self.assertEqual((self.project / "rules/a.md").read_text(), "mine\n")
        self.assertEqual(self.lock()["version"], "0.1.0")

    def test_enable_works_on_the_installed_version_and_asks_for_sync_on_another(self):
        self.assertEqual(quiet(bp.cmd_enable, bp.PackageSource(self.v1, "0.1.0"), "i18n", self.project)[0], 0)
        self.assertEqual((self.project / "rules/i18n.md").read_text(), "i18n v1\n")
        with self.assertRaises(bp.MajlesError):
            bp.cmd_enable(self.v2(), "content", self.project)
        with self.assertRaises(bp.MajlesError):
            bp.cmd_disable(self.v2(), "i18n", self.project)

    def test_check_notices_a_new_version_and_is_silent_when_current(self):
        self.assertEqual(quiet(bp.cmd_check, bp.PackageSource(self.v1, "0.1.0"), self.project), (0, ""))
        code, out = quiet(bp.cmd_check, self.v2(rules__b_md="rule b v2\n"), self.project)
        self.assertEqual(code, 0)
        self.assertIn("1 shared file changed", out)

    def test_a_project_synced_from_a_checkout_moves_to_the_package(self):
        lock = self.lock()
        del lock["version"]
        lock["commit"] = "a" * 40  # synced from a checkout, whose commits the package cannot read
        (self.project / bp.LOCK).write_text(json.dumps(lock))
        src = self.v2(rules__a_md="rule a v2\n")
        self.assertIn("update  rules/a.md", quiet(bp.cmd_sync, src, self.project, True, False, [])[1])
        lock = self.lock()
        self.assertEqual(lock["version"], "0.2.0")
        self.assertNotIn("commit", lock)


class Version(unittest.TestCase):
    def test_version_flag_prints_the_version(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as e:
            bp.main(["--version"])
        self.assertEqual(e.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), f"majles {bp.__version__}")


if __name__ == "__main__":
    unittest.main()
