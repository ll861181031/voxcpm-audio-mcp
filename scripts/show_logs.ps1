$ErrorActionPreference = 'Stop'
$logDir = if ($env:MCP_LOG_DIR) { $env:MCP_LOG_DIR } else { Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\Plugins\voxcpm-audio-mcp\logs' }
$path = Join-Path $logDir 'mcp.jsonl'
if (-not (Test-Path -LiteralPath $path)) { Write-Host "No MCP log found: $path"; exit 0 }
Get-Content -LiteralPath $path -Tail 50
