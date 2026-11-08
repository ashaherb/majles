#!/usr/bin/env python3
"""
render_status.py: render the project's status as one HTML page for the Artifact.

Zero dependencies. Python 3.9+.

    python3 tools/render_status.py OUT.html [--decisions-url URL] [--root DIR]

The page is read in under a minute: where the project is, what is happening,
what comes next, what it looks like, and how it is built. Everything on it is
read from the repo, never hand-edited, and every section is left out when its
input is missing:

- docs/status/tldr.md: three to five lines, the top of the page;
- CLAUDE.md, `## Phases`: one segment of the slice strip per `### Slice N` heading;
- docs/status/now.md and next.md: a handful of one-line items each;
- docs/status/waiting.md: what waits on the developer;
- docs/status/screens/: screenshots, as a contact sheet, with captions.md (optional);
- docs/architecture.md: ```c4 blocks, drawn as C1 to C4 diagrams you zoom through;
- docs/status/spend.md: spend against the budget.

CLAUDE.md's prose never reaches the page. The input formats are in
docs/status/README.md. Screenshots are referenced as `screens/<name>`, not
embedded; their paths are printed after the "wrote" line, and the page is
published with those files beside it. With --decisions-url, every "ADR NNNN"
links to its entry in the published decision log.

It reuses render_decisions.py's Markdown subset and house style.
"""

import argparse
import datetime
import html
import pathlib
import re
import subprocess
import sys
import textwrap

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import render_decisions as rd  # noqa: E402

ROOT = rd.ROOT
IMAGES = (".png", ".jpg", ".jpeg", ".webp", ".gif")
SLICE = re.compile(r"^###\s+Slice\s+(\d+)\b[.:]?\s*(.*)$", re.I)
LATER = re.compile(r"^###\s+Slices\s+(\d+)\s*(?:to|-|–)\s*(\d+)\b", re.I)
STATES = (("gate open", "Gate open", "progress"), ("in progress", "In progress", "progress"),
          ("not started", "Not started", "todo"), ("built", "Built", "done"), ("done", "Done", "done"))
C4_HEADING = re.compile(r"^##\s+(C[1-4])\b[.:]?\s*(.*)$")
ADR_REF = re.compile(r"\b(?:ADR|adr)[ -](\d{4})\b")
LEVEL_NAMES = {"C1": "System context", "C2": "Containers", "C3": "Components", "C4": "Code"}
LIMITS = {"tldr.md": 5, "now.md": 7, "next.md": 7}


def warn(msg):
    print(f"render_status: {msg}", file=sys.stderr)


def project_name(root):
    """The first heading of README.md, as render_decisions.py reads it."""
    if root == rd.ROOT:
        return rd.project_name()
    readme = root / "README.md"
    if readme.exists():
        for line in readme.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return root.name


def repo_url(root):
    """The GitHub page of `origin`, from any SSH alias of github.com; None otherwise."""
    try:
        url = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.match(r"^(?:git@|ssh://git@|https://)([^:/]+)[:/](.+?)(?:\.git)?$", url)
    if not m or "github.com" not in m.group(1):
        return None
    return "https://github.com/" + m.group(2)


def read(path):
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def section(lines, heading):
    """The lines under `## heading`, up to the next `## ` or `# `; None if absent."""
    out, inside, fence = [], False, False
    for line in lines:
        if line.startswith("```"):
            fence = not fence
        if not fence and (line.startswith("## ") or line.startswith("# ")):
            if inside:
                break
            inside = line.startswith("## ") and line[3:].strip().lower() == heading.lower()
            continue
        if inside:
            out.append(line)
    return out if inside or out else None


def render(lines, h="h3"):
    """Markdown lines to HTML, with `### ` sub-headings as `h`."""
    lines = ["## " + l[4:] if l.startswith("### ") else l for l in lines if not l.startswith("# ")]
    return "".join(f"<{h}>{rd.inline(b[0])}</{h}>" if k == "h" else rd.render_block(k, b, None)
                   for k, b in rd.blocks(lines))


def short_input(root, name):
    """A short status file as HTML, or None; warns when it runs past its limit."""
    lines = read(root / "docs" / "status" / name)
    content = [l for l in lines if l.strip() and not l.startswith("# ")]
    if not content:
        return None
    if len(content) > LIMITS[name]:
        warn(f"docs/status/{name} has {len(content)} lines; the page reads best with {LIMITS[name]} at most")
    # One line is one statement: a line break starts a new paragraph, not a continuation.
    return render([part for l in lines for part in ((l,) if l.startswith(("- ", "  ")) else (l, ""))])


# ---------------------------------------------------------------- slices


def state_of(*texts):
    for text in texts:
        low = text.lower()
        for word, label, cls in STATES:
            if word in low:
                return label, cls
    return None


