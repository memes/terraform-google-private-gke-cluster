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

variable "gcr_location" {
  type    = string
  default = "US"
}
