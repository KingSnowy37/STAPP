param(
    [Parameter(Mandatory = $true)]
    [string]$Notes
)

$ErrorActionPreference = "Stop"
$appRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$versionFile = Join-Path $appRoot "screentime\version.py"
$releaseAsset = Join-Path $appRoot "installer-output\ScreenTimeTracker-Setup.exe"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI is required. Install it, run 'gh auth login', then rerun this script."
}

$versionLine = Get-Content $versionFile | Where-Object { $_ -match '^APP_VERSION\s*=\s*"([0-9]+(?:\.[0-9]+)+)"$' }
if (-not $versionLine) {
    throw "Could not read APP_VERSION from $versionFile"
}

$appVersion = [regex]::Match($versionLine, '"([0-9]+(?:\.[0-9]+)+)"').Groups[1].Value
& (Join-Path $appRoot "build_installer.ps1")
gh release create "v$appVersion" $releaseAsset --repo KingSnowy37/STAPP --title "Screen Time Tracker v$appVersion" --notes $Notes
