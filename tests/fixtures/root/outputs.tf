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
