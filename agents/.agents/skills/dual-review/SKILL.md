---
name: dual-review
description: Run two independent read-only code reviews of a GitHub PR in parallel, one by Codex and one by Claude Opus, then compare both reports and recommend what to fix before merging. Needs T3 Code's delegate_task tool. Use when the user says "dual review", "/dual-review", "review this PR before merge", or asks for a Codex and Opus review of a PR.
argument-hint: "<PR#> [codex=<model>] [opus=<model>] [codex-effort=<level>] [opus-effort=<level>]"
---

# Dual review

Two reviewers, one Codex and one Opus, review the same PR on their own. Then this thread compares their reports. The models catch different things, so always run both.

## Rules

- Read-only. Never edit, commit, push, comment on GitHub, or merge. Fixes happen only after the user picks an option, and the usual commit approval still applies.
- A review that didn't finish is not a pass. Say which reviewer is missing.
- Never swap a model or effort level silently.

## 1. Gather the inputs

- PR number: from the arguments. If there isn't one, use `gh pr view --json number` for the current branch. If that finds no PR, ask.
- Repo path: `git rev-parse --show-toplevel`. Repo name: `gh repo view --json nameWithOwner`.
- PR facts: `gh pr view <N> --json title,baseRefName,headRefName,state,files`. If the PR is closed or merged, tell the user and ask before going on.
- Focus docs: read the repo's `AGENTS.md`. If it has a `Review focus` section, or a table that maps areas to docs, pick the docs that cover the changed files. Note each one with its key rule in one line.

## 2. Check the models

Defaults:

| Reviewer | providerInstanceId | model | options |
|---|---|---|---|
| Codex | `codex` | `gpt-6-astra` | `{ reasoningEffort: "max" }` |
| Opus | `claudeAgent` | `claude-opus-5-5` | `{ effort: "max" }` |

Arguments override them: `codex=<model>`, `opus=<model>`, `codex-effort=<level>`, `opus-effort=<level>`.

Load the T3 tools if they're deferred (in Claude Code: `ToolSearch` with `select:mcp__t3-code__orchestrator_capabilities,mcp__t3-code__delegate_task`). Call `orchestrator_capabilities` once. If a model or effort level isn't listed, call it again with `search`. If it's still missing, tell the user and stop.

## 3. Start both reviewers

Fill in `brief.md` from this skill's folder (`~/.agents/skills/dual-review/brief.md`). Send the same text to both reviewers. The reviewers get no history from this thread, so the brief has to stand on its own.

In one message, call `delegate_task` twice with `mode: "async"`, `role: "review"`, `isolation: "shared"`, and these titles:

- `Dual review PR #<N> (Codex)`
- `Dual review PR #<N> (Opus)`

Keep each call's `taskId` and `link`. Tell the user both have started, with their links, and end the turn.

Don't use `mode: "wait"`, polling, sleeps, or `task_status` loops. A max-effort review can take more than 10 minutes. Each reviewer wakes this thread when it finishes. When only one report is in, say so in one line and end the turn again.

## 4. Combined report

When both reports are in, write:

1. **Verdicts:** each reviewer's verdict with its T3 thread `link`.
2. **Agreed:** findings both reviewers raised, merged into one entry each.
3. **Only Codex** and **Only Opus:** findings only one reviewer raised. Before you list a high or medium one, read the cited `file:line` yourself. Mark it confirmed, plausible or rejected, with a one-line reason. Don't present a claim you haven't checked as fact.
4. **Disagreements:** where the reviewers conflict, your call, and why.
5. **Questions** for the user, merged and deduplicated.
6. **Recommendation:** merge now, fix first, or don't merge, plus a short ordered list of fixes.
7. Next-action options, for example: implement fix X, re-run one reviewer with a follow-up question, merge, skip. Use the user's own format if they have one.

To re-run a reviewer, start a new `delegate_task` with the brief, the findings, and the question. Don't send it into the old thread.
