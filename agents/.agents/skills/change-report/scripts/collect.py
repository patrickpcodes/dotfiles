"""Collect a change set into OUT/changes.json and OUT/diffs/NN.diff, plus a starter OUT/report.json.

  collect.py --out DIR svn [--changelist NAME] [--wc PATH] [--timeout SECS] [PATH ...]
  collect.py --out DIR git [--repo PATH] [--base REF] [--head REF] [--uncommitted]
  collect.py list [PATH]    changelists, or branches and worktrees, to pick from

Read-only: runs svn status/diff/info and git diff/log/status/ls-files only.
"""
import argparse
import datetime
import json
import pathlib
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")


def run(args, cwd, timeout=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout)
    if p.returncode:
        sys.exit(f"{' '.join(map(str, args))} failed in {cwd}:\n{p.stderr.decode('utf-8', 'replace').strip()}")
    return p.stdout


def text(b):
    return b.decode("utf-8", "replace")


def is_binary(diff):
    return b"Cannot display: file marked as a binary type" in diff or b"\nBinary files " in diff or diff.startswith(b"Binary files ") or b"GIT binary patch" in diff


def svn_root(start):
    p = pathlib.Path(start).resolve()
    for d in (p, *p.parents):
        if (d / ".svn" / "wc.db").is_file():
            return d
    sys.exit(f"{start} is not inside an SVN working copy")


def svn_status(xml):
    return {e.get("path").replace("\\", "/"): e.find("wc-status").attrib for e in ET.fromstring(xml).iter("entry")}


def detect(start):
    p = pathlib.Path(start).resolve()
    for d in (p, *p.parents):
        if (d / ".git").exists():
            return "git", d
        if (d / ".svn" / "wc.db").is_file():
            return "svn", d
    sys.exit(f"{start} is not inside a Git repo or an SVN working copy")


def svn_status_paths(root, paths):
    entries, batch, size = {}, [], 0
    for p in paths + [None]:
        if batch and (p is None or size + len(p) > 20000):
            entries.update(svn_status(run(["svn", "status", "--xml", *batch], root)))
            batch, size = [], 0
        if p:
            batch.append(p)
            size += len(p) + 3
    return entries


def changelist_status(root, name, timeout):
    if timeout:
        try:
            return svn_status(run(["svn", "status", "--xml", "--cl", name], root, timeout)), "svn status --cl"
        except subprocess.TimeoutExpired:
            print(f"svn status --cl ran over {timeout}s; reading .svn/wc.db instead")
    db = sqlite3.connect((root / ".svn" / "wc.db").as_uri() + "?mode=ro", uri=True)
    paths = [r[0] for r in db.execute("SELECT local_relpath FROM ACTUAL_NODE WHERE changelist = ? ORDER BY local_relpath", (name,))]
    db.close()
    if not paths:
        sys.exit(f"Changelist '{name}' has no files in {root}")
    return svn_status_paths(root, paths), ".svn/wc.db"


def list_svn(root):
    db = sqlite3.connect((root / ".svn" / "wc.db").as_uri() + "?mode=ro", uri=True)
    rows = db.execute("SELECT changelist, local_relpath FROM ACTUAL_NODE WHERE changelist IS NOT NULL ORDER BY changelist, local_relpath").fetchall()
    db.close()
    lists = {}
    for name, path in rows:
        lists.setdefault(name, []).append(path)
    entries = svn_status_paths(root, [p for _, p in rows])
    print(f"SVN working copy {root}")
    for n, (name, paths) in enumerate(lists.items(), 1):
        live = sum(entries.get(p, {}).get("item") not in (None, "normal", "unversioned", "none")
                   or entries.get(p, {}).get("props") in ("modified", "conflicted") for p in paths)
        print(f"{n:>3}. {name}: {live} of {len(paths)} files have pending changes")
    if not lists:
        print("No changelists.")
    print("Or: the whole working copy, or one folder of it (svn status on a large working copy can take minutes).")


