output "kubeconfig" {
  sensitive   = true
  value       = local.kubeconfig
  description = <<-EOD
  A generated Kubeconfig YAML that can be used to access the kubernetes master, using a supplied token or the `gke-gcloud-auth-plugin`.
  EOD
}
