---
name: change-report
description: Build a self-contained HTML change report for a set of code changes. Every changed file gets its diff and a one-line reason why, under narrative sections (goal, approach, architecture, other features touched, testing, deployment, risks). Works for SVN changelists and working copies, and for Git branches and worktrees. Use when the user asks for a change report, changelist report, branch or PR write-up with diffs, or "what changed in each file and why".
argument-hint: "[svn changelist | git branch | worktree path] [base branch]"
---

# Change report

One HTML page for a change set: what the project set out to do, how, and every changed file's diff with a one-line why.

This skill's folder is `~/.agents/skills/change-report/`. Its scripts use only the Python standard library (3.9+):

- `scripts/collect.py` finds the changed files and writes one diff per file.
- `scripts/render.py` turns the diffs plus your `report.json` into the page.
- `assets/template.html` holds the CSS and JS. `assets/report.example.json` shows every `report.json` field.

The page has its CSS and JS inline. Fonts and Mermaid load from a CDN. Offline, the fonts fall back and the diagram shows its source text.

On Windows:

- Set `PYTHONIOENCODING=utf-8` before running Python (in PowerShell: `$env:PYTHONIOENCODING='utf-8'`).
- In PowerShell, write the script path as `$HOME\.agents\skills\change-report\scripts\...`, because PowerShell doesn't expand `~` for programs like Python.

## Rules

- Version control is read-only. No `svn commit`, `revert`, `changelist` or `cleanup`. No `git commit`, `add`, `checkout`, `switch`, `reset`, `stash` or `worktree add`. Never commit.
- Jira, Linear and other trackers are read-only.
- Don't invent the goal, the approach or test results. If you can't find them, ask.

## 1. Pick the change set and the output folder

If the user didn't name one, list the choices and ask which:

```
python ~/.agents/skills/change-report/scripts/collect.py list [<folder>]
```

- It checks the folder you give it (default: the current folder) and works out whether it's SVN or Git.
- **SVN:** it lists each changelist and how many of its files have pending changes. The user can also pick the whole working copy or one folder of it.
- **Git:** it lists the local branches, newest first, with commits ahead of the base, and where each one is checked out, with its uncommitted file count. A remote branch also works: `--head origin/<name>`.
- Show the list and ask. If you have a question tool with choices, offer the most likely ones and let the user type any other.

| The user gives | Run collect.py with |
|---|---|
| SVN changelist name | `svn --changelist NAME --wc <working copy>` |
| SVN working copy, no changelist | `svn --wc <working copy> [PATH ...]` (modified, added and deleted files; unversioned files are left out) |
| Git branch | `git --repo <repo> --head BRANCH` (no checkout needed) |
| Git worktree | `git --repo <worktree path>`. Find it with `git worktree list`. |

- **Git base:** pass `--base`. Otherwise the script tries `dev`, `main`, `master`, then the same names under `origin/`. If none fits the branch, ask.
- **Git uncommitted work:** run `git --no-optional-locks status --porcelain` in the repo or worktree (the flag stops git from rewriting the index). If anything is listed, ask whether to include it. `--uncommitted` adds working-tree changes, and untracked files as Added. The page says which you chose.
- **Output folder:** somewhere outside tracked source, such as the repo's ignored `artifacts/<topic>/change-report/` or a temp folder. If there's no obvious place, ask.

## 2. Collect

```
python ~/.agents/skills/change-report/scripts/collect.py --out <out> svn --changelist portal-renewal-ownership --wc F:\Optikam
python ~/.agents/skills/change-report/scripts/collect.py --out <out> git --repo F:\Repos\app-feature --base dev
```

It writes `<out>/changes.json`, `<out>/diffs/NN.diff` and, if missing, a starter `<out>/report.json`. Read its summary. It lists skipped files (in a changelist but unchanged), binary files and notes. Re-running it replaces the diffs but keeps `report.json`.

What it runs, if you need to do it by hand:

| Mode | Members | Diff per file |
|---|---|---|
| SVN changelist | `svn status --xml --cl NAME`. On large working copies this can run for minutes, so after `--timeout` seconds (default 30; `0` skips it) it reads `.svn/wc.db` (`SELECT local_relpath FROM ACTUAL_NODE WHERE changelist = ?`) and runs `svn status --xml <paths>`. | `svn diff --internal-diff -x "--ignore-eol-style" <path>` |
| SVN working copy | `svn status --xml [paths]` | same |
| Git branch or worktree | `git merge-base <base> <head>`, then `git diff --name-status -z -M <mb> <head>` (`<mb>` alone with `--uncommitted`), plus `git ls-files --others --exclude-standard` with `--uncommitted` | `git diff --ignore-cr-at-eol -M <mb> [<head>] -- <path>`; commits from `git log <base>..<head>` |

- `--ignore-eol-style` and `--ignore-cr-at-eol` hide line-ending flips but keep indentation changes. Don't use `-x -w`: it mispairs braces.
- To run svn by hand on Windows, use PowerShell; from Git Bash it can fail with E020024. The script calls svn directly, so either shell can run the script.
- Status is normalised to Added, Modified, Deleted or Renamed. SVN moves show as Renamed. Binary files get a note instead of a diff.

## 3. Gather the story

Read these, in this order. Note what each says about the goal, the approach, tests and deployment:

