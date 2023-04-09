# Setup

The Terraform in this folder will be executed before creating resources and can
be used to setup service accounts, service principals, etc, that are used by the
inspec-* verifiers.

## Configuration

Create a local `terraform.tfvars` file that configures the testing project
constraints.

```hcl
# The GCP project identifier to use
project_id  = "my-gcp-project"

# The single Compute Engine region where the resources will be created
region = "us-west1"

# Optional labels to add to resources
labels = {
    "owner" = "tester-name"
}

# Optional: Override default Google Container Registry location
gcr_location = "EU"

```

<!-- markdownlint-disable no-inline-html no-bare-urls -->
<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.2 |
| <a name="requirement_google"></a> [google](#requirement\_google) | >= 4.42 |
| <a name="requirement_http"></a> [http](#requirement\_http) | >= 3.2 |
| <a name="requirement_local"></a> [local](#requirement\_local) | >= 2.2 |
| <a name="requirement_random"></a> [random](#requirement\_random) | >= 3.3 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_bastion"></a> [bastion](#module\_bastion) | memes/private-bastion/google | 2.3.5 |
| <a name="module_restricted_apis_dns"></a> [restricted\_apis\_dns](#module\_restricted\_apis\_dns) | memes/restricted-apis-dns/google | 1.2.0 |
| <a name="module_vpc"></a> [vpc](#module\_vpc) | memes/multi-region-private-network/google | 2.0.0 |

## Resources

| Name | Type |
|------|------|
| [google_artifact_registry_repository.gar](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/artifact_registry_repository) | resource |
| [google_compute_firewall.bastion](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_firewall) | resource |
| [google_container_registry.gcr](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_registry) | resource |
| [local_file.harness_tfvars](https://registry.terraform.io/providers/hashicorp/local/latest/docs/resources/file) | resource |
| [random_pet.prefix](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/pet) | resource |
| [random_shuffle.zones](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/shuffle) | resource |
| [google_compute_zones.zones](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/compute_zones) | data source |
| [http_http.my_address](https://registry.terraform.io/providers/hashicorp/http/latest/docs/data-sources/http) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_project_id"></a> [project\_id](#input\_project\_id) | n/a | `string` | n/a | yes |
| <a name="input_region"></a> [region](#input\_region) | n/a | `string` | n/a | yes |
| <a name="input_gcr_location"></a> [gcr\_location](#input\_gcr\_location) | n/a | `string` | `"US"` | no |
| <a name="input_labels"></a> [labels](#input\_labels) | n/a | `map(string)` | `{}` | no |
| <a name="input_prefix"></a> [prefix](#input\_prefix) | n/a | `string` | `"pgke"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_bastion_ip_address"></a> [bastion\_ip\_address](#output\_bastion\_ip\_address) | n/a |
| <a name="output_bastion_public_ip_address"></a> [bastion\_public\_ip\_address](#output\_bastion\_public\_ip\_address) | n/a |
| <a name="output_gar_repo"></a> [gar\_repo](#output\_gar\_repo) | n/a |
| <a name="output_gcr_repo"></a> [gcr\_repo](#output\_gcr\_repo) | n/a |
| <a name="output_prefix"></a> [prefix](#output\_prefix) | n/a |
| <a name="output_project_id"></a> [project\_id](#output\_project\_id) | n/a |
| <a name="output_subnet_template"></a> [subnet\_template](#output\_subnet\_template) | n/a |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
<!-- markdownlint-enable no-inline-html no-bare-urls -->
