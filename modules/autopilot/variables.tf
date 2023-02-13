variable "project_id" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "The project_id variable must must be 6 to 30 lowercase letters, digits, or hyphens; it must start with a letter and cannot end with a hyphen."
  }
  description = <<-EOD
  The GCP project identifier where the Autopilot GKE cluster will be created.
  EOD
}

variable "name" {
  type = string
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
  default     = null
  description = <<-EOD
  An optional description to add to the Autopilot GKE cluster.
  EOD
}

variable "subnet" {
  type = object({
    self_link           = string
    pods_range_name     = string
    services_range_name = string
    master_cidr         = string
  })
  validation {
    condition     = var.subnet == null ? false : can(regex("^(?:https://www.googleapis.com/compute/v1/)?projects/[a-z][a-z0-9-]{4,28}[a-z0-9]/regions/[a-z]{2,}-[a-z]{2,}[0-9]/subnetworks/[a-z]([a-z0-9-]+[a-z0-9])?$", var.subnet.self_link)) && coalesce(var.subnet.pods_range_name, "unspecified") != "unspecified" && coalesce(var.subnet.services_range_name, "unspecified") != "unspecified" && can(cidrhost(var.subnet.master_cidr, 1))
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
  validation {
    condition     = var.master_authorized_networks == null ? false : length(compact([for v in var.master_authorized_networks : can(cidrhost(v.cidr_block, 0)) && coalesce(v.display_name, "unspecified") != "unspecified" ? "x" : ""])) == length(var.master_authorized_networks)
    error_message = "Each master_authorized_networks value must have a valid cidr_block and display_name."
  }
  description = <<-EOD
  A set of CIDRs that are permitted to reach the kubernetes API endpoints.
  EOD
}

variable "service_account" {
  type = string
  validation {
    condition     = can(regex("(?:[a-z][a-z0-9-]{4,28}[a-z0-9]@[a-z][a-z0-9-]{4,28}\\.iam|[1-9][0-9]+-compute@developer)\\.gserviceaccount\\.com$", var.service_account))
    error_message = "The service_account variable must be a valid GCP service account email address."
  }
  description = <<-EOD
    The Compute Engine service account that worker nodes will use.
    EOD
}

variable "labels" {
  type = map(string)
  validation {
    # GCP resource labels must be lowercase alphanumeric, underscore or hyphen,
    # and the key must be <= 63 characters in length
    condition     = length(compact([for k, v in var.labels : can(regex("^[a-z][a-z0-9_-]{0,62}$", k)) && can(regex("^[a-z0-9_-]{0,63}$", v)) ? "x" : ""])) == length(keys(var.labels))
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
    release_channel      = string
    master_global_access = bool
    etcd_kms             = string
  })
  default = {
    release_channel      = "STABLE"
    master_global_access = true
    etcd_kms             = null
  }
  description = <<-EOD
  Defines the set of GKE options to use when provisioning the cluster. Default
  values will initiate an Autopilot cluster from GKE's STABLE release channel,
  with global flag enabled on the master access LB.
  EOD
}

variable "features" {
  type = object({
    binary_authorization = bool
    confidential_nodes   = bool
  })
  default = {
    binary_authorization = false
    confidential_nodes   = false
  }
  description = <<-EOD
  The set of features that will be enabled on the Autopilot cluster. By default,
  binary authorization and confidential worker nodes will NOT be enabled.
  EOD
}

variable "maintenance" {
  type = object({
    start_time = string
    end_time   = string
    exclusions = list(object({
      name            = string
      start_time      = string
      end_time        = string
      exclusion_scope = string
    }))
    recurrence = string
  })
  default = {
    start_time = "05:00"
    end_time   = ""
    exclusions = []
    recurrence = ""
  }
  description = <<-EOD
  Defines the times that GKE is permitted to perform automatic cluster maintenance.
  EOD
}

variable "nap" {
  type = object({
    tags = list(string)
  })
  default     = null
  description = <<-EOD
  Configures cluster-scoped node auto-provisioning parameters for use with autopilot.
  Currently, only network tags can be specified.
  EOD
}
