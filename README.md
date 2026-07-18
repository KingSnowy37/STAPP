# Screen Time Tracker

A lightweight Windows screen-time tracker that:

- runs quietly in the system tray
- starts automatically with Windows
- logs activity locally to SQLite
- opens a lightweight native Windows report window
- can be packaged as `.exe` files

## How it works

The tracker samples Windows idle time once per minute. If the computer has had user input within the last 5 minutes, that minute is counted as active time.

During active minutes, it also records the foreground app locally so the report can show the most-used apps. It stores the process name, executable path when available, and a short window title. Browser window titles are deliberately discarded to avoid logging page names or browsing content.

Everything stays local:

- no cloud sync
- screen-time records stay in a local SQLite database
- no keystroke logging, screenshots, or browser page capture

The optional update checker contacts the configured GitHub release feed only to look for a newer installer; it does not upload screen-time data.

## Files

- `tracker.pyw` - background tracker entry point
- `report.pyw` - launches the native Windows report window
- `build_exe.ps1` - packages both apps as `.exe`
- `install_startup.ps1` - creates a Startup shortcut
- `screentime/` - app code

## Run from Python

Start the tracker:

```powershell
py -3 tracker.pyw
```

When running, it appears in the Windows system tray. Right-click the tray icon to open the report or quit the tracker.

Open the local report window:

```powershell
py -3 report.pyw
```

## Build `.exe` files

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

This creates:

- `dist\ScreenTimeTracker.exe`
- `dist\ScreenTimeReport.exe`

## Install startup shortcut

After building the tracker exe:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_startup.ps1
```

If `dist\ScreenTimeTracker.exe` exists, the shortcut will use it. Otherwise it falls back to `pyw.exe` and `tracker.pyw`.

## Build the installer

After building the executables, compile `installer.iss` with Inno Setup. The setup file will be created at:

`installer-output\ScreenTimeTracker-Setup.exe`

The installer puts the app in `%LOCALAPPDATA%\Programs\Screen Time Tracker`, creates a per-user Windows Startup shortcut, and keeps the database in `%LOCALAPPDATA%\Screen Time Tracker`.

## Updates

The tray app checks the latest release from `https://github.com/KingSnowy37/STAPP` on startup and then once per day. Right-click the tray icon and choose `Check for updates` to run a check at any time.

To publish an update:

1. Change `APP_VERSION` in `screentime\version.py`.
2. Install GitHub CLI and sign in with `gh auth login`.
3. Run `powershell -ExecutionPolicy Bypass -File .\publish_release.ps1 -Notes "What changed"`.

This builds the installer and publishes it as a GitHub release. Use a version tag such as `v1.1.1`; the updater only accepts numeric version tags and downloads the release asset named `ScreenTimeTracker-Setup.exe`.

## GitHub automation

The included `.github\workflows\release.yml` builds and publishes the installer automatically whenever you push a tag such as `v1.0.1`. This is the simplest way to make updates available to installed copies.

## Data location

The SQLite database is stored at:

`data\screentime.db`

## Notes

- This version tracks total active computer time, not specific apps or websites.
- A good next step would be app-by-app tracking or daily limit alerts.
