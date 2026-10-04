; WhisperWriter extra models add-on (Inno Setup 6.5+). Built by build\build.bat.
; Installs into an existing WhisperWriter install: {app}\models\<name>.
; Main setup must be installed first; its uninstaller also removes these models.

#define MyAppName "WhisperWriter"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#define Models "..\models"
; Must match AppId in WhisperWriter.iss.
#define MainAppId "{B8F9A3E2-7C4D-4E1F-8A2B-3C5D6E7F8A9B}"

[Setup]
AppId={{5D2C8E41-9B7A-4F36-A1E0-7C3B9D4F2E68}
AppName={#MyAppName} Extra Models
AppVersion={#MyAppVersion}
AppPublisher=iydebu
AppPublisherURL=https://iydebu.com
AppSupportURL=https://github.com/iydebu
AppCopyright=Copyright (C) 2026 iydebu (Devashish Tiwari)
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany=iydebu
VersionInfoCopyright=Copyright (C) 2026 iydebu (Devashish Tiwari)
DefaultDirName={code:MainAppDir}
DisableDirPage=yes
DisableProgramGroupPage=yes
CreateAppDir=yes
Uninstallable=yes
UninstallFilesDir={app}\models\uninstall-extra
UninstallDisplayName={#MyAppName} Extra Models
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist\installer
OutputBaseFilename=WhisperWriter_ExtraModels_Setup_{#MyAppVersion}
SetupIconFile=..\logo.ico
Compression=lzma2/fast
SolidCompression=no
LZMAUseSeparateProcess=yes
WizardStyle=modern
ShowComponentSizes=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full"; Description: "All extra models"
Name: "custom"; Description: "Custom"; Flags: iscustom

[Components]
Name: "english"; Description: "Indian English model"; Types: full
Name: "hindi"; Description: "Hindi speech -> English translation models"; Types: full
Name: "hindi\small"; Description: "Hindi small"; Types: full
Name: "hindi\medium"; Description: "Hindi medium"; Types: full
Name: "hindi\large"; Description: "Hindi large-v2"; Types: full
Name: "hindi\translator"; Description: "Hindi -> English translator (needed by every Hindi model)"; Types: full; Flags: fixed

[Files]
Source: "{#Models}\indian-accent-english-whisper\*"; DestDir: "{app}\models\indian-accent-english-whisper"; Components: english; Flags: ignoreversion recursesubdirs
Source: "{#Models}\whisper-hindi-small\*"; DestDir: "{app}\models\whisper-hindi-small"; Components: hindi\small; Flags: ignoreversion recursesubdirs
Source: "{#Models}\whisper-hindi-medium\*"; DestDir: "{app}\models\whisper-hindi-medium"; Components: hindi\medium; Flags: ignoreversion recursesubdirs
Source: "{#Models}\whisper-hindi-large-v2\*"; DestDir: "{app}\models\whisper-hindi-large-v2"; Components: hindi\large; Flags: ignoreversion recursesubdirs
Source: "{#Models}\opus-mt-hi-en\*"; DestDir: "{app}\models\opus-mt-hi-en"; Components: hindi\translator; Flags: ignoreversion recursesubdirs

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

// Main setup records its folder in its uninstall key (per-user first, then all-users).
function FindMainAppDir(var Dir: String): Boolean;
var
  Key: String;
begin
  Key := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MainAppId}_is1';
  Result := RegQueryStringValue(HKCU, Key, 'InstallLocation', Dir) or
            RegQueryStringValue(HKLM, Key, 'InstallLocation', Dir);
  if Result then
    Result := FileExists(AddBackslash(Dir) + 'WhisperWriter.exe');
end;

function MainAppDir(Param: String): String;
begin
  if not FindMainAppDir(Result) then
    Result := ExpandConstant('{localappdata}\Programs\WhisperWriter');
end;

function InitializeSetup(): Boolean;
var
  Dir: String;
begin
  Result := FindMainAppDir(Dir);
  if Result then
    CloseWhisperWriter()
  else
    SuppressibleMsgBox('WhisperWriter is not installed. Run WhisperWriter_Setup first, then this add-on.',
                       mbError, MB_OK, IDOK);
end;
