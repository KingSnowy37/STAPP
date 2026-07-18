# Version 1.1 Package

`GitHub Source` contains the files to drag into the root of the GitHub repository.

`ScreenTimeTracker-Setup.exe` is the fresh v1.1.0 installer. Upload this one file to the GitHub Release. It installs both executables and creates the Windows Startup shortcut.

`Release Files` contains the matching fixed executables for manual testing. Keep both files together: run `ScreenTimeTracker.exe`; it opens the report executable from the same folder when you choose `Open report` in the tray menu.

`RELEASE_NOTES.md` lists the changes and `SHA256SUMS.txt` verifies the two executables.

The automatic updater requires a release tag newer than the installed app version and the asset name `ScreenTimeTracker-Setup.exe`. This installer has that exact filename.
