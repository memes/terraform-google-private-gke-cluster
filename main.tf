terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.27"
    }
  }
}

data "google_compute_subnetwork" "subnet" {
  self_link = var.subnet.self_link
}

resource "google_container_cluster" "cluster" {
  provider                    = google-beta
  project                     = var.project_id
  name                        = var.name
  description                 = coalesce(var.description, format("Private standard GKE cluster %s", var.name))
  location                    = data.google_compute_subnetwork.subnet.region
  min_master_version          = var.options.release_channel == "UNSPECIFIED" ? var.options.version : null
  default_max_pods_per_node   = var.options.max_pods_per_node
  enable_kubernetes_alpha     = var.features.alpha
  enable_tpu                  = var.features.tpu
  enable_legacy_abac          = false
  enable_shielded_nodes       = var.features.shielded_nodes
  initial_node_count          = 1
  remove_default_node_pool    = true
  networking_mode             = "VPC_NATIVE"
  network                     = data.google_compute_subnetwork.subnet.network
  resource_labels             = merge({ cluster_name = var.name }, var.labels)
  subnetwork                  = data.google_compute_subnetwork.subnet.self_link
  enable_intranode_visibility = var.features.intranode_visibility
  enable_l4_ilb_subsetting    = var.features.l7_lb # Always enable if HTTP LB option is set
  # TODO @memes - IPv6 support?
  # private_ipv6_google_access = false
  datapath_provider   = "ADVANCED_DATAPATH"
  logging_service     = "logging.googleapis.com/kubernetes"
  monitoring_service  = "monitoring.googleapis.com/kubernetes"
  deletion_protection = var.options.deletion_protection

  addons_config {
    horizontal_pod_autoscaling {
      disabled = !var.features.hpa
    }
    http_load_balancing {
      disabled = !var.features.l7_lb
    }
    # Network policy must be explicitly disabled for use with Datapath V2
    network_policy_config {
      disabled = true
    }
    gcp_filestore_csi_driver_config {
      enabled = var.features.csi_filestore
    }
    cloudrun_config {
      disabled = !var.features.cloudrun
    }
    istio_config {
      disabled = !var.features.istio
      auth     = var.features.istio ? "AUTH_MUTUAL_TLS" : null
    }
    dns_cache_config {
      enabled = false
    }
    gce_persistent_disk_csi_driver_config {
      enabled = var.features.csi_gce_pd
    }
    kalm_config {
      enabled = var.features.kalm
    }
    config_connector_config {
      enabled = var.features.config_connector
    }
    gke_backup_agent_config {
      enabled = var.features.gke_backup
    }
  }

  dynamic "cluster_autoscaling" {
    for_each = var.autoscaling != null ? [1] : []
    content {
      enabled             = true
      autoscaling_profile = var.autoscaling.autoscaling_profile
      dynamic "resource_limits" {
        for_each = try(var.autoscaling.resource_limits, [])
        content {
          resource_type = resource_limits.value.resource_type
          minimum       = resource_limits.value.minimum
          maximum       = resource_limits.value.maximum
        }
      }
      dynamic "auto_provisioning_defaults" {
        for_each = var.autoscaling.nap != null ? [1] : []
        content {
          service_account = var.service_account
          oauth_scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
          ]
          min_cpu_platform  = var.autoscaling.nap.min_cpu_platform
          boot_disk_kms_key = var.autoscaling.nap.boot_disk_kms_key
          disk_size         = var.autoscaling.nap.disk_size
          disk_type         = var.autoscaling.nap.disk_type
          image_type        = var.autoscaling.nap.image_type
          shielded_instance_config {
            enable_integrity_monitoring = var.autoscaling.nap.enable_integrity_monitoring
            enable_secure_boot          = var.autoscaling.nap.enable_secure_boot
          }
          management {
            auto_repair  = var.autoscaling.nap.auto_repair
            auto_upgrade = var.autoscaling.nap.auto_upgrade
          }
        }
      }
    }
  }

  dynamic "node_pool_auto_config" {
    for_each = var.autoscaling == null ? [] : (var.autoscaling.nap == null ? [] : (var.autoscaling.nap.tags == null ? [] : length(var.autoscaling.nap.tags) > 0 ? [1] : []))
    content {
      network_tags {
        tags = var.autoscaling.nap.tags
      }
    }
  }

  binary_authorization {
    evaluation_mode = var.features.binary_authorization ? "PROJECT_SINGLETON_POLICY_ENFORCE" : "DISABLED"
  }

  identity_service_config {
    enabled = var.features.identity_service
  }

  service_external_ips_config {
    enabled = var.features.service_external_ips
  }

  # TODO - keep/refine?
  mesh_certificates {
    enable_certificates = true
  }

  database_encryption {
    state    = can(coalesce(var.options.etcd_kms)) ? "ENCRYPTED" : "DECRYPTED"
    key_name = try(var.options.etcd_kms, "")
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = var.subnet.pods_range_name
    services_secondary_range_name = var.subnet.services_range_name
  }

  maintenance_policy {
    dynamic "daily_maintenance_window" {
      for_each = can(coalesce(var.maintenance.recurrence)) && can(coalesce(var.maintenance.end_time)) ? [] : [1]
      content {
        start_time = var.maintenance.start_time
      }
    }
    dynamic "recurring_window" {
      for_each = can(coalesce(var.maintenance.recurrence)) && can(coalesce(var.maintenance.end_time)) ? [1] : []
      content {
        start_time = var.maintenance.start_time
        end_time   = var.maintenance.end_time
        recurrence = var.maintenance.recurrence
      }
    }
    dynamic "maintenance_exclusion" {
      for_each = try(var.maintenance.exclusions, [])
      content {
        exclusion_name = maintenance_exclusion.value.name
        start_time     = maintenance_exclusion.value.start_time
        end_time       = maintenance_exclusion.value.end_time
        dynamic "exclusion_options" {
          for_each = can(coalesce(maintenance_exclusion.value.exclusion_scope)) ? [maintenance_exclusion.value.exclusion_scope] : []
          content {
            scope = exclusion_options.value
          }
        }
      }
    }
  }

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  dynamic "master_authorized_networks_config" {
    for_each = try(length(var.master_authorized_networks), 0) > 0 ? [1] : []
    content {
      dynamic "cidr_blocks" {
        for_each = var.master_authorized_networks
        content {
          cidr_block   = cidr_blocks.value.cidr_block
          display_name = cidr_blocks.value.display_name
        }
      }
    }
  }

  # Network policy must be explicitly disabled for use with Datapath V2
  network_policy {
    enabled  = false
    provider = null
  }

  confidential_nodes {
    enabled = var.features.confidential_nodes
  }

  pod_security_policy_config {
    enabled = false
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = try(var.options.private_endpoint, true)
    master_ipv4_cidr_block  = var.subnet.master_cidr
    dynamic "master_global_access_config" {
      for_each = var.options.master_global_access ? [var.options.master_global_access] : []
      content {
        enabled = master_global_access_config.value
      }
    }
  }

  release_channel {
    channel = var.options.release_channel
  }

  cost_management_config {
    enabled = false
  }

  vertical_pod_autoscaling {
    enabled = var.features.vpa
  }

  workload_identity_config {
    # NOTE: @memes uses workload identity extensively so always set a sane default if unspecified
    workload_pool = coalesce(var.options.workload_pool, format("%s.svc.id.goog", var.project_id))
  }

  default_snat_status {
    disabled = !try(var.options.default_snat, true)
  }

  dynamic "dns_config" {
    for_each = var.dns == null ? [] : [var.dns]
    content {
      cluster_dns        = dns_config.value.cluster_dns
      cluster_dns_scope  = dns_config.value.cluster_dns_scope
      cluster_dns_domain = dns_config.value.cluster_dns_domain
    }
  }

  lifecycle {
    ignore_changes = [
      node_config,
      node_pool,
      initial_node_count,
      resource_labels,
    ]
  }

  timeouts {
    create = "60m"
    update = "60m"
    delete = "60m"
  }
}

