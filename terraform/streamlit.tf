resource "google_cloud_run_v2_service" "streamlit" {
  name     = "${var.env}-streamlit"
  location = var.project_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    max_instance_request_concurrency = 5
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
    containers {
      image = "asia-northeast1-docker.pkg.dev/${var.project_id}/myrepo/streamlit:latest"
      env {
        name  = "ENDPOINT_URL"
        value = var.endpoint_url
      }
      ports {
        container_port = 8000
      }
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
    service_account = google_service_account.interservices.email
  }
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }
}

resource "google_cloud_run_v2_service_iam_policy" "noauth_streamlit" {
  location = google_cloud_run_v2_service.streamlit.location
  project  = google_cloud_run_v2_service.streamlit.project
  name     = google_cloud_run_v2_service.streamlit.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
