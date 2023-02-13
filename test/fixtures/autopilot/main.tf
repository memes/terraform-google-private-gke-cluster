terraform {
  required_version = ">= 1.2"
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
  maintenance                = var.maintenance
  nap                        = var.nap
}
