provider "google" {
  project = var.project_id
  region  = var.project_region
}
terraform {
  required_version = "~> 1.6.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.10.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4.1"
    }
  }
  backend "gcs" {
    # see: terraform/envs/(env_name)/(env_name).tfbackend
  }
}
