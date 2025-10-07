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
  source               = "../../../modules/kubeconfig/"
  cluster_id           = var.cluster_id
  cluster_name         = var.cluster_name
  context_name         = var.context_name
  use_private_endpoint = var.use_private_endpoint
  proxy_url            = var.proxy_url
  user                 = var.user
}
