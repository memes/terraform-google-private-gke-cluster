variable "prefix" {
  type    = string
  default = "pgke"
}

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "labels" {
  type    = map(string)
  default = {}
}

variable "repositories" {
  type    = list(string)
  default = []
}
