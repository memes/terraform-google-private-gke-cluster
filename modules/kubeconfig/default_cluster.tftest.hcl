# Implement a set of tests to validate the effect of variable combinations on the generated Kubeconfig, when used with a
# simulated GKE cluster having DNS and private IP address endpoints.

mock_provider "google" {}

variables {
  cluster_id = "projects/mock-project/locations/us-west1/clusters/gke-mock"
}

# Default GKE cluster has DNS and private IP address endpoints defined.
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
        enable_private_endpoint     = false
        master_ipv4_cidr_block      = "192.168.0.0/28"
        private_endpoint_subnetwork = "gke-mock"
        master_global_access_config = [
          {
            enabled = false
          },
        ]
        peering_name     = "gke-mock-peer"
        private_endpoint = "192.168.0.2"
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

# Verify cluster name can be changed.
run "cluster_name" {
  variables {
    cluster_name = "override-cluster-name"
  }
  assert {
    condition     = can(yamldecode(output.kubeconfig))
    error_message = "Generated kubeconfig is not valid YAML."
  }
  # NOTE: Tests are using the local.kubeconfig, not output, so that failures show visible diff
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0], "name") == "override-cluster-name"
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

# Verify default behavior is preserved when cluster_name is an empty string.
run "cluster_name_empty_string" {
  variables {
    cluster_name = ""
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

# Verify default behavior is preserved when cluster_name is whitespace string.
run "cluster_name_whitespace" {
  variables {
    cluster_name = "    "
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

# Verify use of an invalid cluster_name raises an error.
run "cluster_name_invalid" {
  command = plan
  variables {
    cluster_name = "emes-test-%%"
  }
  expect_failures = [
    var.cluster_name,
  ]
}

# Verify context name can be changed.
run "context_name" {
  variables {
    context_name = "override-context-name"
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
    condition     = lookup(yamldecode(local.kubeconfig)["contexts"][0], "name") == "override-context-name"
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

# Verify default behavior is preserved when context_name is an empty string.
run "context_name_empty_string" {
  variables {
    context_name = ""
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

# Verify default behavior is preserved when context_name is a whitespace string.
run "context_name_whitespace_string" {
  variables {
    context_name = "   "
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

# Verify use of an invalid context_name raises an error.
run "context_name_invalid" {
  command = plan
  variables {
    context_name = "emes-test-%%"
  }
  expect_failures = [
    var.context_name,
  ]
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
    error_message = "Generated kubeconfig cluster CA certificate does not match expectations."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "server", null) == "https://192.168.0.2"
    error_message = "Generated kubeconfig is not using the private address endpoint."
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

# Verify that specifying a proxy_url shows up in kubeconfig.
run "proxy_url" {
  variables {
    proxy_url = "http://proxy.local:8888"
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
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "certificate-authority-data", null) == null
    error_message = "Generated kubeconfig cluster has unexpected CA certificate definition."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "server", null) == "https://gke-mock.us-west1.gke.goog"
    error_message = "Generated kubeconfig is not using the DNS endpoint."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["clusters"][0]["cluster"], "proxy-url", null) == "http://proxy.local:8888"
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

# Verify default behavior is preserved when proxy_url is an empty string.
run "proxy_url_empty_string" {
  variables {
    proxy_url = ""
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

run "user_name_only" {
  variables {
    user = {
      name = "override-user-name"
    }
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
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0], "name") == "override-user-name"
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

run "user_token_only" {
  variables {
    user = {
      token = "bearer-token"
    }
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
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0]["user"], "token", null) == "bearer-token"
    error_message = "Generated kubeconfig user token authentication does not meet expectations."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0]["user"], "exec", null) == null
    error_message = "Generated kubeconfig user should not have exec authentication block."
  }
}

run "user_name_and_token" {
  variables {
    user = {
      name  = "override-user-name"
      token = "bearer-token"
    }
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
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0], "name") == "override-user-name"
    error_message = "Generated kubeconfig user name does not match expectations."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0]["user"], "token", null) == "bearer-token"
    error_message = "Generated kubeconfig user token authentication does not meet expectations."
  }
  assert {
    condition     = lookup(yamldecode(local.kubeconfig)["users"][0]["user"], "exec", null) == null
    error_message = "Generated kubeconfig user should not have exec authentication block."
  }
}

run "user_name_and_token_empty_string" {
  variables {
    user = {
      name  = ""
      token = ""
    }
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