def current_slice(claude):
    """The first "Slice N" in `## Current phase`, or None."""
    body = section(claude, "Current phase") or []
    m = re.search(r"\bSlice\s+(\d+)\b", " ".join(body), re.I)
    return int(m.group(1)) if m else None


def slices(claude):
    """The slice strip's HTML and the number of slices; (None, 0) without a phase plan."""
    body = section(claude, "Phases")
    if body is None:
        return None, 0
    segs, fence, firsts = [], False, {}
    for line in body:
        if line.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue  # the format example, not a slice
        m, later = SLICE.match(line), LATER.match(line)
        if m:
            title = m.group(2).strip()
            segs.append({"n": m.group(1), "title": title, "first": ""})
        elif later:
            segs.append({"n": f"{later.group(1)}–{later.group(2)}", "title": "", "first": "", "later": True})
        elif segs and line.strip() and not segs[-1]["first"] and not line.startswith("#"):
            segs[-1]["first"] = line
    if not segs:
        return None, 0
    now = current_slice(claude)
    items = []
    for s in segs:
        if s.get("later"):
            state, name, is_now = ("Planned", "todo"), "Later slices", False
        else:
            is_now = now is not None and int(s["n"]) == now
            state = state_of(s["title"], s["first"])
            if state is None:
                state = ("Now", "progress") if is_now else ("Planned", "todo") if now and int(s["n"]) > now else None
            # The title up to its first sentence: the state words after it are the chip.
            name = re.split(r"\.\s|\.$", s["title"])[0].strip() or f"Slice {s['n']}"
            name = name[:1].upper() + name[1:]
        cls = (state[1] if state else "none") + (" now" if is_now else "")
        chip = f'<span class="chip {state[1]}">{state[0]}</span>' if state else ""
        cur = ' aria-current="step"' if is_now else ""
        items.append(f'<li class="seg {cls}"{cur}><span class="seg-n">{s["n"]}</span>'
                     f'<span class="seg-t">{rd.inline(name)}</span>{chip}</li>')
    n = sum(1 for s in segs if not s.get("later"))
    return f'<ol class="strip">{"".join(items)}</ol>', n


# ---------------------------------------------------------------- lists


def waiting(root):
    lines = read(root / "docs" / "status" / "waiting.md")
    lines = [re.sub(r"^\d+\.\s+", "- ", l) for l in lines if not l.startswith("# ")]
    if not any(l.strip() for l in lines):
        return None, 0
    parts, count = [], 0
    for kind, b in rd.blocks(lines):
        if kind == "list":
            count += len(b)
            parts.append("<ol>" + "".join(f"<li>{rd.inline(l[2:].strip())}</li>" for l in b) + "</ol>")
        else:
            parts.append(rd.render_block(kind, b, None))
    return "".join(parts), count


def spend(root):
    lines = read(root / "docs" / "status" / "spend.md")
    if not any(l.strip() and not l.startswith("# ") for l in lines):
        return None, None
    title = next((l[2:].strip() for l in lines if l.startswith("# ")), None)
    return render(lines), title


# ---------------------------------------------------------------- screens


def captions(folder):
    """`name.png: caption` lines from screens/captions.md."""
    out = {}
    for line in read(folder / "captions.md"):
        m = re.match(r"^\s*(?:[-*]\s+)?`?([^`:\s]+\.(?:png|jpe?g|webp|gif))`?\s*[:—–]\s*(.+)$", line, re.I)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def caption_from(stem):
    text = re.sub(r"[-_]+", " ", re.sub(r"^\d+[-_ ]+", "", stem)).strip() or stem
    return text[:1].upper() + text[1:]


def screens(root):
    folder = root / "docs" / "status" / "screens"
    if not folder.is_dir():
        return None, []
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGES)
    if not files:
        return None, []
    named = captions(folder)
    paths = [f"screens/{p.name}" for p in files]
    figs = "".join(
        f'<figure><a href="{html.escape(path)}"><img src="{html.escape(path)}" '
        f'alt="{html.escape(named.get(p.name) or caption_from(p.stem))}" loading="lazy"></a>'
        f"<figcaption>{rd.inline(named.get(p.name) or caption_from(p.stem))}</figcaption></figure>"
        for p, path in zip(files, paths)
    )
    return f'<div class="sheet">{figs}</div>', paths


# ---------------------------------------------------------------- C1 to C4

NODE = re.compile(r'^(person|system|container|component|code|box|store|external)\s+([\w.-]+)\s+"([^"]+)"'
                  r"(?:\s*:\s*(.*))?$", re.I)
EDGE = re.compile(r"^([\w.-]+)\s*->\s*([\w.-]+)(?:\s*:\s*(.*))?$")


