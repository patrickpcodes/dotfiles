"""Render DIR/changes.json + DIR/report.json + DIR/diffs/*.diff into a change report.

  render.py DIR [-o NAME.html] [--max-lines N]

Writes NAME.html (every diff) and NAME-summary.html (no diffs, small enough to preview inline).
"""
import argparse
import html
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = pathlib.Path(__file__).resolve().parent
HUNK = re.compile(r"^(@@|##) -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? (@@|##)")
STATUS = {"Added": "A", "Modified": "M", "Deleted": "D", "Renamed": "R"}
INLINE_LIMIT = 512_000


def esc(s):
    return html.escape(str(s), quote=True)


def inline(s):
    codes = []

    def keep(m):
        codes.append(f"<code>{esc(m[1])}</code>")
        return f"\0{len(codes) - 1}\0"

    s = esc(re.sub(r"`([^`]+)`", keep, str(s)))
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return re.sub(r"\0(\d+)\0", lambda m: codes[int(m[1])], s)


def md(body):
    lines = body if isinstance(body, list) else str(body or "").split("\n")
    out, para, items, kind = [], [], [], None

    def flush():
        nonlocal para, items, kind
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
        if items:
            out.append(f"<{kind}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{kind}>")
        para, items, kind = [], [], None

    for raw in lines:
        line = raw.rstrip()
        bullet = re.match(r"^\s*[-*] (.*)", line)
        number = re.match(r"^\s*\d+[.)] (.*)", line)
        if not line.strip():
            flush()
        elif line.startswith("### "):
            flush()
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif bullet or number:
            k = "ul" if bullet else "ol"
            if para or (kind and kind != k):
                flush()
            kind = k
            items.append((bullet or number).group(1))
        elif items and raw.startswith("  "):
            items[-1] += " " + line.strip()
        else:
            if items:
                flush()
            para.append(line.strip())
    flush()
    return "".join(out)


def read_diff(path):
    data = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("latin-1")


def parse(text):
    rows, adds, dels, hunks = [], 0, 0, 0
    old = new = ro = rn = 0
    props = False
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if ro > 0 or rn > 0:
            if line.startswith("\\"):
                rows.append(("meta", "", "", line))
            elif line.startswith("+"):
                rows.append(("add", "", new, line[1:]))
                new, rn, adds = new + 1, rn - 1, adds + 1
            elif line.startswith("-"):
                rows.append(("del", old, "", line[1:]))
                old, ro, dels = old + 1, ro - 1, dels + 1
            else:
                rows.append(("ctx", old, new, line[1:] if line.startswith(" ") else line))
                old, new, ro, rn = old + 1, new + 1, ro - 1, rn - 1
            continue
        m = HUNK.match(line)
        if m:
            old, new = int(m[2]), int(m[4])
            ro = 1 if m[3] is None else int(m[3])
            rn = 1 if m[5] is None else int(m[5])
            rows.append(("hunk", "", "", line))
            hunks += 1
        elif line.startswith("\\"):
            rows.append(("meta", "", "", line))
        elif line.startswith("Property changes on:"):
            props = True
            rows.append(("meta", "", "", "Property changes"))
        elif props and re.match(r"^(Added|Modified|Deleted): \S", line):
            rows.append(("meta", "", "", line))
    return rows, adds, dels, hunks


def code(rows, limit, total, diff_path):
    mark = {"add": "+", "del": "−", "ctx": " ", "hunk": "", "meta": ""}
    out = [f'<span class="l {k}"><span class="g">{o}</span><span class="g">{n}</span><span class="m">{mark[k]}</span>'
           f'<span class="t">{esc(t) or " "}</span></span>' for k, o, n, t in rows[:limit]]
    if total > limit:
        out.append(f'<span class="l meta"><span class="g"></span><span class="g"></span><span class="m"></span>'
                   f'<span class="t">Cut at {limit} of {total} lines. Full diff: {esc(diff_path)}</span></span>')
    return "".join(out)


def common_dir(paths):
    parts = [p.split("/")[:-1] for p in paths]
    prefix = []
    for segs in zip(*parts):
        if len(set(segs)) != 1:
            break
        prefix.append(segs[0])
    return "/".join(prefix) + "/" if prefix else ""


