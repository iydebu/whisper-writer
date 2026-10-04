; Visual preview of the setup's GPU page (real check on this PC). Never installs.
;   ISCC build\gpu_page_preview.iss  then run build\temp\gpu_page_preview.exe
[Setup]
AppName=WhisperWriter
AppVersion=preview
CreateAppDir=no
Uninstallable=no
PrivilegesRequired=lowest
DisableWelcomePage=no
WizardStyle=modern
OutputDir=temp
OutputBaseFilename=gpu_page_preview
SetupIconFile=..\logo.ico

[Code]
#include "gpu_check.iss"

procedure InitializeWizard();
begin
  CreateOutputMsgPage(wpWelcome, 'Graphics card check',
    'Can WhisperWriter use your graphics card (GPU)?', CheckGpu());
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := PageID = wpWelcome;  // open straight on the GPU page
end;
