# Dotfiles

This repository stores config files I want to keep and version with Git.

It is organized for `stow`, which means files live in this repo in a layout that mirrors where they should appear in my home directory.

## How it works

`stow` creates symlinks from this repository into my home directory.

Example:

- Real file in repo: `~/dotfiles/opencode/.config/opencode/opencode.json`
- Symlink created by `stow`: `~/.config/opencode/opencode.json`

Programs still read files from `~/.config/...`, but the actual tracked files live in `~/dotfiles`.

## Repository structure

Each top-level folder is a `stow` package.

Example:

```text
~/dotfiles/
  opencode/
    .config/
      opencode/
        AGENTS.md
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
stow opencode
stow nvim
```

If a target file already exists in `~/.config`, back it up first so `stow` has a clear place to create the symlink.
