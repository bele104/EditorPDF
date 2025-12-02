Set oWS = WScript.CreateObject("WScript.Shell")
caminho = WScript.ScriptFullName
pasta = Left(caminho, InStrRev(caminho, "\"))

Set link = oWS.CreateShortcut(pasta & "Configurar Program.lnk")
link.TargetPath = pasta & "config.hta"
link.WorkingDirectory = pasta

' --- ICONE PERSONALIZADO ---
' Use um arquivo .ico dentro da mesma pasta:
link.IconLocation = pasta & "assets\icons\monitor-cog.ico"

link.Save
