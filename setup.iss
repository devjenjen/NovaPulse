; NovaPulse – Inno Setup Script
; Builds NovaPulse-Setup.exe
; Requires: Inno Setup 6.x  https://jrsoftware.org/isinfo.php

#define AppName      "NovaPulse"
#define AppVersion   "0.2.0"
#define AppPublisher "devjenjen"
#define AppURL       "https://github.com/devjenjen/NovaPulse"
#define AppExeName   "NovaPulse.exe"

[Setup]
AppId={{96d34880-a886-44be-bf9f-adbfba437626}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases

; Default installation directory using modern auto-path constant
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; No admin rights required
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

OutputDir=dist\installer
OutputBaseFilename=NovaPulse-Setup-{#AppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Minimum Windows version: Windows 10
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german";  MessagesFile: "compiler:Languages\German.isl"

[Tasks]
; Offer autostart during setup – user can also toggle it later via tray menu
Name: "autostart"; Description: "Start NovaPulse automatically with Windows"; GroupDescription: "Additional tasks:"; Flags: unchecked

[Files]
; Main executable built by PyInstaller
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; App icon (used for shortcuts)
Source: "assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#AppName}";       Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional – user can remove)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: not autostart

[Registry]
; Write autostart registry entry if the user checked the task during setup.
; NovaPulse can also toggle this itself via the tray menu at any time.
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\{#AppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
; Launch NovaPulse after setup completes (optional, user can uncheck)
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Kill running instance before uninstalling
Filename: "taskkill"; Parameters: "/IM {#AppExeName} /F"; Flags: runhidden; RunOnceId: "KillNovaPulse"

[UninstallDelete]
; Remove config and log files on uninstall only if the user explicitly chose to
; (left out intentionally – user data in %LOCALAPPDATA%\NovaPulse stays by default)
