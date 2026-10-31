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

Each skill folder gets its own link, not the whole skills folder, because both folders also hold skills installed from elsewhere. `install.sh` tells stow to skip `.agents/skills`, because `--no-folding` would link each skill file separately.

OpenCode finds each skill in both folders and logs a "duplicate skill name" warning, but loads one copy, and both are the same files. Setting `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` removes the warning, but OpenCode then also stops loading the skills in `~/.claude/skills` that aren't in this repo.

To add a skill, copy its folder into `agents/.agents/skills/`. Move the original out of `~/.claude/skills` and `~/.agents/skills`, because the installer stops at a real folder and a backup left beside it loads as a second copy. Then rerun the installer.

To check which skills each tool sees:

```bash
codex debug prompt-input "hi" | grep -o 'browser-testing: .\{0,60\}'   # Codex: render the prompt it would send, find the skill entry
opencode debug skill | grep '"location"'                             # OpenCode: list every skill it found and where
```

In Claude Code, type `/browser-testing` or ask which skills are available.

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
