terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 7.18"
    }
  }
}

data "google_compute_subnetwork" "subnet" {
  self_link = var.subnet.self_link
}

# tflint-ignore: terraform_required_providers
resource "google_container_cluster" "cluster" {
  provider                              = google-beta
  project                               = var.project_id
  name                                  = var.name
  description                           = coalesce(var.description, "Private Autopilot GKE cluster for demo")
  location                              = data.google_compute_subnetwork.subnet.region
  enable_autopilot                      = true
  networking_mode                       = "VPC_NATIVE"
  network                               = data.google_compute_subnetwork.subnet.network
  resource_labels                       = var.labels
  subnetwork                            = data.google_compute_subnetwork.subnet.self_link
  enable_l4_ilb_subsetting              = true
  disable_l4_lb_firewall_reconciliation = try(var.features.disable_auto_lb_firewall, false) ? true : null
  datapath_provider                     = "ADVANCED_DATAPATH"
  deletion_protection                   = false

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:30"
    }
  }

  cluster_autoscaling {
    auto_provisioning_defaults {
      oauth_scopes = [
        "https://www.googleapis.com/auth/cloud-platform",
      ]
      service_account = var.service_account
    }
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = try(var.subnet.pods_range_name, "pods")
    services_secondary_range_name = try(var.subnet.services_range_name, "services")
    # This will fail for IPV6_ONLY subnets, at least until that is a valid GKE option
    stack_type = replace(data.google_compute_subnetwork.subnet.stack_type, "_ONLY", "")
  }

  dynamic "node_pool_auto_config" {
    for_each = length(try(var.nap.tags, [])) > 0 ? { enabled = true } : {}
    content {
      network_tags {
        tags = var.nap.tags
      }
    }
  }

  binary_authorization {
    evaluation_mode = try(var.features.binary_authorization, false) ? "PROJECT_SINGLETON_POLICY_ENFORCE" : "DISABLED"
  }

  dynamic "master_authorized_networks_config" {
    for_each = try(length(var.control_plane_access.authorized_cidrs), 0) > 0 ? { enabled = var.control_plane_access.authorized_cidrs } : {}
    content {
      gcp_public_cidrs_access_enabled      = try(var.control_plane_access.gcp_public_cidrs_access, false)
      private_endpoint_enforcement_enabled = true
      dynamic "cidr_blocks" {
        for_each = master_authorized_networks_config.value
        content {
          cidr_block   = cidr_blocks.value.cidr_block
          display_name = cidr_blocks.value.display_name
        }
      }
    }
  }

  confidential_nodes {
    enabled = try(var.features.confidential_nodes, false)
  }


  control_plane_endpoints_config {
    dynamic "dns_endpoint_config" {
      for_each = try(var.control_plane_access.enable_dns_access, null) == null || var.control_plane_access.enable_dns_access ? { enabled = true } : {}
      content {
        allow_external_traffic    = try(var.control_plane_access.external_dns_access, true)
        enable_k8s_certs_via_dns  = false
        enable_k8s_tokens_via_dns = false
      }
    }
    ip_endpoints_config {
      enabled = try(var.control_plane_access.enable_ip_access, false)
    }
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = true
    master_ipv4_cidr_block  = coalesce(try(var.control_plane_access.master_cidr, "unspecified"), "unspecified") == "unspecified" ? null : var.control_plane_access.master_cidr
    dynamic "master_global_access_config" {
      for_each = try(var.control_plane_access.master_global_access, false) ? { enabled = true } : {}
      content {
        enabled = master_global_access_config.value
      }
    }
  }

  release_channel {
    channel = try(var.options.release_channel, "REGULAR")
  }

  default_snat_status {
    disabled = !try(var.features.default_snat, true)
  }

  secret_manager_config {
    enabled = try(var.features.secret_manager, true)
    rotation_config {
      enabled = true
    }
  }

  gateway_api_config {
    channel = try(var.features.gateway_api, true) ? "CHANNEL_STANDARD" : "CHANNEL_DISABLED"
  }

  dynamic "fleet" {
    for_each = coalesce(try(var.options.fleet, ""), "unspecified") == "unspecified" ? {} : { enabled = var.options.fleet }
    content {
      project = fleet.value
    }
  }

  logging_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "WORKLOADS",
    ]
  }

  monitoring_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "DAEMONSET",
      "DEPLOYMENT",
      "STATEFULSET",
      "JOBSET",
      "STORAGE",
      "HPA",
      "POD",
      "CADVISOR",
      "KUBELET",
      "DCGM",
    ]
    advanced_datapath_observability_config {
      enable_metrics = !try(var.features.dataplane_v2_advanced_observability, false)
      enable_relay   = try(var.features.dataplane_v2_advanced_observability, false)
    }
    managed_prometheus {
      enabled = try(var.features.managed_prometheus, true)
    }
  }

  dynamic "managed_opentelemetry_config" {
    for_each = try(var.features.managed_opentelemetry, false) ? { enabled = true } : {}
    content {
      scope = "COLLECTION_AND_INSTRUMENTATION_COMPONENTS"
    }
  }

  addons_config {
    gke_backup_agent_config {
      enabled = false
    }
    gcp_filestore_csi_driver_config {
      enabled = try(var.features.filestore_csi, true)
    }
    parallelstore_csi_driver_config {
      enabled = try(var.features.parallelstore_csi, false)
    }
    lustre_csi_driver_config {
      enabled = try(var.features.lustre_csi, false)
    }
    ray_operator_config {
      enabled = try(var.features.ray_operator, false)
      # When Ray is enabled, turn on logging and monitoring collectors
      dynamic "ray_cluster_logging_config" {
        for_each = try(var.features.ray_operator, false) ? { enabled = true } : {}
        content {
          enabled = ray_cluster_logging_config.value
        }
      }
      dynamic "ray_cluster_monitoring_config" {
        for_each = try(var.features.ray_operator, false) ? { enabled = true } : {}
        content {
          enabled = ray_cluster_monitoring_config.value
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      initial_node_count,
    ]
  }

  timeouts {
    create = "60m"
    update = "60m"
    delete = "60m"
  }
}
