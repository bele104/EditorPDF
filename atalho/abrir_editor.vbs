Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' Pasta onde está o VBS
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Script Python principal
scriptPath = currentDir & "\main.py"

' Executa Python instalado no sistema sem mostrar console
shell.Run "cmd /c start /B python """ & scriptPath & """", 0, False