def parse_c4(root):
    """Every ```c4 block in docs/architecture.md, as diagrams; [] without any."""
    lines = read(root / "docs" / "architecture.md")
    diagrams, heading, buf = [], None, None
    for line in lines:
        if buf is not None:
            if line.startswith("```"):
                d = parse_block(buf, heading)
                if d:
                    diagrams.append(d)
                buf = None
            else:
                buf.append(line)
            continue
        if line.strip() == "```c4":
            buf = []
            continue
        if line.startswith("## "):
            m = C4_HEADING.match(line)
            heading = (m.group(1), m.group(2).strip()) if m else None
    diagrams.sort(key=lambda d: d["level"])  # stable: blocks keep their order within a level
    seen = set()
    for d in diagrams:
        base = f"c4-{d['level'].lower()}-{slug(d['inside'] or d['title'])}"
        d["id"], i = base, 2
        while d["id"] in seen:
            d["id"], i = f"{base}-{i}", i + 1
        seen.add(d["id"])
    for d in diagrams:  # a node another diagram is inside of zooms into it
        for n in d["nodes"]:
            n["zoom"] = next((c["id"] for c in diagrams if c["inside"] == n["id"] and c["level"] > d["level"]
                              and c["level"][1] == str(int(d["level"][1]) + 1)), None)
        parent = next((n for c in diagrams if c["level"] < d["level"] for n in c["nodes"]
                       if n["id"] == d["inside"]), None)
        d["inside_label"] = parent["label"] if parent else d["inside"]
    return diagrams


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-") or "d"


def parse_block(lines, heading):
    d = {"level": heading[0] if heading else None, "title": heading[1] if heading else "",
         "inside": None, "nodes": [], "edges": []}
    ids = {}
    for raw in lines:
        line = re.sub(r"\s+#\s.*$", "", raw).strip()  # a trailing "# comment" is a note
        if not line or line.startswith("#"):
            continue
        key, _, rest = line.partition(" ")
        if key.lower() == "level" and re.fullmatch(r"C[1-4]", rest.strip(), re.I):
            d["level"] = rest.strip().upper()
        elif key.lower() == "title":
            d["title"] = rest.strip()
        elif key.lower() == "inside":
            d["inside"] = rest.strip()
        elif NODE.match(line):
            m = NODE.match(line)
            n = {"kind": m.group(1).lower(), "id": m.group(2), "label": m.group(3), "desc": (m.group(4) or "").strip()}
            ids[n["id"]] = n
            d["nodes"].append(n)
        elif EDGE.match(line):
            m = EDGE.match(line)
            d["edges"].append((m.group(1), m.group(2), (m.group(3) or "").strip()))
        else:
            warn(f"docs/architecture.md: a c4 line was not understood and is left out: {line}")
    for e in [e for e in d["edges"] if e[0] not in ids or e[1] not in ids or e[0] == e[1]]:
        warn(f"docs/architecture.md: the arrow {e[0]} -> {e[1]} names a box that is not in its diagram")
        d["edges"].remove(e)
    if not d["level"]:
        warn("docs/architecture.md: a c4 block has no `level C1`..`C4` line and is not under a `## C1`..`## C4`"
             " heading; it is left out")
        return None
    if not d["nodes"]:
        return None
    d["title"] = d["title"] or LEVEL_NAMES[d["level"]]
    return d


def ranks(nodes, edges):
    """Longest-path layers over the arrows, ignoring the ones that close a cycle."""
    adj = {n["id"]: [] for n in nodes}
    for a, b, _ in edges:
        adj[a].append(b)
    state, back = {}, set()

    def dfs(u):
        state[u] = 1
        for v in adj[u]:
            if state.get(v) == 1:
                back.add((u, v))
            elif not state.get(v):
                dfs(v)
        state[u] = 2

    for n in nodes:
        if not state.get(n["id"]):
            dfs(n["id"])
    rank = {n["id"]: 0 for n in nodes}
    forward = [(a, b) for a, b, _ in edges if (a, b) not in back]
    for _ in nodes:
        changed = False
        for a, b in forward:
            if rank[b] < rank[a] + 1:
                rank[b], changed = rank[a] + 1, True
        if not changed:
            break
    return rank


WIDE = {"cols": 4, "w": 184, "gx": 40, "gy": 80, "m": 16, "label": 15, "desc": 12.5, "kind": 10, "edge": 11.5}
NARROW = {"cols": 2, "w": 152, "gx": 28, "gy": 76, "m": 8, "label": 14.5, "desc": 12, "kind": 9.5, "edge": 11}


def wrap(text, size, width, max_lines, factor):
    chars = max(6, int(width / (size * factor)))
    lines = textwrap.wrap(text, chars) or [""]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: max(1, chars - 1)].rstrip() + "…"
    return lines


