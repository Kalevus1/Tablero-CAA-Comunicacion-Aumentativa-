@echo off
REM Lanza Mi Tablero (Dia 10) - version portatil: dice las 200 palabras en TU voz
REM (clips incluidos) + voz del sistema para el resto. Sin GPU. Para decir CUALQUIER
REM cosa en tu voz, usa Tablero-mi-voz.bat (necesita GPU).
cd /d "%~dp0"
set "PY=..\.venv_face\Scripts\pythonw.exe"
if not exist "%PY%" set "PY=.venv\Scripts\pythonw.exe"
if not exist "%PY%" (
  echo No encuentro el entorno. Ejecuta primero instalar.bat
  pause & exit /b 1
)
start "" "%PY%" tablero_comunicacion.py
