Reviewer brief for `dual-review`. Fill in the `<...>` parts. Drop the focus-docs sentence if there are none. Send everything below the line.

---

Code review of GitHub PR #<N> (<title>, <head branch> into <base branch>) at commit <head SHA>, in the repo at <repo path> (repo <owner/name>). This is a READ-ONLY review: do not edit files, commit, push, comment on the PR, build, or run anything that changes state.

First run `gh pr view <N> --json headRefOid`. If it doesn't return <head SHA>, the PR changed after this review was requested: say so in SUMMARY, report no findings, and stop. Otherwise get the PR with `gh pr view <N>` and `gh pr diff <N>`, and read the surrounding code as needed. Read every file at that commit, with `git show <head SHA>:<path>` or `gh api "repos/<owner/name>/contents/<path>?ref=<head SHA>"`, and search with `git grep <pattern> <head SHA>`. Don't read files from the working tree, which may be on another branch or have uncommitted edits, and don't switch branches. Read the repo's AGENTS.md and any docs it points to for the areas the diff touches. Read these focus docs: <doc — key rule; doc — key rule>.

Look for: correctness bugs, behaviour regressions, missed call sites or config, data/inventory/order risks, deploy-order risks, doc/code mismatches, and needless complexity. Report only issues you can point to in the code. Don't pad.

Report in exactly this format:

SUMMARY: one or two sentences on what the PR does and your overall verdict (merge as-is / merge with fixes / don't merge).

FINDINGS (most severe first; write "none" if none):
- [severity: high|medium|low] file:line — problem — concrete failure scenario — suggested fix

QUESTIONS: anything you couldn't verify and would need the author to answer.
