@echo off
:: AIOS: Ouroboros — Safe Mode Launcher (Windows)
:: ================================================
:: Run this if the game crashes on normal startup.
:: Forces: windowed 1280×720, Low graphics preset, no camera shake.
::
:: Usage: double-click this file, or right-click → Run as administrator
::        if you have UAC issues with write access to Saved/.

setlocal

:: Find the game executable next to this script
set "SCRIPT_DIR=%~dp0"
set "EXE=%SCRIPT_DIR%Symbiont.exe"

if not exist "%EXE%" (
    echo ERROR: Symbiont.exe not found next to this script.
    echo Expected: %EXE%
    pause
    exit /b 1
)

echo Launching AIOS in Safe Mode...
echo   - Windowed 1280x720
echo   - Low graphics preset
echo   - No camera shake
echo.

start "" "%EXE%" ^
    -safemode ^
    -windowed ^
    -ResX=1280 -ResY=720 ^
    -nosplash

exit /b 0