def layout(d, g):
    """Boxes in rows by rank, wrapped at g['cols']; returns (boxes by id, width, height)."""
    rank = ranks(d["nodes"], d["edges"])
    preds = {n["id"]: [a for a, b, _ in d["edges"] if b == n["id"]] for n in d["nodes"]}
    order = {n["id"]: i for i, n in enumerate(d["nodes"])}
    pad = 12
    boxes, rows, x_of = {}, [], {}
    for r in sorted(set(rank.values())):
        layer = [n for n in d["nodes"] if rank[n["id"]] == r]

        def key(n):  # under the boxes that point at it, to keep arrows short and uncrossed
            xs = [x_of[p] for p in preds[n["id"]] if p in x_of]
            return (sum(xs) / len(xs) if xs else float("inf"), order[n["id"]])

        layer.sort(key=key)
        for i in range(0, len(layer), g["cols"]):
            row = layer[i:i + g["cols"]]
            rows.append(row)
            for j, n in enumerate(row):
                x_of[n["id"]] = j - (len(row) - 1) / 2
    inner = g["w"] - 2 * pad
    width = max(len(r) for r in rows) * g["w"] + (max(len(r) for r in rows) - 1) * g["gx"] + 2 * g["m"]
    y = g["m"] + 4
    for ri, row in enumerate(rows):
        texts = []
        for n in row:
            label = wrap(n["label"], g["label"], inner, 3, 0.56)
            desc = wrap(n["desc"], g["desc"], inner, 3, 0.52) if n["desc"] else []
            texts.append((label, desc))
        h = max(pad + g["kind"] + 8 + len(l) * g["label"] * 1.25 + (6 + len(ds) * g["desc"] * 1.3 if ds else 0) + pad
                for l, ds in texts)
        row_w = len(row) * g["w"] + (len(row) - 1) * g["gx"]
        x = (width - row_w) / 2
        for n, (label, desc) in zip(row, texts):
            boxes[n["id"]] = {"n": n, "x": x, "y": y, "w": g["w"], "h": h, "row": ri, "label": label, "desc": desc}
            x += g["w"] + g["gx"]
        y += h + g["gy"]
    return boxes, width, y - g["gy"] + g["m"] + 4


def anchors(d, boxes):
    """Each arrow's two ends, spread along the side they leave and enter by."""
    sides, plan = {}, []
    for k, (a, b, label) in enumerate(d["edges"]):
        A, B = boxes[a], boxes[b]
        if B["row"] > A["row"]:
            sa, sb = "bottom", "top"
        elif B["row"] < A["row"]:
            sa, sb = "top", "bottom"
        elif abs(A["x"] - B["x"]) <= A["w"] + 60:  # neighbours in a row
            sa, sb = ("right", "left") if B["x"] > A["x"] else ("left", "right")
        else:
            sa, sb = "bottom", "bottom"
        plan.append((sa, label))
        sides.setdefault((a, sa), []).append((b, k, "from"))
        sides.setdefault((b, sb), []).append((a, k, "to"))
    point = {}
    for (nid, side), ends in sides.items():
        box = boxes[nid]
        ends.sort(key=lambda e: boxes[e[0]]["x"] if side in ("top", "bottom") else boxes[e[0]]["y"])
        for i, (_, k, end) in enumerate(ends):
            f = (i + 1) / (len(ends) + 1)
            if side in ("top", "bottom"):
                xy = (box["x"] + box["w"] * (0.2 + 0.6 * f), box["y"] + (box["h"] if side == "bottom" else 0))
            else:
                xy = (box["x"] + (box["w"] if side == "right" else 0), box["y"] + box["h"] * (0.25 + 0.5 * f))
            point[(k, end)] = xy
    return [(point[(k, "from")], point[(k, "to")], sa, label) for k, (sa, label) in enumerate(plan)]


