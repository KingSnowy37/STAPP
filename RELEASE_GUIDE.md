# Publish This Project

This folder is a GitHub-ready copy of Screen Time Tracker. It contains source code and the workflow that builds the installer for every version tag.

## First upload

1. Open `https://github.com/KingSnowy37/STAPP`.
2. Upload the **contents** of this folder to the repository root. Do not create an extra `FOR RELEASE` folder inside the repository.
3. Keep the existing `LICENSE` file in the repository.
4. Commit the upload to the `main` branch.
5. Create and push the tag `v1.0.0`. GitHub Actions will build the installer and publish it under Releases.

If you use Git from a local clone, run:

```powershell
git add .
git commit -m "Add Screen Time Tracker"
git push origin main
git tag v1.0.0
git push origin v1.0.0
```

## Publish future updates

1. Update `APP_VERSION` in `screentime\version.py`, for example from `1.0.0` to `1.0.1`.
2. Commit and push the source changes to `main`.
3. Create and push the matching tag, such as `v1.0.1`.
4. Wait for the `Build and publish release` GitHub Action to finish.

The workflow attaches `ScreenTimeTracker-Setup.exe` to the new GitHub Release. Installed copies check that release feed daily and offer the download through their tray menu.

Do not commit the installer manually. The workflow creates the correct installer asset for each release.
