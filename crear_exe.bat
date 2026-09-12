@echo off
REM Genera Tablero.exe (portatil, sin consola, con icono).
REM Version portatil: dice las 200 palabras en TU voz (clips Chatterbox incluidos en
REM voz_cache) + voz del sistema (SAPI) para palabras nuevas. La voz en vivo que dice
REM CUALQUIER cosa necesita GPU -> usar el .py con Tablero-mi-voz.bat. Por eso aqui se
REM EXCLUYEN los modelos pesados (torch/chatterbox/whisper) y los modulos Qt grandes
REM que no usamos (WebEngine, Quick, Qml...) para que el .exe sea liviano (~150 MB).
cd /d "%~dp0"
set "PYDIR=..\.venv_face\Scripts"
if not exist "%PYDIR%\python.exe" set "PYDIR=.venv\Scripts"
if not exist "%PYDIR%\pyinstaller.exe" (
  echo Instalando PyInstaller...
  "%PYDIR%\python.exe" -m pip install pyinstaller
)
"%PYDIR%\pyinstaller.exe" --noconfirm --clean --windowed --onedir ^
  --name "Tablero" --icon "recursos\icono.ico" ^
  --add-data "voz_cache;voz_cache" ^
  --add-data "vocabulario.json;." ^
  --exclude-module torch --exclude-module torchaudio --exclude-module chatterbox ^
  --exclude-module whisper --exclude-module transformers --exclude-module build_voz ^
  --exclude-module soundfile --exclude-module sounddevice --exclude-module librosa ^
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.QtWebEngineQuick --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtQml --exclude-module PySide6.Qt3DCore ^
  --exclude-module PySide6.QtMultimedia --exclude-module PySide6.QtPdf ^
  --exclude-module PySide6.QtWebChannel --exclude-module PySide6.QtDesigner ^
  tablero_comunicacion.py
echo.
echo Listo: dist\Tablero\Tablero.exe
pause
