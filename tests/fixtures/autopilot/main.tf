terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.27"
    }
  }
}

module "test" {
  source                     = "./../../../modules/autopilot/"
  project_id                 = var.project_id
  name                       = var.name
  description                = var.description
  subnet                     = var.subnet
  master_authorized_networks = var.master_authorized_networks
  service_account            = var.service_account
  labels                     = var.labels
  options                    = var.options
  features                   = var.features
  nap                        = var.nap
  dns                        = var.dns
}
