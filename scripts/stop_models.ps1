$ErrorActionPreference = 'Stop'
$voxcpmHome = if ($env:VOXCPM_HOME) { $env:VOXCPM_HOME } else { 'D:\Desktop\VoxCPM2' }
$stop = Join-Path $voxcpmHome 'Stop-VoxCPM.ps1'
if (-not (Test-Path -LiteralPath $stop)) { throw "VoxCPM2 stop script not found: $stop" }
& $stop
