// GPU check -- included by WhisperWriter.iss [Code] and by gpu_check_test.iss.
// The app runs on any PC: it uses an NVIDIA GPU when it can, else the CPU. This only
// tells the user which one they will get, and unticks the large model when the GPU
// cannot run it well. Rules (CTranslate2 4.x, CUDA 12 build):
//   driver >= 527.41 (CUDA 12 minimum on Windows)
//   compute capability >= 7.0 for the fast int8_float16 mode
//   about 3 GB of video memory for the large model
var
  GpuOk: Boolean;
  GpuPrimeUnticked: Boolean;

function NextField(var S: String): String;
var
  P: Integer;
begin
  P := Pos(',', S);
  if P = 0 then
  begin
    Result := Trim(S);
    S := '';
  end else
  begin
    Result := Trim(Copy(S, 1, P - 1));
    S := Copy(S, P + 1, Length(S));
  end;
end;

// "591.86" -> 59186 (Scale 100), "8.9" -> 89 (Scale 10).
function VersionNumber(V: String; Scale: Integer): Integer;
var
  P: Integer;
begin
  P := Pos('.', V);
  if P = 0 then
    Result := StrToIntDef(V, 0) * Scale
  else
    Result := StrToIntDef(Copy(V, 1, P - 1), 0) * Scale + StrToIntDef(Copy(V, P + 1, 2), 0);
end;

function FindNvidiaSmi(): String;
begin
  Result := ExpandConstant('{sysnative}\nvidia-smi.exe');  // setup is 32-bit: {sys} would be SysWOW64
  if not FileExists(Result) then
    Result := ExpandConstant('{commonpf64}\NVIDIA Corporation\NVSMI\nvidia-smi.exe');
  if not FileExists(Result) then
    Result := '';
end;

// Line = "name, driver, compute_cap, memory MiB" as printed by nvidia-smi. Sets GpuOk.
function ClassifyGpu(Line: String): String;
var
  Name, Drv, Cap, Mem: String;
  DrvN, CapN, MemN: Integer;
begin
  GpuOk := False;
  Name := NextField(Line);
  Drv := NextField(Line);
  Cap := NextField(Line);
  Mem := NextField(Line);
  DrvN := VersionNumber(Drv, 100);
  CapN := VersionNumber(Cap, 10);
  MemN := StrToIntDef(Mem, 0);
  Log(Format('GPU check raw: name=%s driver=%s compute=%s memMiB=%s', [Name, Drv, Cap, Mem]));

  if DrvN < 52741 then
    Result := 'Found: ' + Name + ' (driver ' + Drv + ').' + #13#10 + #13#10 +
              'The driver is too old for WhisperWriter (it needs 527.41 or newer), so it will run on the CPU.' + #13#10 +
              'Update the driver to use the GPU: https://www.nvidia.com/Download/index.aspx'
  else if CapN < 70 then
    Result := 'Found: ' + Name + ' (driver ' + Drv + ', compute ' + Cap + ').' + #13#10 + #13#10 +
              'This card is older than WhisperWriter''s fast GPU mode (it needs compute 7.0: GTX 16xx / RTX 20xx or newer). ' +
              'It may run slowly on the GPU or use the CPU instead.'
  else if (MemN > 0) and (MemN < 3000) then
    Result := 'Found: ' + Name + ' (' + Mem + ' MB video memory).' + #13#10 + #13#10 +
              'The GPU works, but it has less than 3 GB of memory. The Prime (large) model may not fit; ' +
              'Apex (medium) will run on the GPU.'
  else
  begin
    GpuOk := True;
    Result := 'Found: ' + Name + ' (driver ' + Drv + ', ' + Mem + ' MB video memory).' + #13#10 + #13#10 +
              'Your GPU is compatible. WhisperWriter will run on the GPU, and the Prime (large) model will be fast.';
  end;
end;

function CheckGpu(): String;
var
  Smi, OutFile: String;
  Lines: TArrayOfString;
  Code: Integer;
begin
  GpuOk := False;
  Smi := FindNvidiaSmi();
  if Smi = '' then
  begin
    if FileExists(ExpandConstant('{sysnative}\nvcuda.dll')) then
    begin
      GpuOk := True;  // the app itself will try CUDA; do not untick Prime on a guess
      Result := 'An NVIDIA driver is installed, but setup could not read the card details.' + #13#10 +
                'WhisperWriter will try the GPU and use the CPU if the GPU does not work.';
    end
    else
      Result := 'No NVIDIA graphics card found.' + #13#10 +
                'WhisperWriter will run on the CPU. It works, but the Prime (large) model will be slow, ' +
                'so it is unticked on the next pages. Apex (medium) is the better choice here.';
    Exit;
  end;

  OutFile := ExpandConstant('{tmp}\gpu.txt');
  Exec(ExpandConstant('{cmd}'), '/C ""' + Smi + '" --query-gpu=name,driver_version,compute_cap,memory.total ' +
       '--format=csv,noheader,nounits > "' + OutFile + '" 2>&1"', '', SW_HIDE, ewWaitUntilTerminated, Code);
  if (Code <> 0) or not LoadStringsFromFile(OutFile, Lines) or (GetArrayLength(Lines) = 0) then
  begin
    Result := 'An NVIDIA card was found, but its driver did not answer the check (it may be very old).' + #13#10 +
              'WhisperWriter will try the GPU and use the CPU if it does not work. ' +
              'Updating the driver is recommended: https://www.nvidia.com/Download/index.aspx';
    Exit;
  end;
  Result := ClassifyGpu(Lines[0]);
end;
