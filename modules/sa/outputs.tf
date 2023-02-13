output "id" {
  value       = google_service_account.sa.id
  description = <<-EOD
  The fully-qualified service account identifier.
  EOD
}

output "email" {
  value       = google_service_account.sa.email
  description = <<-EOD
  The email address of the service account.
  EOD
}

output "member" {
  value       = google_service_account.sa.member
  description = <<-EOD
  The service account identity for use with IAM declarations. E.g. `serviceAccount:email`
  where email is the value of output `email`.
  EOD
}
