# Dotfiles

This repository stores config files I want to keep and version with Git.

It is organized for `stow`, which means files live in this repo in a layout that mirrors where they should appear in my home directory.

## How it works

`stow` creates symlinks from this repository into my home directory.

Example:

- Real file in repo: `~/dotfiles/opencode/.config/opencode/opencode.json`
- Symlink created by `stow`: `~/.config/opencode/opencode.json`

Programs still read files from `~/.config/...`, but the actual tracked files live in `~/dotfiles`.

## Agent instructions

One `AGENTS.md` holds my personal instructions for every coding agent. Claude Code, Codex and OpenCode all read it through links into this repo.

| Home folder path | Links to | Read by |
| --- | --- | --- |
| `~/.config/agents/AGENTS.md` | `agents/.config/agents/AGENTS.md` | Claude Code, through the import in `CLAUDE.md` |
| `~/.claude/CLAUDE.md` | `claude/.claude/CLAUDE.md` | Claude Code |
| `~/.codex/AGENTS.md` (or `$CODEX_HOME/AGENTS.md`) | `agents/.config/agents/AGENTS.md` | Codex |
| `~/.config/opencode/AGENTS.md` | `agents/.config/agents/AGENTS.md` | OpenCode |

`claude/.claude/CLAUDE.md` imports `@~/.config/agents/AGENTS.md`. That path is a link the installer creates, so the import works wherever this repo is cloned.

A repo's own `AGENTS.md` is loaded by Codex and OpenCode. Claude Code loads it only when the repo has no `CLAUDE.md`, so `CLAUDE.md` tells Claude to read it in the other cases.

### Why the installers create the Codex and OpenCode links themselves

Codex and OpenCode need the same file at two more paths. Stow links each package file to one place, so sharing a file across packages would mean committing symlinks, which Git on Windows often checks out as plain text files. Instead the shared file lives once in the `agents` package, Stow links the `agents` and `claude` packages, and the installers link the Codex and OpenCode paths straight to the shared file.

### Install

Both installers can be rerun safely. They leave correct links alone, replace links that point elsewhere, move a real file to `<file>.backup.<timestamp>` before replacing it, stop if a real folder is in the way, and print every change. They don't touch `~/.claude/settings.json` or `~/.codex/config.toml`.

Windows (needs Developer Mode or an admin shell to create symlinks):

```powershell
cd F:\Repositories\dotfiles   # wherever this repo is cloned
.\install.ps1 -DryRun         # -DryRun = list the changes without making them
.\install.ps1                 # create the links
```

Linux and macOS:

```bash
sudo pacman -S stow           # Arch/Omarchy; Debian/Ubuntu: sudo apt install stow; macOS: brew install stow
cd ~/dotfiles
./install.sh --dry-run        # --dry-run (or -n) = list the changes without making them
./install.sh                  # stow agents + claude, then link the Codex, OpenCode and skill paths
```

To check, start a new session and ask which letters label Next Action Options (`j, k, l, o, p`). In Claude Code, `/context` lists `~/.claude/CLAUDE.md` and `~/.config/agents/AGENTS.md` under Memory files.

### Adding rules

- **Every tool**: edit `agents/.config/agents/AGENTS.md`. Keep the wording tool-neutral.
- **Claude Code only**: add them to `claude/.claude/CLAUDE.md`, below the import.
- **Codex only**: Codex reads one global file and has no import syntax, and `~/.codex/AGENTS.override.md` replaces `AGENTS.md` instead of adding to it. Put Codex-only rules in `developer_instructions` in `~/.codex/config.toml`, which adds to `AGENTS.md`. That file is machine-local and not managed here.
- **OpenCode only**: list extra files in `instructions` in `opencode.json`; they are added to `AGENTS.md`.

Changes apply to new sessions.

## Skills

Each of my own skills lives once in `agents/.agents/skills/`. Claude Code doesn't read `~/.agents/skills`, so the installers link every skill folder there into two places:

| Home folder path | Links to | Read by |
| --- | --- | --- |
| `~/.agents/skills/<name>` | `agents/.agents/skills/<name>` | Codex, OpenCode |
| `~/.claude/skills/<name>` | `agents/.agents/skills/<name>` | Claude Code, OpenCode |

