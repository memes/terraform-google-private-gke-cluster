variable "project_id" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "The project_id variable must must be 6 to 30 lowercase letters, digits, or hyphens; it must start with a letter and cannot end with a hyphen."
  }
  description = <<-EOD
  The GCP project identifier where the private GKE cluster will be created.
  EOD
}

variable "name" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.name))
    error_message = "The name variable must be a valid RFC1035 identifier string."
  }
  description = <<-EOD
  The name to give to the service account.
  EOD
}

variable "display_name" {
  type        = string
  default     = "Generated GKE Service Account"
  description = <<-EOD
  An optional display name to associate with the generated service account. Default
  is 'Generated GKE Service Account'.
  EOD
}

variable "description" {
  type        = string
  default     = <<-EOD
  A Terraform generated Service Account suitable for use by GKE nodes. The service
  account is intended to have minimal roles required to log and report base
  metrics to Google Cloud Operations.
  EOD
  description = <<-EOD
  An optional description to apply to the generated service account. The default
  value describes the purpose of the service account.
  EOD
}

variable "repositories" {
  type = list(string)
  validation {
    condition     = var.repositories == null ? true : alltrue([for repo in var.repositories : can(regex("^(?:(?:(?:asia|eu|us).)?gcr.io|[a-z]{2,}(?:-[a-z]+[1-9])?-docker.pkg.dev/[^/]+/[^/]+)", repo))])
    error_message = "Each repositories entry must be a valid gcr.io or XXX-docker.pkg.dev repository."
  }
  default     = []
  description = <<-EOD
  An optional list of GCR and/or GAR repositories. If provided, the generated
  service account will be given the appropriate GCR or GAR read-only access role
  to the repos.
  EOD
}
