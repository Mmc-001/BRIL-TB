Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
currentFolder = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = currentFolder
shell.Run "python scan_threshold.pyw", 0