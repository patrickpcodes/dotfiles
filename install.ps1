<#
Links the shared agent instructions and skills into Claude Code, Codex and OpenCode.
Usage: .\install.ps1 [-DryRun]
Needs Developer Mode (or an admin shell) to create symlinks.
#>
param([switch]$DryRun)
$ErrorActionPreference = 'Stop'

$shared = Join-Path $PSScriptRoot 'agents\.config\agents\AGENTS.md'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$configHome = if ($env:XDG_CONFIG_HOME) { $env:XDG_CONFIG_HOME } else { Join-Path $HOME '.config' }

$links = [ordered]@{
    (Join-Path $HOME '.config\agents\AGENTS.md') = $shared
    (Join-Path $HOME '.claude\CLAUDE.md')        = Join-Path $PSScriptRoot 'claude\.claude\CLAUDE.md'
    (Join-Path $codexHome 'AGENTS.md')           = $shared
    (Join-Path $configHome 'opencode\AGENTS.md') = $shared
}
# Codex and OpenCode read ~/.agents/skills; Claude Code reads only ~/.claude/skills.
$skills = Join-Path $PSScriptRoot 'agents\.agents\skills'
if (Test-Path -LiteralPath $skills) {
    foreach ($skill in Get-ChildItem -LiteralPath $skills -Directory) {
        $links[(Join-Path $HOME ".agents\skills\$($skill.Name)")] = $skill.FullName
        $links[(Join-Path $HOME ".claude\skills\$($skill.Name)")] = $skill.FullName
    }
}

$changes = 0
function Invoke-Change([string]$Description, [scriptblock]$Action) {
    $script:changes++
    if ($DryRun) {
        Write-Host "would: $Description"
    } else {
        Write-Host "+ $Description"
        & $Action
    }
}

foreach ($link in $links.GetEnumerator()) {
    $path = $link.Key
    $source = [IO.Path]::GetFullPath($link.Value)
    if (-not (Test-Path -LiteralPath $source)) { throw "Missing source: $source" }
    $flags = @(if (Test-Path -LiteralPath $source -PathType Container) { '/D' })

    $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    if ($item -and $item.LinkType -eq 'SymbolicLink') {
        $current = [IO.Path]::GetFullPath([IO.Path]::Combine((Split-Path $path), @($item.Target)[0]))
        if ($current -eq $source) {
            Write-Host "ok: $path"
            continue
        }
        # PowerShell 5.1's Remove-Item can delete a folder link's contents; Delete() removes only the link.
        Invoke-Change "remove link $path -> $current" { $item.Delete() }
    } elseif ($item -is [IO.FileInfo]) {
        Invoke-Change "move $path -> $path.backup.$stamp" { Move-Item -LiteralPath $path -Destination "$path.backup.$stamp" }
    } elseif ($item) {
        throw "$path exists and is not a file or link; move it out of the way first"
    }

    $parent = Split-Path $path
    if (-not (Test-Path -LiteralPath $parent)) {
        Invoke-Change "create folder $parent" { New-Item -ItemType Directory -Path $parent | Out-Null }
    }
    # PowerShell 5.1's New-Item needs admin for symlinks even in Developer Mode; mklink doesn't.
    Invoke-Change "link $path -> $source" {
        cmd /c mklink @flags $path $source | Out-Null
        if ($LASTEXITCODE) { throw "mklink failed for $path" }
    }
}

if ($DryRun) {
    Write-Host "dry run: $changes change(s) planned, nothing changed"
} else {
    Write-Host "$changes change(s) made"
}
