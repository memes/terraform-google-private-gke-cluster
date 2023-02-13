output "kubeconfig" {
  sensitive = true
  value = templatefile("${path.module}/templates/kubeconfig.yaml", {
    cluster_name = coalesce(var.cluster_name, data.google_container_cluster.cluster.name)
    context_name = coalesce(var.context_name, data.google_container_cluster.cluster.name)
    ca_cert      = data.google_container_cluster.cluster.master_auth.0.cluster_ca_certificate
    endpoint     = format("https://%s", try(var.use_private_endpoint, true) ? data.google_container_cluster.cluster.private_cluster_config.0.private_endpoint : data.google_container_cluster.cluster.endpoint)
    proxy_url    = var.proxy_url
    user_name    = coalesce(try(var.user.name, ""), data.google_container_cluster.cluster.name)
    user_token   = try(var.user.token, "")
  })
  description = <<-EOD
  A generated Kubeconfig YAML that can be used to access the kubernetes master,
  using a supplied token or the `gke-gcloud-auth-plugin`.
EOD
}
