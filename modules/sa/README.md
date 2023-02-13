# SA

This module creates a GCP Service Account with minimal Cloud Operations monitoring
and logging roles assigned at the given project, and read-only access to the
GCR and/or Artifact Registry repositories.

> NOTE: This is an opinionated module; use Google's [Service Account module] to
> create a service account with more flexible role assignments, etc.

<!-- markdownlint-disable MD033 MD034-->
<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.2 |
| <a name="requirement_google"></a> [google](#requirement\_google) | >= 4.42 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [google_artifact_registry_repository_iam_member.ar_repo](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/artifact_registry_repository_iam_member) | resource |
| [google_project_iam_member.roles](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_iam_member) | resource |
| [google_service_account.sa](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/service_account) | resource |
| [google_storage_bucket_iam_member.gcr_repo](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket_iam_member) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_name"></a> [name](#input\_name) | The name to give to the service account. | `string` | n/a | yes |
| <a name="input_project_id"></a> [project\_id](#input\_project\_id) | The GCP project identifier where the private GKE cluster will be created. | `string` | n/a | yes |
| <a name="input_description"></a> [description](#input\_description) | An optional description to apply to the generated service account. The default<br>value describes the purpose of the service account. | `string` | `"A Terraform generated Service Account suitable for use by GKE nodes. The service\naccount is intended to have minimal roles required to log and report base\nmetrics to Google Cloud Operations.\n"` | no |
| <a name="input_display_name"></a> [display\_name](#input\_display\_name) | An optional display name to associate with the generated service account. Default<br>is 'Generated GKE Service Account'. | `string` | `"Generated GKE Service Account"` | no |
| <a name="input_repositories"></a> [repositories](#input\_repositories) | An optional list of GCR and/or GAR repositories. If provided, the generated<br>service account will be given the appropriate GCR or GAR read-only access role<br>to the repos. | `list(string)` | `[]` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_email"></a> [email](#output\_email) | The email address of the service account. |
| <a name="output_id"></a> [id](#output\_id) | The fully-qualified service account identifier. |
| <a name="output_member"></a> [member](#output\_member) | The service account identity for use with IAM declarations. E.g. `serviceAccount:email`<br>where email is the value of output `email`. |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
<!-- markdownlint-enable MD033 MD034 -->

[Service Account module]: https://registry.terraform.io/modules/terraform-google-modules/service-accounts/google/latest
