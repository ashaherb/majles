"""Checks on the template itself.   python3 -m unittest discover -s majles -p 'test_*.py'

These keep the template honest as it grows: everything shipped is in the
manifest, shared files carry no project facts, and every placeholder is
documented for setup.
"""

import fnmatch
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from majles import cli as bp  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUIDE = ROOT / "template" / "SETUP.md"  # the setup procedure, shipped once
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")
EXAMPLES = {"LIKE_THIS", "PLACEHOLDER"}  # illustrations in the setup text
# The repo's own files, for Majles as a public project. None reaches a project.
# The project's CLAUDE.md and README.md ship from template/.
REPO_LEVEL = {"README.md", "CLAUDE.md", "DECISIONS.md", "LICENSE", "CHANGELOG.md",
              "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "pyproject.toml",
              "setup.py", ".github/FUNDING.yml", ".github/ISSUE_TEMPLATE/config.yml"}
NOT_SHIPPED = {"MAINTAINING.md"} | REPO_LEVEL  # plus everything under majles/
NOT_SHIPPED_DIRS = (".github", "build", "dist", "majles.egg-info")  # git-ignored build output after .github
# Domain words that only a particular product would bring into a shared file. Neutral
# examples, not any real product's; private names are checked by digest below.
PRODUCT_WORDS = re.compile(r"\b(catalog|invoices?|recipes?|playlists?|arabic)\b", re.I)
# Places where a product word is a deliberate example, not a leak.
ALLOWED_WORDS = {"optional/i18n/.claude/rules/i18n.md",
                 "template/SETUP.md"}  # the interview names example domains

ENTRIES = bp.parse_manifest((ROOT / bp.MANIFEST).read_text(encoding="utf-8"))


def repo_files():
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if p.is_file() and rel.parts[0] not in (".git", "majles") and "__pycache__" not in rel.parts \
                and p.name != ".DS_Store":
            yield rel.as_posix()


def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


class Manifest(unittest.TestCase):
    def test_every_source_exists(self):
        missing = [src for _, _, src, _ in ENTRIES if not (ROOT / src).is_file()]
        self.assertFalse(missing, f"in the manifest but not on disk: {missing}")

    def test_every_shipped_file_is_in_the_manifest(self):
        listed = {src for _, _, src, _ in ENTRIES}
        unlisted = sorted(f for f in set(repo_files()) - listed - NOT_SHIPPED
                          if f.split("/")[0] not in NOT_SHIPPED_DIRS)
        self.assertFalse(unlisted, f"not in {bp.MANIFEST}; add it as shared or once: {unlisted}")

    def test_the_repo_files_never_ship(self):
        # The root CLAUDE.md and README.md describe this repo; a project gets template/'s.
        listed = {src for _, _, src, _ in ENTRIES}
        self.assertFalse(listed & NOT_SHIPPED)
        self.assertFalse([s for s in listed if s.split("/")[0] in NOT_SHIPPED_DIRS])
        for dest in ("CLAUDE.md", "README.md"):
            self.assertIn(("template/" + dest, dest), {(s, d) for _, _, s, d in ENTRIES})

    def test_the_repo_root_is_not_the_template(self):
        # A session opened here reads the root CLAUDE.md; a setup block there would send it
        # off setting up the template as if it were a new project.
        for rel in ("CLAUDE.md", "README.md"):
            real = set(PLACEHOLDER.findall(text(rel))) - EXAMPLES
            self.assertFalse(real, f"{rel} carries a placeholder")
            self.assertNotIn("<!-- SETUP", text(rel), rel)

    def test_no_two_entries_land_on_the_same_path(self):
        dests = [d for _, _, _, d in ENTRIES]
        self.assertEqual(len(dests), len(set(dests)))

    def test_the_role_modules_ship_their_agents(self):
        dests = {(m, d) for m, _, _, d in ENTRIES}
        for module, dest in [("core", ".claude/agents/tester.md"), ("core", ".claude/agents/security.md"),
                             ("core", ".claude/agents/ops.md"), ("core", "docs/security/README.md"),
                             ("core", "ops/README.md"), ("core", "docs/research/backlog.md"),
                             ("ai", ".claude/agents/ai.md"), ("ai", ".claude/rules/ai.md"),
                             ("ai", "evals/README.md"), ("legal", ".claude/agents/legal.md"),
                             ("legal", "docs/legal/README.md"), ("beads", ".claude/rules/beads.md")]:
            self.assertIn((module, dest), dests)

    def test_beads_is_on_by_default(self):
        self.assertIn("beads", bp.DEFAULT_MODULES)

    def test_no_agent_can_start_agents_or_search_but_the_researcher_and_critic(self):
        agents = [d for _, _, _, d in ENTRIES if d.startswith(".claude/agents/")]
        for _, _, src, dest in ENTRIES:
            if dest not in agents:
                continue
            tools = next(l for l in text(src).splitlines() if l.startswith("tools:"))
            self.assertNotIn("Agent", tools, dest)
            if dest not in (".claude/agents/researcher.md", ".claude/agents/critic.md"):
                self.assertNotIn("WebSearch", tools, dest)
                self.assertNotIn("WebFetch", tools, dest)

    def test_no_agent_description_says_use_proactively(self):
        for _, _, src, dest in ENTRIES:
            if dest.startswith(".claude/agents/"):
                self.assertNotIn("proactively", text(src).split("\n---", 1)[0].lower(), dest)

    def test_default_modules_exist(self):
        modules = {m for m, _, _, _ in ENTRIES}
        self.assertTrue(set(bp.DEFAULT_MODULES) <= modules)

    def test_the_manifest_header_names_the_default_modules(self):
        # Issue #26: the comment said core and ui while `new` also turned on beads.
        header = next(l for l in text(bp.MANIFEST).splitlines() if l.startswith("# New projects get"))
        self.assertEqual(set(re.findall(r"\[(\w+)\]", header)), set(bp.DEFAULT_MODULES))

    def test_every_agent_pins_opus_or_sonnet(self):
        # Issue #25: a model some plans lack (fable) left the agent unusable on those plans.
        for _, _, src, dest in ENTRIES:
            if dest.startswith(".claude/agents/"):
                model = next(l for l in text(src).splitlines() if l.startswith("model:"))
                self.assertIn(model.split(":", 1)[1].strip(), ("opus", "sonnet"), dest)