def svg(d, g, uid):
    boxes, width, height = layout(d, g)
    parts = []
    for (x1, y1), (x2, y2), side, label in anchors(d, boxes):
        if side in ("bottom", "top") and y1 != y2:
            mid = (y1 + y2) / 2
            c = (x1, mid, x2, mid)
        elif side == "bottom":  # along one row, under the boxes between
            c = (x1, y1 + 34, x2, y2 + 34)
        else:
            c = (x1 + (x2 - x1) / 2, y1, x1 + (x2 - x1) / 2, y2)
        path = f"M{x1:.1f},{y1:.1f} C{c[0]:.1f},{c[1]:.1f} {c[2]:.1f},{c[3]:.1f} {x2:.1f},{y2:.1f}"
        parts.append(f'<path class="c4-arrow" d="{path}" marker-end="url(#{uid}-head)"/>')
        if label:
            mx = (x1 + 3 * c[0] + 3 * c[2] + x2) / 8
            my = (y1 + 3 * c[1] + 3 * c[3] + y2) / 8
            lines = wrap(label, g["edge"], g["w"] - 24, 2, 0.5)
            y0 = my - (len(lines) - 1) * g["edge"] * 0.6 + g["edge"] * 0.35
            spans = "".join(f'<tspan x="{mx:.1f}" y="{y0 + i * g["edge"] * 1.2:.1f}">{html.escape(t)}</tspan>'
                            for i, t in enumerate(lines))
            parts.append(f'<text class="c4-elabel" font-size="{g["edge"]}" text-anchor="middle">{spans}</text>')
    for b in boxes.values():
        n = b["n"]
        kind = {"person": "person", "store": "store", "external": "external"}.get(n["kind"], "box")
        x, y, w, h = b["x"], b["y"], b["w"], b["h"]
        shape = f'<rect class="c4-box {kind}" x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h:.1f}" rx="{14 if kind == "person" else 4}"/>'
        if kind == "store":
            shape += f'<path class="c4-cap" d="M{x:.1f},{y + 9:.1f} Q{x + w / 2:.1f},{y + 19:.1f} {x + w:.1f},{y + 9:.1f}"/>'
        ty = y + 12 + g["kind"]
        text = [f'<text class="c4-kind" x="{x + 12:.1f}" y="{ty:.1f}" font-size="{g["kind"]}">{n["kind"].upper()}</text>']
        ty += 8
        for line in b["label"]:
            ty += g["label"] * 1.25
            text.append(f'<text class="c4-label" x="{x + 12:.1f}" y="{ty - 4:.1f}" font-size="{g["label"]}">'
                        f"{html.escape(line)}</text>")
        if b["desc"]:
            ty += 6
            for line in b["desc"]:
                ty += g["desc"] * 1.3
                text.append(f'<text class="c4-desc" x="{x + 12:.1f}" y="{ty - 4:.1f}" font-size="{g["desc"]}">'
                            f"{html.escape(line)}</text>")
        group = shape + "".join(text)
        if n["zoom"]:
            cx, cy = x + w - 16, y + 15
            group += (f'<circle class="c4-zoom" cx="{cx:.1f}" cy="{cy:.1f}" r="9"/>'
                      f'<path class="c4-zoom-plus" d="M{cx - 4:.1f},{cy:.1f}h8M{cx:.1f},{cy - 4:.1f}v8"/>')
            group = (f'<a class="c4-link" href="#{n["zoom"]}" aria-label="Zoom into {html.escape(n["label"])}">'
                     f"{group}</a>")
        parts.append(f"<g>{group}</g>")
    desc = "; ".join(f'{a} to {b}' + (f": {l}" if l else "") for a, b, l in d["edges"])
    head = (f'<defs><marker id="{uid}-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path class="c4-head" d="M0,0L10,5L0,10z"/></marker></defs>')
    return (f'<svg class="c4-svg" viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" role="img" '
            f'aria-labelledby="{uid}-t {uid}-d"><title id="{uid}-t">{html.escape(d["level"] + " " + d["title"])}</title>'
            f'<desc id="{uid}-d">{html.escape(desc)}</desc>{head}{"".join(parts)}</svg>')


def architecture(root):
    """The C1 to C4 views, one shown at a time; (None, 0) without a ```c4 block."""
    diagrams = parse_c4(root)
    if not diagrams:
        return None, 0
    views = []
    current = ' aria-current="true"'  # outside the f-string: Python 3.10 allows no backslash there
    for d in diagrams:
        nav = "".join(
            f'<li><a href="#{o["id"]}"{current if o is d else ""}>'
            f'<span class="c4-lv">{o["level"]}</span> {rd.inline(o["title"])}</a></li>'
            for o in diagrams
        )
        inside = (f'<p class="c4-inside">Inside <strong>{rd.inline(d["inside_label"])}</strong>'
                  f' · <a href="#{next((p["id"] for p in diagrams for n in p["nodes"] if n["zoom"] == d["id"]), diagrams[0]["id"])}">'
                  "Zoom out</a></p>" if d["inside"] else "")
        hint = ('<p class="c4-hint">Tap a box marked + to zoom in.</p>'
                if any(n["zoom"] for n in d["nodes"]) else "")
        views.append(
            f'<section class="c4-view" id="{d["id"]}" aria-label="{html.escape(d["level"] + " " + d["title"])}">'
            f'<nav class="c4-nav" aria-label="Architecture levels"><ol>{nav}</ol></nav>{inside}'
            f'<div class="c4-wide">{svg(d, WIDE, d["id"] + "-w")}</div>'
            f'<div class="c4-narrow">{svg(d, NARROW, d["id"] + "-n")}</div>{hint}</section>'
        )
    return f'<div class="c4-views">{"".join(views)}</div>', len(diagrams)


