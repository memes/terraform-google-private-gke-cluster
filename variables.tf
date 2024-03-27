variable "project_id" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "The project_id variable must must be 6 to 30 lowercase letters, digits, or hyphens; it must start with a letter and cannot end with a hyphen."
  }
  description = <<-EOD
  The GCP project identifier where the GKE cluster will be created.
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
  An optional set of key:value string pairs that will be added on the
  EOD
}

variable "options" {
  type = object({
    release_channel      = string
    version              = string
    workload_pool        = string
    master_global_access = bool
    etcd_kms             = string
    max_pods_per_node    = number
    private_endpoint     = bool
    default_snat         = bool
    deletion_protection  = bool
  })
  default = {
    release_channel      = "STABLE"
    version              = null
    workload_pool        = null
    master_global_access = true
    etcd_kms             = null
    max_pods_per_node    = 110
    private_endpoint     = true
    default_snat         = true
    deletion_protection  = false
  }
  description = <<-EOD
  Defines the set of GKE options to use when provisioning the cluster. Default
  values will create cluster from the STABLE release channel with private RFC1918 endpoint.
  EOD
}

variable "features" {
  type = object({
    alpha                = bool
    binary_authorization = bool
    cloudrun             = bool
    confidential_nodes   = bool
    config_connector     = bool
    csi_filestore        = bool
    csi_gce_pd           = bool
    gke_backup           = bool
    hpa                  = bool
    identity_service     = bool
    intranode_visibility = bool
    istio                = bool
    kalm                 = bool
    l7_lb                = bool
    sandbox              = bool
    service_external_ips = bool
    shielded_nodes       = bool
    tpu                  = bool
    vpa                  = bool
  })
  default = {
    alpha                = false
    binary_authorization = false
    cloudrun             = false
    confidential_nodes   = false
    config_connector     = false
    csi_filestore        = false
    csi_gce_pd           = false
    gke_backup           = false
    hpa                  = true
    identity_service     = false
    intranode_visibility = false
    istio                = false
    kalm                 = false
    l7_lb                = true
    sandbox              = false
    service_external_ips = false
    shielded_nodes       = true
    tpu                  = false
    vpa                  = false
  }
  description = <<-EOD
  The set of features that will be enabled on the GKE cluster.
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

variable "node_pools" {
  type = map(object({
    auto_upgrade                = bool
    autoscaling                 = bool
    location_policy             = string
    min_nodes_per_zone          = number
    max_nodes_per_zone          = number
    auto_repair                 = bool
    disk_size                   = number
    disk_type                   = string
    image_type                  = string
    labels                      = map(string)
    local_ssd_count             = number
    ephemeral_local_ssd_count   = number
    machine_type                = string
    min_cpu_platform            = string
    preemptible                 = bool
    spot                        = bool
    boot_disk_kms_key           = string
    enable_gcfs                 = bool
    enable_gvnic                = bool
    enable_gvisor_sandbox       = bool
    enable_secure_boot          = bool
    enable_integrity_monitoring = bool
    max_surge                   = number
    max_unavailable             = number
    placement_policy            = string
    metadata                    = map(string)
    sysctls                     = map(string)
    taints = list(object({
      key    = string
      value  = string
      effect = string
    }))
    tags = list(string)
  }))
  description = <<-EOD
  Defines the mapping of node pool names (keys), to attributes of the node pools.
  EOD
}

variable "autoscaling" {
  type = object({
    autoscaling_profile = string
    resource_limits = list(object({
      resource_type = string
      maximum       = number
      minimum       = number
    }))
    nap = object({
      min_cpu_platform            = string
      boot_disk_kms_key           = string
      disk_size                   = number
      disk_type                   = string
      image_type                  = string
      auto_upgrade                = bool
      auto_repair                 = bool
      enable_secure_boot          = bool
      enable_integrity_monitoring = bool
      tags                        = list(string)
    })
  })
  default     = null
  description = <<-EOD
  Configures cluster-scoped node auto-provisioning parameters. If null (default)
  then autoscaling with node auto-provisioning will be disabled for the cluster
  and node-pool definitions will be required for a functioning cluster. If specified,
  a set of resource_limits containing 'cpu' and 'memory' values must be provided.
  EOD
}

variable "dns" {
  type = object({
    cluster_dns        = string
    cluster_dns_scope  = string
    cluster_dns_domain = string
  })
  default     = null
  description = <<-EOD
  An optional value to trigger integration of Cloud DNS as the preferred DNS
  provider in the cluster. Default is null, which will create a cluster with
  KubeDNS as the provider.
  EOD
}
