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
  }
  backend "gcs" {
    # see: terraform/envs/(env_name)/(env_name).tfbackend
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers"
    ]
  }
}

resource "google_service_account" "interservices" {
  account_id   = "cloud-run-interservice-id"
  description  = "Identity used by a Cloud Run 'streamlit' (public) to call Cloud Run 'estimate' (private)."
  display_name = "cloud-run-interservice-id"
}

data "google_iam_policy" "private" {
  binding {
    role = "roles/run.invoker"
    members = [
      "serviceAccount:${google_service_account.interservices.email}",
    ]
  }
}
