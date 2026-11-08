"""Tests for render_status.py.   python3 -m unittest tools/test_render_status.py"""

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import render_status as rs  # noqa: E402

CLAUDE = """# Sample

## Current phase

**Slice 2, the second thing.** A long paragraph of status prose that never reaches the page.

**Next:**
- finish the form

## Phases

Each slice is one thing a user could try.

```markdown
### Slice N. <name>
```

### Slice 1. The walking skeleton. Built.

A user can sign in.

### Slice 2. The second thing

In progress: the form.

### Slice 3. Later

The third thing.

### Slices 4 to 9, and after

# How we work

### Slice 9. Not a slice, it is outside the Phases section.
"""

ARCH = """# Architecture

Prose that is not drawn.

## C1. System context

```c4
person user "User" : uses it
system app "The app" : does the thing
external mail "Mail service"

user -> app : uses
app -> mail : sends
```

## C2. Containers

```c4
inside app
container web "Web" : <b>routes</b>
store db "Database"
web -> db : SQL
web -> nowhere
this line is nonsense
```

```c4
level C3
title The web module
inside web
component a "A"
component b "B"
a -> b
b -> a : back
```
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "README.md").write_text("# Sample\n", encoding="utf-8")
        (self.root / "CLAUDE.md").write_text(CLAUDE, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def page(self, url=None):
        with contextlib.redirect_stderr(io.StringIO()):
            return rs.build(self.root, url)[0]


class Page(Base):
    def test_claude_md_prose_never_reaches_the_page(self):
        page = self.page()
        self.assertIn("<title>Sample Status</title>", page)
        self.assertNotIn("never reaches the page", page)
        self.assertNotIn("finish the form", page)

    def test_a_project_with_no_inputs_renders_and_names_what_is_missing(self):
        (self.root / "CLAUDE.md").unlink()
        page, n, paths, d = rs.build(self.root)
        self.assertEqual((n, paths, d), (0, [], 0))
        self.assertNotIn('<section class="block', page)
        self.assertIn("Not on this page yet: a TLDR", page)
        self.assertNotIn("<script", page)


class Tldr(Base):
    def test_each_line_is_its_own_statement_in_the_masthead(self):
        self.put("docs/status/tldr.md", "# TLDR\n\nOne thing works.\nThe next is coming. <i>x</i>\n")
        page = self.page()
        tldr = page.split('<div class="tldr">', 1)[1].split("</div>", 1)[0]
        self.assertEqual(tldr, "<p>One thing works.</p><p>The next is coming. &lt;i&gt;x&lt;/i&gt;</p>")
        self.assertLess(page.index('<div class="tldr">'), page.index("</header>"))

    def test_too_long_warns_but_shows_everything(self):
        self.put("docs/status/tldr.md", "\n".join(f"Line {i}." for i in range(7)))
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            page = rs.build(self.root)[0]
        self.assertIn("tldr.md has 7 lines", err.getvalue())
        self.assertIn("<p>Line 6.</p>", page)


class Slices(Base):
    def test_one_segment_per_slice_with_state_and_the_current_one_marked(self):
        page, n, _, _ = rs.build(self.root)
        self.assertEqual(n, 3)
        self.assertEqual(page.count('<li class="seg'), 4)
        self.assertIn('<span class="seg-t">The walking skeleton</span><span class="chip done">Built</span>', page)
        self.assertIn('<li class="seg progress now" aria-current="step"><span class="seg-n">2</span>', page)
        self.assertIn('<span class="seg-n">3</span><span class="seg-t">Later</span><span class="chip todo">Planned', page)
        self.assertIn('<span class="seg-n">4–9</span><span class="seg-t">Later slices</span>', page)

    def test_the_format_example_and_other_sections_are_not_slices(self):
        page = self.page()
        self.assertNotIn("&lt;name&gt;", page)
        self.assertNotIn("Slice 9", page)

    def test_no_phase_plan_no_strip(self):
        self.put("CLAUDE.md", "# Sample\n")
        self.assertNotIn('class="strip"', self.page())


class Lists(Base):
    def test_now_and_next_sit_side_by_side_and_either_may_be_missing(self):
        self.put("docs/status/now.md", "- building the form\n- trying it\n")
        page = self.page()
        self.assertIn('<h2 id="now-h">Now</h2><ul><li>building the form</li><li>trying it</li></ul>', page)
        self.assertNotIn('id="next-h"', page)
        self.assertIn("next (<code>docs/status/next.md</code>)", page)

    def test_waiting_is_a_numbered_list_with_a_count(self):
        self.put("docs/status/waiting.md", "# Waiting\n\n1. Approve the plan\n2. Try slice 2\n")
        page = self.page()
        self.assertIn('Waiting on the developer<span class="count">2</span>', page)
        self.assertIn("<ol><li>Approve the plan</li><li>Try slice 2</li></ol>", page)

    def test_spend_takes_its_title_from_the_file(self):
        self.put("docs/status/spend.md", "# Spend, May\n\n| What | Spent |\n|---|---|\n| Evals | $12 |\n")
        page = self.page()
        self.assertIn('<h2 id="spend-h">Spend, May</h2>', page)
        self.assertIn("<td>$12</td>", page)


class Screens(Base):
    def test_contact_sheet_with_captions_from_the_file_or_the_name(self):
        shots = self.root / "docs" / "status" / "screens"
        shots.mkdir(parents=True)
        for name in ("02-desktop.png", "01-phone_home.webp", "notes.txt"):
            (shots / name).write_bytes(b"x")
        self.put("docs/status/screens/captions.md", "- 02-desktop.png: The home, at desktop size\n")
        out = self.root / "out.html"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rs.main([str(out)], root=self.root)
        page = out.read_text(encoding="utf-8")
        self.assertIn('<a href="screens/01-phone_home.webp"><img src="screens/01-phone_home.webp"', page)
        self.assertIn("<figcaption>Phone home</figcaption>", page)
        self.assertIn("<figcaption>The home, at desktop size</figcaption>", page)
        self.assertNotIn("notes.txt", page)
        printed = buf.getvalue().splitlines()
        self.assertTrue(printed[0].startswith(f"wrote {out}"))
        self.assertEqual(printed[1:], ["screens/01-phone_home.webp", "screens/02-desktop.png"])


class Architecture(Base):
    def build(self):
        self.put("docs/architecture.md", ARCH)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            page, _, _, d = rs.build(self.root, "https://log")
        return page, d, err.getvalue()

    def test_each_block_is_a_view_with_a_wide_and_a_narrow_drawing(self):
        page, d, _ = self.build()
        self.assertEqual(d, 3)
        self.assertEqual(page.count('<section class="c4-view"'), 3)
        self.assertEqual(page.count("<svg"), 6)
        self.assertNotIn("Prose that is not drawn", page)
        self.assertIn('id="c4-c1-system-context"', page)
        self.assertIn('id="c4-c3-web"', page)

    def test_boxes_zoom_into_the_diagram_inside_them_and_back_out(self):
        page, _, _ = self.build()
        self.assertIn('<a class="c4-link" href="#c4-c2-app" aria-label="Zoom into The app">', page)
        self.assertIn('<a class="c4-link" href="#c4-c3-web" aria-label="Zoom into Web">', page)
        self.assertIn('Inside <strong>The app</strong> · <a href="#c4-c1-system-context">Zoom out</a>', page)
        self.assertNotIn('aria-label="Zoom into User"', page)

    def test_text_is_escaped_and_bad_lines_warn(self):
        page, _, err = self.build()
        self.assertIn("&lt;b&gt;routes&lt;/b&gt;", page)
        self.assertNotIn("<b>routes", page)
        self.assertIn("this line is nonsense", err)
        self.assertIn("web -> nowhere", err)

    def test_a_cycle_still_draws_every_arrow(self):
        page, _, _ = self.build()
        view = page.split('id="c4-c3-web"', 1)[1].split("</section>", 1)[0]
        self.assertEqual(view.count('class="c4-arrow"'), 4)  # two arrows, in two drawings

    def test_adr_links_stay_out_of_drawings(self):
        self.put("docs/status/tldr.md", "Built on ADR 0003.\n")
        page, _, _ = self.build()
        self.assertIn('<a href="https://log#adr-0003">ADR 0003</a>', page)
        self.put("docs/architecture.md", ARCH.replace('"Database"', '"Database" : ADR 0004'))
        with contextlib.redirect_stderr(io.StringIO()):
            page = rs.build(self.root, "https://log")[0]
        self.assertNotIn("#adr-0004", page)

    def test_the_example_in_the_status_readme_draws_without_warnings(self):
        readme = (pathlib.Path(rs.__file__).resolve().parent.parent / "docs" / "status" / "README.md").read_text(
            encoding="utf-8")
        example = readme.split("````\n", 1)[1].split("````", 1)[0]
        self.put("docs/architecture.md", "# Architecture\n\n" + example)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            page, _, _, d = rs.build(self.root)
        self.assertEqual((d, err.getvalue()), (1, ""))
        self.assertIn("<title id=\"c4-c2-app-w-t\">C2 Containers</title>", page)

    def test_prose_only_architecture_leaves_the_section_out(self):
        self.put("docs/architecture.md", "# Architecture\n\n## C1. Context\n\nWords only.\n")
        page = self.page()
        self.assertNotIn("Architecture, C1 to C4", page)
        self.assertIn("architecture diagrams", page)


class AdrLinks(Base):
    def test_existing_links_and_diagrams_are_left_alone(self):
        frag = '<a href="https://x">ADR 0001</a> <svg><text>ADR-0002</text></svg> adr 0004'
        out = rs.link_adrs(frag, "https://log")
        self.assertIn('<a href="https://x">ADR 0001</a>', out)
        self.assertIn("<text>ADR-0002</text>", out)
        self.assertIn('<a href="https://log#adr-0004">adr 0004</a>', out)


class RealRepo(unittest.TestCase):
    def test_page_renders_with_whatever_is_in_the_repo(self):
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "status.html"
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rs.main([str(out)])
            page = out.read_text(encoding="utf-8")
        self.assertIn(f"<title>{rs.project_name(rs.ROOT)} Status</title>", page)


if __name__ == "__main__":
    unittest.main()
