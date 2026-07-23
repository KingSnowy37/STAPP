# AGENTS.md

This file applies to the entire repository.

## Mandatory session start

At the beginning of every new chat or coding session, before inspecting files, proposing work, editing code, running tests, or building artifacts:

1. Read this `AGENTS.md` file completely.
2. Treat it as the source of truth for product direction, current release phase, workflow, and constraints.
3. In the first progress update, confirm that `AGENTS.md` was read and name the current development phase.

Use this session-start prompt:

> Read the repository-root `AGENTS.md` completely before doing any work. Follow its product vision, privacy rules, current development phase, testing requirements, and release restrictions. Confirm that you read it before making changes.

## Current development phase

- **v1.2.0 was released on July 22, 2026.**
- The release tag is `v1.2.0`; the published installer is attached to the GitHub release.
- No later development or release phase is active until the user explicitly starts one.
- Do not bump the version or rebuild release artifacts without a newly authorized development/release phase.

## Product vision

Screen Time Tracker is a small, trustworthy Windows utility that helps people understand how long they actually use their computer. It should feel native, quiet, fast, and uncomplicated: start with Windows, live in the system tray, collect useful totals in the background, and show a clear report or optional live timer when asked.

The product is deliberately local-first. It is an awareness tool, not surveillance software, an account platform, or a productivity suite.

When making product or technical tradeoffs, prioritize in this order:

1. User privacy and control.
2. Correct, explainable time tracking.
3. Reliability during long, unattended sessions.
4. Low CPU, memory, disk, and visual overhead.
5. A simple, native Windows experience.
6. New features and visual polish.

## Non-negotiable product guardrails

- Keep screen-time data on the user's machine. Do not add analytics, telemetry, cloud sync, accounts, advertising, or remote storage unless the user explicitly changes the product direction.
- Never capture keystrokes, screenshots, clipboard contents, browser URLs, or browser page titles.
- Continue discarding titles for known browsers. Treat changes to `sanitize_window_title` and browser detection as privacy-sensitive.
- Collect the minimum information needed for a visible user benefit. New data collection must be obvious, justified, documented, and easy to disable or remove.
- Network access is only for an explicit user-facing feature such as checking the configured GitHub release feed. Never upload activity records, app usage, paths, titles, settings, or identifiers.
- The tracker must remain useful offline and without an account.
- Do not introduce nagging, gamification, shame-based language, dark patterns, or attention-grabbing background UI.
- Preserve user history and settings across upgrades. Never silently delete or reset local data.
- Installer upgrades must remove the previous program version and stale shortcuts before copying a new release, while preserving `%LOCALAPPDATA%\Screen Time Tracker` user data.

## Experience principles

- The default experience is set-and-forget: one tracker instance, no console window, no routine prompts, and no unnecessary notifications.
- Keep important actions easy to find in the tray: today's total, report, update, and quit.
- Reports should answer basic questions at a glance: how much time was tracked, how much was active, and which apps accounted for it.
- Prefer plain language and familiar Windows behavior over clever controls or dense dashboards.
- The live timer is optional, compact, glanceable, draggable, and persistently always-on-top across ordinary, maximized, and borderless-windowed applications. Keep it visually restrained: a standard Windows typeface, neutral colors, no decorative shadows, and no oversized or cartoon-like styling. It must never steal focus or be required to use the tracker.
- Installed features must work from the packaged executables without requiring Python or other developer tools on the user's computer.
- Fail softly. A reporting, focus-detection, overlay, or update error should be logged and isolated instead of crashing the background tracker whenever possible.

## Tracking semantics

- The tracker samples once per minute.
- A sample is active when Windows idle time is less than five minutes.
- One active sample represents one active minute in reports. Do not imply precision the sampling model does not provide.
- Focused-app samples are recorded only during active samples.
- Normalize equivalent executable/app names before presenting totals.
- Use local calendar dates consistently for daily summaries.
- If these semantics change, update the implementation, tests, README, and any migration or compatibility behavior together.

## Repository map

