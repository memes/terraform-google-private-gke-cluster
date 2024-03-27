terraform {
  required_version = ">= 1.2"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.21"
    }
  }
}

locals {
  cluster_spec = regex("projects/(?P<project_id>[^/]+)/locations/(?P<location>[^/]+)/clusters/(?P<name>.*)$", var.cluster_id)
}

data "google_container_cluster" "cluster" {
  project  = local.cluster_spec["project_id"]
  name     = local.cluster_spec["name"]
  location = local.cluster_spec["location"]
}
