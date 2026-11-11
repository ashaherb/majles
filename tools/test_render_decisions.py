"""Tests for render_decisions.py.   python3 -m unittest tools/test_render_decisions.py"""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import render_decisions as rd  # noqa: E402


class InlineMarkup(unittest.TestCase):
    def test_escapes_before_marking_up(self):
        self.assertEqual(rd.inline("a <b> & **c**"), "a &lt;b&gt; &amp; <strong>c</strong>")

    def test_code_and_external_links(self):
        self.assertEqual(rd.inline("`x` [d](https://e.f)"), '<code>x</code> <a href="https://e.f">d</a>')

    def test_repo_relative_links_become_plain_text(self):
        self.assertEqual(rd.inline("see [ADR 0000](0000-repo-layout.md)"), "see ADR 0000")


class AdrRendering(unittest.TestCase):
    SAMPLE = """# 0042. A decision, as a claim

Status: accepted
Date: 2026-01-01
Needed by: slice 2
Amends: 0007

## Context

Why it was hard.

## Options considered

**Option A.** Rejected, because.

**Option B.** Chosen.

## Decision

| Directory | Owner |
|---|---|
| `docs/` | architect |

- one
- two

## What would make us revisit this

A new fact.
"""

    def render(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "0042-sample.md"
            p.write_text(self.SAMPLE, encoding="utf-8")
            return rd.render_adr(p)

    def test_header_and_meta(self):
        number, title, status, out = self.render()
        self.assertEqual((number, title, status), ("0042", "A decision, as a claim", "accepted"))
        self.assertIn('<span class="rel">Amends 0007</span>', out)
        self.assertIn('<span class="rel">Needed by slice 2</span>', out)
        self.assertNotIn("<p>Needed by", out)

    def test_only_the_chosen_option_is_marked(self):
        out = self.render()[3]
        self.assertEqual(out.count('class="option chosen"'), 1)
        self.assertEqual(out.count('class="option"'), 1)

    def test_table_list_and_revisit_box(self):
        out = self.render()[3]
        self.assertIn("<td><code>docs/</code></td>", out)
        self.assertIn("<li>one</li><li>two</li>", out)
        self.assertIn('<div class="revisit"><h3>What would make us revisit this</h3><p>A new fact.</p></div>', out)

    def test_bad_title_line_fails_loudly(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "0001-bad.md"
            p.write_text("# No number here\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                rd.render_adr(p)


class Assumptions(unittest.TestCase):
    REGISTER = """# What we assumed for you

```markdown
## A-N. The format example
Status: assumed
```

## A-1. Uploads are at most 5 MB

Status: lifted
Costs the user: no large photos.
Decided: d-3

## A-2. Never <b>cash</b>

Status: Assumed
Assumed by: builder, 2026-11-01
To lift: remove the check in `pay.py`.
"""

    def render(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "assumptions.md"
            p.write_text(self.REGISTER, encoding="utf-8")
            return rd.assumptions(p), rd.render_assumptions(p)

    def test_entries_skip_the_format_example(self):
        entries = self.render()[0]
        self.assertEqual([(e["id"], e["Status"]) for e in entries], [("A-1", "lifted"), ("A-2", "assumed")])

    def test_open_ones_first_escaped_with_their_fields(self):
        out = self.render()[1]
        self.assertLess(out.index("A-2"), out.index("A-1"))
        self.assertIn('<article class="assumption assumed">', out)
        self.assertIn("Never &lt;b&gt;cash&lt;/b&gt;", out)
        self.assertIn("<dt>To lift</dt><dd>remove the check in <code>pay.py</code>.</dd>", out)
        self.assertIn("<dt>Decided</dt><dd>d-3</dd>", out)

    def test_no_register_renders_nothing(self):
        self.assertEqual(rd.render_assumptions(pathlib.Path("/nonexistent/assumptions.md")), "")


class RealRepo(unittest.TestCase):
    def test_every_adr_in_the_repo_renders(self):
        for f in sorted(rd.ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")):
            number, title, status, _ = rd.render_adr(f)
            self.assertEqual(number, f.name[:4], f.name)
            self.assertTrue(title and status, f.name)

    def test_every_rules_file_has_a_title_and_renders(self):
        files = sorted(rd.RULES_DIR.glob("*.md"))
        self.assertTrue(files)
        for f in files:
            self.assertTrue(f.read_text(encoding="utf-8").startswith("# "), f.name)
        out = rd.render_rules()
        self.assertEqual(out.count('class="rule-card"'), len(files))

    def test_page_renders_with_whatever_is_in_the_repo(self):
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "page.html"
            sys.argv = ["render_decisions.py", str(out)]
            rd.main()
            page = out.read_text(encoding="utf-8")
        self.assertIn(f"<title>{rd.project_name()} Decisions</title>", page)
        self.assertIn("How the team works", page)
        self.assertIn("What we assumed for you", page)


if __name__ == "__main__":
    unittest.main()
