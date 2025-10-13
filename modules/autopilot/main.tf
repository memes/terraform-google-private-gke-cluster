terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 7.1"
    }
  }
}

data "google_compute_subnetwork" "subnet" {
  self_link = var.subnet.self_link
}

resource "google_container_cluster" "cluster" {
  project                  = var.project_id
  name                     = var.name
  description              = coalesce(var.description, "Private Autopilot GKE cluster for demo")
  location                 = data.google_compute_subnetwork.subnet.region
  enable_autopilot         = true
  networking_mode          = "VPC_NATIVE"
  network                  = data.google_compute_subnetwork.subnet.network
  resource_labels          = var.labels
  subnetwork               = data.google_compute_subnetwork.subnet.self_link
  enable_l4_ilb_subsetting = true
  datapath_provider        = "ADVANCED_DATAPATH"
  logging_service          = "logging.googleapis.com/kubernetes"
  monitoring_service       = "monitoring.googleapis.com/kubernetes"
  deletion_protection      = false

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
    for_each = try(length(var.master_authorized_networks), 0) > 0 ? { enabled = true } : {}
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
    enabled = try(var.features.confidential_nodes, false)
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = try(var.options.private_endpoint, true) ? true : null
    master_ipv4_cidr_block  = try(var.subnet.master_cidr, "192.168.0.0/28")
    master_global_access_config {
      enabled = try(var.options.master_global_access, false)
    }
  }

  release_channel {
    channel = try(var.options.release_channel, "STABLE")
  }

  default_snat_status {
    disabled = !try(var.options.default_snat, true)
  }

  secret_manager_config {
    enabled = try(var.features.secret_manager, true)
    rotation_config {
      enabled = true
    }
  }

  dynamic "dns_config" {
    for_each = var.dns == null ? {} : { dns = var.dns }
    content {
      cluster_dns                   = try(dns_config.value.cluster_dns, "CLOUD_DNS")
      cluster_dns_scope             = "CLUSTER_SCOPE" # This is the only valid option for Autopilot clusters
      cluster_dns_domain            = try(dns_config.value.cluster_dns_domain, "cluster.local")
      additive_vpc_scope_dns_domain = try(dns_config.value.cluster_dns, "CLOUD_DNS") == "CLOUD_DNS" ? try(dns_config.value.additive_vpc_scope_dns_domain, null) : null
    }
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
