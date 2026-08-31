<#
.SYNOPSIS
  Idempotent Ngabo Connect deadline demo bootstrap (Windows-first).

.DESCRIPTION
  Configures the GCP project for the synthetic zero-touch lab-export demo and
  deploys the ngabo-core / ngabo-connect-intake / ngabo-demo-receiver services.
  Run this once on a machine with authenticated gcloud and Docker auth.

  Prerequisites:
    - gcloud configured
    - project ngabo-amr-2026 (us-central1)
    - Artifact Registry repo "ngabo-artifacts"
#>
[CmdletBinding()]
param(
    [string]$Project = "ngabo-amr-2026",
    [string]$Region = "us-central1",
    [string]$ArtifactRepo = "ngabo-artifacts",
    [string]$PushSa = "ngabo-pubsub-push",
    [string]$IntakeSa = "ngabo-connect-intake",
    [string]$ReceiverSa = "ngabo-demo-receiver",
    [string]$DemoBucket = "ngabo-connect-demo-raw",
    [string]$DemoTopic = "ngabo-connect-batches",
    [string]$DemoSubscription = "ngabo-connect-core",
    [string]$CoreUrl = "",
    [string]$IntakeUrl = "",
    [string]$ReceiverUrl = ""
)
$ErrorActionPreference = "Stop"
function Step($msg) { Write-Host "== $msg ==" }
function Run($args) { & gcloud @args; if ($LASTEXITCODE -ne 0) { throw "gcloud failed: $args" } }

Step "Set project/region"
Run config set project $Project
Run config set run/region $Region

Step "Enable APIs"
foreach ($api in @("run.googleapis.com","cloudbuild.googleapis.com","secretmanager.googleapis.com","storage.googleapis.com","firestore.googleapis.com","pubsub.googleapis.com","artifactregistry.googleapis.com","iamcredentials.googleapis.com")) {
  Run services enable $api --project $Project
}

Step "Create raw GCS bucket (if absent)"
$bucketExists = gcloud storage buckets describe "gs://$DemoBucket" --project $Project 2>$null
if (-not $bucketExists) {
  Run storage buckets create "gs://$DemoBucket" --project $Project --location $Region --uniform-bucket-level-access
}

Step "Create Pub/Sub topic (if absent)"
$topic = gcloud pubsub topics describe "projects/$Project/topics/$DemoTopic" 2>$null
if (-not $topic) {
  Run pubsub topics create $DemoTopic --project $Project
}

Step "Create Pub/Sub push service account"
Run iam service-accounts create $PushSa --project $Project --display-name "Ngabo Connect Pub/Sub push identity"

Step "Grant run.invoker on ngabo-core to the push identity"
Run run services add-iam-policy-binding ngabo-core --project $Project --region $Region `
  --member "serviceAccount:$PushSa@$Project.iam.gserviceaccount.com" --role "roles/run.invoker"

Step "Create/update the push subscription with OIDC identity + private core endpoint"
if (-not $CoreUrl) { throw "CoreUrl must be provided to create the push subscription" }
$subscription = gcloud pubsub subscriptions describe "projects/$Project/subscriptions/$DemoSubscription" 2>$null
if ($subscription) {
  Run pubsub subscriptions update $DemoSubscription --project $Project `
    --push-endpoint "$CoreUrl/surveillance" `
    --push-auth-service-account "$PushSa@$Project.iam.gserviceaccount.com" `
    --push-auth-token-audience "$CoreUrl"
} else {
  Run pubsub subscriptions create $DemoSubscription --project $Project `
    --topic $DemoTopic `
    --push-endpoint "$CoreUrl/surveillance" `
    --push-auth-service-account "$PushSa@$Project.iam.gserviceaccount.com" `
    --push-auth-token-audience "$CoreUrl"
}

Step "Deploy ngabo-core (existing image path — rebuild your container first)"
if ($ReceiverUrl -and $DemoBucket) {
  Run run deploy ngabo-core --project $Project --region $Region `
    --image "$Region-docker.pkg.dev/$Project/$ArtifactRepo/ngabo-core:latest" `
    --set-env-vars "GEMINI_API_KEY=$env:GEMINI_API_KEY,NGABO_RECEIVER_URL=$ReceiverUrl,NGABO_GCS_BUCKET=$DemoBucket" `
    --service-account "$IntakeSa@$Project.iam.gserviceaccount.com"
} else {
  Write-Host "Skipping ngabo-core deploy (provide ReceiverUrl/GCS bucket for full config)"
}

Step "Note: ngabo-connect-intake and ngabo-demo-receiver deploy"
if ($IntakeUrl) { Write-Host "Intake configured at $IntakeUrl" }
if ($ReceiverUrl) { Write-Host "Receiver configured at $ReceiverUrl" }

Step "Print URLs/revisions"
Run run services describe ngabo-core --project $Project --region $Region --format "value(status.url,status.latestReadyRevisionName)" 2>$null
if ($IntakeUrl) { Write-Host "Intake: $IntakeUrl" }
if ($ReceiverUrl) { Write-Host "Receiver: $ReceiverUrl" }

Write-Host "DONE. Trigger the demo by dropping an export into the watched folder."
