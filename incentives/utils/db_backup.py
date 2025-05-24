from google.cloud import storage
import os

APP_DB_PATH = "/app/db.sqlite3"
GCS_BUCKET_NAME = "san-incentive"
GCS_OBJECT_NAME = "database/db.sqlite3"

def upload_db_to_gcs():
    if not os.path.exists(APP_DB_PATH):
        return "DB file not found."

    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(GCS_OBJECT_NAME)
        blob.upload_from_filename(APP_DB_PATH)
        return "Upload successful to GCS."
    except Exception as e:
        return f"Upload failed: {e}"


