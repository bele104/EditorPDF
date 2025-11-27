Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' Pasta onde está o VBS
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Caminho do Python embutido
pythonPath = currentDir & "\assets\python-3.11.9-embed-amd64\pythonw.exe"

' Script Python principal
scriptPath = currentDir & "\src\main.py"

' Executa o Python embutido sem mostrar console
shell.Run """" & currentDir & "\run_python.bat""", 0, False

