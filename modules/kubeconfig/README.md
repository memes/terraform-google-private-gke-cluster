# Private autopilot cluster

This Terraform module creates a private GKE Autopilot cluster.

<!-- markdownlint-disable MD033 MD034 MD060 -->
<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5 |
| <a name="requirement_google"></a> [google](#requirement\_google) | >= 7.1 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [google_container_cluster.cluster](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/container_cluster) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_cluster_id"></a> [cluster\_id](#input\_cluster\_id) | The fully-qualified identifier for the GKE cluster that the generated kubeconfig will be used with. | `string` | n/a | yes |
| <a name="input_cluster_name"></a> [cluster\_name](#input\_cluster\_name) | An optional cluster name to use in preference to the actual GKE cluster name in generated kubeconfig. If empty<br/>(default) the GKE cluster name will be used. | `string` | `null` | no |
| <a name="input_context_name"></a> [context\_name](#input\_context\_name) | An optional context name to use in preference to the GKE cluster name in generated kubeconfig. If empty (default) the<br/>GKE cluster name will be used. | `string` | `null` | no |
| <a name="input_proxy_url"></a> [proxy\_url](#input\_proxy\_url) | If not empty, a proxy field will be added to the generated kubeconfig containing this value. | `string` | `null` | no |
| <a name="input_use_private_endpoint"></a> [use\_private\_endpoint](#input\_use\_private\_endpoint) | By default the generated kubeconfig will use the GKE cluster's DNS endpoint with fallback to private IP endpoint if<br/>DNS endpoint is unknown. This flag can be used to force the use of private IP endpoint if both values are present.<br/><br/>NOTE: This flag will cause an error to be raised if set to true and a private IP endpoint is not available. | `bool` | `false` | no |
| <a name="input_user"></a> [user](#input\_user) | These values override defaults in the generated kubeconfig. If the name field is not empty its value will be the name<br/>of the user in the generated kubeconfig, instead of GKE cluster name (default). If the token field is not empty, the<br/>generated kubeconfig will use the provided token for authentication instead of GKE auth plugin. | <pre>object({<br/>    name  = optional(string)<br/>    token = optional(string)<br/>  })</pre> | `null` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_kubeconfig"></a> [kubeconfig](#output\_kubeconfig) | A generated Kubeconfig YAML that can be used to access the kubernetes master, using a supplied token or the `gke-gcloud-auth-plugin`. |
<!-- END_TF_DOCS -->
<!-- markdownlint-enable MD033 MD034 MD060 -->
