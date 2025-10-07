terraform {
  required_version = ">= 1.5"
}

module "test" {
  source                     = "./../../../"
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
  node_pools                 = var.node_pools
  autoscaling                = var.autoscaling
  dns                        = var.dns
}
