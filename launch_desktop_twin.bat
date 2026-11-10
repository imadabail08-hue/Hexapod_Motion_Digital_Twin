@echo off
title HEXAPOD MOTION DIGITAL TWIN - HEX-01 Industrial Desktop Launcher

:: Fermer silencieusement toute ancienne instance de l'application
taskkill /F /IM HexapodDigitalTwin.exe >nul 2>&1
taskkill /F /IM electron.exe >nul 2>&1

:: Demarrer la passerelle telemetrie ESP32 en arriere-plan (sans fenetre console bloquante)
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0serial_bridge.py"

:: Petite pause de 1 seconde
ping 127.0.0.1 -n 2 >nul

:: Lancer le Digital Twin 3D Desktop natif
cd /d "%~dp0hexapod-digital-twin\threejs-dashboard"
start "" "release\win-unpacked\HexapodDigitalTwin.exe"

exit
