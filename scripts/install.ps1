$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Set-Location -LiteralPath $repo
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    uv venv --python 3.12 .venv
}
uv pip install --python '.venv\Scripts\python.exe' -e '.[dev]'
Write-Host "Installed. Run .\scripts\run.ps1"
