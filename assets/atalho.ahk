; atalho.ahk - Hotkey para abrir Editor PDF
#SingleInstance Force

; Ctrl+Alt+P → Abrir Editor PDF
^!p::
Run, "%A_ScriptDir%\..\abrir_editor.hta"

return