Each skill folder gets its own link, not the whole skills folder, because both folders also hold skills installed from elsewhere. `install.sh` tells stow to skip `.agents`, because `--no-folding` would link each skill file separately, and a `~/.agents` link to somewhere else would make stow stop.

OpenCode finds each skill in both folders and logs a "duplicate skill name" warning, but loads one copy, and both are the same files. Setting `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` removes the warning, but OpenCode then also stops loading the skills in `~/.claude/skills` that aren't in this repo.

Keep only skills I write or maintain here. A skill installed by another tool, such as a plugin or `npx skills`, gets updated by that tool, so leave it where that tool put it.

### Writing a skill that works in every tool

All three tools read the same `SKILL.md` format. To keep one copy working in all of them:

- **Folder name and `name` match.** Use lowercase letters, digits and single hyphens, up to 64 characters, for example `browser-testing`. OpenCode requires the match.
- **`description` says when to use the skill**, in 1 to 1024 characters (OpenCode's limit). Every tool picks skills by matching the request against it.
- **Extra frontmatter is fine.** Claude Code uses fields like `argument-hint`; Codex and OpenCode ignore fields they don't know.
- **Name tools neutrally.** Describe the action and put a tool's own name in brackets, for example "ask the user (with AskUserQuestion in Claude Code)".
- **Refer to bundled files by `~/.agents/skills/<name>/...`** or as "this skill's folder". Avoid `~/.claude/skills/...` and `${CLAUDE_SKILL_DIR}`, which are Claude-specific.
- **Have one `SKILL.md` per skill.** Another `SKILL.md` deeper in the folder, for example an example file in `assets/`, can load as a second skill in OpenCode.
- **Don't write output into the skill folder.** It is this repo's working tree, so anything a script saves there shows up in `git status`. Write to the user's project instead.

### Adding a skill

Replace `my-skill` with the skill's name, and the source path with wherever the skill is now (`~/.claude/skills`, `~/.agents/skills` or `~/.codex/skills`).

1. Copy the folder into `agents/.agents/skills/` on a new branch.
2. Check it against the list above and fix what doesn't fit.
3. Compare the copy with the original, then delete the original. The installer stops if a real folder is in the way, and a backup left there would load as a second copy.
4. Run the installer to link the skill for every tool.
5. Start a new session in each tool and check that the skill is there.
6. Commit the folder.

Windows (PowerShell):

```powershell
cd F:\Repositories\dotfiles                          # the repo
git switch -c chore/my-skill-skill                   # -c = create the branch and switch to it
Copy-Item -Recurse "$HOME\.claude\skills\my-skill" agents\.agents\skills\   # -Recurse = copy the folder and everything in it

# Compare the folders: no output and exit code 0 mean identical. -c core.safecrlf=false hides line-ending warnings.
git -c core.safecrlf=false diff --no-index --stat "$HOME\.claude\skills\my-skill" agents\.agents\skills\my-skill

# Delete the original: /s = with its contents, /q = don't ask. Use rmdir, not Remove-Item:
# PowerShell 5.1's Remove-Item can follow a folder link and delete the files it points to.
cmd /c rmdir /s /q "$HOME\.claude\skills\my-skill"

.\install.ps1 -DryRun                                # list the links it would make
.\install.ps1                                        # make them
```

Linux and macOS:

```bash
cd ~/dotfiles                                        # the repo
git switch -c chore/my-skill-skill                   # -c = create the branch and switch to it
cp -r ~/.claude/skills/my-skill agents/.agents/skills/        # -r = copy the folder and everything in it
diff -r ~/.claude/skills/my-skill agents/.agents/skills/my-skill   # -r = compare whole folders; no output means identical
rm -r ~/.claude/skills/my-skill                      # delete the original; -r = with its contents
./install.sh --dry-run                               # list the links it would make
./install.sh                                         # make them
```

Check each tool (on Windows, run these in Git Bash):

```bash
codex debug prompt-input "hi" | grep -o 'my-skill: .\{0,60\}'   # Codex: render the prompt it would send and find the skill
opencode debug skill | grep '"location".*my-skill'              # OpenCode: show where it loaded the skill from
```

In Claude Code, type `/my-skill`. Then commit:

```bash
git add agents/.agents/skills/my-skill               # stage the skill folder
git commit -m "Add my-skill skill"                   # -m = commit message
```

### Changing, renaming or removing a skill

- **Change:** edit the files in `agents/.agents/skills/<name>/`. Every tool reads them through the links, so new sessions get the edits without rerunning the installer.
- **Rename:** rename the folder and `name` together, delete the old links as below, and rerun the installer.
- **Remove:** delete the folder from the repo, then delete its two links. The installers create links but don't remove old ones.

```powershell
cmd /c rmdir "$HOME\.agents\skills\my-skill"         # Windows: rmdir without /s removes only the link
cmd /c rmdir "$HOME\.claude\skills\my-skill"
```

```bash
rm ~/.agents/skills/my-skill ~/.claude/skills/my-skill   # Linux/macOS: rm without -r removes only the links
```

### browser-testing

Runs smoke tests in T3's preview browser, so it works only in threads where T3 provides its preview tools. On first use in a repo it writes a repo-specific testing doc from `template.md`; the `{{...}}` placeholders there are filled in at that point. Its report scripts in `assets/smoke/` need Python with Pillow (`pip install pillow`). `template.md` refers to `~/.agents/skills/browser-testing/assets/smoke/`, so keep that link.

## Repository structure

Each top-level folder is a `stow` package.

Example:

```text
~/dotfiles/
  install.sh
  install.ps1
  agents/
    .agents/
      skills/
        browser-testing/
          SKILL.md
          template.md
          assets/smoke/
    .config/
      agents/
        AGENTS.md
  claude/
    .claude/
      CLAUDE.md
  opencode/
    .config/
      opencode/
        opencode.json
  nvim/
    .config/
      nvim/
        init.lua
        lua/
          plugins.lua
```

Important rule:

- The folder structure inside each package must match the final destination under `$HOME`

So if a file normally lives at:

`~/.config/nvim/init.lua`

then inside the repo it should live at:

`~/dotfiles/nvim/.config/nvim/init.lua`

## Common commands

Create symlinks for one package:

```bash
cd ~/dotfiles
stow opencode
```

Create symlinks for another package:

```bash
cd ~/dotfiles
stow nvim
```

Remove symlinks for a package:

```bash
cd ~/dotfiles
stow -D opencode
```

Restow a package after changes:

```bash
cd ~/dotfiles
stow -R opencode
```

Check Git status:

```bash
git -C ~/dotfiles status
```

## Adding a new file

Use this process when adding a config file that already exists in `~/.config`.

1. Pick a package name.
2. Create the matching folder structure inside `~/dotfiles`.
3. Copy the existing config file into the repo.
4. Back up the original file in `~/.config`.
5. Remove the original file from its old path.
6. Run `stow` for that package.
7. Verify the symlink.
8. Commit the new file to Git.

## Example: adding Neovim

If I want to track `~/.config/nvim/init.lua`, I would do:

```bash
mkdir -p ~/dotfiles/nvim/.config/nvim
cp ~/.config/nvim/init.lua ~/dotfiles/nvim/.config/nvim/init.lua
mv ~/.config/nvim/init.lua ~/.config/nvim/init.lua.backup
cd ~/dotfiles
stow nvim
ls -l ~/.config/nvim/init.lua
git -C ~/dotfiles add nvim/.config/nvim/init.lua
git -C ~/dotfiles commit -m "Track Neovim config"
```

If Neovim has more files, such as `lua/` modules, they can also be placed under:

```text
~/dotfiles/nvim/.config/nvim/
```

and then managed by the same `stow nvim` package.

## Notes

- Track only files I actually care about.
- Leave untouched Omarchy defaults alone until I want to manage them.
- Avoid tracking caches, logs, `node_modules`, and machine-specific generated files.
- Keep backup files until I am sure the symlinked version works.

## Fresh install workflow

On a new machine:

```bash
git clone <repo-url> ~/dotfiles
cd ~/dotfiles
./install.sh
stow opencode
stow nvim
```

If a target file already exists in `~/.config`, back it up first so `stow` has a clear place to create the symlink.
