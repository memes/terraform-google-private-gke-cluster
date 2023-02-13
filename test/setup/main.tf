terraform {
  required_version = ">= 1.2"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.42"
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
  gke_sa = format("%s-gke@%s.iam.gserviceaccount.com", local.prefix, var.project_id)
  labels = merge({
    use-case = "automated-testing"
    product  = "f5-dc-google-ingress-demo"
    driver   = "kitchen-terraform"
  }, var.labels)
}

module "sa" {
  source       = "../../modules/sa/"
  project_id   = var.project_id
  name         = format("%s-gke", local.prefix)
  repositories = var.repositories
}

module "vpc" {
  source      = "memes/multi-region-private-network/google"
  version     = "1.0.0"
  project_id  = var.project_id
  name        = format("%s-test", local.prefix)
  description = format("test VPC network (%s)", local.prefix)
  regions     = [var.region]
  cidrs = {
    primary             = "172.16.0.0/16"
    primary_subnet_size = 24
    secondaries = {
      pods = {
        cidr        = "10.0.0.0/8"
        subnet_size = 16
      }
      services = {
        cidr        = "10.100.0.0/16"
        subnet_size = 20
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
  }
}

module "restricted_apis_dns" {
  source             = "memes/restricted-apis-dns/google"
  version            = "1.0.1"
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
  version               = "2.3.3"
  project_id            = var.project_id
  prefix                = format("%s-inside", local.prefix)
  proxy_container_image = "ghcr.io/memes/terraform-google-private-bastion/forward-proxy:2.3.3"
  zone                  = random_shuffle.zones.result[0]
  subnet                = module.vpc.subnets[var.region]
  labels                = local.labels
  bastion_targets = {
    service_accounts = [
      local.gke_sa,
    ]
    cidrs    = null
    tags     = null
    priority = 900
  }
  depends_on = [
    module.sa,
    module.vpc,
    module.restricted_apis_dns,
  ]
}

# Not using these values to drive anything, but makes a good sentinel for testing
resource "local_file" "harness_tfvars" {
  filename = "${path.module}/harness.tfvars"
  content  = <<-EOC
  # Empty!
  EOC
  depends_on = [
    module.sa,
    module.vpc,
    module.bastion,
  ]
}
