# Private autopilot cluster

This Terraform module creates a private GKE Autopilot cluster.

<!-- markdownlint-disable MD033 MD034-->
<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.2 |
| <a name="requirement_google"></a> [google](#requirement\_google) | >= 4.52 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [google_container_cluster.cluster](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/container_cluster) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_cluster_id"></a> [cluster\_id](#input\_cluster\_id) | The fully-qualified identifier for the GKE cluster that the generated kubeconfig<br>will be used with. | `string` | n/a | yes |
| <a name="input_cluster_name"></a> [cluster\_name](#input\_cluster\_name) | An optional cluster name to use in preference to the actual GKE cluster name in<br>generated kubeconfig. Default value is null; kubeconfig will container the real<br>cluster name. | `string` | `null` | no |
| <a name="input_context_name"></a> [context\_name](#input\_context\_name) | An optional context name to use in preference to the GKE cluster name in<br>generated kubeconfig. Default value is null; the GKE cluster name will be used<br>for context name. | `string` | `null` | no |
| <a name="input_proxy_url"></a> [proxy\_url](#input\_proxy\_url) | If this is a non-empty value, the generated kubeconfig will set the proxy entry<br>to this value. Default is null. | `string` | `null` | no |
| <a name="input_use_private_endpoint"></a> [use\_private\_endpoint](#input\_use\_private\_endpoint) | Flag to trigger use of private IP address of master as the endpoint for the<br>generated kubeconf. Default is true; if set to false the master public IP will<br>be used if possible. | `bool` | `true` | no |
| <a name="input_user"></a> [user](#input\_user) | These values override defaults in the generated kubeconfig. If the name field<br>is not empty its value will be the name of the user in the generated kubeconfig,<br>instead of cluster name (default). If the token field is not empty, the generated<br>kubeconfig will use the provided token for authentication instead of GKE auth<br>plugin. | <pre>object({<br>    name  = string<br>    token = string<br>  })</pre> | `null` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_kubeconfig"></a> [kubeconfig](#output\_kubeconfig) | A generated Kubeconfig YAML that can be used to access the kubernetes master,<br>using a supplied token or the `gke-gcloud-auth-plugin`. |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
<!-- markdownlint-enable MD033 MD034 -->
