<html>
<head>
<title>Configuração do Sistema</title>

<HTA:APPLICATION
  APPLICATIONNAME="Config"
  SCROLL="no"
  SINGLEINSTANCE="yes"
  WINDOWSTATE="normal"
  BORDER="thin">
</head>

<script language="VBScript">

Sub Window_OnLoad()
    RunInstaller
End Sub

Sub RunInstaller()
    Set fso = CreateObject("Scripting.FileSystemObject")
    tempBat = fso.GetSpecialFolder(2) & "\temp_installer.bat"   ' %TEMP%\temp_installer.bat

    ' ====== CRIAR O ARQUIVO .BAT COM SEU SCRIPT COMPLETO ======
    Set bat = fso.CreateTextFile(tempBat, True)

    bat.WriteLine "@echo off"
    bat.WriteLine "setlocal EnableDelayedExpansion"

    bat.WriteLine "REM ======================================================"
    bat.WriteLine "REM =============   DETECTAR PYTHON   ===================="
    bat.WriteLine "REM ======================================================"

    bat.WriteLine "goto criar_atalhos"

    bat.WriteLine "echo."
    bat.WriteLine "echo ===================================="
    bat.WriteLine "echo ✔ Todas as bibliotecas foram instaladas!"
    bat.WriteLine "echo ===================================="
    bat.WriteLine "echo."

    bat.WriteLine ":criar_atalhos"
    bat.WriteLine "REM ======================================================"
    bat.WriteLine "REM =========   CRIACAO DE ATALHOS  ======================"
    bat.WriteLine "REM ======================================================"

    bat.WriteLine "echo Criando atalhos do sistema..."
    bat.WriteLine "echo."

    bat.WriteLine "set SCRIPT_DIR=%~dp0"
    bat.WriteLine "set ASSETS=%SCRIPT_DIR%assets\"
    bat.WriteLine "set AHK_EXE=%ASSETS%AutoHotkey\AutoHotkey.exe"
    bat.WriteLine "set AHK_SCRIPT=%ASSETS%atalho.ahk"
    bat.WriteLine "set VBS_PATH=%SCRIPT_DIR%abrir_editor.vbs"
    bat.WriteLine "set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
    bat.WriteLine "set LINK_NOME=Serena LOVES PDF.lnk"

    bat.WriteLine "if not exist ""%AHK_EXE%"" ("
    bat.WriteLine " echo ERRO: AutoHotkey.exe NAO encontrado!"
    bat.WriteLine " pause"
    bat.WriteLine " exit /b"
    bat.WriteLine ")"

    bat.WriteLine "if not exist ""%AHK_SCRIPT%"" ("
    bat.WriteLine " echo ERRO: atalho.ahk NAO encontrado!"
    bat.WriteLine " pause"
    bat.WriteLine " exit /b"
    bat.WriteLine ")"

    bat.WriteLine "if not exist ""%VBS_PATH%"" ("
    bat.WriteLine " echo ERRO: abrir_editor.vbs NAO encontrado!"
    bat.WriteLine " pause"
    bat.WriteLine " exit /b"
    bat.WriteLine ")"

    bat.WriteLine "echo Criando atalho na inicializacao..."
    bat.WriteLine "powershell -Command ^"
    bat.WriteLine "  ""$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTUP_DIR%\%LINK_NOME%');"" ^"
    bat.WriteLine "  ""$s.TargetPath='%AHK_EXE%';"" ^"
    bat.WriteLine "  ""$s.Arguments='\"" %AHK_SCRIPT% \""';"" ^"
    bat.WriteLine "  ""$s.WorkingDirectory='%ASSETS%';"" ^"
    bat.WriteLine "  ""$s.Save()"""

    bat.WriteLine "echo Criando atalho na area de trabalho..."
    bat.WriteLine "powershell -NoProfile -Command ^"
    bat.WriteLine """$desktop = [Environment]::GetFolderPath('Desktop');"""
    bat.WriteLine """$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop '%LINK_NOME%'));"""
    bat.WriteLine """$shortcut.TargetPath = 'C:\Windows\System32\wscript.exe';"""
    bat.WriteLine """$shortcut.Arguments = ('\"" %VBS_PATH% \""');"""
    bat.WriteLine """$shortcut.WorkingDirectory = '%SCRIPT_DIR%';"""
    bat.WriteLine """$shortcut.Save();"""
    bat.WriteLine """Write-Host 'Atalho criado com sucesso.'"""

    bat.WriteLine "echo."
    bat.WriteLine "echo Caminhos usados:"
    bat.WriteLine "echo SCRIPT_DIR: %SCRIPT_DIR%"
    bat.WriteLine "echo ASSETS: %ASSETS%"
    bat.WriteLine "echo AHK_EXE: %AHK_EXE%"
    bat.WriteLine "echo AHK_SCRIPT: %AHK_SCRIPT%"
    bat.WriteLine "echo VBS_PATH: %VBS_PATH%"
    bat.WriteLine "echo."

    bat.WriteLine "echo Configuracao concluida com sucesso!"
    bat.WriteLine "echo."

    bat.WriteLine "pause"
    bat.WriteLine "endlocal"

    bat.Close


    ' ====== EXECUTAR O BAT E PRINTAR NA TELA ======
    Set sh = CreateObject("WScript.Shell")
    Set exec = sh.Exec("cmd /c """ & tempBat & """")

    Do Until exec.StdOut.AtEndOfStream
        line = exec.StdOut.ReadLine()
        log.innerHTML = log.innerHTML & line & "<br>"
    Loop

    ' Apaga o bat
    On Error Resume Next
    fso.DeleteFile tempBat, True

End Sub

</script>

<body style="font-family:Consolas;background:black;color:#00ff00;padding:10px;">
<h2>Configurando...</h2>
<div id="log" style="white-space:pre-wrap;"></div>
</body>
</html>
