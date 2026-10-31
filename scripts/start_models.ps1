$ErrorActionPreference = 'Stop'
$voxcpmHome = if ($env:VOXCPM_HOME) { $env:VOXCPM_HOME } else { 'D:\Desktop\VoxCPM2' }
$soulxHome = if ($env:SOULX_HOME) { $env:SOULX_HOME } else { 'D:\Desktop\SoulX-Singer' }
$start = Join-Path $voxcpmHome 'Start-VoxCPM.ps1'

if (-not (Test-Path -LiteralPath $start)) { throw "VoxCPM2 start script not found: $start" }
& $start -NoBrowser

$required = @(
    (Join-Path $soulxHome 'pretrained_models\SoulX-Singer\model.pt'),
    (Join-Path $soulxHome 'soulxsinger\config\soulxsinger.yaml'),
    (Join-Path $soulxHome 'soulxsinger\utils\phoneme\phone_set.json')
)
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) { throw "SoulX-Singer file not found: $path" }
}

Write-Host 'VoxCPM2 is running and SoulX-Singer inference files are present.'
