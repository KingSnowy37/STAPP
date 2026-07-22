$ErrorActionPreference = "Stop"

$appRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $appRoot

py -3 .\tools\create_icon.py
if ($LASTEXITCODE -ne 0) {
    throw "Icon generation failed with exit code $LASTEXITCODE."
}

py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --icon .\assets\screentime.ico --name ScreenTimeTracker tracker.pyw
if ($LASTEXITCODE -ne 0) {
    throw "ScreenTimeTracker build failed with exit code $LASTEXITCODE. Close the running tracker and try again."
}

py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --icon .\assets\screentime.ico --name ScreenTimeReport report.pyw
if ($LASTEXITCODE -ne 0) {
    throw "ScreenTimeReport build failed with exit code $LASTEXITCODE. Close the running report and try again."
}

Write-Host "Built dist\ScreenTimeTracker.exe"
Write-Host "Built dist\ScreenTimeReport.exe"