1. Plan docs (`docs/plans/`, `docs/archive/`) that match the change.
2. Docs the change itself adds or edits. These are often where the story lives.
3. Architecture docs for the area.
4. Commit messages (`changes.json` has them for Git).
5. The PR description, if there is one.
6. The linked issue, read-only.
7. Test logs and earlier reports for this change in the artifacts folder.
8. The current conversation.

If you can't find the goal or the approach, ask the user. Don't guess.

When you read code for the why lines:

- In Git branch mode the branch may not be checked out. Use `git show <head>:<path>` and `git grep <pattern> <head>`.
- Prefer `git grep` to `grep -r`, which also walks `node_modules` and build output.

## 4. Write report.json

Fill in the starter. `assets/report.example.json` shows every field.

- `title` and `subtitle`: what the change set is, and one sentence on what it does for the user.
- `why`: one line per file, keyed by its path as in `changes.json`. Every file needs one.
- `groups`: every file in exactly one group.
- `sections`: the narrative.

### Text format

Text fields take a small Markdown subset:

- paragraphs, `- ` and `1. ` lists, and `### ` subheadings
- `` `code` `` (also inside bold and link text) and `**bold**`
- `[text](#anchor)` links

A `body` can be one string or a list of lines. Anchors are `#s-<section id>`, `#g-<group id>` and `#f<file id>`, and render.py rejects links with no target.

### The why lines

- Read the diff and the code around it, then say why the file changed: the reason, or what it now makes possible. Don't restate the diff.
  - Weak: "Adds method GetOwners and a using statement."
  - Good: "Adds the owner lookup the Renewals list needs, one query for the whole page."
- If a file changed only because of a refactor or a moved helper, say so and say whether behaviour changed.
- If a reason comes from your reading of the code rather than from a doc, word it so (for example "appears to").
- Keep each to one line, about 25 words.

### Groups

- Group by layer, in an order a reader can follow: for example Database, Server, Shared code, Other features touched, Portal/UI, Tests, Docs. Use whatever fits the repo.
- Give each group a one-sentence `blurb`.
- Inside a group, put the files that explain the change first: the rule, then its callers.

### Narrative sections

Keep these ids and titles unless they don't fit. Delete a section only if it truly doesn't apply; otherwise write "None" and the reason.

| id | Title | What goes in it |
|---|---|---|
| `goal` | Goal | The problem, and what the project set out to do. |
| `approach` | How we achieved it | The approach and the key design decisions, as a short list with the reason for each. |
| `flow` | Architecture and flow | A small Mermaid diagram (`mermaid` field, optional `caption`) when it helps; otherwise delete the section. |
| `reach` | Changes that reach other features | Refactors or shared code touched outside the main feature, and why. Put those files in their own group and link it: `[...](#g-<group id>)`. |
| `testing` | Testing and verification | Tests added, suites run and their results, in the `table` field (Check, Result, When, Source). |
| `deploy` | Deployment notes | DB scripts and their order, config, feature flags, manual steps, rollback. |
| `risks` | Risks and follow-ups | What could break, what's left to do, open questions. |

- **Testing:** only report what was actually run, using the newest recorded run of each check, with its numbers, date and source. Anything else is "Not run". In the Result column, a leading Pass, Clean or OK shows green; Fail or Error red; Not run, Skipped or N/A grey.
- **Mermaid** (visual-explainer's rules): `flowchart TD`, at most 10–12 nodes, quoted labels, `<br/>` for line breaks (never `\n`), simple ids, no `color:` in `classDef`. The template handles theming, zoom, pan and expand.

## 5. Render and check

```
python ~/.agents/skills/change-report/scripts/render.py <out>            # optional: -o name.html, --max-lines 1500
```

- **Output:** `<label>-changes.html` (every diff) and `<label>-changes-summary.html` (no diffs). `<label>` is the changelist or branch name made file-safe, so `feature/x` becomes `feature-x`. It prints each page's size.
- **If report.json is incomplete,** it lists every gap and writes nothing. Fix them and run it again.
- **Page size:** the full page has no size limit, since it's opened from disk. Lower `--max-lines` (the per-file diff cut) only if the page gets slow at several MB.

Then look at the page with headless Chrome. Use forward slashes in the `file:///` URL:

```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --hide-scrollbars --virtual-time-budget=15000 --window-size=1440,3000 --screenshot=<out>/shot.png "file:///F:/path/to/<label>-changes.html"
```

- Headless Chrome doesn't scroll to a `#hash`. To see one part, add `?only=<id>` to the URL (for example `?only=s-testing`, `?only=g-portal` or `?only=f07`). The page then shows only the title and that part.
- Check three things:
  - the Mermaid diagram rendered (the zoom label shows a percentage, not "Error")
  - the testing table reads right
  - no text overflows

## 6. Deliver

- If the thread has T3's HTML tools (`html_preview` and `html_render`), pass the summary page to `html_preview`, then `html_render`.
  - Their limit is 512,000 characters. Full pages are usually bigger, and `render.py` flags pages over the limit.
  - Inside a frame, the page hides its menu, drops its padding and background, and uses the host's theme colours.
- Without those tools, give the paths of both pages.
- Reply with:
  - the full page's path
  - the file count and +/- lines
  - anything skipped or marked "Not run"
