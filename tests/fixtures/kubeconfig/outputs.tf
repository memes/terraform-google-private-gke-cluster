output "kubeconfig" {
  sensitive = true
  value     = module.test.kubeconfig
}
