resource "google_storage_bucket" "function_src" {
  name                        = "${var.env}-${var.project_id}-function-src"
  location                    = var.project_region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
}

data "archive_file" "function_archive_estimate" {
  type        = "zip"
  source_dir  = "./python/estimate/"
  output_path = "./src/estimate.zip"
}

resource "google_storage_bucket_object" "function_src_package_estimate" {
  name   = "packages/estimate/functions_estimate_${data.archive_file.function_archive_estimate.output_md5}.zip"
  bucket = google_storage_bucket.function_src.name
  source = data.archive_file.function_archive_estimate.output_path
}

resource "google_cloudfunctions2_function" "estimate" {
  name        = "${var.env}-estimate"
  location    = var.project_region
  description = "get stock price data and estimate time-varing beta"

  build_config {
    runtime     = "python311"
    entry_point = "entry_point"
    source {
      storage_source {
        bucket = google_storage_bucket.function_src.name
        object = google_storage_bucket_object.function_src_package_estimate.name
      }
    }
  }

  lifecycle {
    replace_triggered_by = [google_storage_bucket_object.function_src_package_estimate]
  }

  service_config {
    max_instance_count = 1
    available_memory   = "512M"
    timeout_seconds    = 120
    ingress_settings   = "ALLOW_ALL"
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

# https://stackoverflow.com/questions/73994751/how-to-add-policy-to-restrict-google-cloud-function-invoker-using-terraform
resource "google_cloud_run_v2_service_iam_binding" "binding" {
  location = google_cloudfunctions2_function.estimate.location
  project  = google_cloudfunctions2_function.estimate.project
  name     = google_cloudfunctions2_function.estimate.name
  role     = "roles/run.invoker"
  members = [
    "allUsers"
  ]
}
