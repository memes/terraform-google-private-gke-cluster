# Implement a set of tests to validate the effect of use_private_endpoint on the generated Kubeconfig, when used with a
# simulated GKE cluster having a DNS endpoint only.

mock_provider "google" {}

variables {
  cluster_id = "projects/mock-project/locations/us-west1/clusters/gke-mock"
}

# Define cluster with only DNS endpoint defined.
override_data {
  target = data.google_container_cluster.cluster
  values = {
    control_plane_endpoints_config = [
      {
        dns_endpoint_config = [
          {
            endpoint                  = "gke-mock.us-west1.gke.goog"
            allow_external_traffic    = true
            enable_k8s_certs_via_dns  = false
            enable_k8s_tokens_via_dns = false
          },
        ]
        ip_endpoints_config = null
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
        enable_private_endpoint     = false
        master_ipv4_cidr_block      = "192.168.0.0/28"
        private_endpoint_subnetwork = "gke-mock"
        master_global_access_config = [
          {
            enabled = false
          },
        ]
        peering_name     = "gke-mock-peer"
        private_endpoint = null
        public_endpoint  = "1.2.3.4"
      },
    ]
  }
}

# Default use-case should return the cluster's DNS endpoint.
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
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "certificate-authority-data", null) == null
    error_message = "Generated kubeconfig cluster has unexpected CA certificate definition."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "server", null) == "https://gke-mock.us-west1.gke.goog"
    error_message = "Generated kubeconfig is not using the DNS endpoint."
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

# Attempting to force use of private IP endpoint in a DNS only cluster should raise an error.
run "use_private_endpoint" {
  variables {
    use_private_endpoint = true
  }
  expect_failures = [
    check.cluster_endpoint,
  ]
}
