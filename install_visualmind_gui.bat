@echo off
setlocal
cd /d "%~dp0"

echo [VisualMind] Preparing local Python 3.12 environment...
if not exist "%~dp0.venv\Scripts\python.exe" (
    py -3.12 -m venv "%~dp0.venv"
    if errorlevel 1 goto :error
)

echo [VisualMind] Installing GUI dependencies...
"%~dp0.venv\Scripts\python.exe" -m pip install -r "%~dp0prototype\requirements-gui.txt"
if errorlevel 1 goto :error

echo.
echo [VisualMind] Installation completed successfully.
echo Run run_visualmind_gui.bat to start VisualMind Studio.
pause
exit /b 0

:error
echo.
echo [VisualMind] Installation failed. Review the messages above.
pause
exit /b 1
