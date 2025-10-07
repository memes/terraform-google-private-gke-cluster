variable "cluster_id" {
  type = string
}

variable "cluster_name" {
  type    = string
  default = null
}

variable "context_name" {
  type    = string
  default = null
}

variable "use_private_endpoint" {
  type    = bool
  default = true
}

variable "proxy_url" {
  type    = string
  default = null
}

variable "user" {
  type = object({
    name  = string
    token = string
  })
  default = null
}