class Placeholders(unittest.TestCase):
    def test_shared_files_contain_none(self):
        # A project fact in a shared file would be overwritten by the next sync.
        bad = [src for _, kind, src, _ in ENTRIES if kind == "shared" and PLACEHOLDER.search(text(src))]
        self.assertFalse(bad, f"shared files must be placeholder-free: {bad}")

    def test_every_placeholder_is_documented_in_the_guide(self):
        guide = text("template/SETUP.md")
        missing = sorted({f"{name} ({src})" for _, _, src, _ in ENTRIES
                          for name in PLACEHOLDER.findall(text(src))
                          if name not in EXAMPLES and name not in guide})
        self.assertFalse(missing, f"undocumented placeholders: {missing}")


class SetupGuide(unittest.TestCase):
    def section(self, heading):
        guide = text("template/SETUP.md")
        return guide.split(f"\n## {heading}\n", 1)[1].split("\n## ", 1)[0]

    def test_it_names_the_file_adopt_writes_beside_claude_md(self):
        # Issue #4: setup merges the template adopt wrote beside the project's CLAUDE.md.
        self.assertIn(f"`{bp.CLAUDE_BESIDE}`", text("template/SETUP.md"))

    def test_an_adopted_project_skips_creating_the_repo(self):
        # Issue #6: an adopted project already has a repo, a remote and a main branch.
        repo = self.section("4. Repo")
        self.assertIn("An existing repo", repo.split("1. `git init", 1)[0])
        self.assertIn("An adopted project", self.section("6. Finish"))

    def test_beads_installs_without_homebrew_or_turns_off(self):
        # Issue #23: brew and npm -g were the only ways in, so Linux without Homebrew stopped.
        beads = self.section("4b. The work queue (beads module, on by default)")
        for way in ("brew install beads", "npm i -g @beads/bd", "gh release download",
                    "checksums.txt", "--prefix ~/.local", "majles disable beads"):
            self.assertIn(way, beads)
        self.assertNotIn("sudo npm", beads)

    def bd_binary_block(self):
        beads = self.section("4b. The work queue (beads module, on by default)")
        return next(b.split("\n", 1)[1] for b in beads.split("```bash")[1:] if "gh release download" in b)

    def run_bd_block(self, checksum_ok):
        # Issue #44: the block runs for real against a stand-in gh (it writes the files it
        # is asked for) and a stand-in shasum, so a mismatch must stop before tar and mv.
        root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        stubs, home = root / "stubs", root / "home"
        stubs.mkdir(), home.mkdir()
        (stubs / "gh").write_text(
            '#!/bin/sh\necho "$@" > "$HOME/gh-args"\n'
            'while [ $# -gt 0 ]; do if [ "$1" = -p ]; then shift; case "$1" in\n'
            '  checksums.txt) : > checksums.txt ;;\n'
            '  *) mkdir s && echo stub > s/bd && tar czf "$1" -C s ./bd && rm -r s ;;\n'
            'esac; fi; shift; done\n')
        (stubs / "shasum").write_text(f"#!/bin/sh\nexit {0 if checksum_ok else 1}\n")
        for stub in stubs.iterdir():
            stub.chmod(0o755)
        block = self.bd_binary_block().split("```", 1)[0]
        env = {**os.environ, "HOME": str(home), "PATH": f"{stubs}{os.pathsep}{os.environ['PATH']}"}
        subprocess.run(["bash", "-c", block], cwd=root, env=env, capture_output=True, text=True)
        return home

    def test_bd_installs_only_after_its_checksum_passes(self):
        self.assertFalse((self.run_bd_block(checksum_ok=False) / ".local/bin/bd").exists())
        home = self.run_bd_block(checksum_ok=True)
        self.assertTrue((home / ".local/bin/bd").is_file())

    def test_bd_is_pinned_to_a_release(self):
        home = self.run_bd_block(checksum_ok=True)
        args = (home / "gh-args").read_text().split()
        self.assertRegex(args[2], r"^v\d+\.\d+\.\d+$", "gh release download takes a pinned tag")
        version = args[2][1:]
        beads = self.section("4b. The work queue (beads module, on by default)")
        self.assertIn(f"npm i -g @beads/bd@{version}", beads)
        self.assertIn(f"pinned to version {version}", beads)

    def test_the_decision_log_falls_back_to_files_without_artifacts(self):
        # Issue #24: setup assumed every session can publish Artifacts.
        log = self.section("5. Decision log")
        self.assertIn("python3 tools/render_decisions.py docs/status/decisions.html", log)
        self.assertIn("--decisions-url decisions.html", log)
        self.assertIn("docs/status/*.html", text(".gitignore").splitlines())


