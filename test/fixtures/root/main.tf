terraform {
  required_version = ">= 1.2"
}

module "sa" {
  source     = "../../../modules/sa/"
  project_id = var.project_id
  name       = var.name
}

module "test" {
  source                     = "./../../../"
  project_id                 = var.project_id
  name                       = var.name
  description                = var.description
  subnet                     = var.subnet
  master_authorized_networks = var.master_authorized_networks
  service_account            = module.sa.email
  labels                     = var.labels
  options                    = var.options
  features                   = var.features
  maintenance                = var.maintenance
  node_pools                 = var.node_pools
  autoscaling                = var.autoscaling
  dns                        = var.dns
}

module "kubeconfig" {
  source               = "../../../modules/kubeconfig/"
  cluster_id           = module.test.id
  cluster_name         = var.name
  context_name         = var.name
  use_private_endpoint = try(var.options.private_endpoint, true)
  proxy_url            = var.proxy_url
}
