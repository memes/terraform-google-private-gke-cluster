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

# Optional additional repositories that the test service account will need access to
repositories = []
```

<!-- markdownlint-disable no-inline-html no-bare-urls -->
<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.2 |
| <a name="requirement_google"></a> [google](#requirement\_google) | >= 4.42 |
| <a name="requirement_local"></a> [local](#requirement\_local) | >= 2.2 |
| <a name="requirement_random"></a> [random](#requirement\_random) | >= 3.3 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_bastion"></a> [bastion](#module\_bastion) | memes/private-bastion/google | 2.3.3 |
| <a name="module_restricted_apis_dns"></a> [restricted\_apis\_dns](#module\_restricted\_apis\_dns) | memes/restricted-apis-dns/google | 1.0.1 |
| <a name="module_sa"></a> [sa](#module\_sa) | ../../modules/sa/ | n/a |
| <a name="module_vpc"></a> [vpc](#module\_vpc) | memes/multi-region-private-network/google | 1.0.0 |

## Resources

| Name | Type |
|------|------|
| [local_file.harness_tfvars](https://registry.terraform.io/providers/hashicorp/local/latest/docs/resources/file) | resource |
| [random_pet.prefix](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/pet) | resource |
| [random_shuffle.zones](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/shuffle) | resource |
| [google_compute_zones.zones](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/compute_zones) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_project_id"></a> [project\_id](#input\_project\_id) | n/a | `string` | n/a | yes |
| <a name="input_region"></a> [region](#input\_region) | n/a | `string` | n/a | yes |
| <a name="input_labels"></a> [labels](#input\_labels) | n/a | `map(string)` | `{}` | no |
| <a name="input_prefix"></a> [prefix](#input\_prefix) | n/a | `string` | `"pgke"` | no |
| <a name="input_repositories"></a> [repositories](#input\_repositories) | n/a | `list(string)` | `[]` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_bastion_ip_address"></a> [bastion\_ip\_address](#output\_bastion\_ip\_address) | n/a |
| <a name="output_prefix"></a> [prefix](#output\_prefix) | n/a |
| <a name="output_project_id"></a> [project\_id](#output\_project\_id) | n/a |
| <a name="output_service_account"></a> [service\_account](#output\_service\_account) | n/a |
| <a name="output_subnet_template"></a> [subnet\_template](#output\_subnet\_template) | n/a |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
<!-- markdownlint-enable no-inline-html no-bare-urls -->
