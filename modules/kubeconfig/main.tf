terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 7.1"
    }
  }
}

data "google_container_cluster" "cluster" {
  project  = reverse(split("/", var.cluster_id))[4]
  name     = reverse(split("/", var.cluster_id))[0]
  location = reverse(split("/", var.cluster_id))[2]
}

check "cluster_endpoint" {
  assert {
    condition = var.use_private_endpoint ? try(
      length(trimspace(data.google_container_cluster.cluster.private_cluster_config[0].private_endpoint)), 0
      ) != 0 : length(compact(
        [
          try(data.google_container_cluster.cluster.control_plane_endpoints_config[0].dns_endpoint_config[0].endpoint, null),
          try(data.google_container_cluster.cluster.private_cluster_config[0].private_endpoint, null),
        ]
    )) > 0
    error_message = "A valid endpoint meeting the requirements could not be determined."
  }
}

locals {
  # Trigger IP address endpoint if the flag is true, or if there isn't a DNS endpoint defined.
  use_private_endpoint = var.use_private_endpoint || length(compact([try(data.google_container_cluster.cluster.control_plane_endpoints_config[0].dns_endpoint_config[0].endpoint, null)])) == 0
  # NOTE: CA cert is only required if use_private_endpoint is true or the DNS endpoint is undefined allow terraform/tofu to raise an error if it is
  # not in the cluster data.
  ca_cert = local.use_private_endpoint ? data.google_container_cluster.cluster.master_auth[0].cluster_ca_certificate : null
  # Prefer the DNS endpoint, if present, with fallback to private IP address. Always use private IP address if
  # use_private_address flag is true.
  # NOTE: This deliberately raises an error if the use_private_endpoint flag is true and a private IP address is not
  # present, or if both DNS and private IP address are missing as this indicates a major problem.
  endpoint = local.use_private_endpoint ? try(data.google_container_cluster.cluster.private_cluster_config[0].private_endpoint, null) : try(compact(
    [
      try(data.google_container_cluster.cluster.control_plane_endpoints_config[0].dns_endpoint_config[0].endpoint, null),
      try(data.google_container_cluster.cluster.private_cluster_config[0].private_endpoint, null),
    ]
  )[0], null)
  kubeconfig = templatefile(format("%s/templates/kubeconfig.yaml", path.module), {
    context_name = coalesce(try(trimspace(var.context_name), ""), data.google_container_cluster.cluster.name)
    cluster_name = coalesce(try(trimspace(var.cluster_name), ""), data.google_container_cluster.cluster.name)
    ca_cert      = local.ca_cert
    endpoint     = local.endpoint
    proxy_url    = var.proxy_url
    user_name    = coalesce(try(trimspace(var.user.name), ""), data.google_container_cluster.cluster.name)
    user_token   = try(var.user.token, null)
  })
}
