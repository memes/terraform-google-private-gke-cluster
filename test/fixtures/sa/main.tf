terraform {
  required_version = ">= 1.2"
}

module "test" {
  source       = "../../../modules/sa/"
  project_id   = var.project_id
  name         = var.name
  display_name = var.display_name
  description  = var.description
  repositories = var.repositories
}
