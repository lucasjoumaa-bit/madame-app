"""
config.py — Madame de la Grande Bouche
Settings loaded from environment variables / .env file.
On Streamlit Cloud, secrets are set in the dashboard instead of .env.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Detect if running on Streamlit Cloud ──────────────────────────────────────
IS_CLOUD = os.path.exists("/mount/src") or not os.path.exists(".env")

# ── Model file paths ───────────────────────────────────────────────────────────
if IS_CLOUD:
    # On cloud: models are downloaded to ./models/ at startup
    _MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
    YOLO_MODEL_PATH      = os.path.join(_MODELS_DIR, "best.pt")
    ANNOTATION_JSON_PATH = os.path.join(_MODELS_DIR, "instances_train2020_clean.json")
    ATTR_MODEL_PATH      = os.path.join(_MODELS_DIR, "best_model.pt")
    ATTR_MAP_PATH        = os.path.join(_MODELS_DIR, "attribute_map.json")
else:
    # Local: paths set in .env file
    YOLO_MODEL_PATH      = os.getenv("YOLO_MODEL_PATH",      "")
    ANNOTATION_JSON_PATH = os.getenv("ANNOTATION_JSON_PATH", "")
    ATTR_MODEL_PATH      = os.getenv("ATTR_MODEL_PATH",      "")
    ATTR_MAP_PATH        = os.getenv("ATTR_MAP_PATH",        "")

CHROMA_DB_PATH      = os.getenv("CHROMA_DB_PATH", "./wardrobe_db")

# ── API Keys ───────────────────────────────────────────────────────────────────
GROQ_API_KEY        = os.getenv("GROQ_API_KEY",        "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ── Detection thresholds ───────────────────────────────────────────────────────
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.30"))
IOU_THRESHOLD  = float(os.getenv("IOU_THRESHOLD",  "0.45"))

def validate() -> list[str]:
    issues = []
    if not GROQ_API_KEY:
        issues.append("GROQ_API_KEY not set")
    return issues
