$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$python = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run .\scripts\install.ps1 first.' }
$env:VOXCPM_HOME = 'D:\Desktop\VoxCPM2'
$env:VOXCPM_URL = 'http://127.0.0.1:8808'
$env:SOULX_HOME = 'D:\Desktop\SoulX-Singer'
$env:FFMPEG = 'D:\Desktop\VoxCPM2\tools\ffmpeg\bin\ffmpeg.exe'
& $python (Join-Path $repo 'scripts\run_debug_web.py') --host 127.0.0.1 --port 8810
