variable "project_id" {
  type = string
}

variable "name" {
  type = string
}

variable "description" {
  type    = string
  default = "Private Autopilot GKE cluster for demo"
}

variable "service_account" {
  type = string
}

variable "subnet" {
  type = object({
    self_link           = string
    pods_range_name     = optional(string, "pods")
    services_range_name = optional(string, "services")
    master_cidr         = optional(string, "192.168.0.0/28")
  })
}

variable "master_authorized_networks" {
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
}

variable "labels" {
  type    = map(string)
  default = {}
}

variable "options" {
  type = object({
    release_channel      = optional(string, "STABLE")
    master_global_access = optional(bool, true)
    private_endpoint     = optional(bool, false)
    default_snat         = optional(bool, true)
  })
  default = {
    release_channel      = "STABLE"
    master_global_access = true
    private_endpoint     = true
    default_snat         = true
  }
}

variable "features" {
  type = object({
    binary_authorization = optional(bool, false)
    confidential_nodes   = optional(bool, false)
    secret_manager       = optional(bool, true)
    gateway_api          = optional(bool, true)
  })
  default = {
    binary_authorization = false
    confidential_nodes   = false
    secret_manager       = true
    gateway_api          = true
  }
}

variable "nap" {
  type = object({
    tags = optional(list(string), null)
  })
  default = null
}


variable "dns" {
  type = object({
    cluster_dns                   = optional(string, "CLOUD_DNS")
    cluster_dns_scope             = optional(string, "CLUSTER_SCOPE")
    cluster_dns_domain            = optional(string, "cluster.local")
    additive_vpc_scope_dns_domain = optional(string)
  })
  default = null
}
