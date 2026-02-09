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
  })
  nullable = false
  validation {
    condition     = can(regex("^(?:https://www.googleapis.com/compute/v1/)?projects/[a-z][a-z0-9-]{4,28}[a-z0-9]/regions/[a-z]{2,}-[a-z]{2,}[0-9]/subnetworks/[a-z]([a-z0-9-]+[a-z0-9])?$", var.subnet.self_link)) && coalesce(var.subnet.pods_range_name, "unspecified") != "unspecified" && coalesce(var.subnet.services_range_name, "unspecified") != "unspecified"
    error_message = "The subnet value must have a valid self_link URI, and non-empty pods and services names, and a valid master CIDR."
  }
  description = <<-EOD
  Provides the subnet self_link to which the cluster will be attached, the
  *names* of the secondary ranges to use for pods and services, and the CIDR to
  use for masters.
  EOD
}

variable "control_plane_access" {
  type = object({
    enable_dns_access       = optional(bool, true)
    enable_ip_access        = optional(bool, false)
    external_dns_access     = optional(bool, true)
    gcp_public_cidrs_access = optional(bool, false)
    master_global_access    = optional(bool, false)
    master_cidr             = optional(string) #optional(string, "192.168.0.0/28")
    authorized_cidrs = optional(list(object({
      cidr_block   = string
      display_name = string
    })))
  })
  nullable = true
  validation {
    condition = var.control_plane_access == null ? true : (
      (
        var.control_plane_access.enable_dns_access == null ? true : var.control_plane_access.enable_dns_access
      ) ||
      (
        var.control_plane_access.enable_ip_access == null ? false : var.control_plane_access.enable_ip_access
      )
      ) && (
      coalesce(var.control_plane_access.master_cidr, "unspecified") == "unspecified" ? true : can(cidrhost(var.control_plane_access.master_cidr, 1))
      ) && (
      try(length(var.control_plane_access.authorized_cidrs), 0) == 0 ? true : alltrue([for v in var.control_plane_access.authorized_cidrs : can(cidrhost(v.cidr_block, 0)) && coalesce(v.display_name, "unspecified") != "unspecified"])
    )
    error_message = "At least one of enable_dns_access or enable_ip_access must be true, and, if present, master_cidr must be a valid CIDR, and each authorized_cidrs value must have a valid cidr_block and display_name."
  }
  default = {
    enable_dns_access       = true
    enable_ip_access        = false
    external_dns_access     = true
    gcp_public_cidrs_access = false
    master_global_access    = false
    master_cidr             = null #"192.168.0.0/28"
    authorized_cidrs        = null
  }
  description = <<-EOD
  Defines the control-plane access options. By default, the cluster will allow API access via DNS endpoint from within
  Google Cloud, and direct IP access is disabled. These options can be changed by overriding the default values.
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
  An optional set of key:value string pairs that will be added to the Autopilot resources.
  EOD
}

variable "options" {
  type = object({
    release_channel = optional(string, "REGULAR")
    fleet           = optional(string)
  })
  nullable = true
  validation {
    condition     = var.options == null ? true : (contains(["RAPID", "REGULAR", "STABLE"], coalesce(var.options.release_channel, "REGULAR"))) && (coalesce(var.options.fleet, "unspecified") == "unspecified" ? true : can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.options.fleet)))
    error_message = "The project_id variable must must be 6 to 30 lowercase letters, digits, or hyphens; it must start with a letter and cannot end with a hyphen."
  }
  default = {
    release_channel = "REGULAR"
    fleet           = null
  }
  description = <<-EOD
  Defines the set of GKE options to use when provisioning the cluster. Default values will initiate an Autopilot cluster
  from GKE's REGULAR release channel that is not registered to an Enterprise GKE fleet. If you
  want to use Privately Used Public IP addresses (PUPI) CIDRs for pods or services, set the default_snat flag to false.
  EOD
}

variable "features" {
  type = object({
    default_snat                        = optional(bool, true)
    binary_authorization                = optional(bool, false)
    confidential_nodes                  = optional(bool, false)
    secret_manager                      = optional(bool, true)
    gateway_api                         = optional(bool, true)
    dataplane_v2_advanced_observability = optional(bool, false)
    filestore_csi                       = optional(bool, false)
    parallelstore_csi                   = optional(bool, false)
    lustre_csi                          = optional(bool, false)
    ray_operator                        = optional(bool, false)
    disable_auto_lb_firewall            = optional(bool, false)
    managed_prometheus                  = optional(bool, true)
    managed_opentelemetry               = optional(bool, false)
  })
  default = {
    default_snat                        = true
    binary_authorization                = false
    confidential_nodes                  = false
    secret_manager                      = true
    gateway_api                         = true
    dataplane_v2_advanced_observability = false
    filestore_csi                       = false
    parallelstore_csi                   = false
    lustre_csi                          = false
    ray_operator                        = false
    disable_auto_lb_firewall            = false
    managed_prometheus                  = true
    managed_opentelemetry               = false
  }
  description = <<-EOD
  The set of boolean feature flags that will be enabled on the Autopilot cluster. Unless modified, the cluster will be
  created with Default SNAT, Secret Manager integration, Managed Prometheus, and Gateway API support enabled. Other features will be
  disabled, including some CSIs that are typically enabled when creating a GKE cluster through the console.
  NOTE: To use Privately Used Public IP addresses (PUPI) CIDRs for pods or services, set the default_snat flag to false.
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
