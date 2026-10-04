Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Delay only when launched with an argument (used by the Startup shortcut)
If WScript.Arguments.Count > 0 Then WScript.Sleep 30000

' Get the directory where this VBS file is located (dynamic path)
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Build path to the batch file in the same directory
batchFilePath = scriptDir & "\whisper-writer.bat"

' Run the batch file silently (0 = hidden window)
WshShell.Run Chr(34) & batchFilePath & Chr(34), 0, False

Set fso = Nothing
Set WshShell = Nothing
