"""Packages the template with the CLI. The metadata is in pyproject.toml.

majles/manifest.txt is the single list of shipped files. The build copies each
file it names into the wheel under majles/template/, at the same relative path,
and the source distribution includes the same files, so a wheel built from the
sdist has them too.
"""

import pathlib
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

HERE = pathlib.Path(__file__).resolve().parent
MANIFEST = "majles/manifest.txt"


def template_files():
    """The manifest itself, and every source path it lists."""
    files = [MANIFEST]
    for raw in (HERE / MANIFEST).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("["):
            continue
        kind, _, rest = line.partition(" ")
        if kind in ("shared", "once"):
            files.append(rest.split("->", 1)[0].strip())
    missing = [f for f in files if not (HERE / f).is_file()]
    if missing:
        raise SystemExit(f"{MANIFEST} lists files that do not exist: {missing}")
    return files


class BuildWithTemplate(build_py):
    def find_package_modules(self, package, package_dir):
        # The tests read the repo around the package, so they stay out of the wheel.
        return [m for m in super().find_package_modules(package, package_dir)
                if not m[1].startswith("test_")]

    def run(self):
        super().run()
        out = pathlib.Path(self.build_lib) / "majles" / "template"
        for rel in template_files():
            dest = out / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(HERE / rel, dest)  # copy2 keeps the hook's executable bit


class SdistWithTemplate(sdist):
    def make_release_tree(self, base_dir, files):
        super().make_release_tree(base_dir, sorted(set(files) | set(template_files())))


setup(cmdclass={"build_py": BuildWithTemplate, "sdist": SdistWithTemplate})
