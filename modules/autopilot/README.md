# Private autopilot cluster

This Terraform module creates a private GKE Autopilot cluster.

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
| [google_compute_subnetwork.subnet](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/compute_subnetwork) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_master_authorized_networks"></a> [master\_authorized\_networks](#input\_master\_authorized\_networks) | A set of CIDRs that are permitted to reach the kubernetes API endpoints. | <pre>list(object({<br/>    cidr_block   = string<br/>    display_name = string<br/>  }))</pre> | n/a | yes |
| <a name="input_name"></a> [name](#input\_name) | The name to use when naming resources managed by this module. Must be RFC1035<br/>compliant and between 1 and 63 characters in length, inclusive. | `string` | n/a | yes |
| <a name="input_project_id"></a> [project\_id](#input\_project\_id) | The GCP project identifier where the Autopilot GKE cluster will be created. | `string` | n/a | yes |
| <a name="input_service_account"></a> [service\_account](#input\_service\_account) | The Compute Engine service account that worker nodes will use. | `string` | n/a | yes |
| <a name="input_subnet"></a> [subnet](#input\_subnet) | Provides the subnet self\_link to which the cluster will be attached, the<br/>*names* of the secondary ranges to use for pods and services, and the CIDR to<br/>use for masters. | <pre>object({<br/>    self_link           = string<br/>    pods_range_name     = string<br/>    services_range_name = string<br/>    master_cidr         = string<br/>  })</pre> | n/a | yes |
| <a name="input_description"></a> [description](#input\_description) | An optional description to add to the Autopilot GKE cluster. | `string` | `null` | no |
| <a name="input_features"></a> [features](#input\_features) | The set of features that will be enabled on the Autopilot cluster. By default,<br/>binary authorization and confidential worker nodes will NOT be enabled. | <pre>object({<br/>    binary_authorization = bool<br/>    confidential_nodes   = bool<br/>  })</pre> | <pre>{<br/>  "binary_authorization": false,<br/>  "confidential_nodes": false<br/>}</pre> | no |
| <a name="input_labels"></a> [labels](#input\_labels) | An optional set of key:value string pairs that will be added to the Autopilot<br/>resources. | `map(string)` | `{}` | no |
| <a name="input_maintenance"></a> [maintenance](#input\_maintenance) | Defines the times that GKE is permitted to perform automatic cluster maintenance. | <pre>object({<br/>    start_time = string<br/>    end_time   = string<br/>    exclusions = list(object({<br/>      name            = string<br/>      start_time      = string<br/>      end_time        = string<br/>      exclusion_scope = string<br/>    }))<br/>    recurrence = string<br/>  })</pre> | <pre>{<br/>  "end_time": "",<br/>  "exclusions": [],<br/>  "recurrence": "",<br/>  "start_time": "05:00"<br/>}</pre> | no |
| <a name="input_nap"></a> [nap](#input\_nap) | Configures cluster-scoped node auto-provisioning parameters for use with autopilot.<br/>Currently, only network tags can be specified. | <pre>object({<br/>    tags = list(string)<br/>  })</pre> | `null` | no |
| <a name="input_options"></a> [options](#input\_options) | Defines the set of GKE options to use when provisioning the cluster. Default<br/>values will initiate an Autopilot cluster from GKE's STABLE release channel,<br/>with global flag enabled on the master access LB, and private RFC1918 endpoint. | <pre>object({<br/>    release_channel      = string<br/>    master_global_access = bool<br/>    etcd_kms             = string<br/>    private_endpoint     = bool<br/>    default_snat         = bool<br/>    deletion_protection  = bool<br/>  })</pre> | <pre>{<br/>  "default_snat": true,<br/>  "deletion_protection": false,<br/>  "etcd_kms": null,<br/>  "master_global_access": true,<br/>  "private_endpoint": true,<br/>  "release_channel": "STABLE"<br/>}</pre> | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_ca_cert"></a> [ca\_cert](#output\_ca\_cert) | The base64 encoded CA certificate used by the kubernetes master. |
| <a name="output_endpoint_url"></a> [endpoint\_url](#output\_endpoint\_url) | The URL to use for master access. |
| <a name="output_id"></a> [id](#output\_id) | The unique identifier of the Autopilot cluster. |
| <a name="output_location"></a> [location](#output\_location) | The location of the Autopilot cluster. |
| <a name="output_name"></a> [name](#output\_name) | The name of the Autopilot cluster. |
| <a name="output_public_endpoint_url"></a> [public\_endpoint\_url](#output\_public\_endpoint\_url) | The URL to use for master access. |
<!-- END_TF_DOCS -->
<!-- markdownlint-enable MD033 MD034 -->