def svn_files(root, entries):
    files, skipped, unversioned = [], [], 0
    paths = set(entries)
    for path, a in sorted(entries.items()):
        item, props = a.get("item"), a.get("props")
        moved_from = a.get("moved-from", "").replace("\\", "/")
        moved_to = a.get("moved-to", "").replace("\\", "/")
        note = ""
        if any(p.startswith(path + "/") for p in paths) or (root / path).is_dir():
            continue
        if item == "unversioned":
            unversioned += 1
            continue
        if item == "added":
            status = "Renamed" if moved_from else "Added"
            if not moved_from and a.get("copied") == "true":
                note = "Copied with history; the diff is against the copy source."
        elif item in ("modified", "replaced", "conflicted", "merged"):
            status = "Modified"
            if item == "conflicted":
                note = "Has an unresolved conflict."
        elif item == "deleted":
            if moved_to in paths:
                continue
            status = "Deleted"
            if moved_to:
                note = f"Moved to {moved_to}, which is not in this change set."
        elif item == "missing":
            status, note = "Deleted", "Missing on disk but not deleted in SVN."
        elif item == "normal" and props in ("modified", "conflicted"):
            status, note = "Modified", "Property change only."
        elif item == "normal":
            skipped.append({"path": path, "reason": "No pending change"})
            continue
        else:
            skipped.append({"path": path, "reason": f"SVN status '{item}'"})
            continue
        files.append({"path": path, "old_path": moved_from or None, "status": status, "note": note})
    return files, skipped, unversioned


def collect_svn(a):
    root = svn_root(a.wc)
    if a.changelist:
        entries, source = changelist_status(root, a.changelist, a.timeout)
        kind, label = "SVN changelist", a.changelist
    else:
        targets = [str(pathlib.Path(p).resolve().relative_to(root)) for p in a.paths] or ["."]
        entries, source = svn_status(run(["svn", "status", "--xml", *targets], root)), "svn status"
        kind, label = "SVN working copy", root.name if targets == ["."] else ", ".join(t.replace("\\", "/") for t in targets)
    files, skipped, unversioned = svn_files(root, entries)
    for f in files:
        f["diff_bytes"] = b"" if f["note"].startswith("Missing") else run(
            ["svn", "diff", "--internal-diff", "-x", "--ignore-eol-style", f["path"]], root)
    rev = text(run(["svn", "info", "--show-item", "revision"], root)).strip()
    url = text(run(["svn", "info", "--show-item", "relative-url"], root)).strip()
    if unversioned:
        print(f"{unversioned} unversioned files left out")
    return {
        "vcs": "svn", "kind": kind, "label": label, "root": str(root), "membership": source,
        "base": f"r{rev}", "head": f"working copy ({url})", "uncommitted": True, "dirty": True,
        "diff_command": 'svn diff -x "--ignore-eol-style" <path>', "commits": [],
    }, files, skipped


def git(repo, *args):
    return run(["git", "-c", "core.quotepath=off", "--no-optional-locks", *args], repo)


def ref_ok(repo, ref):
    return subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref + "^{commit}"], cwd=repo, capture_output=True).returncode == 0


def default_base(root, name):
    return next((c for c in ("dev", "main", "master", "origin/dev", "origin/main", "origin/master") if c != name and ref_ok(root, c)), None)


def list_git(root, limit=20):
    trees, wt = {}, None
    for line in text(git(root, "worktree", "list", "--porcelain")).splitlines():
        if line.startswith("worktree "):
            wt = line[9:]
        elif line.startswith("branch "):
            trees[line[7:].removeprefix("refs/heads/")] = wt
    refs = text(git(root, "for-each-ref", "--sort=-committerdate", "--format=%(refname:short)%1f%(committerdate:short)%1f%(subject)", "refs/heads")).splitlines()
    print(f"Git repo {root} (local branches, newest first)")
    for n, line in enumerate(refs[:limit], 1):
        name, date, subject = line.split("\x1f")
        base = default_base(root, name)
        ahead = f"{text(git(root, 'rev-list', '--count', f'{base}..{name}')).strip()} commits ahead of {base}" if base else "no base found"
        where = ""
        if name in trees and pathlib.Path(trees[name]).is_dir():
            dirty = len(text(git(trees[name], "status", "--porcelain", "--untracked-files=all")).splitlines())
            where = f"; checked out in {trees[name]}" + (f" with {dirty} uncommitted files" if dirty else "")
        print(f"{n:>3}. {name}: {ahead}; last commit {date} \"{subject}\"{where}")
    if len(refs) > limit:
        print(f"     {len(refs) - limit} older branches not shown")