def validate(changes, report):
    errors, warnings = [], []
    paths = [f["path"] for f in changes["files"]]
    why = report.get("why", {})
    for p in paths:
        if not str(why.get(p, "")).strip():
            errors.append(f"why missing for {p}")
    for p in why:
        if p not in paths:
            errors.append(f"why given for a path that isn't in the change set: {p}")
    seen, ids = {}, set()
    for g in report.get("groups", []):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", str(g.get("id", ""))) or g["id"] in ids:
            errors.append(f"group id must be unique letters, digits, - or _: {g.get('id')!r}")
        ids.add(g.get("id"))
        for p in g.get("files", []):
            if p not in paths:
                errors.append(f"group {g.get('id')} lists a path that isn't in the change set: {p}")
            if p in seen:
                errors.append(f"{p} is in groups {seen[p]} and {g.get('id')}")
            seen[p] = g.get("id")
    for p in paths:
        if p not in seen:
            errors.append(f"{p} is in no group")
    sids = set()
    for s in report.get("sections", []):
        sid = str(s.get("id", ""))
        if not re.fullmatch(r"[A-Za-z0-9_-]+", sid) or sid in sids:
            errors.append(f"section id must be unique letters, digits, - or _: {sid!r}")
        sids.add(sid)
        body = s.get("body")
        has_body = any(str(x).strip() for x in body) if isinstance(body, list) else bool(str(body or "").strip())
        if not (has_body or s.get("mermaid") or (s.get("table") or {}).get("rows")):
            errors.append(f"section {sid} is empty; write it, say 'None' or 'Not run', or remove it")
        if "</script" in str(s.get("mermaid", "")).lower():
            errors.append(f"section {sid}: mermaid source can't contain </script")
    text = json.dumps(report)
    anchors = {"glance", "commits"} | {f"s-{x}" for x in sids} | {f"g-{x}" for x in ids} | {f"f{f['id']}" for f in changes["files"]}
    for a in sorted(set(re.findall(r"\]\(#([^)\s]+)\)", text)) - anchors):
        errors.append(f"link to #{a} has no target; use #s-<section id>, #g-<group id> or #f<file id>")
    if re.search(r"\bTODO\b|\bTBD\b", text):
        errors.append("report.json still contains TODO or TBD")
    for p, w in why.items():
        if len(str(w)) > 240:
            warnings.append(f"why for {p} is {len(str(w))} chars; aim for one line")
    return errors, warnings


RESULT = re.compile(r"(?i)^(?:(pass(?:ed)?|clean|ok)|(fail(?:ed)?|error)|(not run|skipped|n/a))\b")


def cell(c):
    c = str(c).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?", c):
        return f'<td class="nowrap">{esc(c)}</td>'
    m = RESULT.match(c)
    if not m:
        return f"<td>{inline(c)}</td>"
    kind = "ok" if m[1] else "bad" if m[2] else "na"
    return f'<td><span class="r-{kind}">{esc(m[0])}</span>{inline(c[len(m[0]):])}</td>'


def section_html(s):
    parts = [f'<section class="story" id="s-{esc(s["id"])}"><h2 class="sec-head">{inline(s["title"])}</h2>']
    if s.get("body"):
        parts.append(f'<div class="prose">{md(s["body"])}</div>')
    if s.get("mermaid"):
        parts.append(f'''<div class="diagram-shell">
  <p class="diagram-shell__hint">Ctrl/Cmd + wheel to zoom. Drag to pan. Double-click to fit.</p>
  <div class="mermaid-wrap">
    <div class="zoom-controls">
      <button type="button" data-action="zoom-in" title="Zoom in">+</button>
      <button type="button" data-action="zoom-out" title="Zoom out">&minus;</button>
      <button type="button" data-action="zoom-fit" title="Fit">&#8634;</button>
      <button type="button" data-action="zoom-one" title="1:1 zoom">1:1</button>
      <button type="button" data-action="zoom-expand" title="Open full size">&#x26F6;</button>
      <span class="zoom-label">Loading...</span>
    </div>
    <div class="mermaid-viewport"><div class="mermaid mermaid-canvas"></div></div>
  </div>
  <script type="text/plain" class="diagram-source">{s["mermaid"]}</script>
</div>''')
        if s.get("caption"):
            parts.append(f'<p class="caption">{inline(s["caption"])}</p>')
    t = s.get("table")
    if t and t.get("rows"):
        head = "".join(f"<th>{inline(c)}</th>" for c in t.get("columns", []))
        rows = "".join("<tr>" + "".join(cell(c) for c in r) + "</tr>" for r in t["rows"])
        parts.append(f'<div class="scroll"><table class="story-table"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>')
    parts.append("</section>")
    return "".join(parts)


