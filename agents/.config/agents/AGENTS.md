## Interactive Response System

- **MANDATORY**: At the end of every response, provide 3-5 **Next Action Options** labeled with letters **j, k, l, o, p**
- **Format**: Each option should be a clear, actionable next step the user can choose, displayed on separate lines for easy reading
- **Purpose**: Streamlines conversation flow and reduces back-and-forth communication
- **User Response**: User responds with a single letter (j/k/l/o/p) to select their preferred next action
- **Example Format**:
  ```
  **Next Actions:**
  j) Build and test the changes
  k) Add additional validation to the email service
  l) Create a new Linear issue for email template improvements
  o) Update documentation for the new email system
  p) Move on to a different task
  ```
  
## Code Quality Requirements

- **MANDATORY OBJECT VERIFICATION**: Before implementing any code, verify all objects by reading their properties, methods, constructors, and related DTOs
- **Performance**: Use bulk operations, HashSet for lookups, batch database operations
- **Transactions**: Always wrap multi-step database operations in transactions

## Documentation Update Requirements

**IMPORTANT**: Periodically update these files:
1. **README.md**: Development status, new features, architecture changes
2. **External Issues**: Look for LINEAR.md for instructions(if it exists). Task status, progress updates, technical decisions
3. **AGENTS.md**: Service descriptions, new patterns, architectural decisions

**Update Frequency**: After major features, architecture changes, or at minimum monthly during active development.

## Shell Command Explanations

- **MANDATORY**: When providing shell commands for the user to run, include inline comments explaining:
  - What each command does
  - What special flags/options mean (e.g., `-R` means recursive, `-p` means create parent directories)
  - What symbols mean (e.g., `|` is pipe, `&&` chains commands, `>` redirects output)
  - What the expected outcome is
- **Format**: Use `#` comments on the same line or above each command
- **Example**:
  ```bash
  # Create directory and all parent directories if they don't exist
  sudo mkdir -p /var/lib/postgres/data    # -p = create parents, sudo = run as admin

  # Change ownership recursively to postgres user/group
  sudo chown -R postgres:postgres /var/lib/postgres    # -R = recursive, user:group format
  ```
- **Purpose**: User is learning Linux - commands should be educational, not just functional

### When Starting Work
1. **Read Context**: Always start by reading README.md. Follow the repo's AGENTS.md too; where it conflicts with these global instructions, the repo's rules win.
2. **Review External Task Tracking System**: Read through LINEAR.md file for instructions(if it exists).  Check assigned issues for current priorities


## General Testing Strategy

# C# applications
- **Unit Tests**: Business logic and domain rules
- **Integration Tests**: Database operations with TestContainers and transaction-based isolation
- **Architecture Tests**: Enforce clean architecture boundaries
- **Authorization Tests**: Comprehensive auth verification

### Overall comment reductions
- **MANDATORY**: Let's try to limit the amount of comments left in the code.  I find a lot of comments unnessary
	- When removing code blocks, we don't really need a comment for that, our version tracking keeps track of that
	- For simple/basic logic, we don't need a comment to explain it

	
# Code Commits
- **DO NOT EVER COMMIT CODE WITHOUT GETTING CONFIRMATION**:  I have run into issues where commits are done prematurely and its work to clean up.
- Make commit messages clear and consise, and try to keep commits small and central.
- Unless for a hot fix, never work directly on master, and always ask to switch to a new branch.  Require confirmation on that.
- If we're on a branch, and work seems unrelated to the branch name/goal, highlight that to the user and include an option for them to change/modify it.

## Git Repository Workflow

These rules apply only when the current workspace is a Git repository. Do not apply these branching rules to SVN repositories or other version control systems.

### Long-Lived Branches

- `master` is the stable branch. Code merged here should be deployable and production-ready.
- `dev` is the integration branch. Completed feature, fix, chore, and documentation work lands here first through pull requests.

### Short-Lived Branches

Create short-lived work branches from `dev` and merge them back into `dev` through pull requests.

Use these prefixes:

- `feature/*` for user-facing functionality
- `fix/*` for bug fixes
- `chore/*` for tooling, build, configuration, and maintenance
- `docs/*` for documentation-only changes

Examples:

```text
feature/book-catalog
fix/login-validation
chore/github-actions
docs/branching-strategy
```

### Normal Workflow

```text
dev -> feature/my-work -> pull request -> dev -> release pull request -> master
```

1. Create a work branch from `dev`.
2. Build, test, and commit changes on the work branch.
3. Open a pull request into `dev`.
4. Merge into `dev` after review and passing checks.
5. Open a pull request from `dev` into `master` when the integrated work is ready to release.
6. Merge into `master` only after release checks pass.

### Branch Protection

Protect `dev` and `master`.

For `dev`:

- Require pull requests.
- Require passing automated checks.
- Disallow direct pushes.

For `master`:

- Require pull requests.
- Require passing automated checks.
- Disallow direct pushes.
- Prefer release pull requests from `dev`.

### GitHub Actions Expectations

Pull requests into `dev` should run:

- Build
- Unit tests
- Architecture tests

Pushes or pull requests into `master` should run the same checks and can later include production release or deployment steps.

### Operating Rules

- Keep work branches short-lived.
- Rebase or merge from `dev` regularly while work is active.
- Do not merge unfinished work into `dev` unless it is safely disabled or behind a feature flag.
- Keep `master` deployable.
- Create or link a Linear issue for meaningful implementation work before starting the branch.

## Communication

- Default to short, plain, direct output.  Answer in the fewest words that fully address what was asked.
- Skip filler, hedging, and pleasantries ("happy to help", "sure!", "let me just...")
- No structural padding for short answers: no headers, no bold labels, no scaffolding, no 'in short' or 'to summarize', just answer the question directly
- Answering a question is not permission to be verbose.  Lead with a direct, concise answer.  Add detail only if asked for additional context or explanation.
- Don't teach or give multiple framings unless asked.

## Plans in T3 Code

- **When**: I ask for a plan and you are running in T3 Code (its tools are available, with names ending in `preview_open` and `preview_set_appearance`). Outside T3 Code, give plans in chat as usual.
- **Format**: Write the plan as one self-contained HTML page (inline CSS, no external files) in dark mode: dark background, light text, readable at the side panel's width.
- **Location**: Save it outside the repo at `~/.local/share/agent-plans/<repo>-<YYYY-MM-DD>-<topic>.html` so it can't be committed by accident.
- **Open it**: Show it in T3's preview side panel, ready to read:
  1. Serve that folder on 127.0.0.1 with a short-lived local web server (for example Python's `http.server`).
  2. Open the page's URL with `preview_open`, then set `preview_set_appearance` to dark.
  3. Stop the server once the page has loaded.
- **Chat**: Reply with a 2-3 line summary and the file path. Don't repeat the whole plan in chat.
