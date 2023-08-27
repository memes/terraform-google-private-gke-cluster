output "id" {
  value = module.test.id
}

output "name" {
  value = module.test.name
}

output "location" {
  value = module.test.location
}

output "ca_cert" {
  sensitive = true
  value     = module.test.ca_cert
}

output "endpoint_url" {
  sensitive = true
  value     = module.test.endpoint_url
}

output "public_endpoint_url" {
  sensitive = true
  value     = module.test.public_endpoint_url
}

output "service_account" {
  value = module.sa.email
}

output "kubeconfig" {
  sensitive = true
  value     = module.kubeconfig.kubeconfig
}

# Re-ouput some complex inputs as JSON, for easier parsing in controls
output "subnet_json" {
  value = jsonencode(var.subnet)
}

output "node_pools_json" {
  value = jsonencode(var.node_pools)
}

output "options_json" {
  value = jsonencode(var.options)
}

output "features_json" {
  value = jsonencode(var.features)
}

output "maintenance_json" {
  value = jsonencode(var.maintenance)
}

output "autoscaling_json" {
  value = jsonencode(var.autoscaling)
}

output "dns_json" {
  value = jsonencode(var.dns)
}

output "master_authorized_networks_json" {
  value = jsonencode(var.master_authorized_networks)
}

output "labels_json" {
  value = var.labels == null ? "{}" : jsonencode(var.labels)
}

output "is_autopilot" {
  value = false
}
