$ErrorActionPreference = "Stop"

$appRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $appRoot

py -3 .\tools\create_icon.py
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --icon .\assets\screentime.ico --name ScreenTimeTracker tracker.pyw
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --icon .\assets\screentime.ico --name ScreenTimeReport report.pyw

Write-Host "Built dist\ScreenTimeTracker.exe"
Write-Host "Built dist\ScreenTimeReport.exe"
