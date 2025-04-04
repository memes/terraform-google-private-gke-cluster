# Private regional GKE cluster

![GitHub release](https://img.shields.io/github/v/release/memes/terraform-google-private-gke-cluster?sort=semver)
![Maintenance](https://img.shields.io/maintenance/yes/2024)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

This Terraform module creates a private regional GKE cluster:

* Default node pool will be deleted and a dedicated node pool will be created
* All nodes and masters will have private IP addresses only
* Access to master nodes will be restricted to addresses in the VPC network
* Cluster deletion prevention will be disabled
* Options are opinionated; not all configurations are possible in this module.

> NOTE: This module is deliberately restrictive compared to the
> [Google GKE Terraform](https://registry.terraform.io/modules/terraform-google-modules/kubernetes-engine/google/latest)
> module. If you need flexibility you should use that module instead.

## Submodules

* [autopilot](modules/autopilot) provides a private regional Autopilot GKE
  cluster with a subset of options, as permitted for Autopilot clusters.
* [kubeconfig](module/kubeconfig) provides a way to generate a user or Kubernetes
  service account kubeconfig from a GKE self-link.
* [sa](module/sa) will create a Google Cloud service account with recommended
  IAM roles to log and provide monitoring details. If a list of GCR and/or GAR
  repos are provided, the generated SA will be granted read-only access to the
  repos.

<!-- markdownlint-disable MD033 MD034-->
<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5 |
| <a name="requirement_google"></a> [google](#requirement\_google) | >= 6.27 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [google-beta_google_container_cluster.cluster](https://registry.terraform.io/providers/hashicorp/google-beta/latest/docs/resources/google_container_cluster) | resource |
| [google-beta_google_container_node_pool.pools](https://registry.terraform.io/providers/hashicorp/google-beta/latest/docs/resources/google_container_node_pool) | resource |
| [google_compute_subnetwork.subnet](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/compute_subnetwork) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_master_authorized_networks"></a> [master\_authorized\_networks](#input\_master\_authorized\_networks) | A set of CIDRs that are permitted to reach the kubernetes API endpoints. | <pre>list(object({<br/>    cidr_block   = string<br/>    display_name = string<br/>  }))</pre> | n/a | yes |
| <a name="input_name"></a> [name](#input\_name) | The name to use when naming resources managed by this module. Must be RFC1035<br/>compliant and between 1 and 63 characters in length, inclusive. | `string` | n/a | yes |
| <a name="input_node_pools"></a> [node\_pools](#input\_node\_pools) | Defines the mapping of node pool names (keys), to attributes of the node pools. | <pre>map(object({<br/>    auto_upgrade                = bool<br/>    autoscaling                 = bool<br/>    location_policy             = string<br/>    min_nodes_per_zone          = number<br/>    max_nodes_per_zone          = number<br/>    auto_repair                 = bool<br/>    disk_size                   = number<br/>    disk_type                   = string<br/>    image_type                  = string<br/>    labels                      = map(string)<br/>    local_ssd_count             = number<br/>    ephemeral_local_ssd_count   = number<br/>    machine_type                = string<br/>    min_cpu_platform            = string<br/>    preemptible                 = bool<br/>    spot                        = bool<br/>    boot_disk_kms_key           = string<br/>    enable_gcfs                 = bool<br/>    enable_gvnic                = bool<br/>    enable_gvisor_sandbox       = bool<br/>    enable_secure_boot          = bool<br/>    enable_integrity_monitoring = bool<br/>    max_surge                   = number<br/>    max_unavailable             = number<br/>    placement_policy            = string<br/>    metadata                    = map(string)<br/>    sysctls                     = map(string)<br/>    taints = list(object({<br/>      key    = string<br/>      value  = string<br/>      effect = string<br/>    }))<br/>    tags = list(string)<br/>  }))</pre> | n/a | yes |
| <a name="input_project_id"></a> [project\_id](#input\_project\_id) | The GCP project identifier where the GKE cluster will be created. | `string` | n/a | yes |
| <a name="input_service_account"></a> [service\_account](#input\_service\_account) | The Compute Engine service account that worker nodes will use. | `string` | n/a | yes |
| <a name="input_subnet"></a> [subnet](#input\_subnet) | Provides the subnet self\_link to which the cluster will be attached, the<br/>*names* of the secondary ranges to use for pods and services, and the CIDR to<br/>use for masters. | <pre>object({<br/>    self_link           = string<br/>    pods_range_name     = string<br/>    services_range_name = string<br/>    master_cidr         = string<br/>  })</pre> | n/a | yes |
| <a name="input_autoscaling"></a> [autoscaling](#input\_autoscaling) | Configures cluster-scoped node auto-provisioning parameters. If null (default)<br/>then autoscaling with node auto-provisioning will be disabled for the cluster<br/>and node-pool definitions will be required for a functioning cluster. If specified,<br/>a set of resource\_limits containing 'cpu' and 'memory' values must be provided. | <pre>object({<br/>    autoscaling_profile = string<br/>    resource_limits = list(object({<br/>      resource_type = string<br/>      maximum       = number<br/>      minimum       = number<br/>    }))<br/>    nap = object({<br/>      min_cpu_platform            = string<br/>      boot_disk_kms_key           = string<br/>      disk_size                   = number<br/>      disk_type                   = string<br/>      image_type                  = string<br/>      auto_upgrade                = bool<br/>      auto_repair                 = bool<br/>      enable_secure_boot          = bool<br/>      enable_integrity_monitoring = bool<br/>      tags                        = list(string)<br/>    })<br/>  })</pre> | `null` | no |
| <a name="input_description"></a> [description](#input\_description) | An optional description to add to the Autopilot GKE cluster. | `string` | `null` | no |
| <a name="input_dns"></a> [dns](#input\_dns) | An optional value to trigger integration of Cloud DNS as the preferred DNS<br/>provider in the cluster. Default is null, which will create a cluster with<br/>KubeDNS as the provider. | <pre>object({<br/>    cluster_dns        = string<br/>    cluster_dns_scope  = string<br/>    cluster_dns_domain = string<br/>  })</pre> | `null` | no |
| <a name="input_features"></a> [features](#input\_features) | The set of features that will be enabled on the GKE cluster. | <pre>object({<br/>    alpha                = bool<br/>    binary_authorization = bool<br/>    cloudrun             = bool<br/>    confidential_nodes   = bool<br/>    config_connector     = bool<br/>    csi_filestore        = bool<br/>    csi_gce_pd           = bool<br/>    gke_backup           = bool<br/>    hpa                  = bool<br/>    identity_service     = bool<br/>    intranode_visibility = bool<br/>    istio                = bool<br/>    kalm                 = bool<br/>    l7_lb                = bool<br/>    sandbox              = bool<br/>    service_external_ips = bool<br/>    shielded_nodes       = bool<br/>    tpu                  = bool<br/>    vpa                  = bool<br/>  })</pre> | <pre>{<br/>  "alpha": false,<br/>  "binary_authorization": false,<br/>  "cloudrun": false,<br/>  "confidential_nodes": false,<br/>  "config_connector": false,<br/>  "csi_filestore": false,<br/>  "csi_gce_pd": false,<br/>  "gke_backup": false,<br/>  "hpa": true,<br/>  "identity_service": false,<br/>  "intranode_visibility": false,<br/>  "istio": false,<br/>  "kalm": false,<br/>  "l7_lb": true,<br/>  "sandbox": false,<br/>  "service_external_ips": false,<br/>  "shielded_nodes": true,<br/>  "tpu": false,<br/>  "vpa": false<br/>}</pre> | no |
| <a name="input_labels"></a> [labels](#input\_labels) | An optional set of key:value string pairs that will be added on the | `map(string)` | `{}` | no |
| <a name="input_maintenance"></a> [maintenance](#input\_maintenance) | Defines the times that GKE is permitted to perform automatic cluster maintenance. | <pre>object({<br/>    start_time = string<br/>    end_time   = string<br/>    exclusions = list(object({<br/>      name            = string<br/>      start_time      = string<br/>      end_time        = string<br/>      exclusion_scope = string<br/>    }))<br/>    recurrence = string<br/>  })</pre> | <pre>{<br/>  "end_time": "",<br/>  "exclusions": [],<br/>  "recurrence": "",<br/>  "start_time": "05:00"<br/>}</pre> | no |
| <a name="input_options"></a> [options](#input\_options) | Defines the set of GKE options to use when provisioning the cluster. Default<br/>values will create cluster from the STABLE release channel with private RFC1918 endpoint. | <pre>object({<br/>    release_channel      = string<br/>    version              = string<br/>    workload_pool        = string<br/>    master_global_access = bool<br/>    etcd_kms             = string<br/>    max_pods_per_node    = number<br/>    private_endpoint     = bool<br/>    default_snat         = bool<br/>    deletion_protection  = bool<br/>  })</pre> | <pre>{<br/>  "default_snat": true,<br/>  "deletion_protection": false,<br/>  "etcd_kms": null,<br/>  "master_global_access": true,<br/>  "max_pods_per_node": 110,<br/>  "private_endpoint": true,<br/>  "release_channel": "STABLE",<br/>  "version": null,<br/>  "workload_pool": null<br/>}</pre> | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_ca_cert"></a> [ca\_cert](#output\_ca\_cert) | The base64 encoded CA certificate used by the kubernetes master. |
| <a name="output_endpoint_url"></a> [endpoint\_url](#output\_endpoint\_url) | The URL to use for master access. |
| <a name="output_id"></a> [id](#output\_id) | The unique identifier of the GKE cluster. |
| <a name="output_location"></a> [location](#output\_location) | The location of the GKE cluster. |
| <a name="output_name"></a> [name](#output\_name) | The name of the GKE cluster. |
| <a name="output_public_endpoint_url"></a> [public\_endpoint\_url](#output\_public\_endpoint\_url) | The URL to use for master access. |
<!-- END_TF_DOCS -->
<!-- markdownlint-enable MD033 MD034 -->