def link_adrs(fragment, url):
    """Link "ADR NNNN" in text, never inside a tag, a link or a diagram."""
    if not url:
        return fragment
    base = html.escape(url.split("#")[0])
    out, skip = [], 0
    for piece in re.split(r"(<[^>]+>)", fragment):
        if piece.startswith("<"):
            if re.match(r"<(a|svg)[\s>]", piece):
                skip += 1
            elif re.match(r"</(a|svg)>", piece) and skip:
                skip -= 1
            out.append(piece)
        elif skip:
            out.append(piece)
        else:
            out.append(ADR_REF.sub(lambda m: f'<a href="{base}#adr-{m.group(1)}">{m.group(0)}</a>', piece))
    return "".join(out)


# ---------------------------------------------------------------- page


DARK = """
    --c-ground:#0F1220; --c-surface:#161A2B; --c-surface-sunk:#1C2135;
    --c-rule:#2A3047; --c-rule-strong:#3A415C;
    --c-ink:#E7E9F2; --c-ink-soft:#A9ADC0; --c-ink-faint:#7D8299;
    --c-brand:#8EA0FF; --c-brand-press:#B4C0FF; --c-brand-wash:#1E2650; --c-brand-edge:#34408A;
    --c-warn:#E0A54A; --c-warn-wash:#2A2112; --c-warn-edge:#4A3A1E;
    --c-ok:#6FCF97; --c-ok-wash:#12291D; --c-ok-edge:#245A3A;
"""

