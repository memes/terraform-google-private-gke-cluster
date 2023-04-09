variable "project_id" {
  type = string
}

variable "name" {
  type = string
}

variable "display_name" {
  type    = string
  default = "Generated GKE Service Account"
}

variable "description" {
  type    = string
  default = <<-EOD
  A Terraform generated Service Account suitable for use by GKE nodes. The service
  account is intended to have minimal roles required to log and report base
  metrics to Google Cloud Operations.
  EOD
}

variable "repositories" {
  type    = list(string)
  default = []
}
