<#
.SYNOPSIS
  Prepare the demo watched folder and launch the Ngabo Connect edge client.

  One-time human setup is allowed BEFORE recording. After launch, the ONLY
  workflow trigger is dropping a synthetic .csv export into the watched folder.
#>
[CmdletBinding()]
param(
    [string]$WatchDir = "$env:USERPROFILE\NgaboDemo\Exports"
)
New-Item -ItemType Directory -Force -Path $WatchDir | Out-Null
Write-Host "Watched folder: $WatchDir"
Write-Host "Drop demo/connect/synthetic_gulu_surveillance_export.csv into it."
Write-Host "Ngabo Connect edge client is a python module; launch with:"
Write-Host "  python -m ngabo.infrastructure.connect.edge --watch-dir `"$WatchDir`""
