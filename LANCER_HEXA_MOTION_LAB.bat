@echo off
title HEXA MOTION LAB - DIGITAL TWIN PROFESSIONNEL
cd /d "%~dp0"
echo ==============================================================================
echo    HEXA MOTION LAB - DIGITAL TWIN INDUSTRIEL POUR HEXAPODE
echo ==============================================================================
echo Lancement du serveur et ouverture automatique de l'interface...
".venv\Scripts\python.exe" launch_hexa_motion_lab.py
pause
