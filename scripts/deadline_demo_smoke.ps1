<#
.SYNOPSIS
  Non-destructive Ngabo Connect deadline demo health/infrastructure checks.
#>
[CmdletBinding()]
param(
    [string]$Project = "ngabo-amr-2026",
    [string]$Region = "us-central1"
)
$ErrorActionPreference = "Stop"
Run services list --project $Project --region $Region --format "table(status.url,status.latestReadyRevisionName)"
Write-Host "GCS raw bucket:"
gcloud storage buckets list --project $Project --filter "name:ngabo-connect-demo-raw" 2>$null
Write-Host "Pub/Sub push subscription:"
gcloud pubsub subscriptions describe ngabo-connect-core --project $Project --format "value(pushConfig.pushEndpoint,pushConfig.oidcToken.serviceAccountEmail)" 2>$null
Write-Host "SMOKE COMPLETE"
function Run($args) { & gcloud @args }