def untracked_diff(root, path):
    data = (root / path).read_bytes()
    head = f"diff --git a/{path} b/{path}\nnew file (untracked)\n--- /dev/null\n+++ b/{path}\n".encode()
    if b"\0" in data[:8000]:
        return head + f"Binary files /dev/null and b/{path} differ\n".encode()
    if not data:
        return head
    lines = data.split(b"\n")
    tail = b""
    if lines[-1] == b"":
        lines.pop()
    else:
        tail = b"\\ No newline at end of file\n"
    body = b"".join(b"+" + l.rstrip(b"\r") + b"\n" for l in lines)
    return head + f"@@ -0,0 +1,{len(lines)} @@\n".encode() + body + tail


def collect_git(a):
    root = pathlib.Path(text(git(a.repo, "rev-parse", "--show-toplevel")).strip())
    head = a.head
    on_head = text(git(root, "rev-parse", head)) == text(git(root, "rev-parse", "HEAD"))
    if a.uncommitted and not on_head:
        sys.exit("--uncommitted only works when --head is the checked-out HEAD")
    name = text(git(root, "rev-parse", "--abbrev-ref", head)).strip()
    if name == "HEAD":
        name = text(git(root, "rev-parse", "--short", head)).strip()
    base = a.base or default_base(root, name)
    if not base:
        sys.exit("No dev, main or master branch found; pass --base")
    mb = text(git(root, "merge-base", base, head)).strip()
    rng = [mb] if a.uncommitted else [mb, head]
    dirty = on_head and bool(text(git(root, "status", "--porcelain")).strip())

    files = []
    parts = text(git(root, "diff", "--name-status", "-z", "-M", "--no-ext-diff", *rng)).split("\0")
    i = 0
    while i < len(parts) and parts[i]:
        code = parts[i]
        if code[0] in "RC":
            old, path = parts[i + 1], parts[i + 2]
            i += 3
        else:
            old, path = None, parts[i + 1]
            i += 2
        status = {"A": "Added", "D": "Deleted", "R": "Renamed", "C": "Added"}.get(code[0], "Modified")
        note = {"C": f"Copied from {old}.", "T": "File type changed.", "U": "Has an unresolved merge conflict."}.get(code[0], "")
        files.append({"path": path, "old_path": old if code[0] == "R" else None, "status": status, "note": note,
                      "_pathspec": [old, path] if old else [path]})
    for f in files:
        f["diff_bytes"] = git(root, "diff", "--no-color", "--no-ext-diff", "--ignore-cr-at-eol", "-M", *rng, "--", *f.pop("_pathspec"))
    if a.uncommitted:
        for path in filter(None, text(git(root, "ls-files", "--others", "--exclude-standard", "-z")).split("\0")):
            files.append({"path": path, "old_path": None, "status": "Added", "note": "Untracked file.", "diff_bytes": untracked_diff(root, path)})
    files.sort(key=lambda f: f["path"])

    log = text(git(root, "log", "--format=%H%x1f%h%x1f%an%x1f%ad%x1f%s%x1f%b%x1e", "--date=short", f"{base}..{head}"))
    commits = [dict(zip(("sha", "short", "author", "date", "subject", "body"), c.strip("\n").split("\x1f")))
               for c in log.split("\x1e") if c.strip()]
    for c in commits:
        c["body"] = c["body"].strip()
    main_tree = text(git(root, "worktree", "list", "--porcelain")).split("\n")[0].removeprefix("worktree ")
    kind = "Git worktree" if pathlib.Path(main_tree).resolve() != root.resolve() else "Git branch"
    return {
        "vcs": "git", "kind": kind, "label": name, "root": str(root), "membership": "git diff --name-status",
        "base": f"{base} (merge base {mb[:9]})", "base_ref": base, "merge_base": mb,
        "head": f"{name} @ {text(git(root, 'rev-parse', '--short', head)).strip()}",
        "uncommitted": a.uncommitted, "dirty": dirty,
        "diff_command": f"git diff --ignore-cr-at-eol -M {mb[:9]}{'' if a.uncommitted else ' ' + head} -- <path>",
        "commits": commits,
    }, files, []


