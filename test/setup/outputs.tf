output "prefix" {
  value = local.prefix
}

output "project_id" {
  value = var.project_id
}

output "bastion_ip_address" {
  value = module.bastion.ip_address
}

output "bastion_public_ip_address" {
  value = module.bastion.public_ip_address
}

output "subnet_template" {
  value = {
    self_link           = module.vpc.subnets_by_region[var.region].self_link
    pods_range_name     = "pods"
    services_range_name = "services"
  }
}

output "gcr_repo" {
  value = format("%s.gcr.io/%s", lower(google_container_registry.gcr.location), google_container_registry.gcr.project)
}

output "gar_repo" {
  value = format("%s-docker.pkg.dev/%s/%s", google_artifact_registry_repository.gar.location, google_artifact_registry_repository.gar.project, google_artifact_registry_repository.gar.name)
}
