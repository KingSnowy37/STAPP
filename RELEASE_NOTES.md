# Screen Time Tracker v1.2.0

## Highlights

- Added a compact, transparent live timer using restrained native Windows styling.
- Added direct live-timer control to the tray menu, including packaged builds that do not require Python on the user's computer.
- Made the report window resizable and maximizable, with sections that adapt to the available space.
- Improved upgrade safety by removing the previous program version and stale shortcuts before installing while preserving local history and preferences.

## Fixed

- Kept the live timer above ordinary, maximized, borderless-windowed, and competing topmost applications without stealing focus.
- Kept accurate live seconds while the overlay is hidden so toggling it no longer resets to a rounded database minute.
- Fixed fractional-second accumulation and minute-boundary scheduling.
- Fixed duplicate app labels caused by executable suffixes, versioned Python names, and meaningful dots in display names.
- Preserved browser-title privacy filtering and local-only data storage.
- Made executable builds fail clearly when an output file is locked instead of incorrectly reporting success.

## Upgrade notes

- Close Screen Time Tracker and its report window before installing.
- Setup automatically removes the previous installed program files and stale shortcuts.
- Screen-time history and preferences in `%LOCALAPPDATA%\Screen Time Tracker` are preserved.
- If automatic removal fails, uninstall Screen Time Tracker from Windows Settings and run the v1.2.0 installer again.

## Validation

- 14 automated tests pass.
- Native Windows checks pass for report maximization, timer transparency, topmost reassertion, and source application startup.