class Neutrality(unittest.TestCase):
    def test_shipped_files_name_no_particular_product(self):
        hits = []
        for _, _, src, _ in ENTRIES:
            if src in ALLOWED_WORDS or src.startswith("tools/"):
                continue
            for n, line in enumerate(text(src).splitlines(), 1):
                if PRODUCT_WORDS.search(line):
                    hits.append(f"{src}:{n}: {line.strip()[:80]}")
        self.assertFalse(hits, "product-specific words in shipped files:\n" + "\n".join(hits))


# Words from the one machine Majles was first built on. None may appear in a
# shipped file, or anywhere in the repo outside the compatibility code and tests.
# Generic path and account patterns are written out, split so this file does not
# match itself.
BLOCKLIST = re.compile("|".join(re.escape(w) for w in (
    "/Us" + "ers/", "/ho" + "me/", "~/" + "Personal", "asha" + "herb")), re.I)
# Private names (other projects, products, accounts and repos) are kept only as the
# first 16 hex digits of the SHA-256 of the lowercased word, so this public file does
# not name them. That hides them from a reader, not from someone guessing words and
# hashing them. To add one: python3 -c 'import hashlib,sys;
# print(hashlib.sha256(sys.argv[1].lower().encode()).hexdigest()[:16])' <word>
PRIVATE_DIGESTS = frozenset((
    "fa6b37ce6c8c55da", "57a3bd5ec8fe4e6c", "58ad7768e3dda79c", "521e394a04020307",
    "03410778d20da2cf", "de323ff15874fcf6", "6ce3e618ee87dce1", "4bbe89d001880a72",
    "fcc8b8f27f40bb4f", "0db15b57404158b9", "8cdb169b45db566d", "4840a07c7067788b",
    "115facefbdc83bda", "be0171563305dae1", "38620bece05ef08f"))
