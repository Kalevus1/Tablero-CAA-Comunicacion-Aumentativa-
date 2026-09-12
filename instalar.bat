@echo off
REM Crea un entorno virtual local (.venv) e instala PySide6.
cd /d "%~dp0"
if exist "..\.venv_face\Scripts\python.exe" (
  echo Se usara el entorno compartido ..\.venv_face  (ya tiene PySide6).
  pause & exit /b 0
)
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Listo. Ahora ejecuta Tablero.bat
pause
