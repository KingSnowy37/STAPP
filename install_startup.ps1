param(
    [switch]$UseSource
)

$ErrorActionPreference = "Stop"

$startupFolder = [Environment]::GetFolderPath("Startup")
$appRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$distTrackerPath = Join-Path $appRoot "dist\ScreenTimeTracker.exe"
$shortcutPath = Join-Path $startupFolder "Screen Time Tracker.lnk"

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)

if ((Test-Path $distTrackerPath) -and -not $UseSource) {
    $shortcut.TargetPath = $distTrackerPath
    $shortcut.Arguments = ""
}
else {
    $pythonwPath = (Get-Command pyw.exe -ErrorAction SilentlyContinue).Source
    if (-not $pythonwPath) {
        throw "Neither dist\ScreenTimeTracker.exe nor pyw.exe was found."
    }

    $trackerPath = Join-Path $appRoot "tracker.pyw"
    if (-not (Test-Path $trackerPath)) {
        throw "Tracker source was not found at $trackerPath"
    }
    $shortcut.TargetPath = $pythonwPath
    $shortcut.Arguments = "`"$trackerPath`""
}

$shortcut.WorkingDirectory = $appRoot
$iconPath = Join-Path $appRoot "assets\screentime.ico"
$shortcut.IconLocation = if (Test-Path $iconPath) { $iconPath } else { "$env:SystemRoot\System32\shell32.dll,44" }
$shortcut.Save()

Write-Host "Startup shortcut created at $shortcutPath"
