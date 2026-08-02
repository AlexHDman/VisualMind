@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0prototype\gui_app.py"
) else (
    py -3.12 "%~dp0prototype\gui_app.py"
)

if errorlevel 1 (
    echo.
    echo [VisualMind] GUI stopped with an error.
    echo Run install_visualmind_gui.bat if PySide6 is not installed.
    pause
    exit /b 1
)
