output "id" {
  value       = google_container_cluster.cluster.id
  description = <<-EOD
  The unique identifier of the GKE cluster.
  EOD
  depends_on = [
    google_container_cluster.cluster,
    google_container_node_pool.pools,
  ]
}

output "name" {
  value       = google_container_cluster.cluster.name
  description = <<-EOD
  The name of the GKE cluster.
  EOD
  depends_on = [
    google_container_cluster.cluster,
    google_container_node_pool.pools,
  ]
}

output "location" {
  value       = google_container_cluster.cluster.location
  description = <<-EOD
  The location of the GKE cluster.
  EOD
}

output "ca_cert" {
  sensitive   = true
  value       = google_container_cluster.cluster.master_auth.0.cluster_ca_certificate
  description = <<-EOD
  The base64 encoded CA certificate used by the kubernetes master.
  EOD
  depends_on = [
    google_container_cluster.cluster,
    google_container_node_pool.pools,
  ]
}

output "endpoint_url" {
  sensitive   = true
  value       = format("https://%s", google_container_cluster.cluster.private_cluster_config.0.private_endpoint)
  description = <<-EOD
  The URL to use for master access.
  EOD
  depends_on = [
    google_container_cluster.cluster,
    google_container_node_pool.pools,
  ]
}
