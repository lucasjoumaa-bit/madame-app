import os
import requests

MODEL_FILES = {
    "best.pt":                       "16TxxwOUcT6sN0yMaC59MSD2-qghXS3WO",
    "instances_train2020_clean.json": "1fwr9wmodQqI66SmtvkiiGpFweEe1zHHR",
    "best_model.pt":                  "17UPUnoEFBc_HWslmK0w0CN9HJP0Uftgu",
    "attribute_map.json":             "1JJeqKuuxQZhn5htjRXnUnWTI3h6rsKwR",
}

MODELS_DIR = "/tmp/madame_models"

def _download_file(file_id, dest_path):
    URL = "https://drive.google.com/uc"
    session = requests.Session()
    response = session.get(URL, params={"id": file_id, "export": "download"}, stream=True)
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break
    if token:
        response = session.get(URL, params={"id": file_id, "export": "download", "confirm": token}, stream=True)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

def ensure_models_downloaded():
    os.makedirs(MODELS_DIR, exist_ok=True)
    paths = {}
    for filename, file_id in MODEL_FILES.items():
        dest = os.path.join(MODELS_DIR, filename)
        paths[filename] = dest
        if os.path.exists(dest):
            continue
        print(f"Downloading {filename}...")
        _download_file(file_id, dest)
        print(f"Done: {filename}")
    return paths
