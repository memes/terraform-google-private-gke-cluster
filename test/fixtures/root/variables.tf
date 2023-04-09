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

variable "labels" {
  type    = map(string)
  default = {}
}

variable "options" {
  type = object({
    release_channel      = string
    version              = string
    workload_pool        = string
    master_global_access = bool
    etcd_kms             = string
    max_pods_per_node    = number
  })
  default = {
    release_channel      = "STABLE"
    version              = null
    workload_pool        = null
    master_global_access = true
    etcd_kms             = null
    max_pods_per_node    = 110
  }
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
  default = null
}

variable "dns" {
  type = object({
    cluster_dns        = string
    cluster_dns_scope  = string
    cluster_dns_domain = string
  })
  default = null
}

variable "proxy_url" {
  type = string
}
