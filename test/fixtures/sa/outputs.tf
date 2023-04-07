output "id" {
  value = module.test.id
}

output "email" {
  value = module.test.email
}

output "member" {
  value = module.test.member
}

# Re-ouput some complex inputs as JSON, for easier parsing in controls
output "repositories_json" {
  value = var.repositories != null ? jsonencode(var.repositories) : "[]"
}
