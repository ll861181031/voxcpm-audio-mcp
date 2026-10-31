param(
    [int]$RetentionDays = 30,
    [int]$KeepLast = 200,
    [switch]$Clean
)
$ErrorActionPreference = 'Stop'
$dir = if ($env:AUDIO_OUTPUT_DIR) { $env:AUDIO_OUTPUT_DIR } else { Join-Path $HOME 'Music\VoxCPM-MCP' }
if (-not (Test-Path -LiteralPath $dir)) { Write-Host "Output directory does not exist: $dir"; exit 0 }

$files = Get-ChildItem -LiteralPath $dir -File -Include *.wav,*.mp3 -Recurse |
    Sort-Object LastWriteTime -Descending
$stale = $files | Select-Object -Skip $KeepLast | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) }
$size = ($files | Measure-Object Length -Sum).Sum

Write-Host ("Output directory: {0}" -f $dir)
Write-Host ("Files: {0}" -f $files.Count)
Write-Host ("Total size MB: {0:N2}" -f ($size / 1MB))
Write-Host ("Clean candidates: {0}" -f $stale.Count)

if ($Clean) {
    foreach ($file in $stale) {
        Remove-Item -LiteralPath $file.FullName
    }
    Write-Host "Cleanup complete."
} else {
    Write-Host "Dry run only. Add -Clean to delete the listed files."
}
