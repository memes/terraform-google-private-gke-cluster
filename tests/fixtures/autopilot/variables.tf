variable "project_id" {
  type = string
}

variable "name" {
  type = string
}

variable "description" {
  type    = string
  default = null
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
  })
  default = {
    binary_authorization = false
    confidential_nodes   = false
    secret_manager       = true
  }
}

variable "nap" {
  type = object({
    tags = optional(list(string), null)
  })
  default = null
}
