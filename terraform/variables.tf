variable "env" {
  type        = string
  description = "Environment Name"
}

variable "project_region" {
  type        = string
  description = "Google Cloud Region"
}

variable "project_id" {
  type        = string
  description = "Project ID"
}

variable "endpoint_url" {
  type        = string
  description = "Cloud Run URL of Estimate Endpoint"
}
