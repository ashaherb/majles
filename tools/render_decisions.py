#!/usr/bin/env python3
"""
render_decisions.py: render the decision log as one HTML page for the Artifact.

Zero dependencies. Python 3.9+.

    python3 tools/render_decisions.py OUT.html

Reads every docs/adr/NNNN-*.md, every docs/research/*/decision.md and every
.claude/rules/*.md, and writes a single self-contained page. The repo is the source of truth: this page is only
ever regenerated from it, never edited by hand, so the two cannot drift.

Understands the small Markdown subset the ADRs use: headings, paragraphs,
bullet lists, pipe tables, fenced code, **bold**, `code` and [links](url).
Anything fancier should be simplified in the ADR rather than taught to this
script.
"""

import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ADR_DIR = ROOT / "docs" / "adr"
RESEARCH_DIR = ROOT / "docs" / "research"
RULES_DIR = ROOT / ".claude" / "rules"
README = ROOT / "README.md"


def project_name():
    """The project's name is the first heading of README.md."""
    for line in README.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ROOT.name

META_KEYS = ("Status", "Date", "Needed by", "Amends", "Supersedes")


def inline(text):
    """Escape, then apply the inline markup the ADRs use."""
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)

    def link(m):
        label, href = m.group(1), m.group(2)
        if href.startswith(("http://", "https://")):
            return f'<a href="{html.escape(href)}">{label}</a>'
        return label  # repo-relative links mean nothing on the published page

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, out)


def blocks(lines):
    """Split body lines into (kind, lines) blocks."""
    out, buf, kind, fence = [], [], None, False

    def flush():
        nonlocal buf, kind
        if buf:
            out.append((kind, buf))
        buf, kind = [], None

    for line in lines:
        if line.startswith("```"):
            if fence:
                buf.append(line)
                flush()
                fence = False
            else:
                flush()
                kind, fence = "code", True
                buf.append(line)
            continue
        if fence:
            buf.append(line)
            continue
        if not line.strip():
            flush()
            continue
        if line.startswith("## "):
            flush()
            out.append(("h", [line[3:].strip()]))
            continue
        this = "table" if line.startswith("|") else "list" if line.startswith("- ") else "p"
        if kind == "list" and this == "p" and line.startswith("  "):
            buf[-1] += " " + line.strip()  # continuation of a list item
            continue
        if kind and kind != this:
            flush()
        kind = this
        buf.append(line)
    flush()
    return out


def render_block(kind, lines, section):
    if kind == "code":
        body = "\n".join(lines[1:-1])
        return f'<pre class="code"><code>{html.escape(body)}</code></pre>'
    if kind == "list":
        items = "".join(f"<li>{inline(l[2:].strip())}</li>" for l in lines)
        return f"<ul>{items}</ul>"
    if kind == "table":
        rows = [
            [c.strip() for c in l.strip().strip("|").split("|")]
            for l in lines
            if not re.fullmatch(r"\|?[\s:|-]+\|?", l.strip())
        ]
        head, body = rows[0], rows[1:]
        th = "".join(f"<th>{inline(c)}</th>" for c in head)
        trs = "".join(
            "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body
        )
        return (
            '<div class="tbl-wrap"><table class="tbl">'
            f"<thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>"
        )
    text = inline(" ".join(l.strip() for l in lines))
    if section == "Options considered" and text.startswith("<strong>"):
        chosen = " chosen" if re.search(r"\bChosen\b", text) else ""
        return f'<div class="option{chosen}"><p>{text}</p></div>'
    return f"<p>{text}</p>"