TOKEN = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*")


def digest(word):
    return hashlib.sha256(word.lower().encode()).hexdigest()[:16]


class PrivateName:
    """A pattern-like matcher: search(line) is true when any word, or any run of words
    joined by "." or "-", has a digest in the set. "a.b-c" is checked as a, b, c, a.b,
    b-c and a.b-c."""

    def __init__(self, digests):
        self.digests = digests

    def search(self, line):
        for token in TOKEN.findall(line.lower()):
            parts = re.split(r"([.-])", token)  # words at even indexes, separators between
            for i in range(0, len(parts), 2):
                for j in range(i, len(parts), 2):
                    if digest("".join(parts[i:j + 1])) in self.digests:
                        return True
        return False


PRIVATE = PrivateName(PRIVATE_DIGESTS)
# The old name may stay only where it is needed to read projects made before the rename.
OLD_NAME = re.compile("boiler" + "plate|maj" + "lis", re.I)  # the two earlier names
COMPATIBILITY = {"majles/cli.py", "majles/test_cli.py", "majles/test_template.py"}
# Repo-level files that name the maintainer's account on purpose: the sponsor link,
# the author line, the conduct contact and the package URLs. Exempt by name only.
# The issue chooser links to the repo's private security advisories.
NAMES_THE_MAINTAINER = {".github/FUNDING.yml", ".github/ISSUE_TEMPLATE/config.yml", "README.md",
                        "CODE_OF_CONDUCT.md", "pyproject.toml"}
# The standard Apache 2.0 text has the phrase "boilerplate notice"; the changelog and the
# decision log name the earlier names on purpose, to say what was renamed.
SAYS_THE_OLD_NAME = {"LICENSE", "CHANGELOG.md", "DECISIONS.md"}


def all_repo_files():
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if p.is_file() and rel.parts[0] != ".git" and "__pycache__" not in rel.parts \
                and p.name != ".DS_Store":
            yield rel.as_posix()


class Portability(unittest.TestCase):
    def hits(self, pattern, files):
        out = []
        for rel in sorted(files):
            for n, line in enumerate(text(rel).splitlines(), 1):
                if pattern.search(line):
                    out.append(f"{rel}:{n}: {line.strip()[:80]}")
        return out

    def test_the_blocklist_catches_each_word(self):
        # A guard against a regex that quietly matches nothing.
        for sample in ("/Us" "ers/me/x", "/ho" "me/me/x", "~/" "Personal/x", "asha" "herb"):
            self.assertTrue(BLOCKLIST.search(sample), sample)
        self.assertFalse(BLOCKLIST.search("majles new my-idea"))

    def test_the_private_names_are_digests_and_are_caught_in_context(self):
        # The digests cannot be checked against the words without naming them here, so the
        # matcher is checked with stand-in words instead.
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{16}", d) for d in PRIVATE_DIGESTS))
        stand_in = PrivateName({digest("acme"), digest("acme-lab"), digest("lab.py")})
        for line in ("see ../Acme/README", "git@host:me/acme-lab.git", "run tools/lab.py now",
                     "mail x.y@acme.example"):
            self.assertTrue(stand_in.search(line), line)
        for line in ("acmes", "lab", "a lab.pyc file", "majles new my-idea"):
            self.assertFalse(stand_in.search(line), line)

    def test_the_exempt_files_are_never_shipped(self):
        # An exemption covers the repo's own copy only. A shipped file is always checked in full.
        exempt = NAMES_THE_MAINTAINER | SAYS_THE_OLD_NAME
        self.assertFalse(exempt & {src for _, _, src, _ in ENTRIES}, "an exempt file is shipped")
        self.assertTrue(exempt <= REPO_LEVEL, "only repo-level files may be exempt")

    def test_shipped_files_carry_no_personal_paths_or_accounts(self):
        shipped = {src for _, _, src, _ in ENTRIES}
        hits = self.hits(BLOCKLIST, shipped) + self.hits(PRIVATE, shipped)
        self.assertFalse(hits, "personal words in shipped files:\n" + "\n".join(hits))

    def test_the_repo_carries_none_outside_the_compatibility_code(self):
        hits = self.hits(BLOCKLIST, set(all_repo_files()) - COMPATIBILITY - NAMES_THE_MAINTAINER)
        hits += self.hits(PRIVATE, set(all_repo_files()) - COMPATIBILITY)
        self.assertFalse(hits, "personal words in the repo:\n" + "\n".join(hits))

    def test_the_old_name_is_only_in_the_compatibility_code(self):
        hits = self.hits(OLD_NAME, set(all_repo_files()) - COMPATIBILITY - SAYS_THE_OLD_NAME)
        self.assertFalse(hits, "the old name outside the compatibility code:\n" + "\n".join(hits))


