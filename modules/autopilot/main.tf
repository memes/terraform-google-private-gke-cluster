terraform {
  required_version = ">= 1.2"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.42"
    }
  }
}

data "google_compute_subnetwork" "subnet" {
  self_link = var.subnet.self_link
}

locals {
  labels = merge({
    cluster_name     = var.name
    terraform_module = "private-gke-cluster_autopilot"
  }, var.labels)
}

resource "google_container_cluster" "cluster" {
  provider                 = google-beta
  project                  = var.project_id
  name                     = var.name
  description              = coalesce(var.description, format("Private autopilot GKE cluster %s", var.name))
  location                 = data.google_compute_subnetwork.subnet.region
  enable_autopilot         = true
  min_master_version       = var.options.release_channel == "UNSPECIFIED" ? var.options.version : null
  networking_mode          = "VPC_NATIVE"
  network                  = data.google_compute_subnetwork.subnet.network
  resource_labels          = local.labels
  subnetwork               = data.google_compute_subnetwork.subnet.self_link
  enable_l4_ilb_subsetting = true
  datapath_provider        = "ADVANCED_DATAPATH"
  logging_service          = "logging.googleapis.com/kubernetes"
  monitoring_service       = "monitoring.googleapis.com/kubernetes"

  # These addons are required to be enabled for autopilot clusters
  addons_config {
    horizontal_pod_autoscaling {
      disabled = false
    }
    http_load_balancing {
      disabled = false
    }
  }

  dynamic "node_pool_auto_config" {
    for_each = length(try(var.nap.tags, [])) > 0 ? [1] : []
    content {
      network_tags {
        tags = var.nap.tags
      }
    }
  }

  binary_authorization {
    evaluation_mode = var.features.binary_authorization ? "PROJECT_SINGLETON_POLICY_ENFORCE" : "DISABLED"
  }

  service_external_ips_config {
    enabled = false
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

  confidential_nodes {
    enabled = var.features.confidential_nodes
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = try(var.options.private_endpoint, true) ? true : null
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
    enabled = true
  }

  default_snat_status {
    disabled = !try(var.options.default_snat, true)
  }

  lifecycle {
    ignore_changes = [
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
