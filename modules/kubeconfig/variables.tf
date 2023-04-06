variable "cluster_id" {
  type = string
  validation {
    condition     = can(regex("^(?:https://www.googleapis.com/compute/v1/)?projects/[a-z][a-z0-9-]{4,28}[a-z0-9]/locations/[a-z]{2,}-[a-z]+[1-9](?:-[a-z])?/clusters/[a-z][a-z0-9-]{0,38}[a-z0-9]$", var.cluster_id))
    error_message = "The cluster_id value must be a valid GKE cluster identifier."
  }
  description = <<-EOD
  The fully-qualified identifier for the GKE cluster that the generated kubeconfig
  will be used with.
  EOD
}

variable "cluster_name" {
  type        = string
  default     = null
  description = <<-EOD
  An optional cluster name to use in preference to the actual GKE cluster name in
  generated kubeconfig. Default value is null; kubeconfig will container the real
  cluster name.
  EOD
}

variable "context_name" {
  type        = string
  default     = null
  description = <<-EOD
  An optional context name to use in preference to the GKE cluster name in
  generated kubeconfig. Default value is null; the GKE cluster name will be used
  for context name.
  EOD
}

variable "use_private_endpoint" {
  type        = bool
  default     = true
  description = <<-EOD
  Flag to trigger use of private IP address of master as the endpoint for the
  generated kubeconf. Default is true; if set to false the master public IP will
  be used if possible.
  EOD
}

variable "proxy_url" {
  type        = string
  default     = null
  description = <<-EOD
  If this is a non-empty value, the generated kubeconfig will set the proxy entry
  to this value. Default is null.
  EOD
}

variable "user" {
  type = object({
    name  = string
    token = string
  })
  default     = null
  description = <<-EOD
  These values override defaults in the generated kubeconfig. If the name field
  is not empty its value will be the name of the user in the generated kubeconfig,
  instead of cluster name (default). If the token field is not empty, the generated
  kubeconfig will use the provided token for authentication instead of GKE auth
  plugin.
  EOD
}
