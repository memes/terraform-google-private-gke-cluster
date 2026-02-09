variable "cluster_id" {
  type     = string
  nullable = false
  validation {
    condition     = can(regex("^(?:https://www.googleapis.com/compute/v1/)?projects/[a-z][a-z0-9-]{4,28}[a-z0-9]/locations/[a-z]{2,}-[a-z]+[1-9](?:-[a-z])?/clusters/[a-z][a-z0-9-]{0,38}[a-z0-9]$", var.cluster_id))
    error_message = "The cluster_id value must be a valid GKE cluster identifier."
  }
  description = <<-EOD
  The fully-qualified identifier for the GKE cluster that the generated kubeconfig will be used with.
  EOD
}

variable "cluster_name" {
  type     = string
  nullable = true
  validation {
    condition     = try(length(trimspace(var.cluster_name)), 0) == 0 ? true : can(regex("^[a-z0-9][-a-z0-9]{0,61}[a-z0-9]?$", var.cluster_name))
    error_message = "If specified, cluster_name must be lowercase RFC1123 compliant."
  }
  default     = null
  description = <<-EOD
  An optional cluster name to use in preference to the actual GKE cluster name in generated kubeconfig. If empty
  (default) the GKE cluster name will be used.
  EOD
}

variable "context_name" {
  type = string
  validation {
    condition     = try(length(trimspace(var.context_name)), 0) == 0 ? true : can(regex("^[a-z0-9][-a-z0-9]{0,61}[a-z0-9]?$", var.context_name))
    error_message = "If specified, context_name must be lowercase RFC1123 compliant."
  }
  nullable    = true
  default     = null
  description = <<-EOD
  An optional context name to use in preference to the GKE cluster name in generated kubeconfig. If empty (default) the
  GKE cluster name will be used.
  EOD
}

variable "use_private_endpoint" {
  type        = bool
  nullable    = false
  default     = false
  description = <<-EOD
  By default the generated kubeconfig will use the GKE cluster's DNS endpoint with fallback to private IP endpoint if
  DNS endpoint is unknown. This flag can be used to force the use of private IP endpoint if both values are present.

  NOTE: This flag will cause an error to be raised if set to true and a private IP endpoint is not available.
  EOD
}

variable "proxy_url" {
  type        = string
  nullable    = true
  default     = null
  description = <<-EOD
  If not empty, a proxy field will be added to the generated kubeconfig containing this value.
  EOD
}

variable "user" {
  type = object({
    name  = optional(string)
    token = optional(string)
  })
  nullable    = true
  default     = null
  description = <<-EOD
  These values override defaults in the generated kubeconfig. If the name field is not empty its value will be the name
  of the user in the generated kubeconfig, instead of GKE cluster name (default). If the token field is not empty, the
  generated kubeconfig will use the provided token for authentication instead of GKE auth plugin.
  EOD
}
