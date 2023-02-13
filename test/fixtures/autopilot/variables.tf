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

variable "subnet" {
  type = object({
    self_link           = string
    pods_range_name     = string
    services_range_name = string
    master_cidr         = string
  })
}

variable "master_authorized_networks" {
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
}

variable "service_account" {
  type = string
}

variable "labels" {
  type    = map(string)
  default = {}
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
}

variable "nap" {
  type = object({
    tags = list(string)
  })
  default = null
}
