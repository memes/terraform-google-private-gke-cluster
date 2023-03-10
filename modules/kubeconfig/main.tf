terraform {
  required_version = ">= 1.2"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.42, < 4.49.0, > 4.51.0" # See https://github.com/hashicorp/terraform-provider-google/issues/13507kitchen
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