def parse_adr(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    m = re.match(r"#\s+(\d{4})\.\s+(.*)", lines[0])
    if not m:
        raise SystemExit(f"{path.name}: first line must be '# NNNN. Title'")
    number, title = m.group(1), m.group(2).strip()
    meta, i = {}, 1
    while i < len(lines) and (not lines[i].strip() or lines[i].split(":")[0] in META_KEYS):
        if lines[i].strip():
            key, _, value = lines[i].partition(":")
            meta[key] = value.strip()
        i += 1
    return number, title, meta, lines[i:]


def render_adr(path):
    number, title, meta, body = parse_adr(path)
    parts, section, revisit = [], None, []
    for kind, blines in blocks(body):
        if kind == "h":
            section = blines[0]
            target = revisit if section.startswith("What would make us revisit") else parts
            target.append(f"<h3>{inline(section)}</h3>")
            continue
        target = revisit if revisit and section.startswith("What would make us revisit") else parts
        target.append(render_block(kind, blines, section))

    chips = [f'<span class="status">{html.escape(meta.get("Status", "proposed"))}</span>']
    if "Date" in meta:
        chips.append(f'<span class="date">{html.escape(meta["Date"])}</span>')
    if "Needed by" in meta:
        chips.append(f'<span class="rel">Needed by {html.escape(meta["Needed by"])}</span>')
    for key in ("Amends", "Supersedes"):
        if key in meta:
            chips.append(f'<span class="rel">{key} {inline(meta[key])}</span>')

    revisit_html = f'<div class="revisit">{"".join(revisit)}</div>' if revisit else ""
    return number, title, meta.get("Status", ""), f"""
    <article class="entry" id="adr-{number}">
      <p class="entry-num">{number}</p>
      <div>
        <div class="entry-head">
          <h2>{inline(title)}</h2>
          <div class="meta">{"".join(chips)}</div>
        </div>
        <div class="entry-body">{"".join(parts)}{revisit_html}</div>
      </div>
    </article>"""


def research_decisions():
    rows = []
    for d in sorted(RESEARCH_DIR.glob("*/decision.md")):
        text = d.read_text(encoding="utf-8").splitlines()
        title = next((l[2:].removeprefix("Decision:").strip() for l in text if l.startswith("# ")), d.parent.name)
        by = next((l.split(":", 1)[1].strip() for l in text if l.startswith("Decided by:")), "")
        date = next((l.split(":", 1)[1].strip() for l in text if l.startswith("Date:")), "")
        rows.append(
            f'<li><span class="date">{html.escape(date)}</span>'
            f"<span>{inline(title)}</span>"
            f'<span class="who">{html.escape(by)} · <code>docs/research/{html.escape(d.parent.name)}/</code></span></li>'
        )
    if not rows:
        return (
            '<p class="empty">No research has been commissioned yet. Each choice an agent '
            "makes from research will be listed here, with the directory that holds its "
            "request, findings and reasoning.</p>"
        )
    return f'<ul class="rlist">{"".join(rows)}</ul>'



def render_rules():
    """Each rules file: its rule headings visible, the full text on demand."""
    cards = []
    for f in sorted(RULES_DIR.glob("*.md")):
        lines = f.read_text(encoding="utf-8").splitlines()
        title = next((l[2:].strip() for l in lines if l.startswith("# ")), f.stem)
        body = [l for l in lines if not l.startswith("# ")]
        heads = [l[3:].strip() for l in body if l.startswith("## ")]
        summary = (
            "<ul>" + "".join(f"<li>{inline(h)}</li>" for h in heads) + "</ul>" if heads else ""
        )
        full = "".join(
            f"<h4>{inline(b[0])}</h4>" if k == "h" else render_block(k, b, None)
            for k, b in blocks(body)
        )
        cards.append(
            f'<article class="rule-card"><h3>{inline(title)} <code>{html.escape(f.name)}</code></h3>'
            f"{summary}<details><summary>Full text and reasons</summary>"
            f'<div class="rule-full">{full}</div></details></article>'
        )
    return "".join(cards) or '<p class="empty">No rules yet.</p>'


CSS = """
  /* The decision log's own house style, the same for every project built from
     the template. It is deliberately not the product's design system, which
     the designer establishes from research. One light ground, with every colour
     painted explicitly rather than borrowed from a host theme. */
  :root {
    --c-ground:#FCFCFB; --c-surface:#FFFFFF; --c-surface-sunk:#F4F3F0;
    --c-rule:#E3E1DB; --c-rule-strong:#C9C6BD;
    --c-ink:#131A33; --c-ink-soft:#5B5F71; --c-ink-faint:#8A8D99;
    --c-brand:#24379B; --c-brand-press:#1A2872; --c-brand-wash:#E7EAF7; --c-brand-edge:#C3CAEA;
    --c-warn:#A2610B; --c-warn-wash:#FAF0DF; --c-warn-edge:#E8D5AE;
    --font-sans:"IBM Plex Sans Arabic","IBM Plex Sans",ui-sans-serif,system-ui,"Segoe UI",sans-serif;
    --font-mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,monospace;
    --w-light:300; --w-regular:400; --w-medium:500; --w-semi:600;
    --t-xs:.75rem; --t-sm:.875rem; --t-base:1rem; --t-md:1.125rem;
    --t-lg:1.375rem; --t-xl:1.875rem; --t-2xl:2.75rem;
    --lh-tight:1.15; --lh-snug:1.3; --lh-normal:1.55; --track-tight:-.02em;
    --measure:62ch;
    --s-1:.25rem; --s-2:.5rem; --s-3:.75rem; --s-4:1rem; --s-5:1.5rem;
    --s-6:2rem; --s-7:3rem; --s-8:4rem; --s-9:6rem;
    --r-control:6px; --r-panel:3px; --r-pill:999px;
    --border:1px solid var(--c-rule); --border-strong:1px solid var(--c-rule-strong);
    --page-max:60rem; --gutter:var(--s-5);
  }
  @media (max-width:40rem){ :root{ --t-2xl:1.875rem; --t-xl:1.5rem; --gutter:var(--s-4); } }

  *,*::before,*::after{ box-sizing:border-box; }
  html{ -webkit-text-size-adjust:100%; }
  body{ margin:0; background:var(--c-ground); color:var(--c-ink); font-family:var(--font-sans);
    font-size:var(--t-base); line-height:var(--lh-normal); font-feature-settings:"kern" 1; }
  h1,h2,h3,p,ul,table,pre{ margin-block:0; }
  a{ color:var(--c-brand); text-decoration-thickness:1px; text-underline-offset:.18em; }
  a:hover{ color:var(--c-brand-press); }
  :focus-visible{ outline:2px solid var(--c-brand); outline-offset:2px; border-radius:var(--r-control); }
  code{ font-family:var(--font-mono); font-size:.88em; background:var(--c-surface-sunk);
    padding:.1em .35em; border-radius:var(--r-panel); overflow-wrap:anywhere; }
  strong{ font-weight:var(--w-semi); }

  .page{ max-inline-size:var(--page-max); margin-inline:auto; padding-inline:var(--gutter); }

  .masthead{ padding-block:var(--s-8) var(--s-6); border-block-end:var(--border-strong); }
  .eyebrow, .section-label{ font-family:var(--font-mono); font-size:var(--t-xs); font-weight:500;
    letter-spacing:.12em; text-transform:uppercase; color:var(--c-ink-faint); }
  .eyebrow{ margin-block-end:var(--s-4); }
  .masthead h1{ font-size:var(--t-2xl); font-weight:var(--w-semi); line-height:var(--lh-tight);
    letter-spacing:var(--track-tight); text-wrap:balance; }
  .masthead h1 .ar{ font-weight:var(--w-light); color:var(--c-ink-soft); }
  .standfirst{ margin-block-start:var(--s-4); font-size:var(--t-md); color:var(--c-ink-soft);
    max-inline-size:var(--measure); }

  .rules{ display:grid; grid-template-columns:repeat(auto-fit,minmax(15rem,1fr)); gap:var(--s-5);
    padding-block:var(--s-6); border-block-end:var(--border); margin:0; }
  .rules dt{ font-family:var(--font-mono); font-size:var(--t-xs); font-weight:500;
    letter-spacing:.1em; text-transform:uppercase; color:var(--c-brand); margin-block-end:var(--s-2); }
  .rules dd{ margin:0; font-size:var(--t-sm); color:var(--c-ink-soft); }

  /* Index: the log is numbered because order carries meaning: later entries
     amend earlier ones. */
  .index{ padding-block:var(--s-6); border-block-end:var(--border); }
  .index ol{ list-style:none; padding:0; margin:var(--s-4) 0 0; display:grid; gap:var(--s-2); }
  .index li a{ display:grid; grid-template-columns:3.5rem 1fr; gap:var(--s-4); align-items:baseline;
    color:var(--c-ink); text-decoration:none; padding-block:var(--s-1); }
  .index li a:hover .t{ color:var(--c-brand); text-decoration:underline; text-underline-offset:.18em; }
  .index .n{ font-family:var(--font-mono); font-size:var(--t-sm); color:var(--c-ink-faint);
    font-variant-numeric:tabular-nums; }

  .log{ display:grid; gap:var(--s-8); padding-block:var(--s-7); }
  .entry{ display:grid; grid-template-columns:5.5rem 1fr; gap:var(--s-6); }
  .entry + .entry{ padding-block-start:var(--s-8); border-block-start:var(--border); }
  @media (max-width:48rem){ .entry{ grid-template-columns:1fr; gap:var(--s-3); } }
  .entry-num{ font-family:var(--font-mono); font-size:var(--t-lg); font-weight:500;
    color:var(--c-rule-strong); line-height:var(--lh-tight); font-variant-numeric:tabular-nums;
    padding-block-start:.15em; }
  .entry-head h2{ font-size:var(--t-xl); font-weight:var(--w-semi); line-height:var(--lh-snug);
    letter-spacing:var(--track-tight); text-wrap:balance; }
  .meta{ display:flex; flex-wrap:wrap; align-items:center; gap:var(--s-3); margin-block-start:var(--s-3); }
  .status{ font-family:var(--font-mono); font-size:var(--t-xs); font-weight:500; letter-spacing:.08em;
    text-transform:uppercase; padding:.25em .7em; border-radius:var(--r-pill);
    background:var(--c-brand-wash); color:var(--c-brand-press); border:1px solid var(--c-brand-edge); }
  .date, .rel{ font-family:var(--font-mono); font-size:var(--t-xs); color:var(--c-ink-faint);
    font-variant-numeric:tabular-nums; }

  .entry-body{ margin-block-start:var(--s-6); }
  .entry-body > * + *{ margin-block-start:var(--s-4); }
  .entry-body p, .entry-body ul{ max-inline-size:var(--measure); }
  .entry-body ul{ padding-inline-start:var(--s-5); }
  .entry-body li + li{ margin-block-start:var(--s-2); }
  .entry-body h3{ font-family:var(--font-mono); font-size:var(--t-xs); font-weight:500;
    letter-spacing:.12em; text-transform:uppercase; color:var(--c-ink-faint);
    margin-block-start:var(--s-7); padding-block-end:var(--s-2); border-block-end:var(--border);
    max-inline-size:var(--measure); }
  .entry-body > h3:first-child{ margin-block-start:0; }

  /* The alternatives. An ADR without them is a preference, not a decision, so
     each gets a rail; the one chosen takes the brand colour. */
  .option{ border-inline-start:2px solid var(--c-rule-strong); padding-inline-start:var(--s-4);
    padding-block:var(--s-1); max-inline-size:var(--measure); }
  .option.chosen{ border-inline-start-color:var(--c-brand); }
  .option.chosen strong{ color:var(--c-brand-press); }

  .tbl-wrap{ overflow-x:auto; }
  .tbl{ inline-size:100%; border-collapse:collapse; font-size:var(--t-sm); }
  .tbl th, .tbl td{ text-align:start; padding:var(--s-3) var(--s-4); border-block-end:var(--border);
    vertical-align:baseline; }
  .tbl thead th{ font-family:var(--font-mono); font-size:var(--t-xs); font-weight:500;
    letter-spacing:.1em; text-transform:uppercase; color:var(--c-ink-faint);
    border-block-end:var(--border-strong); }
  .tbl td:first-child{ white-space:nowrap; }

  pre.code{ background:var(--c-surface-sunk); padding:var(--s-4); border-radius:var(--r-panel);
    overflow-x:auto; font-size:var(--t-sm); }
  pre.code code{ background:none; padding:0; }

  .revisit{ padding:var(--s-5); background:var(--c-warn-wash); border-radius:var(--r-panel);
    max-inline-size:var(--measure); margin-block-start:var(--s-6) !important; }
  .revisit > * + *{ margin-block-start:var(--s-3); }
  .revisit h3{ margin-block-start:0; color:var(--c-warn); border-block-end-color:var(--c-warn-edge); }
  .revisit p{ font-size:var(--t-sm); }

  .research{ padding-block:var(--s-7); border-block-start:var(--border-strong); }
  .research h2{ font-size:var(--t-lg); font-weight:var(--w-semi); margin-block:var(--s-3) var(--s-4); }
  .research .empty{ color:var(--c-ink-soft); max-inline-size:var(--measure); }
  .rlist{ list-style:none; padding:0; display:grid; gap:var(--s-3); }
  .rlist li{ display:grid; grid-template-columns:6.5rem 1fr; gap:var(--s-1) var(--s-4); }
  .rlist .who{ grid-column:2; font-size:var(--t-sm); color:var(--c-ink-faint); }

  .empty{ color:var(--c-ink-soft); max-inline-size:var(--measure); }
  .section-head{ padding-block:var(--s-7) 0; }
  .section-head h2{ font-size:var(--t-lg); font-weight:var(--w-semi); margin-block-start:var(--s-3); }
  .section-head p:not(.section-label){ margin-block-start:var(--s-2); color:var(--c-ink-soft);
    max-inline-size:var(--measure); font-size:var(--t-sm); }

  .rules-grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(18rem,1fr));
    gap:var(--s-4); padding-block:var(--s-5) var(--s-7); }
  .rule-card{ background:var(--c-surface); border:var(--border); border-radius:var(--r-panel);
    padding:var(--s-4) var(--s-5); display:grid; gap:var(--s-3); align-content:start; }
  .rule-card h3{ font-size:var(--t-base); font-weight:var(--w-semi); display:flex;
    flex-wrap:wrap; gap:var(--s-2); align-items:baseline; }
  .rule-card h3 code{ font-size:var(--t-xs); font-weight:var(--w-regular); color:var(--c-ink-faint); }
  .rule-card ul{ margin:0; padding-inline-start:var(--s-4); font-size:var(--t-sm); display:grid; gap:var(--s-1); }
  .rule-card summary{ cursor:pointer; font-size:var(--t-xs); font-family:var(--font-mono);
    color:var(--c-brand); letter-spacing:.04em; }
  .rule-full{ margin-block-start:var(--s-3); font-size:var(--t-sm); display:grid; gap:var(--s-3); }
  .rule-full h4{ font-size:var(--t-sm); font-weight:var(--w-semi); margin:var(--s-2) 0 0; }
  .rule-full p, .rule-full ul{ margin:0; }

  .colophon{ border-block-start:var(--border); padding-block:var(--s-5) var(--s-8);
    font-size:var(--t-sm); color:var(--c-ink-faint); max-inline-size:var(--measure); }
"""


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: render_decisions.py OUT.html")
    adrs = [render_adr(p) for p in sorted(ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"))]
    if adrs:
        index = "".join(
            f'<li><a href="#adr-{n}"><span class="n">{n}</span><span class="t">{inline(t)}</span></a></li>'
            for n, t, _, _ in adrs
        )
        adr_html = (
            f'<nav class="index" aria-label="Architecture decisions"><ol>{index}</ol></nav>'
            f'<main class="log">{"".join(a[3] for a in adrs)}</main>'
        )
    else:
        adr_html = (
            '<p class="empty" style="padding-block:var(--s-4) var(--s-7)">No architecture '
            "decisions yet. The first will be the stack, from the Phase 0 planning pass.</p>"
        )
    count = f"{len(adrs)} architecture decision{'s' if len(adrs) != 1 else ''}"
    name = html.escape(project_name())
    page = f"""<title>{name} Decisions</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
<div class="page">
  <header class="masthead">
    <p class="eyebrow">Decision log · {count}</p>
    <h1>{name} Decisions</h1>
    <p class="standfirst">Generated from the repository by <code>tools/render_decisions.py</code>;
    if this page and the repository ever disagree, the repository wins.</p>
  </header>
  <dl class="rules">
    <div><dt>Architecture only</dt><dd>An ADR is for a decision that is expensive to reverse and that later work builds on. Everything smaller is a rule.</dd></div>
    <div><dt>Append only</dt><dd>ADRs are never edited. A decision that changes gets a new entry saying what changed and why.</dd></div>
    <div><dt>Research what blocks</dt><dd>Research runs only when its answer could change a decision the next step waits on, and the reasoning over the findings is written down before the work begins.</dd></div>
  </dl>
  <div class="section-head">
    <p class="section-label">docs/adr/</p>
    <h2>Architecture decisions</h2>
  </div>
  {adr_html}
  <section class="research" aria-labelledby="research-h">
    <p class="section-label">docs/research/</p>
    <h2 id="research-h">Choices agents made from research</h2>
    {research_decisions()}
  </section>
  <section class="research" aria-labelledby="rules-h">
    <p class="section-label">.claude/rules/</p>
    <h2 id="rules-h">How the team works</h2>
    <p class="empty">Living rules, edited in place. Every agent loads them in every session.</p>
    <div class="rules-grid">{render_rules()}</div>
  </section>
  <footer class="colophon"><p>The decision log's house style, shared by every project
  built from the Majles template. It is not the product's own design.</p></footer>
</div>
"""
    pathlib.Path(sys.argv[1]).write_text(page, encoding="utf-8")
    print(f"wrote {sys.argv[1]} ({count})")


if __name__ == "__main__":
    main()
