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
OutputDir=installer-output
OutputBaseFilename=ScreenTimeTracker-Setup
SetupIconFile=assets\screentime.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#ReportExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autostartup}\Screen Time Tracker"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\Screen Time Report"; Filename: "{app}\{#ReportExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#ReportExeName}"
Name: "{group}\Uninstall Screen Time Tracker"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch Screen Time Tracker"; Flags: nowait postinstall skipifsilent