def build(changes, report, parsed, prefix, out_path, summary_name, summary, limit):
    files = {f["path"]: f for f in changes["files"]}
    names = [p.rsplit("/", 1)[-1] for p in files]

    def split(path):
        d, _, b = path.removeprefix(prefix).rpartition("/")
        return d, b

    def short(path):
        d, b = split(path)
        return b if names.count(b) == 1 or not d else f"{d.rsplit('/', 1)[-1]}/{b}"

    def pill(f):
        return f'<span class="st {STATUS[f["status"]]}">{f["status"]}</span>'

    def counts(f):
        if f["binary"]:
            return '<span class="dim">binary</span>'
        _, a, d, _ = parsed[f["path"]]
        return f'<span class="plus">+{a}</span> <span class="minus">−{d}</span>'

    total_add = sum(v[1] for v in parsed.values())
    total_del = sum(v[2] for v in parsed.values())
    by_status = {s: sum(f["status"] == s for f in files.values()) for s in STATUS}

    sections = report.get("sections", [])
    toc = ['<div class="toc-group">Overview</div>']
    toc += [f'<a class="sec" href="#s-{esc(s["id"])}">{inline(s["title"])}</a>' for s in sections]
    if changes.get("commits"):
        toc.append('<a class="sec" href="#commits">Commits</a>')
    toc.append('<a class="sec" href="#glance">At a glance</a>')
    if not summary:
        toc.append('<div class="toc-group">Files</div>')

    if changes["vcs"] == "svn":
        source = f'{esc(changes["kind"])} <code>{esc(changes["label"])}</code> in {esc(changes["root"])}, against {esc(changes["base"])}.'
        scope = "Line-ending changes are ignored; indentation changes are shown."
    else:
        source = f'{esc(changes["kind"])} <code>{esc(changes["head"])}</code> in {esc(changes["root"])}, against <code>{esc(changes["base"])}</code>.'
        scope = ("Includes uncommitted and untracked files." if changes["uncommitted"] else
                 "Committed changes only; the working tree has uncommitted changes that are not included." if changes["dirty"] else
                 "Committed changes only; the working tree is clean.") + " Line-ending changes are ignored."
    if prefix:
        scope += f" Paths are under <code>{esc(prefix)}</code>."

    main = [f'<header class="top"><p class="eyebrow">Change report</p><h1>{inline(report.get("title") or changes["label"])}</h1>']
    if report.get("subtitle"):
        main.append(f'<p class="lede">{inline(report["subtitle"])}</p>')
    main.append(f'<p class="subtitle">{source} {scope} Generated {esc(changes["generated"])}.</p>')
    if summary:
        main.append(f'<p class="summary-note">Summary without diffs. Full report with every diff: <a href="{esc(out_path.name)}">{esc(out_path)}</a></p>')
    main.append("</header>")

    kpis = [(len(files), "files", "")]
    kpis += [(by_status[s], s.lower(), "") for s in STATUS if by_status[s] or s in ("Added", "Modified")]
    kpis += [(f"+{total_add}", "lines added", "add"), (f"−{total_del}", "lines removed", "del")]
    if changes.get("commits"):
        kpis.insert(1, (len(changes["commits"]), "commits", ""))
    main.append('<div class="kpis">' + "".join(f'<div class="kpi {c}"><b>{v}</b><span>{l}</span></div>' for v, l, c in kpis) + "</div>")

    main += [section_html(s) for s in sections]

    if changes.get("commits"):
        rows = "".join(f'<tr><td class="mono">{esc(c["short"])}</td><td class="mono nowrap">{esc(c["date"])}</td><td>{esc(c["author"])}</td>'
                       f'<td>{esc(c["subject"])}</td></tr>' for c in changes["commits"])
        main.append(f'<section class="story" id="commits"><h2 class="sec-head">Commits <span>{len(changes["commits"])}</span></h2>'
                    f'<div class="scroll"><table class="story-table"><thead><tr><th>Commit</th><th>Date</th><th>Author</th><th>Subject</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div></section>')

    glance, body = [], []
    for g in report["groups"]:
        gid = f'g-{g["id"]}'
        if summary:
            glance.append(f'<tr class="grp" id="{gid}"><td colspan="4">{inline(g["title"])}</td></tr>')
        else:
            glance.append(f'<tr class="grp"><td colspan="4"><a href="#{gid}">{inline(g["title"])}</a></td></tr>')
        if not summary:
            toc.append(f'<a class="sec" href="#{gid}">{inline(g["title"])}</a>')
            body.append(f'<section class="group" id="{gid}"><h2 class="sec-head">{inline(g["title"])} <span>{len(g["files"])} files</span></h2>')
            if g.get("blurb"):
                body.append(f'<div class="blurb">{md(g["blurb"])}</div>')
        for p in g["files"]:
            f = files[p]
            d, b = split(p)
            why = inline(report["why"][p])
            name = esc(b) if summary else f'<a href="#f{f["id"]}">{esc(b)}</a>'
            moved = f'<div class="dir">from {esc(f["old_path"].removeprefix(prefix))}</div>' if f.get("old_path") else ""
            glance.append(f'<tr><td>{name}<div class="dir">{esc(d)}</div>{moved}</td><td>{pill(f)}</td><td class="num">{counts(f)}</td><td>{why}</td></tr>')
            if summary:
                continue
            toc.append(f'<a class="file" href="#f{f["id"]}">{esc(short(p))}</a>')
            rows, a, dl, hunks = parsed[p]
            notes = [f["note"]] if f.get("note") else []
            if f.get("old_path"):
                notes.insert(0, f'Renamed from {f["old_path"]}.')
            if f["binary"]:
                block = '<p class="nodiff">Binary file; no text diff.</p>'
            elif not hunks:
                block = '<p class="nodiff">' + ("No content change." if f["status"] == "Renamed" else
                                                "Empty file." if f["status"] == "Added" else
                                                "Only line endings or file properties changed.") + "</p>"
            else:
                block = f'<pre class="diff"><code>{code(rows, limit, len(rows), f["diff"])}</code></pre>'
            note_html = "".join(f'<p class="file-note">{esc(n)}</p>' for n in notes)
            body.append(f'''<article class="file-card" id="f{f["id"]}">
<header><div class="name"><span class="dir">{esc(d + "/" if d else "")}</span><strong>{esc(b)}</strong></div>
<div class="tags">{pill(f)}{counts(f)}</div></header>
<p class="why">{why}</p>{note_html}
{block}
</article>''')
        if not summary:
            body.append("</section>")

    skipped = changes.get("skipped") or []
    skip_html = ("<p class=\"note\">In the change set but left out: " +
                 "; ".join(f"<code>{esc(s['path'].removeprefix(prefix))}</code> ({esc(s['reason'])})" for s in skipped) + ".</p>") if skipped else ""
    main.append(f'''<section class="panel" id="glance"><h2>At a glance</h2>
<div class="scroll"><table class="glance"><thead><tr><th>File</th><th>Status</th><th>Lines</th><th>Why</th></tr></thead>
<tbody>{"".join(glance)}</tbody></table></div>{skip_html}</section>''')
    main += body
    main.append(f'<p class="note foot">Built by the change-report skill from {esc(changes["root"])}. Diffs: <code>{esc(changes["diff_command"])}</code>.'
                + ("" if summary else f' Summary page: <a href="{esc(summary_name)}">{esc(summary_name)}</a>.') + "</p>")

    title = re.sub(r"[`*]", "", str(report.get("title") or changes["label"]))
    page = (HERE.parent / "assets" / "template.html").read_text(encoding="utf-8")
    for key, value in (("TITLE", esc(title)), ("TOC", "".join(toc)), ("MAIN", "\n".join(main))):
        page = page.replace("{{" + key + "}}", value)
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir", help="folder with changes.json, report.json and diffs/")
    ap.add_argument("-o", "--out", help="HTML file name or path; default <label>-changes.html in DIR")
    ap.add_argument("--max-lines", type=int, default=1500, help="cut each file's diff after this many lines")
    a = ap.parse_args()

    d = pathlib.Path(a.dir).resolve()
    changes = json.loads((d / "changes.json").read_text(encoding="utf-8"))
    report = json.loads((d / "report.json").read_text(encoding="utf-8-sig"))
    errors, warnings = validate(changes, report)
    for w in warnings:
        print("warning:", w)
    if errors:
        print("report.json needs fixing:\n  " + "\n  ".join(errors))
        sys.exit(1)

    parsed = {f["path"]: parse(read_diff(d / f["diff"])) for f in changes["files"]}
    prefix = common_dir(list(parsed))
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", changes["label"]).strip("-") or "change-report"
    out = pathlib.Path(a.out) if a.out else d / f"{slug}-changes.html"
    if not out.is_absolute():
        out = d / out
    summary_out = out.with_name(out.stem + "-summary.html")
    for path, summary in ((out, False), (summary_out, True)):
        page = build(changes, report, parsed, prefix, out, summary_out.name, summary, a.max_lines)
        path.write_text(page, encoding="utf-8")
        size = len(page)
        flag = "" if size <= INLINE_LIMIT else "  (over the 512,000-char inline preview limit)"
        print(f"{path}  {size:,} chars{flag}")
    print(f"{len(parsed)} files, +{sum(v[1] for v in parsed.values())} -{sum(v[2] for v in parsed.values())}")


if __name__ == "__main__":
    main()