resource "google_container_node_pool" "pools" {
  provider           = google-beta
  for_each           = var.node_pools == null ? {} : var.node_pools
  project            = var.project_id
  name_prefix        = format("%s-", each.key)
  cluster            = google_container_cluster.cluster.name
  location           = google_container_cluster.cluster.location
  initial_node_count = var.autoscaling != null ? null : each.value.min_nodes_per_zone
  # TODO @memes - review
  # node_count = var.autoscaling != null ? null : each.value.min_nodes_per_zone
  max_pods_per_node = google_container_cluster.cluster.default_max_pods_per_node
  version           = each.value.auto_upgrade ? null : google_container_cluster.cluster.min_master_version

  dynamic "autoscaling" {
    for_each = each.value.autoscaling ? [1] : []
    content {
      min_node_count = each.value.min_nodes_per_zone
      max_node_count = each.value.max_nodes_per_zone
    }
  }

  management {
    auto_repair  = each.value.auto_repair
    auto_upgrade = each.value.auto_upgrade
  }

  node_config {
    disk_size_gb = each.value.disk_size
    disk_type    = each.value.disk_type
    image_type   = each.value.image_type
    labels = merge({
      node_pool    = each.key
      cluster_name = var.name
    }, var.labels, each.value.labels)
    local_ssd_count = each.value.local_ssd_count
    machine_type    = each.value.machine_type
    metadata = merge({
      cluster_name = var.name
      node_pool    = each.key
    }, each.value.metadata, { disable-legacy-endpoints = true })
    min_cpu_platform = each.value.min_cpu_platform
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
    preemptible       = each.value.preemptible
    spot              = each.value.spot
    boot_disk_kms_key = each.value.boot_disk_kms_key
    service_account   = var.service_account
    tags              = each.value.tags

    dynamic "ephemeral_storage_config" {
      for_each = each.value.ephemeral_local_ssd_count > 0 ? [each.value.ephemeral_local_ssd_count] : []
      content {
        local_ssd_count = ephemeral_storage_config.value
      }
    }

    gcfs_config {
      enabled = each.value.enable_gcfs
    }

    gvnic {
      enabled = each.value.enable_gvnic
    }

    dynamic "sandbox_config" {
      for_each = each.value.enable_gvisor_sandbox ? ["gvisor"] : []
      content {
        sandbox_type = sandbox_config.value
      }
    }

    shielded_instance_config {
      enable_secure_boot          = each.value.enable_secure_boot
      enable_integrity_monitoring = each.value.enable_integrity_monitoring
    }

    dynamic "taint" {
      for_each = each.value.taints == null ? [] : each.value.taints
      content {
        key    = taint.value.key
        value  = taint.value.value
        effect = taint.value.effect
      }
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    dynamic "linux_node_config" {
      for_each = try(length(each.value.sysctls), 0) > 0 ? [each.value.sysctls] : []
      content {
        sysctls = linux_node_config.value
      }
    }

    dynamic "guest_accelerator" {
      for_each = try(length(each.value.gpus), 0) > 0 ? {} : {}
      content {
        type  = guest_accelerator.value.type
        count = try(guest_accelerator.value.count, 0)
        dynamic "gpu_driver_installation_config" {
          for_each = try(guest_accelerator.value.install_driver, false) ? { version = coalesce(guest_accelerator.value.driver_version, "GPU_DRIVER_VERSION_UNSPECIFIED") } : {}
          content {
            gpu_driver_version = gpu_driver_installation_config.value
          }
        }
        # gpu_partition_size = XXX
        dynamic "gpu_sharing_config" {
          for_each = try(guest_accelerator.value.sharing, null) != null ? { sharing = guest_accelerator.value.sharing } : {}
          content {
            gpu_sharing_strategy       = coalesce(try(gpu_sharing_config.value.strategy, null), "TIME_SHARING")
            max_shared_clients_per_gpu = gpu_sharing_config.value.max_clients
          }
        }
      }
    }
  }

  upgrade_settings {
    max_surge       = each.value.max_surge
    max_unavailable = each.value.max_unavailable
    strategy        = "SURGE"
  }

  dynamic "placement_policy" {
    for_each = can(coalesce(each.value.placement_policy)) ? [each.value.placement_policy] : []
    content {
      type = placement_policy.value
    }
  }

  lifecycle {
    ignore_changes = [
      initial_node_count,
      node_config.0.taint,
    ]
    create_before_destroy = true
  }

  timeouts {
    create = "60m"
    update = "60m"
    delete = "60m"
  }
}
