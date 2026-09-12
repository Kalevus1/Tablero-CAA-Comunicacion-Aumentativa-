@echo off
REM Tablero con TU VOZ EN VIVO (dice cualquier palabra o frase). Usa la GPU (Chatterbox).
REM Tarda unos segundos en cargar tu voz al abrir.
cd /d "%~dp0"
set "PY=..\Voz-Lab\.venv_chatter\Scripts\pythonw.exe"
if not exist "%PY%" (
  echo No encuentro el entorno de voz (..\Voz-Lab\.venv_chatter).
  echo Se abrira en modo basico. Para tu voz en vivo, revisa ese entorno.
  set "PY=..\.venv_face\Scripts\pythonw.exe"
)
start "" "%PY%" tablero_comunicacion.py
