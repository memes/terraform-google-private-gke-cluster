output "my_address" {
  value = trimspace(data.http.my_address.response_body)
}

output "bastion_ip_address" {
  value = module.bastion.ip_address
}

output "bastion_public_ip_address" {
  value = module.bastion.public_ip_address
}

output "self_link" {
  value = module.vpc.self_link
}

output "subnet" {
  value = {
    self_link           = module.vpc.subnets_by_region[var.region].self_link
    pods_range_name     = "pods"
    services_range_name = "services"
  }
}
