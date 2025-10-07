terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.27"
    }
  }
}

resource "google_artifact_registry_repository" "gar" {
  project       = var.project_id
  repository_id = var.name
  format        = "DOCKER"
  location      = var.region
  description   = "Testing GAR for terraform-google-private-gke-cluster"
  labels        = var.labels
}
