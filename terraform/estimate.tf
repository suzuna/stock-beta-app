resource "google_cloud_run_v2_service" "estimate" {
  name     = "${var.env}-estimate"
  location = var.project_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
    containers {
      image = "asia-northeast1-docker.pkg.dev/${var.project_id}/myrepo/estimate:latest"
      ports {
        container_port = 8080
      }
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }
}

resource "google_cloud_run_v2_service_iam_policy" "noauth_estimate" {
  location = google_cloud_run_v2_service.estimate.location
  project  = google_cloud_run_v2_service.estimate.project
  name     = google_cloud_run_v2_service.estimate.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
