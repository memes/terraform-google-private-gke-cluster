output "repo" {
  value = format("%s-docker.pkg.dev/%s/%s", google_artifact_registry_repository.gar.location, google_artifact_registry_repository.gar.project, google_artifact_registry_repository.gar.name)
}