class MainGuard(unittest.TestCase):
    """The shipped .githooks/pre-push, run by a real git push to a scratch remote."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.remote, self.repo = root / "remote.git", root / "repo"
        self.git(root, "init", "-q", "--bare", str(self.remote))
        self.git(root, "init", "-q", "-b", "main", str(self.repo))
        hooks = self.repo / ".githooks"
        hooks.mkdir()
        shutil.copy2(ROOT / ".githooks/pre-push", hooks / "pre-push")
        self.git(self.repo, "config", "core.hooksPath", ".githooks")
        self.git(self.repo, "remote", "add", "origin", str(self.remote))
        (self.repo / "f").write_text("x")
        self.git(self.repo, "add", "-A")
        self.git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "c")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, cwd, *args, env=None):
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                              env={**os.environ, **(env or {})})

    def test_shipped_executable(self):
        self.assertTrue(os.access(ROOT / ".githooks/pre-push", os.X_OK))

    def test_a_push_to_main_is_refused(self):
        r = self.git(self.repo, "push", "origin", "main")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("refusing to push to main", r.stderr)
        r = self.git(self.repo, "push", "origin", "HEAD:refs/heads/main")
        self.assertNotEqual(r.returncode, 0)

    def test_a_branch_push_and_the_first_push_pass(self):
        self.assertEqual(self.git(self.repo, "push", "origin", "main:feature").returncode, 0)
        self.assertEqual(self.git(self.repo, "push", "origin", "main", env={"ALLOW_MAIN_PUSH": "1"}).returncode, 0)

    def test_the_local_hook_runs_with_the_refs(self):
        local = self.repo / ".githooks/pre-push.local"
        local.write_text('#!/bin/sh\ncat > "$(dirname "$0")/seen"\nexit 3\n')
        local.chmod(0o755)
        r = self.git(self.repo, "push", "origin", "main:feature")
        self.assertNotEqual(r.returncode, 0)  # the local hook's failure blocks the push
        self.assertIn("refs/heads/feature", (self.repo / ".githooks/seen").read_text())

    def branch_push(self, name, path, lines):
        """Push a branch off main that adds `lines` lines at `path`; return (code, stderr)."""
        self.git(self.repo, "push", "origin", "main", env={"ALLOW_MAIN_PUSH": "1"})  # gives origin/main
        self.git(self.repo, "checkout", "-q", "-b", name, "main")
        f = self.repo / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("".join(f"{i}\n" for i in range(lines)))
        self.git(self.repo, "add", "-A")
        self.git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", name)
        r = self.git(self.repo, "push", "origin", name)
        return r.returncode, r.stderr

    def test_a_large_branch_warns_but_is_pushed(self):
        code, err = self.branch_push("big", "src/app.ts", 1200)
        self.assertEqual(code, 0)
        self.assertIn("warning: big adds 1200 lines", err)

    def test_a_path_containing_lock_still_counts(self):
        self.assertIn("warning", self.branch_push("blocks", "web/src/blocks/card.tsx", 1200)[1])

    def test_lockfiles_and_small_branches_do_not_warn(self):
        self.assertNotIn("warning", self.branch_push("lock", "web/pnpm-lock.yaml", 1200)[1])
        self.git(self.repo, "checkout", "-q", "main")
        self.assertNotIn("warning", self.branch_push("small", "src/small.ts", 50)[1])


    def test_unchanged_template_files_do_not_count(self):
        # A first adoption: 1,200 lines of template files, recorded in .majles.json as installed.
        body = "".join(f"{i}\n" for i in range(1200))
        lock = {"files": {".claude/rules/big.md": hashlib.sha256(body.encode()).hexdigest()}}
        (self.repo / ".majles.json").write_text(json.dumps(lock))
        self.assertNotIn("warning", self.branch_push("adopt", ".claude/rules/big.md", 1200)[1])

    def test_an_edited_template_file_counts(self):
        (self.repo / ".majles.json").write_text(json.dumps({"files": {".claude/rules/big.md": "0" * 64}}))
        self.assertIn("warning", self.branch_push("edited", ".claude/rules/big.md", 1200)[1])


class Settings(unittest.TestCase):
    def test_settings_parse_and_wire_the_update_check(self):
        settings = json.loads(text(".claude/settings.json"))
        self.assertEqual(settings["fallbackModel"], ["opus"])
        command = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        self.assertIn("command -v majles", command)
        self.assertIn("majles check", command)
        self.assertIn(" check ", command)
        self.assertTrue(command.rstrip().endswith("exit 0"), "the hook must never fail a session")


    def denied(self, path):
        # Each rule is Read(./<glob>) for the project root or Read(**/<glob>) for any folder.
        # fnmatchcase on the file name is a stand-in for Claude Code's own matching.
        rules = json.loads(text(".claude/settings.json"))["permissions"]["deny"]
        name, nested = path.split("/")[-1], "/" in path
        for rule in rules:
            where, glob = rule[len("Read("):-1].split("/", 1)
            if fnmatch.fnmatchcase(name, glob) and (where == "**" or not nested):
                return True
        return False

    def test_secret_files_are_denied_to_the_read_tool(self):
        # Issue #45. A deny rule stops Claude's Read tool, not a shell command; the agents
        # rule and the README say so. Each name is denied at the root and in any folder.
        rules = json.loads(text(".claude/settings.json"))["permissions"]["deny"]
        self.assertTrue(all(r.startswith("Read(") for r in rules))
        for path in (".env", ".env.local", ".env.production.local", ".env.development",
                     ".env.production", ".env.staging", ".env.test", "server.pem", "tls/private.key",
                     "gcp-service-account.json", "service-account.json", "serviceAccountKey.json",
                     "api/.env", "api/.env.production", "keys/deploy.pem"):
            self.assertTrue(self.denied(path), path)

    def test_the_committed_example_stays_readable(self):
        # .env.example is committed and holds names only (.gitignore keeps it), so agents
        # must be able to read and edit it. A blanket .env.* would deny it.
        for path in (".env.example", "api/.env.example", "package.json", "keys.md"):
            self.assertFalse(self.denied(path), path)

    def test_the_limit_of_a_deny_rule_is_stated(self):
        for rel in (".claude/rules/agents.md", "README.md"):
            self.assertTrue("shell command" in " ".join(text(rel).split()), rel)


class Release(unittest.TestCase):
    def test_the_readme_banner_matches_the_version(self):
        # Issue #38: the pre-release banner leaves the README in the same pull request
        # that sets the final version, and the upload follows the merge (MAINTAINING.md).
        import majles
        prerelease = bool(re.search(r"(a|b|rc|dev)\d*$", majles.__version__))
        readme = text("README.md")
        for marker in ("**Status: pre-release.**", "### Installing before 0.1.0"):
            self.assertEqual(marker in readme, prerelease, f"{marker} vs {majles.__version__}")

class TheUsersWords(unittest.TestCase):
    def test_no_shipped_rule_attributes_dated_words_to_the_developer(self):
        # Issue #37: in a project, "the developer" is its user. A dated quote of "the
        # developer" in a shipped file reads as something that user said. Only
        # docs/direction.md holds the developer's words, and it ships empty.
        date = re.compile(r"\b20\d\d-\d\d-\d\d\b")
        hits = []
        for _, _, src, _ in ENTRIES:
            if not src.endswith(".md") or src.startswith("docs/research/"):
                continue
            for para in text(src).split("\n\n"):
                if "developer" in para.lower() and date.search(para):
                    hits.append(f"{src}: {para.strip()[:80]}")
                if re.search(r"\*\*Why:\*\* the developer", para):
                    hits.append(f"{src}: {para.strip()[:80]}")
        self.assertFalse(hits, "dated or unscoped words given as the developer's:\n" + "\n".join(hits))

if __name__ == "__main__":
    unittest.main()
