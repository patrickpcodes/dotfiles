Reviewer brief for `dual-review`. Fill in the `<...>` parts. Drop the focus-docs sentence if there are none. Send everything below the line.

---

Code review of GitHub PR #<N> (<title>, <head branch> into <base branch>) in the repo at <repo path> (repo <owner/name>). This is a READ-ONLY review: do not edit files, commit, push, comment on the PR, build, or run anything that changes state.

Get the PR with `gh pr view <N>` and `gh pr diff <N>`. Read the surrounding code as needed. If the PR branch isn't checked out locally, read files at the PR head with `gh api` or `git show origin/<head branch>:<path>`. Don't switch branches. Read the repo's AGENTS.md and any docs it points to for the areas the diff touches. Read these focus docs: <doc — key rule; doc — key rule>.

Look for: correctness bugs, behaviour regressions, missed call sites or config, data/inventory/order risks, deploy-order risks, doc/code mismatches, and needless complexity. Report only issues you can point to in the code. Don't pad.

Report in exactly this format:

SUMMARY: one or two sentences on what the PR does and your overall verdict (merge as-is / merge with fixes / don't merge).

FINDINGS (most severe first; write "none" if none):
- [severity: high|medium|low] file:line — problem — concrete failure scenario — suggested fix

QUESTIONS: anything you couldn't verify and would need the author to answer.