- `tracker.pyw`: background application entry point.
- `report.pyw`: report application entry point.
- `screentime/tracker.py`: sampling loop, tray menu, single-instance behavior, and update flow.
- `screentime/activity.py`: Windows idle/focus APIs, app-name normalization, and privacy filtering.
- `screentime/db.py`: SQLite schema and connections.
- `screentime/reporting.py`: queries and presentation-ready aggregates.
- `screentime/native_report.py`: native Win32 report window.
- `screentime/live_timer.py`: optional live timer overlay and controller.
- `screentime/settings.py`: local settings persistence.
- `screentime/updates.py`: GitHub release checks and installer downloads.
- `screentime/paths.py`: source and packaged data locations.
- `tests/`: privacy, timing, and reporting regression tests.
- `build_exe.ps1`, `build_installer.ps1`, `installer.iss`: Windows packaging.
- `FOR RELEASE/`, `installer-output/`, `dist/`, `build/`, `data/`, and `__pycache__/`: generated, copied, packaged, or user/runtime artifacts; do not use them as source-of-truth code and do not edit them unless the task explicitly targets release artifacts.

## Engineering guidelines

- Target Windows first. Win32/`ctypes` code is intentional; avoid replacing the native utility with a browser, hosted service, or heavyweight framework without an explicit product decision.
- Keep dependencies few and justified. Prefer the standard library and existing dependencies when they solve the problem cleanly.
- Keep background work bounded. Avoid busy loops, frequent disk writes, blocking network calls on UI/tracking threads, and unbounded logs or in-memory collections.
- Preserve the single-instance tracker guarantee and clean thread shutdown behavior.
- Use context managers for SQLite access, parameterized SQL, explicit commits for writes, and additive/backward-compatible schema changes. Existing databases may come from older installed versions.
- Keep collection, storage, aggregation, and presentation separated. Put testable calculations outside Win32 event procedures.
- Declare `ctypes` argument and return types for Windows API calls, check failure results, release handles/GDI objects, and retain callback references for as long as Windows can invoke them.
- Catch exceptions at process, thread, and UI callback boundaries with useful local logging. Do not broadly suppress errors inside pure logic.
- Keep source-mode and PyInstaller-frozen paths working. Do not assume the current working directory is the app directory.
- Follow the existing Python style: type hints for public and non-obvious interfaces, small focused functions, descriptive constants, four-space indentation, and imports grouped as standard library then third party then local.

## Testing and verification

Run the automated suite after code changes:

```powershell
py -3 -m unittest discover -s tests -v
```

Add or update tests for changed pure logic, especially:

- privacy filtering and app-name normalization;
- active-time and live-timer calculations;
- SQLite aggregation, ordering, date boundaries, and migrations;
- update version parsing or selection;
- settings defaults and malformed local files.

For changes involving Win32 UI, tray behavior, startup, packaging, or the installer, also perform the relevant manual Windows check. Verify source execution before packaging when possible:

```powershell
py -3 tracker.pyw
py -3 report.pyw
```

Do not run release publishing as routine verification. During feature work, do not rebuild executables or the installer unless the user explicitly requests a build at that time.

## Release discipline

- `screentime/version.py` is the application version source of truth.
- The required order for every release is: finish feature work, receive explicit user confirmation that the version is ready, update the version and release notes, run the full test suite, then rebuild and verify the executables and installer before pushing the release tag.
- Never rebuild or overwrite `dist/` or `installer-output/` preemptively during feature development, even when a change affects packaged behavior. Source-level verification is sufficient until the authorized release-build step.
- Keep the installer upgrade notice and previous-version removal flow intact. If that flow changes, verify clean install, upgrade, failed-uninstall recovery, startup shortcut uniqueness, and user-data preservation before release.
- Keep the updater compatible with numeric `vX.Y.Z` GitHub tags and the expected `ScreenTimeTracker-Setup.exe` asset unless coordinating a full release-protocol change.
- A version bump should include user-facing notes for meaningful changes.
- Do not publish a release, overwrite installer artifacts, or modify copies under `FOR RELEASE/` unless explicitly requested.
- Never commit runtime databases, logs, update state, personal settings, build output, or secrets.

## Definition of done

A change is complete when it:

- supports the local-first, low-friction product vision;
- preserves the privacy guardrails above;
- handles failure without destabilizing unrelated tracker functions;
- includes focused regression coverage where practical;
- passes the automated tests;
- has been manually checked on Windows when behavior cannot be covered by unit tests;
- updates README or release-facing documentation when setup, behavior, data collection, or tracking semantics changed;
- leaves generated artifacts and user data untouched unless they were explicitly in scope.

When requirements are ambiguous, choose the smaller, more private, more reversible change and state the assumption.
