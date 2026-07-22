#define AppName "Screen Time Tracker"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppPublisher "Local Screen Time"
#define AppExeName "ScreenTimeTracker.exe"
#define ReportExeName "ScreenTimeReport.exe"

[Setup]
AppId={{B4C3F723-33E9-4AE3-97C3-14A90975F0F5}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
InfoBeforeFile=installer-upgrade.txt
OutputDir=installer-output
OutputBaseFilename=ScreenTimeTracker-Setup
SetupIconFile=assets\screentime.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UsePreviousGroup=yes

[InstallDelete]
; Remove stale shortcuts from old/manual installs before recreating one canonical set.
Type: files; Name: "{autostartup}\Screen Time Tracker.lnk"
Type: files; Name: "{group}\Screen Time Report.lnk"
Type: files; Name: "{group}\Uninstall Screen Time Tracker.lnk"

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#ReportExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autostartup}\Screen Time Tracker"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\Screen Time Report"; Filename: "{app}\{#ReportExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#ReportExeName}"
Name: "{group}\Uninstall Screen Time Tracker"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch Screen Time Tracker"; Flags: nowait postinstall skipifsilent

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  PreviousUninstaller: String;
  ResultCode: Integer;
begin
  Result := '';
  PreviousUninstaller := AddBackslash(WizardDirValue) + 'unins000.exe';

  if not FileExists(PreviousUninstaller) then
    exit;

  WizardForm.StatusLabel.Caption := 'Removing the previous version...';
  if not Exec(
    PreviousUninstaller,
    '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
  begin
    Result :=
      'Setup could not start the previous version''s uninstaller. ' +
      'Uninstall Screen Time Tracker from Windows Settings, then run Setup again.';
    exit;
  end;

  if ResultCode <> 0 then
    Result :=
      'The previous version could not be fully removed. Close Screen Time Tracker ' +
      'and its report window, uninstall it from Windows Settings, then run Setup again.';
end;