def starter(changes):
    files = [f["path"] for f in changes["files"]]
    return {
        "title": changes["label"],
        "subtitle": "",
        "sections": [
            {"id": "goal", "title": "Goal", "body": ""},
            {"id": "approach", "title": "How we achieved it", "body": ""},
            {"id": "flow", "title": "Architecture and flow", "body": "", "mermaid": ""},
            {"id": "reach", "title": "Changes that reach other features", "body": ""},
            {"id": "testing", "title": "Testing and verification", "body": "", "table": {"columns": ["Check", "Result", "When", "Source"], "rows": []}},
            {"id": "deploy", "title": "Deployment notes", "body": ""},
            {"id": "risks", "title": "Risks and follow-ups", "body": ""},
        ],
        "groups": [{"id": "files", "title": "Files", "blurb": "", "files": files}],
        "why": {p: "" for p in files},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="output folder (outside tracked source); required for svn and git")
    sub = ap.add_subparsers(dest="vcs", required=True)
    s = sub.add_parser("svn")
    s.add_argument("--changelist", "--cl")
    s.add_argument("--wc", default=".", help="any folder inside the working copy")
    s.add_argument("--timeout", type=int, default=30, help="seconds to wait for svn status --cl before reading wc.db; 0 = go straight to wc.db")
    s.add_argument("paths", nargs="*", help="without --changelist: limit to these paths")
    g = sub.add_parser("git")
    g.add_argument("--repo", default=".", help="repo or worktree folder")
    g.add_argument("--base", help="base branch; default dev, then main, then master")
    g.add_argument("--head", default="HEAD", help="branch or commit to report; no checkout needed")
    g.add_argument("--uncommitted", action="store_true", help="include working-tree changes and untracked files")
    l = sub.add_parser("list", help="list changelists, or branches and worktrees, to pick from")
    l.add_argument("path", nargs="?", default=".", help="any folder inside the repo or working copy")
    a = ap.parse_args()
    if a.vcs == "list":
        vcs, root = detect(a.path)
        return (list_svn if vcs == "svn" else list_git)(root)
    if not a.out:
        ap.error("--out is required")

    out = pathlib.Path(a.out).resolve()
    (out / "diffs").mkdir(parents=True, exist_ok=True)
    for old in (out / "diffs").glob("*.diff"):
        old.unlink()
    changes, files, skipped = (collect_svn if a.vcs == "svn" else collect_git)(a)
    width = max(2, len(str(len(files))))
    for n, f in enumerate(files, 1):
        f["id"] = str(n).zfill(width)
        f["diff"] = f"diffs/{f['id']}.diff"
        data = f.pop("diff_bytes")
        f["binary"] = is_binary(data)
        (out / f["diff"]).write_bytes(data)
    changes.update(files=files, skipped=skipped, generated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    (out / "changes.json").write_text(json.dumps(changes, indent=2, ensure_ascii=False), encoding="utf-8")

    report = out / "report.json"
    if not report.exists():
        report.write_text(json.dumps(starter(changes), indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote starter {report}")
    else:
        print(f"Kept existing {report}; render.py reports files it doesn't cover")

    counts = {s: sum(f["status"] == s for f in files) for s in ("Added", "Modified", "Deleted", "Renamed")}
    print(f"{changes['kind']} {changes['label']}: {len(files)} files ({', '.join(f'{v} {k.lower()}' for k, v in counts.items() if v)}), base {changes['base']}, via {changes['membership']}")
    if changes["vcs"] == "git":
        print(f"{len(changes['commits'])} commits. Uncommitted changes: " +
              ("included" if changes["uncommitted"] else "present but NOT included (pass --uncommitted)" if changes["dirty"] else "none"))
    for s in skipped:
        print(f"skipped {s['path']}: {s['reason']}")
    for f in files:
        if f["binary"] or f["note"]:
            print(f"{f['id']} {f['path']}: {'binary. ' if f['binary'] else ''}{f['note']}")
    print(f"Output: {out}")


if __name__ == "__main__":
    main()
