; atalho.ahk - Hotkey para abrir Editor PDF
#SingleInstance Force

; Ctrl+Alt+F → Abrir Editor PDF
^!p::
Run, "%A_ScriptDir%\..\abrir_editor.vbs"

return

