@echo off
setlocal

set "PLUGIN_ROOT=%~dp0.."
if defined PLUGIN_DATA (
    set "DATA_ROOT=%PLUGIN_DATA%"
) else (
    set "DATA_ROOT=%LOCALAPPDATA%\OpenAI\Codex\Plugins\voxcpm-audio-mcp"
)
set "LOG_DIR=%DATA_ROOT%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ensure_mcp.ps1" -PluginRoot "%PLUGIN_ROOT%" >> "%LOG_DIR%\install.log" 2>&1
if errorlevel 1 exit /b 1

set "PYTHON=%DATA_ROOT%\venv\Scripts\python.exe"
set "PYTHONUTF8=1"
"%PYTHON%" -m voxcpm_audio_mcp.server
