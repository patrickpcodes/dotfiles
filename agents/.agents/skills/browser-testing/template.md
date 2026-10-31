# Testing {{APP}} in the T3 browser

Handoff for any chat that needs to drive {{APP}} in T3's preview browser.
Dev only. {{CREDENTIALS_NOTE}}

## 1. Pick a target

| Target | URL | When |
|---|---|---|
| {{DEPLOYED_NAME}} | {{DEPLOYED_URL}} | Test what is deployed. {{VERSION_CHECK}} |
| Local | {{LOCAL_URL}} | Test uncommitted code. You must start it yourself (below) |

{{SHARED_DATA_NOTE}}

### Running {{APP}} locally

```bash
{{START_COMMAND}}
```

- Run it as a background process so the session can keep working. In Claude Code, use the Bash tool's `run_in_background` (timeout up to 7200000 ms); the app stops when that ends.
- Ready when {{READY_CHECK}}.
- {{PREREQUISITES}}
- {{CHANGE_NOTES}}
- Check the port before starting: {{PORT_CHECK}}. If it's taken, ask first. The user may have the app open in an IDE.
- {{LOCAL_DIFFERENCES}}

## 2. Logins

| Login | Role | Password | Notes |
|---|---|---|---|
{{LOGIN_ROWS}}

{{ACCOUNT_NOTES}}

## 3. Driving the browser

These tools come from T3 Code. Their prefix depends on the agent: `mcp__t3-code__` in Claude Code, `mcp__t3_code__` in Codex. In Claude Code, load them first with ToolSearch:
`select:mcp__t3-code__preview_open,mcp__t3-code__preview_evaluate,mcp__t3-code__preview_navigate,mcp__t3-code__preview_snapshot,mcp__t3-code__preview_status,mcp__t3-code__preview_dialog,mcp__t3-code__preview_act,mcp__t3-code__preview_resize,mcp__t3-code__t3_preview_close`

- Open: `preview_open({ url, reuseExistingTab: false })`. Use `profileId: "incognito"` for a clean session or a second login.
- Use `preview_evaluate` for setup and for reading the page.
- For the clicks a test is about, use `preview_act`:
  - Click with `x`/`y` taken from `getBoundingClientRect()`. Clicks given a `selector` can time out.
  - `select` with `values` set to the option's label works on native `<select>`s.
  - `press` sends real key presses, which is what keyboard tests need.
  - Typing through `preview_act` may not reach {{UI_FRAMEWORK}} bindings. Set the value in evaluate with the native setter and dispatch input/change (see the login below).
- Window size: `preview_resize({ mode: "freeform", width: 1280, height: 900 })`.
  - If the preview panel is hidden, the new size only applies after the next `preview_navigate`.
  - Some layouts are only built when the page loads narrow. Reload after resizing to a phone size.
- Log in:
  ```js
  const s=(sel,v)=>{const e=document.querySelector(sel);Object.getOwnPropertyDescriptor(Object.getPrototypeOf(e),'value').set.call(e,v);['input','change','blur'].forEach(t=>e.dispatchEvent(new Event(t,{bubbles:true})))};
  s('{{USER_SELECTOR}}','<login>'); s('{{PASSWORD_SELECTOR}}','<password>');
  document.querySelector('{{SUBMIT_SELECTOR}}').click();
  ```
- **15 s limit per evaluate.** For longer flows, start async work and store the result, then poll in later calls:
  ```js
  // call 1
  (()=>{window.__o=null;(async()=>{ /* steps with await new Promise(r=>setTimeout(r,5000)) */ window.__o={...}})().catch(e=>window.__o={err:String(e)});return 'started'})()
  // call 2+, repeat until not 'pending'
  (async()=>{for(let i=0;i<13&&!window.__o;i++)await new Promise(r=>setTimeout(r,1000));return window.__o||'pending'})()
  ```
- Click menu items, tabs and tree nodes by exact leaf text:
  `[...document.querySelectorAll('*')].find(e=>e.children.length===0&&e.textContent.trim()==='<TEXT>'&&e.offsetParent).click()`
  Wait for the page to settle after logins and navigation: poll for an element or text rather than a fixed sleep.
- Read the page: `document.body.innerText`.
- Server calls and statuses: `performance.getEntriesByType('resource').map(r=>r.name+' '+r.responseStatus)`. {{API_URL_SHAPE}} HTTP 200 can still carry an app error in the body, so check it.
- Call the API with the logged-in session: {{API_CALL}}
- After a frontend rebuild the browser may keep serving cached assets. Run `await fetch(url, { cache: "reload" })` on each changed file, then reload the page.
- Screenshots: `preview_snapshot({ save: true })` returns a PNG path. Snapshots time out unless the tab is visible, so call `preview_open` on that tab first.
- Switch user: {{SWITCH_USER}}
- {{DRIVING_NOTES}}
- Stuck alert: if `preview_status` shows a dialog that `preview_dialog` can't dismiss, close the tab and open a new one.
- A fresh deploy or restart can return 503 for a minute. Poll {{HEALTH_URL}} until 200.
- Close your own tabs with `t3_preview_close` when done.

## 4. Smoke test process (always)

Every browser smoke run follows these steps, in `{{ARTIFACTS_DIR}}/<feature>/smoke/`.
Start by copying the files in `~/.agents/skills/browser-testing/assets/smoke/` into that folder, and rename `report-template.source.html` to `<feature>-smoke-tests.source.html`. The scripts need Python with Pillow (`pip install pillow`).

1. **Write the test list first.** Number the tests and give each one steps and an expected result.
   - Flag the tests that write data, and get the user's OK for each write.
   - Put the data back afterwards, and confirm it through the API.
2. **Keep a sleek HTML report** in `<feature>-smoke-tests.source.html`.
   - Dark mode. It opens with a summary table and progress bar, followed by an environment block: code revision, server, browser size, logins, and which data was touched.
   - Each test gets Steps, Expected, Actual, notes and screenshots.
   - Set each test's status with `data-s="pass|partial|fail|skip|todo"`, in both the summary row and the test.
   - Findings go in a table with `data-sev="high|medium|low|fixed"`, a fix suggestion, and where they were seen.
   - `python build-report.py` turns every `*.source.html` in its folder into a self-contained `.html`, with the screenshots inlined as WebP.
3. **Take screenshots of every test, and mark them up.**
   - An **amber arrow** with a label points at what was clicked. Number the steps when there is more than one (`1 Picked <option>`, `2 Clicked Save`).
   - A **red box** surrounds what changed, or what to focus on, with a short label where there's room.
   - Record each element's position with `getBoundingClientRect()` at capture time, before anything moves. At the 1280×900 freeform size, CSS pixels match screenshot pixels.
   - Keep the unmarked capture in `raw/`, and write a spec at `raw/NN-spec.json`.
   - Run `python annotate.py raw/NN-spec.json`, which draws the marks and crops the image. The spec format is in the script's docstring.
   - Look at every marked image before it goes into the report.
4. **Rebuild the report after each batch**, then send the user its link and the key screenshot.

## 5. Ground rules

- Read-only by default. Never send emails or notifications, and don't create, edit or delete data unless the user asked.
- {{WRITABLE_DATA}}
- Don't restart deployed apps, change cloud config or storage, or commit without the user's explicit OK.
- {{ISSUE_TRACKER}} is read-only.
- Never print secrets or connection strings.

## 6. If something is missing

{{FEATURE_CONFIG_NOTES}}

- Check the logged-in role. Pages and actions are often hidden by role.
- Compare local and deployed config.
- Clear cached assets (section 3) and reload.
