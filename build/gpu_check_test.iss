; Test harness for gpu_check.iss (no files, no install). Build + run:
;   ISCC build\gpu_check_test.iss  then  build\temp\gpu_check_test.exe /VERYSILENT
; Writes build\temp\gpu_check_test.txt and exits without installing anything.
[Setup]
AppName=GpuCheckTest
AppVersion=1
CreateAppDir=no
Uninstallable=no
PrivilegesRequired=lowest
OutputDir=temp
OutputBaseFilename=gpu_check_test

[Code]
#include "gpu_check.iss"

var
  Report: TArrayOfString;

procedure Add(Title, Msg: String);
var
  N: Integer;
begin
  N := GetArrayLength(Report);
  SetArrayLength(Report, N + 1);
  if GpuOk then
    Report[N] := '[' + Title + '] GpuOk=True  | ' + Msg
  else
    Report[N] := '[' + Title + '] GpuOk=False | ' + Msg;
end;

function InitializeSetup(): Boolean;
begin
  Add('this PC (real nvidia-smi)', CheckGpu());
  Add('fake modern', ClassifyGpu('NVIDIA GeForce RTX 3060, 560.94, 8.6, 12288'));
  Add('fake old driver', ClassifyGpu('NVIDIA GeForce RTX 2060, 472.12, 7.5, 6144'));
  Add('fake old card', ClassifyGpu('NVIDIA GeForce GTX 1060 6GB, 560.94, 6.1, 6144'));
  Add('fake low memory', ClassifyGpu('NVIDIA GeForce GTX 1650, 560.94, 7.5, 2048'));
  Add('fake edge driver 527.41', ClassifyGpu('NVIDIA T400, 527.41, 7.5, 4096'));
  SaveStringsToUTF8File(ExpandConstant('{src}\gpu_check_test.txt'), Report, False);
  Result := False;  // never install anything
end;
