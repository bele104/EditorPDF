Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' Pasta onde o VBS está
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Caminho do AutoHotkey portátil
ahkExe = currentDir & "\AutoHotkey\AutoHotkey.exe"
ahkScript = currentDir & "\atalho.ahk"

' Inicia o AutoHotkey carregando o atalho
If fso.FileExists(ahkExe) And fso.FileExists(ahkScript) Then
    shell.Run """" & ahkExe & """ """ & ahkScript & """", 0, False
End If
