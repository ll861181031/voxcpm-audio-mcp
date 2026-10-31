param([string]$PluginRoot)
$ErrorActionPreference = 'Stop'

$plugin = [IO.Path]::GetFullPath($PluginRoot)
$data = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\Plugins\voxcpm-audio-mcp'
$venv = Join-Path $data 'venv'
$logs = Join-Path $data 'logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null

if (-not (Test-Path -LiteralPath (Join-Path $venv 'Scripts\python.exe'))) {
    uv venv --python 3.12 $venv
}

uv pip install --python (Join-Path $venv 'Scripts\python.exe') -e $plugin
