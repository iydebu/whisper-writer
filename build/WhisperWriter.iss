; WhisperWriter installer (Inno Setup 6.5+).
; Build with build\build.bat -- it passes /DMyAppVersion from the VERSION file.
; Input:  dist\WhisperWriter-<version>\WhisperWriter\ (PyInstaller onedir) + models\
; Output: dist\installer\WhisperWriter_Setup_<version>.exe

#define MyAppName "WhisperWriter"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#define MyAppPublisher "iydebu"
#define MyAppDev "iydebu (Devashish Tiwari)"
#define MyAppURL "https://iydebu.com"
#define MyAppExeName "WhisperWriter.exe"
#define Models "..\models"
#ifndef AppDist
  #error Build through build\build.bat -- it passes /DAppDist (the PyInstaller output folder).
#endif

[Setup]
; Never change AppId: upgrades find the old install through it.
AppId={{B8F9A3E2-7C4D-4E1F-8A2B-3C5D6E7F8A9B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL=https://github.com/iydebu
AppContact={#MyAppURL}
AppCopyright=Copyright (C) 2026 {#MyAppDev}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoCopyright=Copyright (C) 2026 {#MyAppDev}

; Per-user install into %LOCALAPPDATA%\Programs -- no admin prompt. The user can
; still pick "all users" on the first page.
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

OutputDir=..\dist\installer
OutputBaseFilename=WhisperWriter_Setup_{#MyAppVersion}
SetupIconFile=..\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; Model weights barely compress, so ultra64 only costs time. One single setup.exe
; (Inno 6.5+ allows up to ~4 GB without disk spanning).
Compression=lzma2/fast
SolidCompression=no
LZMAUseSeparateProcess=yes

CloseApplications=yes
RestartApplications=no

WizardStyle=modern
ShowComponentSizes=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nDeveloped by {#MyAppDev}%n{#MyAppURL}%n%nIt is recommended that you close all other applications before continuing.

[Types]
Name: "recommended"; Description: "Recommended"
Name: "custom"; Description: "Custom"; Flags: iscustom

[Components]
Name: "app"; Description: "WhisperWriter app"; Types: recommended custom; Flags: fixed
Name: "roman"; Description: "Hinglish Roman models (Hindi speech -> English letters)"; Types: recommended
Name: "roman\medium"; Description: "Apex - medium quality, fast, fine on CPU"; Types: recommended
Name: "roman\large"; Description: "Prime - large quality, most accurate, best with an NVIDIA GPU"; Types: recommended
Name: "wake"; Description: "Wake word model (say ""whisper"" to start dictation)"; Types: recommended
; Indian English / Hindi->English models: separate WhisperWriter_ExtraModels_Setup (a single
; Setup.exe tops out at ~4.2 GB).

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "Start WhisperWriter when I sign in to Windows"; GroupDescription: "Startup:"; Flags: unchecked

[InstallDelete]
; Upgrades: drop the old app code so no stale library is left behind. Models stay.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#AppDist}\*"; DestDir: "{app}"; Components: app; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Models}\whisper-hindi2hinglish-apex\*"; DestDir: "{app}\models\whisper-hindi2hinglish-apex"; Components: roman\medium; Flags: ignoreversion recursesubdirs
Source: "{#Models}\whisper-hindi2hinglish-prime\*"; DestDir: "{app}\models\whisper-hindi2hinglish-prime"; Components: roman\large; Flags: ignoreversion recursesubdirs
Source: "{#Models}\vosk-model-small-en-us-0.15\*"; DestDir: "{app}\models\vosk-model-small-en-us-0.15"; Components: wake; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\models"
Type: filesandordirs; Name: "{app}\_internal"
Type: dirifempty; Name: "{app}"

[Code]
// WhisperWriter lives in the tray, so Restart Manager cannot close it. End it here
// (settings are saved as they change) so upgrade/uninstall never stalls on files in use.
procedure CloseWhisperWriter();
var
  Code: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM WhisperWriter.exe', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Sleep(500);
end;

function InitializeSetup(): Boolean;
begin
  CloseWhisperWriter();
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  CloseWhisperWriter();
  Result := True;
end;

#include "gpu_check.iss"

procedure InitializeWizard();
var
  Msg: String;
begin
  Msg := CheckGpu();
  Log('GPU check: ' + Msg);
  if GpuOk then
    Log('GPU check result: GPU OK')
  else
    Log('GPU check result: CPU or limited GPU');
  CreateOutputMsgPage(wpWelcome, 'Graphics card check',
    'Can WhisperWriter use your graphics card (GPU)?', Msg);
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  // Untick the large model once, when the GPU cannot run it well. The user can tick it back.
  if (CurPageID = wpSelectComponents) and not GpuOk and not GpuPrimeUnticked then
  begin
    WizardSelectComponents('!roman\large');
    GpuPrimeUnticked := True;
  end;
end;

// Settings live in %APPDATA%\WhisperWriter (see src/paths.py). Keep them unless the user says otherwise.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserDir, Extra: String;
  Code: Integer;
begin
  // Remove the extra-models add-on first, so its Apps & features entry goes with it.
  if CurUninstallStep = usUninstall then
  begin
    Extra := ExpandConstant('{app}\models\uninstall-extra\unins000.exe');
    if FileExists(Extra) then
      Exec(Extra, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '', SW_HIDE, ewWaitUntilTerminated, Code);
  end;
  if CurUninstallStep = usPostUninstall then
  begin
    UserDir := ExpandConstant('{userappdata}\WhisperWriter');
    if DirExists(UserDir) and not UninstallSilent then
      if MsgBox('Also delete your WhisperWriter settings and log?' #13#10 + UserDir,
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(UserDir, True, True, True);
  end;
end;
