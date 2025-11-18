@echo off
title Verificando Python, Instalando Bibliotecas e Criando Atalhos
setlocal

echo ===================================================
echo  Iniciando o processo de instalao...
echo ===================================================

REM ======================================================
REM =============   DETECTAR PYTHON   ====================
REM ======================================================

python --version >nul 2>&1
if %errorlevel%==0 (
    echo Python encontrado!
    goto instalar
)

python3 --version >nul 2>&1
if %errorlevel%==0 (
    echo Python3 encontrado!
    goto instalar
)

echo.
echo =============================
echo  Python NÃO está instalado!
echo Instale o Python para continuar.
echo =============================
echo.
pause
exit /b


REM ======================================================
REM =========== INSTALAR BIBLIOTECAS  ====================
REM ======================================================
:instalar
echo.
echo Instalando bibliotecas...
echo.

python -m pip install --upgrade pip
python -m pip install PyQt6 PyQt6-sip PyMuPDF pandas matplotlib pdfkit reportlab Pillow python-docx docx2pdf

echo.
echo ====================================
echo ✔ Todas as bibliotecas foram instaladas!
echo ====================================
echo.


REM ======================================================
REM =========   CRIAÇÃO DE ATALHOS  ======================
REM ======================================================

echo Criando atalhos do sistema...
echo.

:: Caminhos
set SCRIPT_DIR=%~dp0
set AHK_EXE=%SCRIPT_DIR%AutoHotkey\AutoHotkey.exe
set AHK_SCRIPT=%SCRIPT_DIR%atalho.ahk
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set DESKTOP_DIR=%USERPROFILE%\Desktop
set LINK_NOME=Serena LOVE PDF.lnk
set ICON_PATH=%SCRIPT_DIR%icone.ico

:: Verifica se o executável e o script existem
if not exist "%AHK_EXE%" (
    echo ERRO: AutoHotkey.exe NÃO encontrado em:
    echo %AHK_EXE%
    pause
    exit /b
)

if not exist "%AHK_SCRIPT%" (
    echo ERRO: Script atalho.ahk NÃO encontrado!
    pause
    exit /b
)

:: Comando final que precisa estar no atalho
set TARGET=%AHK_EXE% "%AHK_SCRIPT%"


:: Criar atalho na inicialização
echo  Criando atalho para iniciar com o Windows...
powershell -Command ^
  "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTUP_DIR%\%LINK_NOME%');" ^
  "$s.TargetPath='%AHK_EXE%';" ^
  "$s.Arguments='\"%AHK_SCRIPT%\"';" ^
  "$s.WorkingDirectory='%SCRIPT_DIR%';" ^
  "if (Test-Path '%ICON_PATH%') {$s.IconLocation='%ICON_PATH%';}" ^
  "$s.Save()"
echo  Atalho criado no Startup.


:: Criar atalho na área de trabalho
echo Criando atalho na área de trabalho...

if exist "%ICON_PATH%" (
    powershell -NoProfile -Command ^
    "$s = New-Object -ComObject WScript.Shell; ^
     $shortcut = $s.CreateShortcut('%DESKTOP_DIR%\%LINK_NOME%'); ^
     $shortcut.TargetPath = 'C:\Windows\System32\wscript.exe'; ^
     $shortcut.Arguments = '\"%SCRIPT_DIR%\abrir_editor.vbs\"'; ^
     $shortcut.WorkingDirectory = '%SCRIPT_DIR%'; ^
     $shortcut.IconLocation = '%ICON_PATH%'; ^
     $shortcut.Save()"

    echo Caminho procurado: "%ICON_PATH%"

)



echo.
echo  Configuração concluída com sucesso!
echo.

pause


