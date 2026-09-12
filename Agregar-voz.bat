@echo off
REM Genera TU voz para las palabras nuevas que agregaste en el tablero.
REM Requiere el entorno con GPU (Chatterbox). Corre en ..\Voz-Lab\.venv_chatter.
cd /d "%~dp0"
set "PY=..\Voz-Lab\.venv_chatter\Scripts\python.exe"
if not exist "%PY%" (
  echo No encuentro el entorno de voz (..\Voz-Lab\.venv_chatter). No puedo generar tu voz aqui.
  pause & exit /b 1
)
echo Generando tu voz para las palabras nuevas... (puede tardar un poco)
"%PY%" agregar_palabras.py
echo.
echo Listo. Reabre el tablero (Tablero.bat) para escuchar las nuevas con tu voz.
pause
