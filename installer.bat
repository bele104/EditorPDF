@echo off
title Verificando Python, Instalando Bibliotecas e Criando Atalhos
setlocal

echo ===================================================
echo  Iniciando o processo de instalacao...
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
echo  Python NAO esta instalado!
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
REM =========   CRIACAO DE ATALHOS  ======================
REM ======================================================

echo Criando atalhos do sistema...
echo.

:: Caminhos
set SCRIPT_DIR=%~dp0
set ASSETS=%SCRIPT_DIR%assets\
set AHK_EXE=%ASSETS%AutoHotkey\AutoHotkey.exe
set AHK_SCRIPT=%ASSETS%atalho.ahk
set VBS_PATH=%SCRIPT_DIR%abrir_editor.vbs
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set LINK_NOME=Serena LOVE PDF.lnk

:: Verifica se o executável e o script existem
if not exist "%AHK_EXE%" (
    echo ERRO: AutoHotkey.exe NAO encontrado em:
    echo %AHK_EXE%
    pause
    exit /b
)

if not exist "%AHK_SCRIPT%" (
    echo ERRO: Script atalho.ahk NAO encontrado!
    pause
    exit /b
)

if not exist "%VBS_PATH%" (
    echo ERRO: abrir_editor.vbs NAO encontrado!
    pause
    exit /b
)

:: Criar atalho na inicialização
echo  Criando atalho para iniciar com o Windows...
powershell -Command ^
  "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTUP_DIR%\%LINK_NOME%');" ^
  "$s.TargetPath='%AHK_EXE%';" ^
  "$s.Arguments='\"%AHK_SCRIPT%\"';" ^
  "$s.WorkingDirectory='%ASSETS%';" ^
  "$s.Save()"
echo  Atalho criado no Startup.


:: Criar atalho na área de trabalho
echo Criando atalho na area de trabalho...
powershell -NoProfile -Command ^
"$desktop = [Environment]::GetFolderPath('Desktop'); ^
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop '%LINK_NOME%')); ^
$shortcut.TargetPath = 'C:\Windows\System32\wscript.exe'; ^
$shortcut.Arguments = ('\"%VBS_PATH%\"'); ^
$shortcut.WorkingDirectory = '%SCRIPT_DIR%'; ^
$shortcut.Save(); ^
Write-Host 'Atalho criado com sucesso.'"


echo.
echo Caminhos usados:
echo SCRIPT_DIR: %SCRIPT_DIR%
echo ASSETS: %ASSETS%
echo AHK_EXE: %AHK_EXE%
echo AHK_SCRIPT: %AHK_SCRIPT%
echo VBS_PATH: %VBS_PATH%
echo.

echo  Configuracao concluida com sucesso!
echo.

pause
endlocal
exit /b
