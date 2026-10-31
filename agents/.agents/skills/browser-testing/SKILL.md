---
name: browser-testing
description: Set up and run browser smoke tests in T3's preview browser for the current repo. Use when the user wants to test a web app in the T3 browser, run a browser smoke test, or set up browser testing for a project. On first use in a repo it interviews the user and writes a repo-specific testing doc from a generic template.
argument-hint: "setup | <what to test>"
---

# Browser testing

Each repo gets its own testing doc. This skill writes it once, then follows it.

## 1. Find the repo doc

Look for `docs/browser-testing.md`, any other `*browser-testing*.md` in the repo, and links to one in AGENTS.md or CLAUDE.md.

- Found, and the user didn't ask for setup: read it and follow it. Skip to section 3.
- Not found, or the user asked to set up or redo it: go to section 2.

## 2. Setup

### 2a. Scan the repo

Pre-fill everything the code shows. Don't ask for anything you can find.

| Look in | For |
|---|---|
| `Properties/launchSettings.json`, `package.json` scripts, `vite.config.*`, `next.config.*`, `docker-compose*.yml`, `manage.py`, `Procfile`, `Makefile` | start command, port, launch profile |
| health and version routes (`MapHealthChecks`, `/health`, `/version`) | ready check, version endpoint |
| login page markup (`type="password"`) | user, password and submit selectors, UI framework |
| README, `appsettings*.json`, `.env.example`, CI deploy workflows | deployed URLs, prerequisites (cloud login, Docker, env vars) |
| `LINEAR.md`, README | issue tracker |
| `.git` or `.svn` | version control, for the ignore check |
| existing `artifacts/` or test-output folder | artifacts dir |
| frontend build config (`tsconfig.json`, bundler) | rebuild command, what needs a restart |

### 2b. Ask for the rest

First, ask the user (with AskUserQuestion in Claude Code):

- Where passwords go: "In the doc, and keep the doc out of version control (Recommended)" or "Not in the doc, ask with `request_secret` each run".
- Where the doc goes: `docs/browser-testing.md` (Recommended) or `BROWSER-TESTING.md` at the repo root.

Then show a draft profile table: every value found, with the file it came from, and every gap. Ask for the gaps in one message and wait for the reply:

1. **Targets.** Local URL, deployed dev or staging URLs, and whether they share a database and storage.
2. **Test accounts.** One line each: `login | role | password or secret name | notes (scope, data it owns)`. Skip passwords if they stay out of the doc. Also disabled or leftover accounts to avoid, and how accounts relate (parent and child, tenants).
3. **Starting locally.** Prerequisites such as a cloud login, Docker, env vars or seed scripts, if the scan didn't show them.
4. **Writes.** What tests may change without asking, if anything.
5. **Quirks.** For example: a reload logs you out, layouts built at load time, where feature flags live, an API helper the page exposes.

Never guess a value the user didn't give and the repo didn't show. Leave its line out.

### 2c. Write the doc

1. Fill [template.md](template.md) (placeholders below). Replace every `{{...}}`. Delete each line, row or paragraph whose value is unknown or doesn't apply. Grep the result for `{{` and fix any hit.
2. Keep sections 3 to 6 as written, apart from their placeholders.
3. If passwords are in the doc, check it's ignored by version control: `git check-ignore -q <path>` (exit code 0 means ignored) or `svn status <path>` (`I` means ignored). If it isn't, ask before adding it to `.gitignore` or `svn:ignore`.
4. Ask whether to add a one-line pointer to the doc in the repo's AGENTS.md (or CLAUDE.md), so other sessions find it.
5. Don't commit.
6. Give the user the doc's path, what came from the scan and what came from them, and any lines left out.
7. Offer a check run: reach the target, open it in the preview, log in with one account, confirm the login worked, close the tab. Fix the doc if anything was wrong.

### Placeholders

| Placeholder | Value |
|---|---|
| `APP` | app name |
| `CREDENTIALS_NOTE` | passwords in doc: "These credentials must never go into version control, tickets or chat with outsiders." Otherwise: "Passwords aren't stored here. Ask for them with `request_secret`." |
| `DEPLOYED_NAME`, `DEPLOYED_URL`, `VERSION_CHECK` | one row per deployed dev or staging target. `VERSION_CHECK` like "Check the build with `/version`" |
| `SHARED_DATA_NOTE` | whether the targets share a database and storage, so logins and data are shared |
| `START_COMMAND` | full command: `cd` to the app, run it, send output to `<artifacts dir>/<app>-run.log` |
| `READY_CHECK` | like "the log shows it listening on 5000, or `curl -s http://localhost:5000/health` answers" |
| `PREREQUISITES` | cloud login, Docker, env vars, seed data |
| `CHANGE_NOTES` | which changes need a rebuild (and its command) and which need a restart |
| `PORT_CHECK` | `Get-NetTCPConnection -LocalPort <port> -State Listen` on Windows, `lsof -i :<port>` elsewhere |
| `LOCAL_DIFFERENCES` | where local config differs from deployed |
| `LOGIN_ROWS` | one table row per account |
| `ACCOUNT_NOTES` | how accounts relate, which own test data, disabled ones to avoid |
| `UI_FRAMEWORK` | React, Vue, Angular, Knockout, ... |
| `USER_SELECTOR`, `PASSWORD_SELECTOR`, `SUBMIT_SELECTOR` | login form selectors |
| `API_URL_SHAPE` | like "API URLs look like `/api/orders/1`." |
| `API_CALL` | how to call the API from the page with the session: `fetch` with cookies, a token from storage, or an app helper |
| `SWITCH_USER` | default: "log out through the UI, then `preview_navigate` to the site root, or use an incognito tab". Add what to avoid |
| `DRIVING_NOTES` | quirks, one bullet each |
| `HEALTH_URL` | ready or version endpoint |
| `ARTIFACTS_DIR` | where smoke runs are kept |
| `WRITABLE_DATA` | what tests may change without asking |
| `ISSUE_TRACKER` | Jira, Linear, GitHub Issues, ... |
| `FEATURE_CONFIG_NOTES` | where feature flags and permissions come from, and how they resolve |

## 3. Run tests

Follow the repo doc. Where it and this skill disagree, the doc wins.

- If the doc's smoke tooling path is missing, use `assets/smoke/` in this skill's folder.
- When the user gives new facts (a new account, a quirk, a changed URL), update the repo doc.