CSS = rd.CSS + """
  :root{ --c-ok:#1E7A46; --c-ok-wash:#E3F3E9; --c-ok-edge:#B5DCC4; color-scheme:light;
    --thumb:13rem; --strip-min:9.5rem; }
  @media (max-width:40rem){ :root{ --thumb:9.5rem; --strip-min:8.5rem; } }
  @media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){ color-scheme:dark; %s } }
  :root[data-theme="dark"]{ color-scheme:dark; %s }

  .masthead{ padding-block:var(--s-7) var(--s-6); }
  .masthead .links{ margin-block-start:var(--s-3); font-size:var(--t-sm); color:var(--c-ink-faint);
    display:flex; flex-wrap:wrap; gap:var(--s-2) var(--s-4); }
  /* The one bold thing on the page: the TLDR, read first and in large type. */
  .tldr{ margin-block-start:var(--s-5); font-size:var(--t-lg); line-height:var(--lh-snug);
    max-inline-size:40ch; display:grid; gap:var(--s-3); }
  .tldr ul{ padding-inline-start:var(--s-5); display:grid; gap:var(--s-2); margin:0; }
  @media (max-width:40rem){ .tldr{ font-size:var(--t-md); } }

  .block{ padding-block:var(--s-6); border-block-end:var(--border); }
  .block > * + *{ margin-block-start:var(--s-4); }
  .block p, .block ul, .block ol{ max-inline-size:var(--measure); }
  .block ul, .block ol{ padding-inline-start:var(--s-5); }
  .block li + li{ margin-block-start:var(--s-2); }
  .block h2{ font-size:var(--t-md); font-weight:var(--w-semi); }
  .block h2 .count{ font-family:var(--font-mono); font-size:var(--t-sm); color:var(--c-ink-faint);
    font-weight:var(--w-regular); margin-inline-start:var(--s-2); }
  .block h3{ font-size:var(--t-base); font-weight:var(--w-semi); }

  .block .strip, .block .c4-nav ol{ max-inline-size:none; }
  .strip{ list-style:none; padding:0 !important; display:grid; gap:var(--s-2);
    grid-template-columns:repeat(auto-fit,minmax(min(100%%,var(--strip-min)),1fr)); }
  .strip li + li{ margin-block-start:0; }
  .seg{ border-block-start:4px solid var(--c-rule-strong); padding-block:var(--s-2) 0; display:grid;
    gap:var(--s-1); align-content:start; min-inline-size:0; }
  .seg.done{ border-block-start-color:var(--c-ok); }
  .seg.progress{ border-block-start-color:var(--c-brand); }
  .seg.now .seg-t{ font-weight:var(--w-semi); color:var(--c-ink); }
  .seg-n{ font-family:var(--font-mono); font-size:var(--t-xs); color:var(--c-ink-faint); }
  .seg-t{ font-size:var(--t-sm); line-height:var(--lh-snug); color:var(--c-ink-soft);
    display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
  .seg .chip{ justify-self:start; }
  .chip{ font-family:var(--font-mono); font-size:var(--t-xs); font-weight:500; letter-spacing:.06em;
    text-transform:uppercase; padding:.1em .6em; border-radius:var(--r-pill); border:1px solid; }
  .chip.done{ background:var(--c-ok-wash); color:var(--c-ok); border-color:var(--c-ok-edge); }
  .chip.progress{ background:var(--c-brand-wash); color:var(--c-brand-press); border-color:var(--c-brand-edge); }
  .chip.todo{ background:var(--c-surface-sunk); color:var(--c-ink-soft); border-color:var(--c-rule-strong); }

  .pair{ display:grid; gap:var(--s-5) var(--s-6);
    grid-template-columns:repeat(auto-fit,minmax(min(100%%,18rem),1fr)); }
  .pair > div{ display:grid; gap:var(--s-3); align-content:start; min-inline-size:0; }
  .pair ul{ list-style:none; padding:0 !important; margin:0; }
  .pair li{ padding-block:var(--s-2); border-block-start:var(--border); }
  .pair li + li{ margin-block-start:0; }

  .waiting ol{ display:grid; gap:var(--s-2); }
  .waiting li + li{ margin-block-start:0; }

  .sheet{ display:flex; flex-wrap:wrap; gap:var(--s-4) var(--s-3); }
  .sheet figure{ margin:0; display:grid; gap:var(--s-2); max-inline-size:100%%; align-content:start; }
  .sheet a{ display:block; border-radius:var(--r-panel); }
  .sheet img{ display:block; block-size:var(--thumb); inline-size:auto; max-inline-size:100%%;
    min-inline-size:calc(var(--thumb) * .55);
    object-fit:cover; object-position:top; border:var(--border); border-radius:var(--r-panel);
    background:var(--c-surface); }
  .sheet figcaption{ font-size:var(--t-xs); color:var(--c-ink-soft); max-inline-size:16rem; }

  .c4-view{ display:grid; gap:var(--s-3); }
  .c4-views:has(.c4-view:target) .c4-view:not(:target),
  .c4-views:not(:has(.c4-view:target)) .c4-view ~ .c4-view{ display:none; }
  .c4-view:target{ animation:c4-zoom .22s ease-out; scroll-margin-block-start:var(--s-5); }
  @keyframes c4-zoom{ from{ opacity:.35; transform:scale(.97); } to{ opacity:1; transform:none; } }
  @media (prefers-reduced-motion:reduce){ .c4-view:target{ animation:none; } }
  .c4-nav ol{ list-style:none; padding:0 !important; margin:0; display:flex; flex-wrap:wrap; gap:var(--s-2); }
  .c4-nav li + li{ margin-block-start:0; }
  .c4-nav a{ display:inline-block; font-size:var(--t-sm); padding:.2em .7em; border:var(--border);
    border-radius:var(--r-pill); text-decoration:none; color:var(--c-ink-soft); background:var(--c-surface); }
  .c4-nav a[aria-current]{ color:var(--c-brand-press); background:var(--c-brand-wash); border-color:var(--c-brand-edge); }
  .c4-lv{ font-family:var(--font-mono); font-size:var(--t-xs); color:var(--c-brand); }
  .c4-inside, .c4-hint{ font-size:var(--t-sm); color:var(--c-ink-soft); }
  .c4-wide, .c4-narrow{ background:var(--c-surface); border:var(--border); border-radius:var(--r-panel);
    padding:var(--s-2); }
  .c4-narrow{ display:none; }
  @media (max-width:40rem){ .c4-wide{ display:none; } .c4-narrow{ display:block; } }
  .c4-svg{ display:block; max-inline-size:100%%; block-size:auto; margin-inline:auto; }
  .c4-svg text{ font-family:var(--font-sans); }
  .c4-box{ fill:var(--c-surface); stroke:var(--c-brand-edge); stroke-width:1.5; }
  .c4-box.person{ fill:var(--c-brand-wash); stroke:var(--c-brand); }
  .c4-box.store{ fill:var(--c-surface-sunk); stroke:var(--c-rule-strong); }
  .c4-box.external{ fill:var(--c-surface-sunk); stroke:var(--c-rule-strong); stroke-dasharray:5 4; }
  .c4-cap{ fill:none; stroke:var(--c-rule-strong); stroke-width:1.5; }
  .c4-kind{ fill:var(--c-ink-faint); font-family:var(--font-mono) !important; letter-spacing:.08em; }
  .c4-label{ fill:var(--c-ink); font-weight:var(--w-semi); }
  .c4-desc{ fill:var(--c-ink-soft); }
  .c4-arrow{ fill:none; stroke:var(--c-ink-faint); stroke-width:1.4; }
  .c4-head{ fill:var(--c-ink-faint); }
  .c4-elabel{ fill:var(--c-ink-soft); paint-order:stroke; stroke:var(--c-surface); stroke-width:4px;
    stroke-linejoin:round; }
  .c4-zoom{ fill:var(--c-brand); }
  .c4-zoom-plus{ stroke:var(--c-surface); stroke-width:2; }
  .c4-link{ cursor:pointer; }
  .c4-link:hover .c4-box, .c4-link:focus-visible .c4-box{ stroke:var(--c-brand); stroke-width:2.5; }
  .c4-link:focus-visible{ outline:none; }

  .block .tbl td:first-child{ white-space:normal; }
  @media (max-width:40rem){ .block .tbl th, .block .tbl td{ padding-inline:var(--s-2); } }

  .colophon{ border-block-start:0; }
  .colophon p + p{ margin-block-start:var(--s-2); }
""" % (DARK, DARK)


