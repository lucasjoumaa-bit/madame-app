"""
download_models.py — Madame de la Grande Bouche
Auto-downloads model files from Google Drive when running on Streamlit Cloud.
Called once at app startup before any model is loaded.
"""
import os
import requests

# ── Google Drive file IDs (extracted from share links) ───────────────────────
MODEL_FILES = {
    "best.pt":                       "16TxxwOUcT6sN0yMaC59MSD2-qghXS3WO",
    "instances_train2020_clean.json": "1fwr9wmodQqI66SmtvkiiGpFweEe1zHHR",
    "best_model.pt":                  "17UPUnoEFBc_HWslmK0w0CN9HJP0Uftgu",
    "attribute_map.json":             "1JJeqKuuxQZhn5htjRXnUnWTI3h6rsKwR",
}

# Models are downloaded to this folder inside the app
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


def _download_file(file_id: str, dest_path: str) -> None:
    """Download a file from Google Drive using its file ID."""
    URL = "https://drive.google.com/uc"
    session = requests.Session()

    response = session.get(URL, params={"id": file_id, "export": "download"}, stream=True)

    # Handle the virus-scan warning page for large files
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break

    if token:
        response = session.get(
            URL,
            params={"id": file_id, "export": "download", "confirm": token},
            stream=True,
        )

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)


def ensure_models_downloaded() -> dict[str, str]:
    """
    Downloads any missing model files from Google Drive.
    Returns a dict of {filename: local_path} for all 4 files.
    Safe to call multiple times — skips files that already exist.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    paths = {}

    for filename, file_id in MODEL_FILES.items():
        dest = os.path.join(MODELS_DIR, filename)
        paths[filename] = dest

        if os.path.exists(dest):
            print(f"[models] {filename} already present, skipping download")
            continue

        print(f"[models] Downloading {filename}...")
        try:
            _download_file(file_id, dest)
            size_mb = os.path.getsize(dest) / 1_048_576
            print(f"[models] {filename} downloaded ({size_mb:.1f} MB)")
        except Exception as e:
            print(f"[models] ERROR downloading {filename}: {e}")

    return paths
