$ErrorActionPreference = "Stop"

$appRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$versionFile = Join-Path $appRoot "screentime\version.py"
$innoCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$innoCompiler = $innoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $innoCompiler) {
    throw "Inno Setup 6 is required. Install it, then rerun this script."
}

Set-Location $appRoot
$versionLine = Get-Content $versionFile | Where-Object { $_ -match '^APP_VERSION\s*=\s*"([0-9]+(?:\.[0-9]+)+)"$' }
if (-not $versionLine) {
    throw "Could not read APP_VERSION from $versionFile"
}

$appVersion = [regex]::Match($versionLine, '"([0-9]+(?:\.[0-9]+)+)"').Groups[1].Value
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
& $innoCompiler "/DAppVersion=$appVersion" .\installer.iss

Write-Host "Built installer-output\ScreenTimeTracker-Setup.exe"
