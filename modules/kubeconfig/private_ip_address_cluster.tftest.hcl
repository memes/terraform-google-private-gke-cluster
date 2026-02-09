# Implement a set of tests to validate the effect of use_private_endpoint variable on the generated Kubeconfig, when
# used with a simulated GKE cluster having private IP address endpoint only.

mock_provider "google" {}

variables {
  cluster_id = "projects/mock-project/locations/us-west1/clusters/gke-mock"
}

# Define cluster with only private IP address endpoint defined.
override_data {
  target = data.google_container_cluster.cluster
  values = {
    control_plane_endpoints_config = [
      {
        dns_endpoint_config = null
        ip_endpoints_config = [
          {
            enabled = true
          }
        ]
      },
    ]
    master_auth = [
      {
        client_certificate        = null
        client_certificate_config = []
        client_key                = null
        cluster_ca_certificate    = "base64 encoded PEM"
      },
    ]
    private_cluster_config = [
      {
        enable_private_nodes        = true
        enable_private_endpoint     = true
        master_ipv4_cidr_block      = "192.168.0.0/28"
        private_endpoint_subnetwork = "gke-mock"
        master_global_access_config = [
          {
            enabled = false
          },
        ]
        peering_name     = "gke-mock-peer"
        private_endpoint = "192.168.0.2"
        public_endpoint  = null
      },
    ]
  }
}

# Default case should fall back to private IP endpoint as the DNS endpoint is missing.
run "default" {
  assert {
    condition     = can(yamldecode(output.kubeconfig))
    error_message = "Generated kubeconfig is not valid YAML."
  }
  # NOTE: Tests are using the local.kubeconfig, not output, so that failures show visible diff
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0], "name") == "gke-mock"
    error_message = "Generated kubeconfig cluster name does not match expectations."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "certificate-authority-data", null) == "base64 encoded PEM"
    error_message = "Generated kubeconfig cluster has unexpected CA certificate definition."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "server", null) == "https://192.168.0.2"
    error_message = "Generated kubeconfig is not using the private IP address endpoint."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "proxy-url", null) == null
    error_message = "Generated kubeconfig should not have proxy-url defined."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["contexts"][0], "name") == "gke-mock"
    error_message = "Generated kubeconfig context name does not match expectations."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0], "name") == "gke-mock"
    error_message = "Generated kubeconfig user name does not match expectations."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0]["user"], "token", null) == null
    error_message = "Generated kubeconfig user should not have token authentication."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0]["user"], "exec", null) != null
    error_message = "Generated kubeconfig user is missing exec authentication block."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0]["user"]["exec"], "command", null) == "gke-gcloud-auth-plugin"
    error_message = "Generated kubeconfig user exec authentication command does not meet expectations."
  }
}

# Explicit use of private endpoint should return the private IP address endpoint.
run "use_private_endpoint" {
  variables {
    use_private_endpoint = true
  }
  assert {
    condition     = can(yamldecode(output.kubeconfig))
    error_message = "Generated kubeconfig is not valid YAML."
  }
  # NOTE: Tests are using the local.kubeconfig, not output, so that failures show visible diff
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0], "name") == "gke-mock"
    error_message = "Generated kubeconfig cluster name does not match expectations."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "certificate-authority-data", null) == "base64 encoded PEM"
    error_message = "Generated kubeconfig cluster has unexpected CA certificate definition '${lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "certificate-authority-data", null)}'"
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "server", null) == "https://192.168.0.2"
    error_message = "Generated kubeconfig is not using the private IP address endpoint."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "proxy-url", null) == null
    error_message = "Generated kubeconfig should not have proxy-url defined."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["contexts"][0], "name") == "gke-mock"
    error_message = "Generated kubeconfig context name does not match expectations."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0], "name") == "gke-mock"
    error_message = "Generated kubeconfig user name does not match expectations."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0]["user"], "token", null) == null
    error_message = "Generated kubeconfig user should not have token authentication."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0]["user"], "exec", null) != null
    error_message = "Generated kubeconfig user is missing exec authentication block."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0]["user"]["exec"], "command", null) == "gke-gcloud-auth-plugin"
    error_message = "Generated kubeconfig user exec authentication command does not meet expectations."
  }
}
