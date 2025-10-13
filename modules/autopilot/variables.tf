variable "project_id" {
  type     = string
  nullable = false
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "The project_id variable must must be 6 to 30 lowercase letters, digits, or hyphens; it must start with a letter and cannot end with a hyphen."
  }
  description = <<-EOD
  The GCP project identifier where the Autopilot GKE cluster will be created.
  EOD
}

variable "name" {
  type     = string
  nullable = false
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,62}$", var.name))
    error_message = "The name variable must be RFC1035 compliant and between 1 and 63 characters in length."
  }
  description = <<-EOD
  The name to use when naming resources managed by this module. Must be RFC1035
  compliant and between 1 and 63 characters in length, inclusive.
  EOD
}

variable "description" {
  type        = string
  nullable    = true
  default     = "Private Autopilot GKE cluster for demo"
  description = <<-EOD
  An optional description to add to the Autopilot GKE cluster.
  EOD
}

variable "subnet" {
  type = object({
    self_link           = string
    pods_range_name     = optional(string, "pods")
    services_range_name = optional(string, "services")
    master_cidr         = optional(string, "192.168.0.0/28")
  })
  nullable = false
  validation {
    condition     = can(regex("^(?:https://www.googleapis.com/compute/v1/)?projects/[a-z][a-z0-9-]{4,28}[a-z0-9]/regions/[a-z]{2,}-[a-z]{2,}[0-9]/subnetworks/[a-z]([a-z0-9-]+[a-z0-9])?$", var.subnet.self_link)) && coalesce(var.subnet.pods_range_name, "unspecified") != "unspecified" && coalesce(var.subnet.services_range_name, "unspecified") != "unspecified" && can(cidrhost(var.subnet.master_cidr, 1))
    error_message = "The subnet value must have a valid self_link URI, and non-empty pods and services names, and a valid master CIDR."
  }
  description = <<-EOD
  Provides the subnet self_link to which the cluster will be attached, the
  *names* of the secondary ranges to use for pods and services, and the CIDR to
  use for masters.
  EOD
}

variable "master_authorized_networks" {
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  nullable = true
  validation {
    condition     = var.master_authorized_networks == null ? false : alltrue([for v in var.master_authorized_networks : can(cidrhost(v.cidr_block, 0)) && coalesce(v.display_name, "unspecified") != "unspecified"])
    error_message = "Each master_authorized_networks value must have a valid cidr_block and display_name."
  }
  description = <<-EOD
  A set of CIDRs that are permitted to reach the kubernetes API endpoints.
  EOD
}

variable "service_account" {
  type     = string
  nullable = false
  validation {
    condition     = can(regex("(?:[a-z][a-z0-9-]{4,28}[a-z0-9]@[a-z][a-z0-9-]{4,28}\\.iam|[1-9][0-9]+-compute@developer)\\.gserviceaccount\\.com$", var.service_account))
    error_message = "The service_account variable must be a valid GCP service account email address."
  }
  description = <<-EOD
    The Compute Engine service account that worker nodes will use.
    EOD
}

variable "labels" {
  type     = map(string)
  nullable = true
  validation {
    # GCP resource labels must be lowercase alphanumeric, underscore or hyphen,
    # and the key must be <= 63 characters in length
    condition     = var.labels == null ? true : length(compact([for k, v in var.labels : can(regex("^[a-z][a-z0-9_-]{0,62}$", k)) && can(regex("^[a-z0-9_-]{0,63}$", v)) ? "x" : ""])) == length(keys(var.labels))
    error_message = "Each label key:value pair must match expectations."
  }
  default     = {}
  description = <<-EOD
  An optional set of key:value string pairs that will be added to the Autopilot
  resources.
  EOD
}

variable "options" {
  type = object({
    release_channel      = optional(string, "STABLE")
    master_global_access = optional(bool, true)
    private_endpoint     = optional(bool, false)
    default_snat         = optional(bool, true)
  })
  nullable = false
  default = {
    release_channel      = "STABLE"
    master_global_access = true
    private_endpoint     = true
    default_snat         = true
  }
  description = <<-EOD
  Defines the set of GKE options to use when provisioning the cluster. Default
  values will initiate an Autopilot cluster from GKE's STABLE release channel,
  with global flag enabled on the master access LB, and private RFC1918 endpoint.
  EOD
}

variable "features" {
  type = object({
    binary_authorization = optional(bool, false)
    confidential_nodes   = optional(bool, false)
    secret_manager       = optional(bool, true)
  })
  default = {
    binary_authorization = false
    confidential_nodes   = false
    secret_manager       = true
  }
  description = <<-EOD
  The set of features that will be enabled on the Autopilot cluster. By default Secret Manager integration will be
  enabled, but binary authorization and confidential worker nodes will be disabled.
  EOD
}

variable "nap" {
  type = object({
    tags = optional(list(string), null)
  })
  nullable = true
  validation {
    condition     = var.nap == null ? true : (try(var.nap.tags, null) == null ? true : alltrue([for tag in var.nap.tags : can(regex("^[a-z][a-z0-9-]{0,62}$", tag))]))
    error_message = "Each tag in the nap variable must be RFC1035 compliant."
  }
  default     = null
  description = <<-EOD
  Configures cluster-scoped node auto-provisioning parameters for use with autopilot.
  Currently, only network tags can be specified.
  EOD
}

variable "dns" {
  type = object({
    cluster_dns                   = optional(string, "CLOUD_DNS")
    cluster_dns_scope             = optional(string, "CLUSTER_SCOPE")
    cluster_dns_domain            = optional(string, "cluster.local")
    additive_vpc_scope_dns_domain = optional(string)
  })
  default     = null
  description = <<-EOD
  An optional value to trigger integration of Cloud DNS as the preferred DNS
  provider in the cluster. Default is null, which will create a cluster with
  KubeDNS as the provider.
  EOD
}