def block(title, body, hid, cls="", count=None):
    n = f'<span class="count">{count}</span>' if count else ""
    return f'<section class="block {cls}" aria-labelledby="{hid}"><h2 id="{hid}">{title}{n}</h2>{body}</section>'


def build(root, decisions_url=None, today=None):
    """Returns (page, number of slices, screenshot paths, number of diagrams)."""
    claude = read(root / "CLAUDE.md")
    name = html.escape(project_name(root))
    parts, missing = [], []

    tldr = short_input(root, "tldr.md")
    if not tldr:
        missing.append("a TLDR (<code>docs/status/tldr.md</code>)")

    strip, n_slices = slices(claude)
    if strip:
        parts.append(block("Slices", strip, "slices-h"))

    cols = []
    for file, title in (("now.md", "Now"), ("next.md", "Next")):
        body = short_input(root, file)
        if body:
            cols.append(f'<div><h2 id="{file[:-3]}-h">{title}</h2>{body}</div>')
        else:
            missing.append(f"{title.lower()} (<code>docs/status/{file}</code>)")
    if cols:
        parts.append(f'<section class="block" aria-label="Now and next"><div class="pair">{"".join(cols)}</div></section>')

    w, n_wait = waiting(root)
    if w:
        parts.append(block("Waiting on the developer", w, "waiting-h", "waiting", n_wait))

    shots, paths = screens(root)
    if shots:
        parts.append(block("The screens", shots, "screens-h", count=len(paths)))
    else:
        missing.append("screenshots (<code>docs/status/screens/</code>)")

    arch, n_diagrams = architecture(root)
    if arch:
        parts.append(block("Architecture, C1 to C4", arch, "arch-h"))
    else:
        missing.append("architecture diagrams (<code>```c4</code> blocks in <code>docs/architecture.md</code>)")

    s, spend_title = spend(root)
    if s:
        parts.append(block(rd.inline(spend_title or "Spend"), s, "spend-h"))

    body = link_adrs("".join(parts), decisions_url)
    tldr_html = link_adrs(f'<div class="tldr">{tldr}</div>', decisions_url) if tldr else ""
    date = (today or datetime.date.today()).isoformat()
    links = []
    if decisions_url:
        links.append(f'<a href="{html.escape(decisions_url)}">Decision log</a>')
    repo = repo_url(root)
    if repo:
        links.append(f'<a href="{html.escape(repo)}">Repository</a>')
    links_html = f'<p class="links">{"".join(f"<span>{l}</span>" for l in links)}</p>' if links else ""
    gap = (f"<p>Not on this page yet: {', '.join(missing)}. The formats are in "
           "<code>docs/status/README.md</code>.</p>" if missing else "")
    page = f"""<title>{name} Status</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
<div class="page">
  <header class="masthead">
    <p class="eyebrow">Status · {date}</p>
    <h1>{name}</h1>
    {tldr_html}
    {links_html}
  </header>
  {body}
  <footer class="colophon"><p>Generated from the repository by <code>tools/render_status.py</code>; if this
  page and the repository disagree, the repository wins.</p>{gap}</footer>
</div>"""
    return page, n_slices, paths, n_diagrams


def main(argv=None, root=None):
    ap = argparse.ArgumentParser(description="Render the project's status page.")
    ap.add_argument("out")
    ap.add_argument("--decisions-url")
    ap.add_argument("--root", help="the project to render (default: the one this file is in)")
    args = ap.parse_args(argv)
    page, n, paths, d = build(root or (pathlib.Path(args.root).resolve() if args.root else ROOT), args.decisions_url)
    pathlib.Path(args.out).write_text(page, encoding="utf-8")
    plural = lambda k, word: f"{k} {word}{'s' if k != 1 else ''}"  # noqa: E731
    print(f"wrote {args.out} ({plural(n, 'slice')}, {plural(len(paths), 'screenshot')}, {plural(d, 'diagram')})")
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
