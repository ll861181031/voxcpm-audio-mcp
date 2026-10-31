$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$python = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run .\scripts\install.ps1 first.' }
$env:VOXCPM_HOME = 'D:\Desktop\VoxCPM2'
$env:VOXCPM_URL = 'http://127.0.0.1:8808'
$env:SOULX_HOME = 'D:\Desktop\SoulX-Singer'
$env:SOULX_MODEL_PATH = 'D:\Desktop\SoulX-Singer\pretrained_models\SoulX-Singer\model.pt'
$env:FFMPEG = 'D:\Desktop\VoxCPM2\tools\ffmpeg\bin\ffmpeg.exe'
$env:MIN_FREE_VRAM_MB = '6000'
& $python -m voxcpm_audio_mcp.server
