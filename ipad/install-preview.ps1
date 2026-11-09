param([string]$Distro)
$ErrorActionPreference = 'Stop'

# Run this locally: Apple authentication must remain interactive.
$taskDistros = @(& wsl.exe --list --quiet | ForEach-Object { ($_ -replace "`0", '').Trim() } | Where-Object { $_ -and $_ -notlike 'docker-desktop*' })
if (-not $Distro) {
    if ($taskDistros.Count -eq 1) { $Distro = $taskDistros[0] }
    else { throw 'Choose a regular WSL Linux distribution with -Distro Ubuntu. If none exists, follow the upstream xtool Windows setup first. Docker Desktop internal distributions are not supported.' }
}
if ($Distro -notin $taskDistros) { throw 'The selected WSL distribution is not installed.' }
$taskTool = Join-Path $PSScriptRoot 'xtool-x86_64.AppImage'
if (-not (Test-Path -LiteralPath $taskTool)) {
    Invoke-WebRequest -Uri 'https://github.com/xtool-org/xtool/releases/download/1.24.0/xtool-x86_64.AppImage' -OutFile $taskTool
}
$taskIpa = Join-Path $PSScriptRoot 'OpenLabeliPad.ipa'
if (-not (Test-Path -LiteralPath $taskIpa)) { throw 'Place the built OpenLabeliPad.ipa next to this script.' }
$taskLinuxTool = (& wsl.exe -d $Distro -- wslpath -a $taskTool).Trim()
$taskLinuxIpa = (& wsl.exe -d $Distro -- wslpath -a $taskIpa).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Could not resolve files inside WSL.' }
& wsl.exe -d $Distro -- chmod +x $taskLinuxTool
if ($LASTEXITCODE -ne 0) { throw 'Could not mark xtool executable.' }
Write-Host 'This installs the EDITOR PREVIEW only. It does not enable printer USB access.'
Write-Host 'Complete authentication in the local tool. Do not share your password or 2FA code in chat.'
& wsl.exe -d $Distro -- env APPIMAGE_EXTRACT_AND_RUN=1 $taskLinuxTool auth login
if ($LASTEXITCODE -ne 0) { throw 'xtool authentication did not complete.' }
& wsl.exe -d $Distro -- env APPIMAGE_EXTRACT_AND_RUN=1 $taskLinuxTool devices
if ($LASTEXITCODE -ne 0) { throw 'Check iPad pairing and WSL USB access.' }
& wsl.exe -d $Distro -- env APPIMAGE_EXTRACT_AND_RUN=1 $taskLinuxTool install $taskLinuxIpa
if ($LASTEXITCODE -ne 0) { throw 'xtool installation failed. Review its error above.' }
