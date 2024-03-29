terraform {
  required_version = ">= 1.2"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.21"
    }
    http = {
      source  = "hashicorp/http"
      version = ">= 3.2"
    }
    local = {
      source  = "hashicorp/local"
      version = ">= 2.2"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.3"
    }
  }
}

data "http" "my_address" {
  url = "https://checkip.amazonaws.com"
  lifecycle {
    postcondition {
      condition     = self.status_code == 200
      error_message = "Failed to get local IP address"
    }
  }
}

data "google_compute_zones" "zones" {
  project = var.project_id
  region  = var.region
  status  = "UP"
}

resource "random_shuffle" "zones" {
  input = data.google_compute_zones.zones.names
}

resource "random_pet" "prefix" {
  length = 1
  prefix = coalesce(var.prefix, "pgke")
  keepers = {
    project_id = var.project_id
  }
}

locals {
  prefix = random_pet.prefix.id
  labels = merge({
    use-case = "automated-testing"
    product  = "terraform-google-private-gke-cluster"
    driver   = "kitchen-terraform"
  }, var.labels)
}

module "vpc" {
  source      = "memes/multi-region-private-network/google"
  version     = "2.1.0"
  project_id  = var.project_id
  name        = format("%s-test", local.prefix)
  description = format("test VPC network (%s)", local.prefix)
  regions     = [var.region]
  cidrs = {
    primary_ipv4_cidr        = "172.16.0.0/16"
    primary_ipv4_subnet_size = 24
    primary_ipv6_cidr        = null
    secondaries = {
      pods = {
        ipv4_cidr        = "10.0.0.0/8"
        ipv4_subnet_size = 16
      }
      services = {
        ipv4_cidr        = "10.100.0.0/16"
        ipv4_subnet_size = 20
      }
    }
  }
  options = {
    delete_default_routes = false
    restricted_apis       = true
    nat                   = true
    nat_tags              = []
    mtu                   = 1460
    routing_mode          = "GLOBAL"
    flow_logs             = false
    ipv6_ula              = false
    nat_logs              = false
    private_apis          = false
  }
}

module "restricted_apis_dns" {
  source             = "memes/restricted-apis-dns/google"
  version            = "1.3.0"
  project_id         = var.project_id
  name               = format("%s-restricted-apis", local.prefix)
  labels             = local.labels
  network_self_links = [module.vpc.self_link]
  depends_on = [
    module.vpc,
  ]
}

module "bastion" {
  source                = "memes/private-bastion/google"
  version               = "3.0.0"
  project_id            = var.project_id
  name                  = format("%s-test", local.prefix)
  external_ip           = true
  proxy_container_image = "ghcr.io/memes/terraform-google-private-bastion/forward-proxy:3.0.0"
  zone                  = random_shuffle.zones.result[0]
  subnet                = module.vpc.subnets_by_region[var.region].self_link
  labels                = local.labels
  bastion_targets = {
    cidrs = [
      "172.16.0.0/16",
    ]
    service_accounts = null
    priority         = 900
  }
  depends_on = [
    module.vpc,
    module.restricted_apis_dns,
  ]
}

resource "google_compute_firewall" "bastion" {
  project     = var.project_id
  name        = format("%s-allow-proxy-ingress", local.prefix)
  network     = module.vpc.self_link
  description = format("Allow tester access to proxy (%s)", local.prefix)
  direction   = "INGRESS"
  source_ranges = [
    format("%s/32", trimspace(data.http.my_address.response_body)),
  ]
  target_service_accounts = [
    module.bastion.service_account,
  ]
  allow {
    protocol = "TCP"
    ports = [
      8888,
    ]
  }
  depends_on = [
    module.bastion,
  ]
}

resource "google_container_registry" "gcr" {
  project  = var.project_id
  location = var.gcr_location
}

resource "google_artifact_registry_repository" "gar" {
  project       = var.project_id
  repository_id = format("%s-test", local.prefix)
  format        = "DOCKER"
  location      = var.region
  description   = "Testing GAR for terraform-google-private-gke-cluster"
  labels        = local.labels
}

# Not using these values to drive anything, but makes a good sentinel for testing
resource "local_file" "harness_tfvars" {
  filename = "${path.module}/harness.tfvars"
  content  = <<-EOC
  # Empty!
  EOC
  depends_on = [
    module.vpc,
    module.bastion,
  ]
}
