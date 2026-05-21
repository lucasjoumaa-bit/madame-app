"""
config.py — Madame de la Grande Bouche
All deployment settings loaded from environment variables / .env file.
End users never see or touch any of this.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Your trained model files ───────────────────────────────────────────────────
YOLO_MODEL_PATH     = os.getenv("YOLO_MODEL_PATH",     "")   # best.pt from yolo26s training
ANNOTATION_JSON_PATH= os.getenv("ANNOTATION_JSON_PATH","")   # instances_train2020_clean.json
ATTR_MODEL_PATH     = os.getenv("ATTR_MODEL_PATH",     "")   # attribute_classifier/best_model.pt
ATTR_MAP_PATH       = os.getenv("ATTR_MAP_PATH",       "")   # attribute_classifier/attribute_map.json
CHROMA_DB_PATH      = os.getenv("CHROMA_DB_PATH",      "./wardrobe_db")

# ── API Keys ───────────────────────────────────────────────────────────────────
GROQ_API_KEY        = os.getenv("GROQ_API_KEY",         "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY",  "")

# ── Detection thresholds ───────────────────────────────────────────────────────
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.30"))
IOU_THRESHOLD  = float(os.getenv("IOU_THRESHOLD",  "0.45"))

def validate() -> list[str]:
    issues = []
    if not YOLO_MODEL_PATH:
        issues.append("YOLO_MODEL_PATH not set")
    elif not os.path.exists(YOLO_MODEL_PATH):
        issues.append(f"YOLO_MODEL_PATH not found: {YOLO_MODEL_PATH}")
    if not GROQ_API_KEY:
        issues.append("GROQ_API_KEY not set")
    return issues
