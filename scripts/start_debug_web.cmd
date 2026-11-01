@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_debug_web.ps1"
if errorlevel 1 pause
