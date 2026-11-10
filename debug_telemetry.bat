@echo off
title Debug ESP32 Telemetry Stream - COM8
echo ==============================================================================
echo   FLUX TELEMETRIE SERIE ESP32 (COM8 - 115200 BAUD)
echo ==============================================================================
echo Appuyez sur Ctrl+C pour arreter.
echo.
"%~dp0.venv\Scripts\python.exe" -u "%~dp0serial_bridge.py"
pause
