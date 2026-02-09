# Private autopilot cluster

This Terraform module creates a private GKE Autopilot cluster.

<!-- markdownlint-disable MD033 MD034 MD060 -->
<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5 |
| <a name="requirement_google"></a> [google](#requirement\_google) | >= 7.18 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [google-beta_google_container_cluster.cluster](https://registry.terraform.io/providers/hashicorp/google-beta/latest/docs/resources/google_container_cluster) | resource |
| [google_compute_subnetwork.subnet](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/compute_subnetwork) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_name"></a> [name](#input\_name) | The name to use when naming resources managed by this module. Must be RFC1035<br/>compliant and between 1 and 63 characters in length, inclusive. | `string` | n/a | yes |
| <a name="input_project_id"></a> [project\_id](#input\_project\_id) | The GCP project identifier where the Autopilot GKE cluster will be created. | `string` | n/a | yes |
| <a name="input_service_account"></a> [service\_account](#input\_service\_account) | The Compute Engine service account that worker nodes will use. | `string` | n/a | yes |
| <a name="input_subnet"></a> [subnet](#input\_subnet) | Provides the subnet self\_link to which the cluster will be attached, the<br/>*names* of the secondary ranges to use for pods and services, and the CIDR to<br/>use for masters. | <pre>object({<br/>    self_link           = string<br/>    pods_range_name     = optional(string, "pods")<br/>    services_range_name = optional(string, "services")<br/>  })</pre> | n/a | yes |
| <a name="input_control_plane_access"></a> [control\_plane\_access](#input\_control\_plane\_access) | Defines the control-plane access options. By default, the cluster will allow API access via DNS endpoint from within<br/>Google Cloud, and direct IP access is disabled. These options can be changed by overriding the default values. | <pre>object({<br/>    enable_dns_access       = optional(bool, true)<br/>    enable_ip_access        = optional(bool, false)<br/>    external_dns_access     = optional(bool, true)<br/>    gcp_public_cidrs_access = optional(bool, false)<br/>    master_global_access    = optional(bool, false)<br/>    master_cidr             = optional(string) #optional(string, "192.168.0.0/28")<br/>    authorized_cidrs = optional(list(object({<br/>      cidr_block   = string<br/>      display_name = string<br/>    })))<br/>  })</pre> | <pre>{<br/>  "authorized_cidrs": null,<br/>  "enable_dns_access": true,<br/>  "enable_ip_access": false,<br/>  "external_dns_access": true,<br/>  "gcp_public_cidrs_access": false,<br/>  "master_cidr": null,<br/>  "master_global_access": false<br/>}</pre> | no |
| <a name="input_description"></a> [description](#input\_description) | An optional description to add to the Autopilot GKE cluster. | `string` | `"Private Autopilot GKE cluster for demo"` | no |
| <a name="input_features"></a> [features](#input\_features) | The set of boolean feature flags that will be enabled on the Autopilot cluster. Unless modified, the cluster will be<br/>created with Default SNAT, Secret Manager integration, Managed Prometheus, and Gateway API support enabled. Other features will be<br/>disabled, including some CSIs that are typically enabled when creating a GKE cluster through the console.<br/>NOTE: To use Privately Used Public IP addresses (PUPI) CIDRs for pods or services, set the default\_snat flag to false. | <pre>object({<br/>    default_snat                        = optional(bool, true)<br/>    binary_authorization                = optional(bool, false)<br/>    confidential_nodes                  = optional(bool, false)<br/>    secret_manager                      = optional(bool, true)<br/>    gateway_api                         = optional(bool, true)<br/>    dataplane_v2_advanced_observability = optional(bool, false)<br/>    filestore_csi                       = optional(bool, false)<br/>    parallelstore_csi                   = optional(bool, false)<br/>    lustre_csi                          = optional(bool, false)<br/>    ray_operator                        = optional(bool, false)<br/>    disable_auto_lb_firewall            = optional(bool, false)<br/>    managed_prometheus                  = optional(bool, true)<br/>    managed_opentelemetry               = optional(bool, false)<br/>  })</pre> | <pre>{<br/>  "binary_authorization": false,<br/>  "confidential_nodes": false,<br/>  "dataplane_v2_advanced_observability": false,<br/>  "default_snat": true,<br/>  "disable_auto_lb_firewall": false,<br/>  "filestore_csi": false,<br/>  "gateway_api": true,<br/>  "lustre_csi": false,<br/>  "managed_opentelemetry": false,<br/>  "managed_prometheus": true,<br/>  "parallelstore_csi": false,<br/>  "ray_operator": false,<br/>  "secret_manager": true<br/>}</pre> | no |
| <a name="input_labels"></a> [labels](#input\_labels) | An optional set of key:value string pairs that will be added to the Autopilot resources. | `map(string)` | `{}` | no |
| <a name="input_nap"></a> [nap](#input\_nap) | Configures cluster-scoped node auto-provisioning parameters for use with autopilot.<br/>Currently, only network tags can be specified. | <pre>object({<br/>    tags = optional(list(string), null)<br/>  })</pre> | `null` | no |
| <a name="input_options"></a> [options](#input\_options) | Defines the set of GKE options to use when provisioning the cluster. Default values will initiate an Autopilot cluster<br/>from GKE's REGULAR release channel that is not registered to an Enterprise GKE fleet. If you<br/>want to use Privately Used Public IP addresses (PUPI) CIDRs for pods or services, set the default\_snat flag to false. | <pre>object({<br/>    release_channel = optional(string, "REGULAR")<br/>    fleet           = optional(string)<br/>  })</pre> | <pre>{<br/>  "fleet": null,<br/>  "release_channel": "REGULAR"<br/>}</pre> | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_ca_cert"></a> [ca\_cert](#output\_ca\_cert) | The base64 encoded CA certificate used by the kubernetes master. |
| <a name="output_dns_endpoint_url"></a> [dns\_endpoint\_url](#output\_dns\_endpoint\_url) | n/a |
| <a name="output_id"></a> [id](#output\_id) | The unique identifier of the Autopilot cluster. |
| <a name="output_location"></a> [location](#output\_location) | The location of the Autopilot cluster. |
| <a name="output_name"></a> [name](#output\_name) | The name of the Autopilot cluster. |
| <a name="output_private_ip_endpoint_url"></a> [private\_ip\_endpoint\_url](#output\_private\_ip\_endpoint\_url) | The URL to use for master access. |
<!-- END_TF_DOCS -->
<!-- markdownlint-enable MD033 MD034 MD060 -->
