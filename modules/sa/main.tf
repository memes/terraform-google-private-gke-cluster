terraform {
  required_version = ">= 1.2"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.42"
    }
  }
}

resource "google_service_account" "sa" {
  project      = var.project_id
  account_id   = var.name
  display_name = coalesce(var.display_name, "Generated service account for GKE")
  description  = var.description
}

resource "google_project_iam_member" "roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer",
  ])
  project = var.project_id
  role    = each.value
  member  = google_service_account.sa.member
}

locals {
  gcr_buckets = var.repositories == null ? [] : [for name in var.repositories : format("%sartifacts.%s.appspot.com", try(regex("^((asia|eu|us).)gcr.io", name)[0], ""), regex("gcr.io/([^/]+)", name)[0]) if can(regex("^(?:(?:asia|eu|us).)?gcr.io", name))]
  ar_repos    = var.repositories == null ? {} : { for name in var.repositories : regex("^[^-]+-docker.pkg.dev/[^/]+/([^/]+)", name)[0] => { location = regex("^([^-]+)-docker", name)[0], project = regex("docker.pkg.dev/([^/]+)/", name)[0] } if can(regex("^[^-]+-docker.pkg.dev/[^/]+/[^/]+", name)) }
}

# For the unique set of GCR repos, assign objectViewer role to the service account
# at the GCS bucket that backs each repo.
resource "google_storage_bucket_iam_member" "gcr_repo" {
  for_each = toset(local.gcr_buckets)
  bucket   = each.value
  role     = "roles/storage.objectViewer"
  member   = google_service_account.sa.member
}


# For the unique set of AR repos, assign reader role to the service account
# at each unique repo root.
resource "google_artifact_registry_repository_iam_member" "ar_repo" {
  for_each   = local.ar_repos
  project    = each.value.project
  location   = each.value.location
  repository = each.key
  role       = "roles/artifactregistry.reader"
  member     = google_service_account.sa.member
}
