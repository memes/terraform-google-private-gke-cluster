output "prefix" {
  value = local.prefix
}

output "project_id" {
  value = var.project_id
}

output "bastion_ip_address" {
  value = module.bastion.ip_address
}

output "service_account" {
  value = local.gke_sa
}

output "subnet_template" {
  value = {
    self_link           = module.vpc.subnets[var.region]
    pods_range_name     = "pods"
    services_range_name = "services"
  }
}
